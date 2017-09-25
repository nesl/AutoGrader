import json

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

    if not user.has_perm('view_assignment',course):
        return HttpResponse("Not enough privilege")

    author = User.objects.get(username=submission.student_fk)
    if not user.has_perm('modify_assignment',course):
        if author.username != user.username:
            return HttpResponse("Not enough privilege")
    submitter_name = user_info_helper.get_first_last_name(author)
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

    template_context = {
        'myuser': user,
        'now': now,
        'submission': submission,
        'assignment': assignment,
        'course': course,
        'submitter_name': submitter_name,
        'team_member_names': team_member_names,
        'student_score': sum_student_score,
        'total_score': sum_total_score,
        'submission_file_list': submission_file_list,
        'task_grading_status_list': task_grading_status_list,
        'can_see_feedback_details': can_see_hidden_cases_and_feedback_details,
        'AssignmentTask': AssignmentTask,
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

    author = submission.student_fk
    if not user.has_perm('modify_assignment', course):
        if author != user:
            print("Not author")
            return HttpResponse("Not enough privilege")
    submitter_name = user_info_helper.get_first_last_name(author)
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
    #output_full_log = []  # A list of {field_name, content}

    visualizer_manager = VisualizerManager()

    for field_name in output_files:
        file = output_files[field_name].file
        raw_content = file.read()
        url = file.url
        visualizer_manager.add_file(field_name, raw_content, url)
    output_visualizations = visualizer_manager.get_visualizations_for_template()

    if task_grading_status.grading_detail:
        feedback = task_grading_status.grading_detail.read()
    else:
        feedback = '(feedback unavailable...)'

    # if not grading.output_file:
    #     print('Something serious wrong. output file cannot be found in TaskGradingStatus ID=%d' % grading.id)
    #     return HttpResponse("Please contact PI (TaskGradingStatus ID=%d)" % grading.id)

    # with open(assignment_task.test_input.path, 'r') as f:
    #     lines = f.readlines()
    # lines = [l.strip().split(',') for l in lines]
    # in_events = [(float(l[1]), int(l[2])) for l in lines if int(l[0]) == 68]
    # if not in_events:
    #     in_events = [(0.0, 0)]
    # elif in_events[0][0] != 0:
    #     in_events[0:0] = [(0.0, 0)]

    # with open(grading.output_file.path, 'r') as f:
    #     lines = f.readlines()
    # lines = [l.strip().split(',') for l in lines]
    # out_events = [(float(l[1]), int(l[2])) for l in lines if int(l[0]) == 68]
    # if not out_events:
    #     out_events = [(0.0, 0)]
    # elif out_events[0][0] != 0:
    #     out_events[0:0] = [(0.0, 0)]

    # #TODO: remove the assumption of 1 sec = 5000 ticks
    # session_length = assignment_task.execution_duration * 5000.0
    #
    # #TODO: now only assume 13 input pins and 2 output pins, which we should generalize this part
    # events = []
    # in_idx = 0
    # out_idx = 0
    # in_last_val = 0
    # out_last_val = 0
    # while in_idx < len(in_events) or out_idx < len(out_events):
    #     if in_idx == len(in_events):
    #         cur_time = out_events[out_idx][0]
    #         out_last_val = out_events[out_idx][1]
    #         out_idx += 1
    #     elif out_idx == len(out_events):
    #         cur_time = in_events[in_idx][0]
    #         in_last_val = in_events[in_idx][1]
    #         in_idx += 1
    #     else:
    #         cur_time = min(in_events[in_idx][0], out_events[out_idx][0])
    #         if in_events[in_idx][0] == cur_time:
    #             in_last_val = in_events[in_idx][1]
    #             in_idx += 1
    #         if out_events[out_idx][0] == cur_time:
    #             out_last_val = out_events[out_idx][1]
    #             out_idx += 1
    #     cur_val = in_last_val | (out_last_val) << 13
    #     events.append((cur_time, cur_val))
    # events.append((session_length + 0.01, cur_val))
    #
    # plot_time = []
    # plot_data = [[] for _ in range(3 + 2)]
    # plot_labels = [
    #         'D6-D2 (period)',
    #         'D13-D7 (ratio)',
    #         'D1 (req)',
    #         'D14 (hardware PWM)',
    #         'D0 (software PWM)']
    # bit_lens = [5, 7, 1, 1, 1]
    # for i in range(len(events) - 1):
    #     plot_time.append(events[i][0])
    #     v = events[i][1]
    #     for j in range(5):
    #         mask = (1 << bit_lens[j]) - 1
    #         plot_data[j].append(v & mask)
    #         v >>= bit_lens[j]
    #
    #     plot_time.append(events[i+1][0] - 0.01)
    #     v = events[i][1]
    #     for j in range(5):
    #         mask = (1 << bit_lens[j]) - 1
    #         plot_data[j].append(v & mask)
    #         v >>= bit_lens[j]
    # plot_pack = {'time': plot_time, 'data': plot_data, 'labels': plot_labels}
    # js_plot_pack_string = json.dumps(plot_pack)

    print(output_visualizations)
    template_context = {
        'myuser': request.user,
        'course': course,
        'assignment': assignment,
        'submission': submission,
        'submitter_name': submitter_name,
        'team_member_names': team_member_names,
        'grading': task_grading_status,
        'assignment_task': assignment_task,
        'output_visualizations': output_visualizations,
        'feedback': feedback,
        # 'js_plot_pack_string': js_plot_pack_string,
    }

    return render(request, 'serapis/task_grading_detail.html', template_context)


@login_required(login_url='/login/')
def submissions_full_log(request):
    user = User.objects.get(username=request.user)

    #TODO: submission objects should be queried by teams. Put as a todo because submission_full_log
    # view is going to be remodeled.
    submission_list = Submission.objects.filter(student_fk=user).order_by('-id')
    
    template_context = {
        'myuser': user,
        'myuser_name': user_info_helper.get_first_last_name(user),
        'submission_list': submission_list,
        'now': timezone.now(),
    }

    return render(request, 'serapis/submissions_full_log.html', template_context)


@login_required(login_url='/login/')
def student_submission_full_log(request):
    user = User.objects.get(username=request.user)
    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponse("Not enough privilege")
    courses_as_instructor = [o.course_fk for o in 
            CourseUserList.objects.filter(user_fk=user).exclude(role=CourseUserList.ROLE_STUDENT)]

    assignment_list = []
    for course in courses_as_instructor:
        course_assignments = Assignment.objects.filter(course_fk=course)
        assignment_list.extend(course_assignments)

    submission_list = []
    for assign in assignment_list:
        #TODO: why do we want to exclude the instructor herself?
        #TODO: submission objects should be queried by teams. Put as a todo because
        # student_submission_full_log view is going to be remodeled.
        assign_submissions = Submission.objects.filter(assignment_fk=assign).exclude(student_fk=user)
        submission_list.extend(assign_submissions)

    template_context = {
        'myuser': user,
        'submission_list': submission_list
    }
    return render(request, 'serapis/student_submission_full_log.html', template_context)


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
