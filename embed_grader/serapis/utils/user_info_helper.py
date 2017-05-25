from serapis.models import *


def get_first_last_name(user):
    return user.first_name + ' ' + user.last_name

def get_last_first_name(user):
    return user.last_name + ' ' + user.first_name

def all_submission_graded_on_assignment(user, assignment):
    query = Submission.objects.filter(student_fk=user, assignment_fk=assignment)
    if query.count() == 0:
        return True
    
    # since students cannot see hidden tasks before deadline, we only need to consider those tasks
    # which are hidden
    return query.latest('id').is_fully_graded(include_hidden=False)
