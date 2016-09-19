import requests
import datetime
import time
import subprocess

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from serapis.models import *


K_TESTBED_INVALIDATION_OFFLINE_SEC = 30
K_TESTBED_INVALIDATION_REMOVE_SEC = 10 * 60
K_SUBMISSION_INVALIDATION_SEC = 30

K_CYCLE_DURATION_SEC = 5


class Command(BaseCommand):
    help = 'Daemon of sending grading tasks to backend'

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
            if timer_testbed_invalidation_remove <= 0:
                threshold_time = now - datetime.timedelta(0, K_TESTBED_INVALIDATION_REMOVE_SEC)
                testbed_list = Testbed.objects.filter(report_time__lt=threshold_time)
                for testbed in testbed_list:
                    print('Testbed id=%d removed from testbed' % (testbed.id))
                testbed_list.delete()
                timer_testbed_invalidation_remove = K_TESTBED_INVALIDATION_REMOVE_SEC

            if timer_testbed_invalidation_offline <= 0:
                threshold_time = now - datetime.timedelta(0, K_TESTBED_INVALIDATION_OFFLINE_SEC)
                testbed_list = Testbed.objects.filter(report_time__lt=threshold_time)
                for testbed in testbed_list:
                    print('Set testbed id=%d offline' % (testbed.id))
                testbed_list.update(status=Testbed.STATUS_OFFLINE)
                timer_testbed_invalidation_offline = K_TESTBED_INVALIDATION_OFFLINE_SEC

            if timer_submission_invalidation <= 0:
                threshold_time = now - datetime.timedelta(0, K_SUBMISSION_INVALIDATION_SEC)
                grading_task_list = TaskGradingStatus.objects.filter(
                        grading_status=TaskGradingStatus.STAT_EXECUTING,
                        status_update_time__lt=threshold_time
                        )
                for grading_task in grading_task_list:
                    print('Reset stale grading task id=%d' % (grading_task.id))
                grading_task_list.update(grading_status=TaskGradingStatus.STAT_PENDING)
                timer_submission_invalidation = K_SUBMISSION_INVALIDATION_SEC

            #TODO: delete the following thing, currently for debugging
            #task_list = TaskGradingStatus.objects.all()
            #n = len(task_list)
            #t = task_list[n-1]
            #t.grading_status = TaskGradingStatus.STAT_PENDING
            #t.save()
            
            #
            # task assignment
            #
            while True:
                #TODO: I also need to check the testbed type
                testbed_list = Testbed.objects.filter(status=Testbed.STATUS_AVAILABLE)
                if not testbed_list:
                    break
                
                task_list = TaskGradingStatus.objects.filter(grading_status=TaskGradingStatus.STAT_PENDING)
                if not task_list:
                    break
                
                testbed = testbed_list[0]
                task = task_list[0]

                testbed.status = Testbed.STATUS_BUSY
                testbed.task_being_graded = task
                testbed.save()

                task.grading_status = TaskGradingStatus.STAT_EXECUTING
                task.status_update_time = timezone.now()
                task.save()

                print('grading grading task id=%d using testbed hardware_id=%s' % (task.id, testbed.unique_hardware_id))

                try:
                    # upload firmware command
                    filename = task.submission_id.file.path
                    files = {'firmware': ('filename', open(filename, 'rb'), 'text/plain')}
                    url = 'http://' + testbed.ip_address + '/dut/program/'
                    r = requests.post(url, data={'dut': testbed.unique_hardware_id}, files=files)

                    # upload input waveform command
                    filename = task.assignment_task_id.test_input.path
                    files = {'waveform': ('filename', open(filename, 'rb'), 'text/plain')}
                    url = 'http://' + testbed.ip_address + '/tester/waveform/'
                    r = requests.post(url, data={'dut': testbed.unique_hardware_id}, files=files)

                    # reset command
                    url = 'http://' + testbed.ip_address + '/tester/reset/'
                    r = requests.post(url)
                    
                    # start command
                    url = 'http://' + testbed.ip_address + '/tester/start/'
                    r = requests.post(url)

                except requests.exceptions.ConnectionError:
                    testbed.status = Testbed.STATUS_OFFLINE
                    testbed.save()
                    task.grading_status = TaskGradingStatus.STAT_PENDING
                    task.save()



            #
            # output checking
            #
            grading_task_list = TaskGradingStatus.objects.filter(grading_status=TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED)
            for grading_task in grading_task_list:
                if grading_task.execution_status == TaskGradingStatus.EXEC_SEG_FAULT:
                    grading_task.grading_status = TaskGradingStatus.STAT_FINISH
                    grading_task.points = 0.0
                else:
                    assignment_task = grading_task.assignment_task_id
                    grading_script_filename = assignment_task.grading_script.path
                    output_filename = grading_task.output_file.path
                    proc = subprocess.Popen(
                            ['python3', grading_script_filename, output_filename], 
                            stdout=subprocess.PIPE)
                    try:
                        normalized_score = float(proc.communicate()[0].decode('ascii'))
                        normalized_score = min(1., max(0., normalized_score))
                        grading_task.grading_status = TaskGradingStatus.STAT_FINISH
                        grading_task.points = assignment_task.points * normalized_score
                    except ValueError:
                        grading_task.grading_status = TaskGradingStatus.STAT_INTERNAL_ERROR
                        grading_task.points = 0.0

                grading_task.status_update_time = timezone.now()
                grading_task.save()
                print('Graded task %d, status=%s, pts=%f' % (
                    grading_task.id, grading_task.get_grading_status_display(), grading_task.points))

                num_graded_tasks = len(TaskGradingStatus.objects.filter(
                        Q(grading_status=TaskGradingStatus.STAT_FINISH)
                        | Q(grading_status=TaskGradingStatus.STAT_INTERNAL_ERROR),
                        submission_id=grading_task.submission_id))
                num_assignment_tasks = len(AssignmentTask.objects.filter(assignment_id=grading_task.submission_id.assignment_id))
                print('num_graded_tasks=%d, num_assignment_tasks=%d' % (num_graded_tasks, num_assignment_tasks))
                if num_graded_tasks == num_assignment_tasks:
                    s = grading_task.submission_id
                    s.status = Submission.STAT_GRADED
                    s.save()
            
            # go to sleep
            print('go to sleep')
            time.sleep(K_CYCLE_DURATION_SEC)
