from django.db import transaction

from serapis.models import *

from serapis.utils import submission_helper


def abort_task(testbed, set_status=Testbed.STATUS_AVAILABLE,
        tolerate_task_is_not_present=False, check_task_status_is_executing=True):
    """
    Paremeter:
      - set_status: The status going to be set for this testbed
      - tolerate_task_is_not_present: True if the grading task does not have to be present
      - check_testbed_status_is_executing: True to check the status of the task is executing.
            Will have no effect if tolerate_task_is_not_present is True.
    """
    check_task_status_is_executing &= not tolerate_task_is_not_present

    task = testbed.task_being_graded
    if not tolerate_task_is_not_present:
        if not task:
            raise Exception('No task to abort')
    if check_task_status_is_executing:
        if task.grading_status != TaskGradingStatus.STAT_EXECUTING:
            raise Exception('Status of the graded task is not executing')
            
    with transaction.atomic():
        if task:
            submission_helper.update_task_grading_status(
                    task, grading_status=TaskGradingStatus.STAT_PENDING)
        testbed.task_being_graded = None
        testbed.status = set_status
        testbed.secret_code = ''
        testbed.save()

def grade_task(testbed, chosen_task, duration, force_detach_currently_graded_task=False,
        check_testbed_status_is_available=True, check_task_status_is_pending=True):
    """
    Paremeter:
      - chosen_task: TaskGradingStatus, the task to be graded
      - duration: Float, how much time the task can be executed
      - force_detach_currently_grading_task: True to abort the currently graded task if
            present. Otherwise an exception is raised if task_being_graded is not None.
      - check_testbed_status_available: True if want to check this testbed is available
      - check_task_status_pending: True if want to check the status of chosen_task is pending
    """
    if force_detach_currently_graded_task:
        if testbed.task_being_graded:
            abort_task(set_status=testbed.status, check_task_status_is_executing=False)
    if testbed.task_being_graded:
        raise Exception('This testbed is still grading one task')
    if check_testbed_status_is_available:
        if testbed.status != Testbed.STATUS_AVAILABLE:
            raise Exception('Request grading a task but status is not available')
    if check_task_status_is_pending:
        if chosen_task.grading_status != TaskGradingStatus.STAT_PENDING:
            raise Exception('Requested task is not in pending status')
    
    with transaction.atomic():
        testbed.status = Testbed.STATUS_BUSY
        testbed.task_being_graded = chosen_task
        testbed.grading_deadline = timezone.now() + datetime.timedelta(0, duration)
        testbed.secret_code = str(timezone.now())
        testbed.save()

        submission_helper.update_task_grading_status(
                chosen_task,
                grading_status=TaskGradingStatus.STAT_EXECUTING,
                status_update_time=timezone.now(),
                points=0.,
                grading_detail=None,
        )

def finish_grading(testbed, task_execution_status):
    task = testbed.task_being_graded
    if not task:
        raise Exception('No grading task is associated with this testbed')

    with transaction.atomic():
        now = timezone.now()

        submission_helper.update_task_grading_status(
                task,
                grading_status=TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED,
                execution_status=task_execution_status,
                status_update_time=now,
        )
        
        testbed.task_being_graded = None
        testbed.report_time = now
        testbed.report_status = Testbed.STATUS_AVAILABLE
        testbed.status = Testbed.STATUS_AVAILABLE
        testbed.secret_code = ''
        testbed.save()
