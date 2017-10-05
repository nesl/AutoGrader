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
from serapis.utils import team_helper
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

    course = assignment.course_fk
    if not user.has_perm('view_assignment', course):
        return HttpResponse("Not enough privilege")

    # retrieve team status
    team = team_helper.get_belonged_team(user, assignment)
    num_team_members = team_helper.get_num_team_members(team)

    # if the user does not belong to any team yet it's an individual assignment, just create the
    # one-person team
    if team is None and assignment.num_max_team_members == 1:
        team, _ = team_helper.create_team(assignment=assignment, users=[user])
        num_team_members = 1

    # retrieve passcode
    passcode = None
    if team is not None:
        user_team_member = team_helper.get_specific_team_member(team, user)
        if user_team_member is not None and user_team_member.is_leader:
            passcode = team.passcode

    # a string of team member names
    team_members_human_readable = team_helper.get_team_member_full_name_list(team, last_and=True)

    # handle POST the request
    if team is not None and request.method == 'POST':
        form = AssignmentSubmissionForm(
                request.POST, request.FILES, user=user, team=team, assignment=assignment)
        if form.is_valid():
            form.save_and_commit()

    # compute remaining time for submission
    now = timezone.now()
    time_remaining = _display_remaining_time(assignment.deadline - now)

    # retrieve task status
    can_see_hidden_cases = (
            assignment.viewing_scope_by_user(user) == Assignment.VIEWING_SCOPE_FULL)

    assignment_tasks, _ = assignment.retrieve_assignment_tasks_and_score_sum(can_see_hidden_cases)
    public_points, total_points = assignment.get_assignment_task_total_scores()

    assignment_task_files_list = []
    for task in assignment_tasks:
        task_files = task.retrieve_assignment_task_files_url(user)
        assignment_task_files_list.append(task_files)

    if user.has_perm('modify_assignment', course):
        can_submit, reason_of_cannot_submit = True, None
    elif assignment.is_deadline_passed():
        can_submit, reason_of_cannot_submit = False, 'Deadline has passed'
    elif team is None:
        can_submit, reason_of_cannot_submit = False, 'You have to create or join a team first'
    elif not user_info_helper.all_submission_graded_on_assignment(user, assignment):
        can_submit, reason_of_cannot_submit = (
                False, 'Please wait until current submission if fully graded')
    else:
        can_submit, reason_of_cannot_submit = True, None

    # render the submission form
    submission_form = (AssignmentSubmissionForm(user=user, team=team, assignment=assignment)
            if can_submit else None)

    # retrieve submission lists
    submission_lists = {}
    if not user.has_perm('modify_assignment', course):
        if not team:
            submission_lists['team'] = None
        else:
            submission_lists['team'] = Submission.objects.filter(
                    team_fk=team, assignment_fk=assignment).order_by('-id')[:10]
    else:
        teams = Team.objects.filter(assignment_fk=assignment)
        graded_list = []
        grading_list = []

        for team in teams:
            sub = grading.get_last_fully_graded_submission(team, assignment)
            if sub:
                graded_list.append(sub)

            sub = grading.get_last_grading_submission(team, assignment)
            if sub:
                grading_list.append(sub)

        submission_lists['graded'] = graded_list
        submission_lists['grading'] = grading_list

    # score distribution
    is_deadline_passed = assignment.is_deadline_passed()
    _, num_attempting_teams, score_statistics = score_distribution.get_class_statistics(
                assignment=assignment, include_hidden=is_deadline_passed)

    assignment_tasks_with_file_list = zip(assignment_tasks, assignment_task_files_list)


    template_context = {
            # user
            'myuser': request.user,
            'user_profile': user_profile,
            # assignment/course
            'course': course,
            'assignment': assignment,
            # assignment task section
            'public_points': public_points,
            'total_points': total_points,
            'assignment_tasks': assignment_tasks_with_file_list,
            # team info
            'team': team,
            'num_team_members': num_team_members,
            'team_members_human_readable': team_members_human_readable,
            'passcode': passcode,
            # form
            'submission_form': submission_form,
            'reason_of_cannot_submit': reason_of_cannot_submit,
            'now': now,
            'time_remaining': time_remaining,
            # score distribution
            'num_attempting_teams': num_attempting_teams,
            'score_statistics': score_statistics,
            'submission_unit': 'student' if assignment.num_max_team_members == 1 else 'team',
            # submission section
            'submission_lists': submission_lists,
    }

    return render(request, 'serapis/assignment.html', template_context)


@login_required(login_url='/login/')
def assignment_run_final_grade(request, assignment_id):
    user = User.objects.get(username=request.user)

    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found.")

    course = assignment.course_fk
    if not user.has_perm('modify_assignment', course):
        return HttpResponse("Not enough privilege")

    now = timezone.now()

    assignment_tasks = assignment.retrieve_assignment_tasks_by_accumulative_scope(
            AssignmentTask.MODE_HIDDEN)

    students = [o.user_fk for o in CourseUserList.objects.filter(course_fk=course)]
    for student in students:
        submission = grading.get_last_submission(student, assignment)
        if submission is None:
            continue

        graded_task_obj_for_submission = TaskGradingStatus.objects.filter(submission_fk=submission)
        graded_task_for_submission = [t.assignment_task_fk for t in graded_task_obj_for_submission]
        task_to_be_added = [t for t in assignment_tasks if t not in graded_task_for_submission]

        with transaction.atomic():
            for task in task_to_be_added:
                grading_task = TaskGradingStatus.objects.create(
                    submission_fk=submission,
                    assignment_task_fk=task,
                    grading_status=TaskGradingStatus.STAT_PENDING,
                    execution_status=TaskGradingStatus.EXEC_UNKNOWN,
                    status_update_time=now,
                    )
                file_schema.create_empty_task_grading_status_schema_files(grading_task)

            submission.task_scope = AssignmentTask.MODE_HIDDEN
            submission.save()

    return HttpResponseRedirect(reverse('assignment', kwargs={'assignment_id': assignment_id}))


@login_required(login_url='/login/')
def assignment_create_team(request, assignment_id):
    user = User.objects.get(username=request.user)

    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found.")

    course = assignment.course_fk
    if not user.has_perm('view_assignment', course):
        return HttpResponse("Not enough privilege")

    if assignment.is_deadline_passed():
        return HttpResponse("Deadline is passed")

    team_helper.create_team(assignment, [user])

    return HttpResponseRedirect(reverse('assignment', kwargs={'assignment_id': assignment_id}))


@login_required(login_url='/login/')
def assignment_join_team(request, assignment_id):
    user = User.objects.get(username=request.user)

    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found.")

    course = assignment.course_fk
    if not user.has_perm('view_assignment', course):
        return HttpResponse("Not enough privilege")

    if assignment.is_deadline_passed():
        return HttpResponse("Deadline is passed")

    if team_helper.get_belonged_team(user, assignment) is not None:
        return HttpResponse("Already involved in some team")

    if request.method != 'POST':
        return HttpResponse("Invalid request")

    form = JoinTeamForm(request.POST, user=user, assignment=assignment)
    if not form.is_valid():
        #TODO: show error message of incorrect passcode in the next page
        return HttpResponse("Invalid request")

    form.save()

    return HttpResponseRedirect(reverse('assignment', kwargs={'assignment_id': assignment_id}))


@login_required(login_url='/login/')
def view_assignment_team_list(request, assignment_id):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found.")

    course = assignment.course_fk
    if not user.has_perm('modify_assignment', course):
        return HttpResponse("Not enough privilege")

    if assignment.num_max_team_members == 1:
        return HttpResponse("Not a team-based assignment")

    #TODO: The original plan of view_assignment_team_list view is that each student is represented
    # as a box in the table, and instructors can drag and drop the boxes to arrange students to
    # different teams.

    teams = Team.objects.filter(assignment_fk=assignment)
    team_bundles = []
    for team in teams:
        team_members = team_helper.get_team_members(team)
        team_member_names = [user_info_helper.get_first_last_name(tm.user_fk)
                for tm in team_members]
        team_bundle = {
                'team': team,
                'leader_name': team_member_names[0],
                'teammate_names': team_member_names[1:],
        }
        team_bundles.append(team_bundle)

    template_context = {
            'myuser': user,
            'user_profile': user_profile,
            'course': course,
            'assignment': assignment,
            'team_bundles': team_bundles,
    }

    return render(request, 'serapis/assignment_team_list.html', template_context)


@login_required(login_url='/login/')
def delete_team(request, assignment_id, team_id):
    user = User.objects.get(username=request.user)

    try:
        assignment = Assignment.objects.get(id=assignment_id)
        team = Team.objects.get(id=team_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment or team cannot be found.")

    course = assignment.course_fk
    if not user.has_perm('modify_assignment', course):
        return HttpResponse("Not enough privilege")

    if team.assignment_fk != assignment:
        return HttpResponse("Invalid request")

    team.delete()

    return HttpResponseRedirect(
            reverse('view-assignment-team-list', kwargs={'assignment_id': assignment_id}))


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
            assignment = form.save_and_commit()
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
            request=request, course_id=assignment.course_fk.id, assignment=assignment)


@login_required(login_url='/login/')
def delete_assignment(request, assignment_id):
    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Cannot find the assignment.")

    user = User.objects.get(username=request.user)

    course = assignment.course_fk

    if not user.has_perm('create_assignment', course):
        return HttpResponse("Not enough privilege")

    assignment.delete()

    return HttpResponseRedirect(reverse('course', kwargs={'course_id': course.id}))
