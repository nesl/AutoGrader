from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group

from django.shortcuts import render, get_object_or_404
from django.http import *
from django.core.exceptions import PermissionDenied

from django.template import RequestContext
from django import forms
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Max

from django.utils import timezone
from datetime import timedelta

from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from guardian.decorators import permission_required_or_403
from guardian.compat import get_user_model
from guardian.shortcuts import assign_perm

from serapis.models import *
from serapis.utils import grading
from serapis.utils import user_info_helper
from serapis.utils import score_distribution
from serapis.forms.assignment_forms import *


def _plural(n, s):
    return '%d %s%s' % (n, s, 's' if n == 1 else '')


def _display_remaining_time(tdelta):
    if tdelta < datetime.timedelta(0):
        return 'Deadline passed'
    
    days = tdelta.days
    hours, rem = divmod(tdelta.seconds, 3600)
    mins, secs = divmod(rem, 60)
    if days:
        return '%s %s' % (_plural(days, 'day'), _plural(hours, 'hour'))
    elif hours:
        return '%s %s' % (_plural(hours, 'hour'), _plural(mins, 'minute'))
    else:
        return '%s %s' % (_plural(mins, 'minute'), _plural(secs, 'second'))


@login_required(login_url='/login/')
def assignment(request, assignment_id):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found.")

    course = assignment.course_id
    if not user.has_perm('view_assignment', course):
        return HttpResponse("Not enough privilege")

    now = timezone.now()
    time_remaining = _display_remaining_time(assignment.deadline - now)

    # Handle POST the request
    if request.method == 'POST':
        form = AssignmentSubmissionForm(
                request.POST, request.FILES, user=user, assignment=assignment)
        if form.is_valid():
            form.save_and_commit()

    can_see_hidden_cases = (
            assignment.viewing_scope_by_user(user) == Assignment.VIEWING_SCOPE_FULL)

    (assignment_tasks, _) = assignment.retrieve_assignment_tasks_and_score_sum(can_see_hidden_cases)
    (public_points, total_points) = assignment.get_assignment_task_total_scores()

    if user.has_perm('modify_assignment', course):
        can_submit, reason_of_cannot_submit = True, None
    elif assignment.is_deadline_passed():
        can_submit, reason_of_cannot_submit = False, 'Deadline has passed'
    elif not user_info_helper.all_submission_graded_on_assignment(user, assignment):
        can_submit, reason_of_cannot_submit = (
                False, 'Please wait until current submission if fully graded')
    else:
        can_submit, reason_of_cannot_submit = True, None

    submission_form = (AssignmentSubmissionForm(user=user, assignment=assignment)
            if can_submit else None)

    if user.has_perm('modify_assignment', course):
        students = [o.user_id for o in CourseUserList.objects.filter(course_id=course)]
        submission_list = []
        for student in students:
            sub = grading.get_last_fully_graded_submission(student, assignment)
            if sub:
                submission_list.append(sub)
    else:
        submission_list = Submission.objects.filter(
                student_id=user, assignment_id=assignment).order_by('-id')[:10]

    is_deadline_passed = assignment.is_deadline_passed()
    enrollment, contributors, score_statistics = score_distribution.get_class_statistics(
            assignment=assignment, include_hidden=is_deadline_passed)

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'course': course,
            'assignment': assignment,
            'submission_form': submission_form,
            'reason_of_cannot_submit': reason_of_cannot_submit,
            'submission_list': submission_list,
            'assignment_tasks': assignment_tasks,
            'public_points': public_points,
            'total_points': total_points,
            'now': now,
            'time_remaining': time_remaining,
            'total_student_num': enrollment,
            'num_contributed_students': contributors,
            'score_statistics': score_statistics,
    }

    return render(request, 'serapis/assignment.html', template_context)


def _create_or_modify_assignment(request, course_id, assignment):
    """
    if assignment is None, it is in creating mode, otherwise it is in updating mode
    """
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return HttpResponse("Cannot find the course.")

    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    # Only super user has access to create a course
    if not user.has_perm('create_assignment', course):
        return HttpResponse("Not enough privilege")
    
    mode = 'modify' if assignment else 'create'

    if request.method == 'POST':
        form = AssignmentForm(request.POST, course=course, instance=assignment)
        if form.is_valid():
            assignment = form.save()
            return HttpResponseRedirect(reverse('assignment',
                kwargs={'assignment_id': assignment.id}))
    else:
        form = AssignmentForm(course=course, instance=assignment)
    
    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'mode': mode,
            'course': course,
            'assignment': assignment,
            'form': form,
    }
    return render(request, 'serapis/create_or_modify_assignment.html', template_context)


@login_required(login_url='/login/')
def create_assignment(request, course_id):
    return _create_or_modify_assignment(
            request=request, course_id=course_id, assignment=None)


@login_required(login_url='/login/')
def modify_assignment(request, assignment_id):
    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Cannot find the assignment.")

    return _create_or_modify_assignment(
            request=request, course_id=assignment.course_id.id, assignment=assignment)
