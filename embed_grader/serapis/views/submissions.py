import json
import itertools

from django.shortcuts import render, get_object_or_404
from django.http import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, context_processors
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied

from django.template import RequestContext
from django.forms import modelform_factory
from django import forms
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User, Group
from guardian.decorators import permission_required_or_403
from guardian.compat import get_user_model
from guardian.shortcuts import assign_perm

from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from serapis.models import *
from serapis.forms.submission_forms import *
from serapis.utils import grading
from serapis.utils import file_schema
from serapis.utils import user_info_helper
from serapis.utils import team_helper
from serapis.utils import task_grading_status_helper
from serapis.utils.visualizer_manager import VisualizerManager


@login_required(login_url='/login/')
def submission(request, submission_id):
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        return HttpResponse("Submission cannot be found")

    user = User.objects.get(username=request.user)
    assignment = submission.assignment_fk
    course = assignment.course_fk

    if not user.has_perm('view_assignment', course):
        return HttpResponse("Not enough privilege")

    # for normal students, one can only see the submission if she is in the team
    if not user.has_perm('modify_assignment', course):
        if not team_helper.is_user_in_team(user, submission.team_fk):
            return HttpResponse("Not enough privilege")
    submitter_name = user_info_helper.get_first_last_name(submission.student_fk)
    team_member_names = team_helper.get_team_member_full_name_list(submission.team_fk)

    task_grading_status_list = TaskGradingStatus.objects.filter(
            submission_fk=submission_id).order_by('assignment_task_fk')
    now = timezone.now()
    can_see_hidden_cases_and_feedback_details = (
            assignment.viewing_scope_by_user(user) == Assignment.VIEWING_SCOPE_FULL)

    task_grading_status_list, sum_student_score, sum_total_score = (
            submission.retrieve_task_grading_status_and_score_sum(
                can_see_hidden_cases_and_feedback_details))

    submission_file_dict = file_schema.get_dict_schema_name_to_submission_schema_files(submission)
    submission_file_list = []  # a list of {filename, file_field}

    for s in submission_file_dict:
        if submission_file_dict[s].file:
            submission_file_list.append({
                'filename': s,
                'file_field': submission_file_dict[s].file,
            })

    showing_grading_detail_check_func = task_grading_status_helper.can_show_grading_details_to_user

    template_context = {
        # general
        'myuser': user,
        'now': now,
        # topic objects
        'submission': submission,
        'assignment': assignment,
        'course': course,
        # submission info
        'submitter_name': submitter_name,
        'team_member_names': team_member_names,
        'student_score': sum_student_score,
        'total_score': sum_total_score,
        # submission files for download
        'submission_file_list': submission_file_list,
        # details of solving tasks
        'task_grading_status_list': task_grading_status_list,
        # permission
        'can_see_feedback_details': can_see_hidden_cases_and_feedback_details,
        # classes
        'AssignmentTask': AssignmentTask,
        # functions
        'showing_grading_detail_check_func': [showing_grading_detail_check_func],
    }

    return render(request, 'serapis/submission.html', template_context)


@login_required(login_url='/login/')
def task_grading_detail(request, task_grading_id):
    try:
        task_grading_status = TaskGradingStatus.objects.get(id=task_grading_id)
    except Submission.DoesNotExist:
        return HttpResponse("Task grading detail cannot be found")

    user = User.objects.get(username=request.user)
    submission = task_grading_status.submission_fk
    assignment = submission.assignment_fk
    course = assignment.course_fk
    if not user.has_perm('view_assignment', course):
        print("not enrolled")
        return HttpResponse("Not enough privilege")

    # for normal students, one can only see the submission if she is in the team
    if not user.has_perm('modify_assignment', course):
        if not team_helper.is_user_in_team(user, submission.team_fk):
            return HttpResponse("Not enough privilege")
    submitter_name = user_info_helper.get_first_last_name(submission.student_fk)
    team_member_names = team_helper.get_team_member_full_name_list(submission.team_fk)

    assignment_task = task_grading_status.assignment_task_fk
    if not assignment_task.can_access_grading_details_by_user(user):
        print("cannot view detail")
        return HttpResponse("Not enough privilege")

    if task_grading_status.grading_status != TaskGradingStatus.STAT_FINISH:
        return HttpResponse("Detail is not ready")

    now = timezone.now()

    output_files = file_schema.get_dict_schema_name_to_task_grading_status_schema_files(
            task_grading_status, enforce_check=True)

    visualizer_manager = VisualizerManager()

    for field_name in output_files:
        file = output_files[field_name].file
        raw_content = file.read()
        url = file.url
        visualizer_manager.add_file(field_name, raw_content, url)

    if task_grading_status.grading_detail:
        feedback = task_grading_status.grading_detail.read()
    else:
        feedback = '(feedback unavailable...)'

    template_context = {
        'myuser': request.user,
        'course': course,
        'assignment': assignment,
        'submission': submission,
        'submitter_name': submitter_name,
        'team_member_names': team_member_names,
        'grading': task_grading_status,
        'assignment_task': assignment_task,
        'visualizer_manager': visualizer_manager,
        'feedback': feedback,
    }

    return render(request, 'serapis/task_grading_detail.html', template_context)


@login_required(login_url='/login/')
def all_submission_logs_as_teacher(request):
    """
    The definition of teacher covers all the roles who have permission to alter students' grades.
    Specifically, it includes instructors, teaching assistants, and graders.
    """

    user = User.objects.get(username=request.user)
    
    # get all the courses that this user teaches
    covered_roles = [
        CourseUserList.ROLE_INSTRUCTOR,
        CourseUserList.ROLE_TA,
        CourseUserList.ROLE_GRADER,
    ]
    course_user_list = list(itertools.chain(*[
                CourseUserList.objects.filter(user_fk=user, role=r) for r in covered_roles]))
    courses = [o.course_fk for o in course_user_list]
    
    # get all the assignments from the courses
    assignments = list(itertools.chain(*[Assignment.objects.filter(course_fk=c) for c in courses]))

    # get all the submissions associated with these assignments
    submission_list = list(itertools.chain(*[
                Submission.objects.filter(assignment_fk=a) for a in assignments]))

    template_context = {
        'myuser': user,
        'submission_list': submission_list,
    }
    return render(request, 'serapis/submission_logs_teacher.html', template_context)


@login_required(login_url='/login/')
def all_submission_logs_as_student(request):
    user = User.objects.get(username=request.user)
    
    # get all the courses that this user has taken so far
    course_user_list = CourseUserList.objects.filter(
            user_fk=user, role=CourseUserList.ROLE_STUDENT)
    courses = [o.course_fk for o in course_user_list]
    
    # get all the assignments from the courses and each team that this user participates
    assignments = list(itertools.chain(*[Assignment.objects.filter(course_fk=c) for c in courses]))
    teams = [team_helper.get_belonged_team(user, assignment=a) for a in assignments]

    # get all the submissions associated with these teams
    submission_list = list(itertools.chain(*[
                Submission.objects.filter(team_fk=t) for t in teams]))

    template_context = {
        'myuser': user,
        'submission_list': submission_list,
    }
    return render(request, 'serapis/submission_logs_student.html', template_context)


@login_required(login_url='/login/')
def regrade(request, assignment_id):
    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found")

    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    course = assignment.course_fk
    if not user.has_perm('modify_assignment', course):
        return HttpResponse("Not enough privilege")

    previous_commit_result = None
    if request.method == 'POST':
        form = RegradeForm(request.POST, request.FILES, assignment=assignment)
        if form.is_valid():
            t_sub, t_grading = form.save_and_commit()
            previous_commit_result = {
                    'num_successful_submissions': t_sub,
                    'num_successful_task_grading_status': t_grading,
            }
            form = RegradeForm(assignment=assignment)  # start a new empty form
    else:
        form = RegradeForm(assignment=assignment)

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'previous_commit_result': previous_commit_result,
            'form': form,
            'course': assignment.course_fk,
            'assignment': assignment,
    }
    return render(request, 'serapis/regrade.html', template_context)
