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

from serapis.models import *
from serapis.utils import file_schema
from serapis.utils import send_email_helper


K_TESTBED_INVALIDATION_OFFLINE_SEC = 30
K_TESTBED_INVALIDATION_REMOVE_SEC = 10 * 60

K_GRADING_GRACE_PERIOD_SEC = 600

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
        time_str = timezone.now().astimezone(pytz.timezone('US/Pacific')).strftime("%H:%M:%S")
        if self.just_printed_idle_msg:
            print()
            self.just_printed_idle_msg = False
            self.idle_cnt = 0
        final_msg = '%s - %s' % (time_str, msg)
        print(final_msg)
        with open('/tmp/embed_grader_scheduler.log', 'a') as fo:
            fo.write(final_msg + '\n')
        self.print_lock.release()

    def _schemaFiles2postFiles(self, dict_schema_files):
        postFiles = {}
        for schema_name in submission_files:
            postFiles[schema_name] = ('filename',
                    open(submission_files[schema_name].file.path, 'rb'), 'text/plain')
        return postFiles

    def _grade(self, testbed, task):
        TaskGradingStatusFile.objects.filter(
                task_grading_status_id=task).update(file=None)

        self._printMessage('Executing task %d, sub=%s, hw_task=%s, hw=%s, course=%s' % (
            task.id,
            task.submission_id,
            task.assignment_task_id,
            task.submission_id.assignment_id,
            task.submission_id.assignment_id.course_id.course_code))

        try:
            submission = task.submission_id
            files = _schemaFiles2postFiles(file_schema
                    .get_dict_schema_name_to_submission_schema_files(submission))
            
            assignment_task = task.assignment_task_id
            files.update(_schemaFiles2postFiles(file_schema
                    .get_dict_schema_name_to_assignment_task_schema_files(assignment_task)))

            data = {'execution_time': task.execution_duration}

            url = 'http://' + testbed.ip_address + '/tb/grade_assignment/'
            
            r = requests.post(url, data=data, files=files)
            if r.status_code != 200  # testbed is not available
                task.grading_status = TaskGradingStatus.STAT_PENDING
                task.save()
                testbed.task_being_graded = None
                testbed.save()
                self._printMessage('Testbed id=%d abort task %d' % (testbed.id, task.id))
                
        except:
            testbed.status = Testbed.STATUS_OFFLINE
            testbed.save()
            task.grading_status = TaskGradingStatus.STAT_PENDING
            task.save()
            self._printMessage('Testbed id=%d goes offline since something goes wrong:'
                    % testbed.id)
            exc_type, exc_value, exc_tb = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_tb)

    def handle(self, *args, **options):
        timer_testbed_invalidation_offline = 0
        timer_testbed_invalidation_remove = 0
        timer_submission_invalidation = 0

        while True:
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
                    testbed.status = Testbed.STATUS_OFFLINE
                    graded_task = testbed.task_being_graded
                    testbed.task_being_graded = None
                    testbed.save()
                    if graded_task:
                        graded_task.grading_status = TaskGradingStatus.STAT_PENDING
                        graded_task.save()
                        self._printMessage('Abort the grading task id=%d and reset to pending'
                                % (graded_task.id))
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
                testbed.status = Testbed.STATUS_AVAILABLE
                testbed.task_being_graded = None
                testbed.save()
                self._printMessage('Testbed id=%d passed the grading deadline' % testbed.id)
                if graded_task:
                    graded_task.grading_status = TaskGradingStatus.STAT_PENDING
                    graded_task.save()
                    self._printMessage('Abort the grading task id=%d and reset to pending'
                            % (graded_task.id))
                else:
                    self._printMessage('Wait, no grading task is found, why being busy then')

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
                            assignment_task_id__assignment_id__testbed_type_id=testbed)
                        .order_by('submission_id__task_scope', 'submission_id', 'id'))

                if task_list.count() == 0:
                    # next testbed
                    continue

                chosen_task = task_list[0]

                testbed.status = Testbed.STATUS_BUSY
                testbed.task_being_graded = chosen_task
                duration = (chosen_task.assignment_task_id.execution_duration
                        + K_GRADING_GRACE_PERIOD_SEC)
                testbed.grading_deadline = timezone.now() + datetime.timedelta(0, duration)
                testbed.secret_code = str(timezone.now())
                testbed.save()

                chosen_task.grading_status = TaskGradingStatus.STAT_EXECUTING
                chosen_task.status_update_time = timezone.now()
                chosen_task.points = 0.
                chosen_task.grading_detail = None
                chosen_task.save()

                threading.Thread(target=self._grade, name=('id=%s' % testbed.unique_hardware_id),
                        kwargs={'testbed': testbed, 'task': chosen_task}).start()


            #
            # output checking
            #
            grading_task_list = TaskGradingStatus.objects.filter(
                    grading_status=TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED)
            for grading_task in grading_task_list:
                if grading_task.execution_status == TaskGradingStatus.EXEC_SEG_FAULT:
                    grading_task.grading_status = TaskGradingStatus.STAT_FINISH
                    grading_task.points = 0.0
                else:
                    assignment_task = grading_task.assignment_task_id
                    grading_script_path = assignment_task.grading_script.path
                    cmd = ['python3', grading_script_path]
                    task_grading_status_files = (file_schema.
                            get_dict_schema_name_to_task_grading_statusschema_files(grading_task))
                    for field in task_grading_status_files:
                        cmd.append('%s:%s' % (field, task_grading_status_files[field].file.path))

                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                    try:
                        result_pack = json.loads(proc.communicate()[0].decode('ascii'))
                        normalized_score = float(result_pack['score'])
                        normalized_score = min(1., max(0., normalized_score))
                        grading_task.grading_detail.save(
                                'description.txt', ContentFile(result_pack['detail']))
                        grading_task.grading_status = TaskGradingStatus.STAT_FINISH
                        grading_task.points = assignment_task.points * normalized_score
                    except (ValueError):
                        #grading_task.grading_status = TaskGradingStatus.STAT_INTERNAL_ERROR
                        grading_task.grading_status = TaskGradingStatus.STAT_PENDING
                        grading_task.points = 0.0
                        exc_type, exc_value, exc_tb = sys.exc_info()
                        traceback.print_exception(exc_type, exc_value, exc_tb)

                grading_task.status_update_time = timezone.now()
                grading_task.save()
                self._printMessage(
                        'Graded task=%d, status=%s, pts=%f, sub=%s, hw_task=%s, hw=%s' % (
                                grading_task.id, grading_task.get_grading_status_display(),
                                grading_task.points, grading_task.submission_id,
                                grading_task.assignment_task_id,
                                grading_task.submission_id.assignment_id))

                num_graded_tasks = len(TaskGradingStatus.objects.filter(
                        Q(grading_status=TaskGradingStatus.STAT_FINISH)
                        | Q(grading_status=TaskGradingStatus.STAT_INTERNAL_ERROR),
                        submission_id=grading_task.submission_id))
                num_assignment_tasks = len(AssignmentTask.objects.filter(
                        assignment_id=grading_task.submission_id.assignment_id))
                self._printMessage('num_graded_tasks=%d, num_assignment_tasks=%d' % (
                        num_graded_tasks, num_assignment_tasks))
                if num_graded_tasks == num_assignment_tasks:
                    submission = grading_task.submission_id
                    submission.status = Submission.STAT_GRADED
                    submission.save()

                    # send email to the student
                    subject = 'Your submission has been graded (ID:%d)' % submission.id
                    context = {
                            'user': submission.student_id,
                            'submission': submission,
                            'assignment': submission.assignment_id,
                    }
                    send_email_helper.send_by_template(
                            subject=subject,
                            recipient_email_list=[submission.student_id.email],
                            template_path='serapis/email/grading_done_email.html',
                            context=context,
                    )

            # go to sleep
            self._printAlive()
            time.sleep(K_CYCLE_DURATION_SEC)

