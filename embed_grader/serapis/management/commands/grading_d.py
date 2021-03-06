import os
import sys
import requests
import datetime
import time
import subprocess
import json
import pytz
import random
import threading
import traceback

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from embed_grader import settings
from serapis.models import *
from serapis.utils import file_schema
from serapis.utils import send_mail_helper
from serapis.utils import submission_helper
from serapis.utils import testbed_helper
from serapis.utils import team_helper
from serapis.utils.grading_scheduler_heartbeat import GradingSchedulerHeartbeat

K_TESTBED_INVALIDATION_OFFLINE_SEC = 30
K_TESTBED_INVALIDATION_REMOVE_SEC = 10 * 60

K_GRADING_GRACE_PERIOD_SEC = 60

K_CYCLE_DURATION_SEC = 3


class Command(BaseCommand):
    help = 'Daemon of sending grading tasks to backend'

    just_printed_idle_msg = False
    idle_cnt = 0
    print_lock = threading.Lock()

    def _printAlive(self):
        self.print_lock.acquire()
        self.idle_cnt += 1
        if self.idle_cnt > 0:
            sys.stdout.write('.')
            sys.stdout.flush()
            self.just_printed_idle_msg = True
        self.print_lock.release()

    def _printMessage(self, msg):
        self.print_lock.acquire()
        now = timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE))
        time_str = now.strftime("%H:%M:%S")
        if self.just_printed_idle_msg:
            print()
            self.just_printed_idle_msg = False
            self.idle_cnt = 0
        display_msg = '%s - %s' % (time_str, msg)
        print(display_msg)
        log_msg = '[%5d] %s' % (os.getpid(), display_msg)
        with open(settings.GRADING_SCHEDULER_LOG_PATH, 'a') as fo:
            fo.write(log_msg + '\n')
        self.print_lock.release()

    def _schemaFiles2postFiles(self, dict_schema_files):
        postFiles = {}
        for schema_name in dict_schema_files:
            field_name = 'file_' + schema_name
            postFiles[field_name] = ('filename',
                    open(dict_schema_files[schema_name].file.path, 'rb'), 'text/plain')
        return postFiles

    def _grade(self, testbed, task):
        TaskGradingStatusFile.objects.filter(
                task_grading_status_fk=task).update(file=None)

        self._printMessage('Send job for grading: task %d, sub=%s, hw_task=%s, hw=%s, course=%s' % (
            task.id,
            task.submission_fk,
            task.assignment_task_fk,
            task.submission_fk.assignment_fk,
            task.submission_fk.assignment_fk.course_fk.course_code))

        try:
            submission = task.submission_fk
            files = self._schemaFiles2postFiles(file_schema
                    .get_dict_schema_name_to_submission_schema_files(submission))
            
            assignment_task = task.assignment_task_fk
            files.update(self._schemaFiles2postFiles(file_schema
                    .get_dict_schema_name_to_assignment_task_schema_files(assignment_task)))

            data = {
                    'execution_time': task.assignment_task_fk.execution_duration,
                    'secret_code': testbed.secret_code,
            }

            url = 'http://' + testbed.ip_address + '/tb/grade_assignment/'
            
            r = requests.post(url, data=data, files=files)
            if r.status_code != 200:  # testbed is not available
                testbed_helper.abort_task(testbed, set_testbed_status=Testbed.STATUS_BUSY)
                self._printMessage('Testbed id=%d abort task %d' % (testbed.id, task.id))
                
        except:
            testbed_helper.abort_task(testbed, set_testbed_status=Testbed.STATUS_OFFLINE)
            self._printMessage('Testbed id=%d goes offline since something goes wrong:'
                    % testbed.id)
            exc_type, exc_value, exc_tb = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_tb)

    def handle(self, *args, **options):
        # heartbeat initialization
        heartbeat = GradingSchedulerHeartbeat()

        # timer initialization
        timer_testbed_invalidation_offline = 0
        timer_testbed_invalidation_remove = 0
        timer_submission_invalidation = 0

        while True:
            # at any given time, if we detect another grading scheduler running, this scheulder
            # should abort. The new scheduler should respawn.
            if GradingSchedulerHeartbeat.detect_if_other_scheduler_exists():
                self._printMessage('Found other scheduler, terminate self')
                exit(0)

            # leave a heartbeat
            heartbeat.send_heartbeat()

            timer_testbed_invalidation_offline -= K_CYCLE_DURATION_SEC
            timer_testbed_invalidation_remove -= K_CYCLE_DURATION_SEC
            timer_submission_invalidation -= K_CYCLE_DURATION_SEC

            now = timezone.now()

            #
            # invalidation
            #

            # remove testbed records in database when timeout
            if timer_testbed_invalidation_remove <= 0:
                threshold_time = now - datetime.timedelta(0, K_TESTBED_INVALIDATION_REMOVE_SEC)
                testbed_list = Testbed.objects.filter(report_time__lt=threshold_time)
                for testbed in testbed_list:
                    # make sure that no task is associated with this testbed
                    testbed_helper.abort_task(testbed, set_testbed_status=Testbed.STATUS_OFFLINE,
                            enforce_task_present=False)
                    self._printMessage('Testbed id=%d removed from testbed' % (testbed.id))
                testbed_list.delete()
                timer_testbed_invalidation_remove = K_TESTBED_INVALIDATION_REMOVE_SEC

            # set testbed to offline in database when timeout
            if timer_testbed_invalidation_offline <= 0:
                threshold_time = now - datetime.timedelta(0, K_TESTBED_INVALIDATION_OFFLINE_SEC)
                testbed_list = Testbed.objects.filter(
                        ~Q(status=Testbed.STATUS_OFFLINE),
                        report_time__lt=threshold_time,
                )
                for testbed in testbed_list:
                    self._printMessage('Set testbed id=%d offline' % (testbed.id))
                    graded_task = testbed.task_being_graded
                    if graded_task:
                        self._printMessage('Abort the grading task id=%d and reset to pending'
                                % (graded_task.id))
                    testbed_helper.abort_task(testbed, set_testbed_status=Testbed.STATUS_OFFLINE,
                            enforce_task_present=False)
                
                timer_testbed_invalidation_offline = K_TESTBED_INVALIDATION_OFFLINE_SEC

            # Since hardware front end does not keep track of the status of grading, what can
            # happen is that somehow some hardware (either hardware engine or DUT) go wrong but
            # they are not aware the error. If the testbed passed the grading deadline without
            # reporting grading results, we abort the grading task and reset the status
            testbed_list = Testbed.objects.filter(
                    status=Testbed.STATUS_BUSY,
                    grading_deadline__lt=now)
            for testbed in testbed_list:
                graded_task = testbed.task_being_graded
                self._printMessage('Testbed id=%d passed the grading deadline' % testbed.id)
                if graded_task:
                    self._printMessage('Abort the grading task id=%d and reset to pending'
                            % (graded_task.id))
                else:
                    self._printMessage('Wait, no grading task is found, why being busy then')
                testbed_helper.abort_task(testbed, set_testbed_status=Testbed.STATUS_AVAILABLE,
                        enforce_task_present=False)

            #TODO(#160): Remove the following code when the issue is resolved
            # What happens right now is that a testbed sometimes mysteriously detach the task
            # which the testbed should be grading, leaving the task hanging on there and showing
            # status as executing. The following is to clear this when orphan task grading status
            # is found
            executing_task_grading_status_list = TaskGradingStatus.objects.filter(
                    grading_status=TaskGradingStatus.STAT_EXECUTING)
            for task in executing_task_grading_status_list:
                if Testbed.objects.filter(task_being_graded=task).count() == 0:
                    self._printMessage('Orphan test grading status is found (id=%d)' % task.id)
                    task.grading_status = TaskGradingStatus.STAT_PENDING
                    task.save()

            #
            # task assignment
            #

            # task assignment policy: choose an available tesbed, find one task which can be
            # executed on this testbed, and do it
            testbed_list = Testbed.objects.filter(status=Testbed.STATUS_AVAILABLE)
            for testbed in testbed_list:
                # We choose a task whose belonged submission has the smallest execution scope.
                task_list = (TaskGradingStatus.objects
                        .filter(grading_status=TaskGradingStatus.STAT_PENDING,
                            assignment_task_fk__assignment_fk__testbed_type_fk=testbed.testbed_type_fk)
                        .order_by('submission_fk__task_scope', 'submission_fk', 'id'))

                if task_list.count() == 0:
                    # next testbed
                    continue

                chosen_task = task_list[0]

                duration = (chosen_task.assignment_task_fk.execution_duration
                        + K_GRADING_GRACE_PERIOD_SEC)
                testbed_helper.grade_task(
                        testbed, chosen_task, duration, force_detach_currently_graded_task=True)

                threading.Thread(target=self._grade, name=('id=%s' % testbed.ip_address),
                        kwargs={'testbed': testbed, 'task': chosen_task}).start()


            #
            # output checking
            #
            grading_task_list = TaskGradingStatus.objects.filter(
                    grading_status=TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED)
            for grading_task in grading_task_list:
                if grading_task.execution_status == TaskGradingStatus.EXEC_SEG_FAULT:
                    submission_helper.update_task_grading_status(
                            grading_task,
                            grading_status=TaskGradingStatus.STAT_FINISH,
                            points=0.0,
                    )
                else:
                    assignment_task = grading_task.assignment_task_fk
                    submission = grading_task.submission_fk
                    grading_script_path = assignment_task.grading_script.path
                    cmd = ['python3', grading_script_path]
                    schema_files = {}
                    schema_files.update(file_schema.
                            get_dict_schema_name_to_assignment_task_schema_files(assignment_task))
                    schema_files.update(file_schema.
                            get_dict_schema_name_to_submission_schema_files(submission))
                    schema_files.update(file_schema.
                            get_dict_schema_name_to_task_grading_status_schema_files(grading_task))
                    for field in schema_files:
                        cmd.append('%s:%s' % (field, schema_files[field].file.path))

                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                    try:
                        result_pack = json.loads(proc.communicate()[0].decode('ascii'))
                        normalized_score = float(result_pack['score'])
                        normalized_score = min(1., max(0., normalized_score))
                        grading_task.grading_detail.save(
                                'description.txt', ContentFile(result_pack['detail']))
                        points = assignment_task.points * normalized_score
                        submission_helper.update_task_grading_status(
                                grading_task,
                                grading_status=TaskGradingStatus.STAT_FINISH,
                                points=points,
                                status_update_time=timezone.now(),
                        )
                    except (ValueError):
                        submission_helper.update_task_grading_status(
                                grading_task,
                                grading_status=TaskGradingStatus.STAT_PENDING,
                                points=0.0,
                        )
                        exc_type, exc_value, exc_tb = sys.exc_info()
                        traceback.print_exception(exc_type, exc_value, exc_tb)

                self._printMessage(
                        'Graded task=%d, status=%s, pts=%f, sub=%s, hw_task=%s, hw=%s' % (
                                grading_task.id, grading_task.get_grading_status_display(),
                                grading_task.points, grading_task.submission_fk,
                                grading_task.assignment_task_fk,
                                grading_task.submission_fk.assignment_fk))

                num_graded_tasks = len(TaskGradingStatus.objects.filter(
                        Q(grading_status=TaskGradingStatus.STAT_FINISH)
                        | Q(grading_status=TaskGradingStatus.STAT_INTERNAL_ERROR),
                        submission_fk=grading_task.submission_fk))
                num_assignment_tasks = len(TaskGradingStatus.objects.filter(
                        submission_fk=grading_task.submission_fk))
                self._printMessage('num_graded_tasks=%d, num_assignment_tasks=%d' % (
                        num_graded_tasks, num_assignment_tasks))
                if num_graded_tasks == num_assignment_tasks:
                    submission = grading_task.submission_fk
                    submission.status = Submission.STAT_GRADED
                    submission.save()

                    # send email to the student
                    #subject = 'Your submission has been graded (ID:%d)' % submission.id
                    #team = submission.team_fk
                    #recipient_email_list = [tm.user_fk.email
                    #        for tm in team_helper.get_team_members(team)]
                    #context = {
                    #        'user': submission.student_fk,
                    #        'submission': submission,
                    #        'assignment': submission.assignment_fk,
                    #}
                    #send_mail_helper.send_by_template(
                    #        subject=subject,
                    #        recipient_email_list=recipient_email_list,
                    #        template_path='serapis/email/grading_done_email.html',
                    #        context_dict=context,
                    #)

            # go to sleep
            self._printAlive()
            time.sleep(K_CYCLE_DURATION_SEC)

