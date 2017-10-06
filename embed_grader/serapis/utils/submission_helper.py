from django.db import transaction

from django.utils import timezone

from serapis.models import *

from serapis.utils import team_helper


def can_submission_file_be_accessed_by_user(submission, user):
    if user.has_perm('modify_assignment', submission.assignment_fk.course_fk):
        return True
    return team_helper.is_user_in_team(user, submission.team_fk)

def create_task_grading_status(submission, assignment_task):
    """
    Return: TaskGradingStatus
    """

    with transaction.atomic():
        # create TaskGradingStatus
        grading_task = TaskGradingStatus.objects.create(
                submission_fk=submission,
                assignment_task_fk=assignment_task,
                grading_status=TaskGradingStatus.STAT_PENDING,
                execution_status=TaskGradingStatus.EXEC_UNKNOWN,
                status_update_time=timezone.now(),
        )

        # update submission
        submission.num_total_tasks += 1
        submission.save()

    return grading_task

def remove_task_grading_status(task_grading_status):
    submission = task_grading_status.submission_fk
    
    submission.num_total_tasks -= 1
    if task_grading_status.is_grading_done():
        submission.num_graded_tasks -= 1

    with transaction.atomic():
        submission.save()
        task_grading_status.delete()

def update_task_grading_status(task_grading_status, grading_status, **kwargs):
    """
    Param:
      - task_grading_status: the target to be changed
      - grading_status: TaskGradingStatus.GRADING_STATES
      - **kwargs: for updating the rest of task_grading_status attributes
    """

    submission = task_grading_status.submission_fk

    # update grading_status
    if task_grading_status.is_grading_done():
        submission.num_graded_tasks -= 1

    task_grading_status.grading_status = grading_status

    if task_grading_status.is_grading_done():
        submission.num_graded_tasks += 1

    # update the rest of attributes
    if 'grading_status' in kwargs:
        task_grading_status.grading_status = kwargs['grading_status']
    if 'execution_status' in kwargs:
        task_grading_status.execution_status = kwargs['execution_status']
    if 'status_update_time' in kwargs:
        task_grading_status.status_update_time = kwargs['status_update_time']
    if 'points' in kwargs:
        task_grading_status.points = kwargs['points']
    if 'grading_detail' in kwargs:
        task_grading_status.grading_detail = kwargs['grading_detail']

    with transaction.atomic():
        submission.save()
        task_grading_status.save()
