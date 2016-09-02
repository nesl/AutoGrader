import requests
import datetime

from django.core.management.base import BaseCommand

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

            now = datetime.datetime.now()

            #
            # invalidation
            #
            if timer_testbed_invalidation_remove <= 0:
                threshold_time = now - datetime.deltatime(0, K_TESTBED_INVALIDATION_REMOVE_SEC)
                Testbed.objects.filter(report_time__gt=threshold_time).delete()

            if timer_testbed_invalidation_offline <= 0:
                threshold_time = now - datetime.deltatime(0, K_TESTBED_INVALIDATION_OFFLINE_SEC)
                Testbed.objects.filter(report_time__gt=threshold_time).update(status=STATUS_OFFLINE)

            if timer_submission_invalidation <= 0:
                threshold_time = now - datetime.deltatime(0, K_SUBMISSION_INVALIDATION_SEC)
                TaskGradingStatus.objects.filter(
                        grading_status=TaskGradingStatus.STAT_EXECUTING,
                        status_update_time__gt=threshold_time
                        ).update(grading_status=TaskGradingStatus.STAT_PENDING)

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
                testbed.save()

                task.grading_status = TaskGradingStatus.STAT_EXECUTING
                task.status_update_time = datetime.datetime.now()
                task.save()

                filename = task.submission_id.file  #TODO: path?

                files = {'firmware': ('filename', open(filename, 'rb'), 'text/plain')}
                r = requests.post(testbed.ip_address + 'dut/program/', data={'dut': 1}, files=files)

            #
            # output checking
            #
            task_list = TaskGradingStatus.objects.filter(grading_status=TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED)
            for task in task_list:
                pass
                #TODO: execute the grading script
                #TODO: update database

            # Sleep for n seconds
            
