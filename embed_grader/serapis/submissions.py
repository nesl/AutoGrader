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

from serapis.models import *
from serapis.model_forms import *
from serapis.utils import grading

from django.contrib.auth.models import User, Group
from guardian.decorators import permission_required_or_403
from guardian.compat import get_user_model
from guardian.shortcuts import assign_perm

import hashlib, random, pytz

from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


@login_required(login_url='/login/')
def submission(request, submission_id):
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        return HttpResponse("Submission cannot be found")

    user = User.objects.get(username=request.user)
    assignment = submission.assignment_id
    course = assignment.course_id

    if not user.has_perm('view_assignment',course):
    	return HttpResponse("Not enough privilege")

    author = User.objects.get(username=submission.student_id)
    if not user.has_perm('modify_assignment',course):
        if author.username != user.username:
            return HttpResponse("Not enough privilege")

    gradings = TaskGradingStatus.objects.filter(submission_id=submission_id).order_by('assignment_task_id')
    now = datetime.now(tz=pytz.timezone('UTC'))
    if user.has_perm('modify_assignment',course) or now > assignment.deadline:
        assignment_tasks = AssignmentTask.objects.filter(assignment_id=assignment).order_by('id')
    else:
        assignment_tasks = AssignmentTask.objects.filter(assignment_id=assignment).exclude(mode=AssignmentTask.MODE_HIDDEN).order_by('id')

    task_symbols = []
    score = 0;
    for task in gradings:
        if user.has_perm('modify_assignment', course) or task.assignment_task_id.mode != AssignmentTask.MODE_HIDDEN or now > assignment.deadline:
            if task.grading_status == TaskGradingStatus.STAT_PENDING:
                task_symbols.append('Pending')
            elif task.grading_status == TaskGradingStatus.STAT_EXECUTING:
                task_symbols.append('Executing')
            elif task.grading_status == TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED:
                task_symbols.append('Checking')
            elif task.grading_status == TaskGradingStatus.STAT_FINISH:
                    score += task.points
                    task.points = round(task.points, 2)
                    task_symbols.append('Finalized')
            elif task.grading_status == TaskGradingStatus.STAT_INTERNAL_ERROR:
                task_symbols.append('Error')

    total_points = 0
    for a in assignment_tasks:
        total_points += a.points

    score = round(score, 2)

    submission_n_detail_short_list = zip(gradings, task_symbols, assignment_tasks)

    template_context = {
        'submission':submission,
        'assignment': assignment,
        'course': course,
        'author':author,
        'submission_n_detail_short_list':submission_n_detail_short_list,
        'score':score,
        'total_points':total_points,
        'myuser': request.user,
        'now':now
    }
    return render(request, 'serapis/submission.html', template_context)



@login_required(login_url='/login/')
def task_grading_detail(request, task_grading_id):
    try:
        grading = TaskGradingStatus.objects.get(id=task_grading_id)
    except Submission.DoesNotExist:
        return HttpResponse("Task grading detail cannot be found")

    user = User.objects.get(username=request.user)
    submission = grading.submission_id
    assignment = submission.assignment_id
    course = assignment.course_id
    if not user.has_perm('view_assignment', course):
    	return HttpResponse("Not enough privilege")

    author = submission.student_id
    if not user.has_perm('modify_assignment', course):
        if author != user:
            return HttpResponse("Not enough privilege")

    assignment_task = grading.assignment_task_id
    grading.points = round(grading.points, 2)

    if grading.grading_detail:
        feedback = open(grading.grading_detail.path, 'r').read()

    if not grading.output_file:
        print('Something serious wrong. output file cannot be found in TaskGradingStatus ID=%d' % grading.id)
        return HttpResponse("Please contact PI (TaskGradingStatus ID=%d)" % grading.id)

    with open(assignment_task.test_input.path, 'r') as f:
        lines = f.readlines()
    lines = [l.strip().split(',') for l in lines]
    in_events = [(float(l[1]), int(l[2])) for l in lines if int(l[0]) == 68]
    if not in_events:
        in_events = [(0.0, 0)]
    elif in_events[0][0] != 0:
        in_events[0:0] = [(0.0, 0)]

    with open(grading.output_file.path, 'r') as f:
        lines = f.readlines()
    lines = [l.strip().split(',') for l in lines]
    out_events = [(float(l[1]), int(l[2])) for l in lines if int(l[0]) == 68]
    if not out_events:
        out_events = [(0.0, 0)]
    elif out_events[0][0] != 0:
        out_events[0:0] = [(0.0, 0)]

    #TODO: remove the assumption of 1 sec = 5000 ticks
    session_length = assignment_task.execution_duration * 5000.0

    #TODO: now only assume 13 input pins and 2 output pins, which we should generalize this part
    events = []
    in_idx = 0
    out_idx = 0
    in_last_val = 0
    out_last_val = 0
    while in_idx < len(in_events) or out_idx < len(out_events):
        if in_idx == len(in_events):
            cur_time = out_events[out_idx][0]
            out_last_val = out_events[out_idx][1]
            out_idx += 1
        elif out_idx == len(out_events):
            cur_time = in_events[in_idx][0]
            in_last_val = in_events[in_idx][1]
            in_idx += 1
        else:
            cur_time = min(in_events[in_idx][0], out_events[out_idx][0])
            if in_events[in_idx][0] == cur_time:
                in_last_val = in_events[in_idx][1]
                in_idx += 1
            if out_events[out_idx][0] == cur_time:
                out_last_val = out_events[out_idx][1]
                out_idx += 1
        cur_val = in_last_val | (out_last_val) << 13
        events.append((cur_time, cur_val))
    events.append((session_length + 0.01, cur_val))

    plot_time = []
    plot_data = [[] for _ in range(3 + 2)]
    plot_labels = [
            'D6-D2 (period)',
            'D13-D7 (ratio)',
            'D1 (req)',
            'D14 (hardware PWM)',
            'D0 (software PWM)']
    bit_lens = [5, 7, 1, 1, 1]
    for i in range(len(events) - 1):
        plot_time.append(events[i][0])
        v = events[i][1]
        for j in range(5):
            mask = (1 << bit_lens[j]) - 1
            plot_data[j].append(v & mask)
            v >>= bit_lens[j]

        plot_time.append(events[i+1][0] - 0.01)
        v = events[i][1]
        for j in range(5):
            mask = (1 << bit_lens[j]) - 1
            plot_data[j].append(v & mask)
            v >>= bit_lens[j]
    plot_pack = {'time': plot_time, 'data': plot_data, 'labels': plot_labels}
    js_plot_pack_string = json.dumps(plot_pack)

    template_context = {
        'myuser': request.user,
        'course': course,
        'assignment': assignment,
        'submission': submission,
        'author': author,
        'grading': grading,
        'assignment_task': assignment_task,
        'feedback': feedback,
        'js_plot_pack_string': js_plot_pack_string,
    }

    return render(request, 'serapis/task_grading_detail.html', template_context)



@login_required(login_url='/login/')
def submissions_full_log(request):
    user = User.objects.get(username=request.user)

    # check filters
    filtered_course = request.GET.get('course')
    filtered_assignment = request.GET.get('assignment')

    if filtered_assignment and int(filtered_assignment) > 0:
        assignment_obj = Assignment.objects.filter(id=filtered_assignment)
        submission_list = Submission.objects.filter(student_id=user, assignment_id=filtered_assignment)
        submissions_count = len(submission_list)
    elif filtered_course and int(filtered_course) > 0:
        filtered_assign_list = Assignment.objects.filter(course_id=filtered_course)
        submission_list = Submission.objects.filter(student_id=user, assignment_id__in=filtered_assign_list)
        submissions_count = len(submission_list)
        print(submission_list)

    else:
        submission_list = Submission.objects.filter(student_id = user).order_by('-submission_time')
        submissions_count = len(submission_list)

    course_list = [];
    assignment_list = [];
    score_list = [];
    total_points_list = [];
    for s in submission_list:
        course = s.assignment_id.course_id
        course_list.append(course)

        assignment = s.assignment_id;
        assignment_list.append(assignment)
        now = datetime.now(tz=pytz.timezone('UTC'))

        gradings = TaskGradingStatus.objects.filter(submission_id=s.id).order_by('assignment_task_id')
        score = 0;
        for task in gradings:
            if user.has_perm('modify_assignment', course) or task.assignment_task_id.mode != AssignmentTask.MODE_HIDDEN or now > assignment.deadline:
                if task.grading_status == TaskGradingStatus.STAT_FINISH:
                    score += task.points
        score = round(score, 2)
        score_list.append(score)

        if user.has_perm('modify_assignment', course) or now > assignment.deadline:
            assignment_tasks = AssignmentTask.objects.filter(assignment_id=s.assignment_id).order_by('id')
        else:
            assignment_tasks = AssignmentTask.objects.filter(assignment_id=s.assignment_id).exclude(mode=2).order_by('id')

        total_points = 0
        for a in assignment_tasks:
            total_points += a.points
        total_points_list.append(round(total_points,2))

    page = request.GET.get('page',1)
    submission_full_log_list = list(zip(submission_list, course_list, score_list, total_points_list))
    paginator = Paginator(submission_full_log_list, 10)
    try:
        submission_full_log = paginator.page(page)
    except PageNotAnInteger:
        submission_full_log = paginator.page(1)
    except EmptyPage:
        submission_full_log = paginator.page(paginator.num_pages)

    index = submission_full_log.number - 1
    max_index = len(paginator.page_range)
    start_index = index - 3 if index >= 3 else 0
    end_index = index + 3 if index <= max_index - 3 else max_index
    page_range = paginator.page_range[start_index:end_index]


    template_context = {
        'user': user,
        'submission_full_log':submission_full_log,
        'myuser': request.user,
        'page_range':page_range,
        'course_list':set(course_list),
        'assignment_list':set(assignment_list)
    }

    return render(request, 'serapis/submissions_full_log.html', template_context)
