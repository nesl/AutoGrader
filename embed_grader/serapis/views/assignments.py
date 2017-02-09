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
from serapis.forms.assignment_forms import *


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
    time_remaining = str(assignment.deadline - now)

    # Handle POST the request
    assignment_tasks = AssignmentTask.objects.filter(assignment_id=assignment).order_by('id')
    total_points = 0
    public_points = 0
    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES, assignment=assignment)
        if form.is_valid():
            if assignment.is_deadline_passed() and not user.has_perm('modify_assignment', course):
                #TODO: Show error message: deadline is passed
                print('Silent error msg: deadline is passed')
            else:
                submission, _ = form.save_and_commit(student=user)

                # dispatch grading tasks
                for assignment_task in assignment_tasks:
                    grading_task = TaskGradingStatus.objects.create(
                        submission_id=submission,
                        assignment_task_id=assignment_task,
                        grading_status=TaskGradingStatus.STAT_PENDING,
                        execution_status=TaskGradingStatus.EXEC_UNKNOWN,
                        status_update_time=timezone.now()
                    )

                    # create file records for each task
                    schema_list = TaskGradingStatusFileSchema.objects.filter(
                            assignment_id=assignment)
                    for sch in schema_list:
                        TaskGradingStatusFile.objects.create(
                            task_grading_status_id=grading_task,
                            file_schema_id=sch,
                            file=None,
                        )

    # get true total points and total points to students
    for assignment_task in assignment_tasks:
        total_points += assignment_task.points
        if assignment_task.mode != AssignmentTask.MODE_HIDDEN or now > assignment.deadline:
            public_points += assignment_task.points

    submission_form = AssignmentSubmissionForm(assignment=assignment)
    submission_short_list = []
    if user.has_perm('modify_assignment', course):
        students = CourseUserList.objects.filter(course_id=course)
        submission_short_list = []
        for student in students:
            sub = grading.get_last_fully_graded_submission(student, assignment)
            if sub:
                submission_short_list.append(sub)
    else:
        submission_short_list = Submission.objects.filter(
                student_id=user, assignment_id=assignment).order_by('-id')[:10]

    submission_grading_detail = []
    student_list = []
    gradings = []
    for submission in submission_short_list:
        student = User.objects.get(username = submission.student_id)
        #TODO: is there a function for this?
        student_name = student.first_name + " " + student.last_name
        student_list.append(student_name)

        total_submission_points = 0.
        tasks = TaskGradingStatus.objects.filter(
                submission_id=submission, grading_status=TaskGradingStatus.STAT_FINISH)

        for task in tasks:
            if task.grading_status == TaskGradingStatus.STAT_FINISH:
                if user.has_perm('modify_assignment', course) or task.assignment_task_id.mode != AssignmentTask.MODE_HIDDEN or now > assignment.deadline:
                    total_submission_points += task.points

        submission_grading_detail.append(total_submission_points)
        gradings.append(round(total_submission_points, 2))

    recent_submission_list = list(zip(submission_short_list, submission_grading_detail, gradings, student_list))

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'assignment': assignment,
            'course': course,
            'submission_form': submission_form,
            'submission_n_detail_short_list': recent_submission_list,
            'tasks': assignment_tasks,
            'total_points': total_points,
            'public_points': public_points,
            'time_remaining': time_remaining,
            'now': now
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
