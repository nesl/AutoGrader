from serapis.models import *

from serapis.utils import team_helper


def can_access_grading_details_by_user(task_grading_status, user):
    """
    The grading details here is defined the same as in AssignmentTask, which includes output files,
    grading feedback, and score.
    
    Parameters:
      task_grading_status: A TaskGradingStatus object
      user: A User object
    Returns:
      A bool to indicate the user has the access of this task grading status. Note different from
      `can_show_grading_details_to_user` function, it only checks whether the user has the
      ownership over this task_grading_status
    """

    # If the user is an instructor, she can see the output file
    course = task_grading_status.assignment_task_fk.assignment_fk.course_fk
    if user.has_perm('create_assignment', course):
        return True

    # Otherwise, the user is a student. We need to make sure the user is the owner of this output
    # file
    if team_helper.is_user_in_team(user, self.submission_fk):
        return False

    # After the ownership checks, we need to make sure one more thing, that is the mode of the
    # task (e.g., public or hidden). Fortunately, the accessibility of input files and output files
    # within the same assignment task should be the identical. We can simply use the same
    # permission check from the AssignmentTask.
    return task_grading_status.assignment_task_fk.can_access_grading_details_by_user(user)

def can_show_grading_details_to_user(task_grading_status, user):
    """
    The grading details can be displayed on web only if the user has the permission to see this
    information and the content is ready.
    
    Parameters:
      task_grading_status: A TaskGradingStatus object
      user: A User object
    Returns:
      A bool to indicate the user can see the task grading details on the web.
    """
    return (task_grading_status.is_grading_done()
            and can_access_grading_details_by_user(task_grading_status, user))
