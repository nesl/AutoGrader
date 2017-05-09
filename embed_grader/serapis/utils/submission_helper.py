from serapis.models import *

from serapis.utils import team_helper


def can_submission_file_be_accessed_by_user(submission, user):
    if user.has_perm('modify_assignment', submission.assignment_id.course_id):
        return True;
    return submission.team == team_helper.get_belonged_team(user, self.assignment_id)

