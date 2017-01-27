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
from serapis.utils import file_schema


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

    task_grading_status_list = TaskGradingStatus.objects.filter(
            submission_id=submission_id).order_by('assignment_task_id')
    now = timezone.now()
    can_see_hidden_cases = user.has_perm('modify_assignment', course) or now > assignment.deadline
    
    if not can_see_hidden_cases:
        task_grading_status_list = [t for t in task_grading_status_list
                if t.assignment_task_id.mode != ASSIGNMENT_TASK_HIDDEN]

    task_symbols = []
    student_score = 0.
    total_score = 0.

    for grading_status in task_grading_status_list:
        total_score += grading_status.assignment_task_id.points
        student_score += grading_status.points
        tmp = grading_status.points
        grading_status.points = round(tmp, 2)
        tmp = grading_status.assignment_task_id.points
        grading_status.assignment_task_id.points = round(tmp, 2)

    student_score = round(student_score, 2)
    total_score = round(total_score, 2)

    submission_file_dict = file_schema.get_submission_files(submission)
    submission_file_list = []  # a list of {filename, file_field}

    for s in submission_file_dict:
        if submission_file_dict[s].file:
            submission_file_list.append({
                'filename': s,
                'file_field': submission_file_dict[s].file,
            })

    template_context = {
        'myuser': request.user,
        'now': now,
        'submission': submission,
        'assignment': assignment,
        'course': course,
        'author': author,
        'student_score': student_score,
        'total_score': total_score,
        'submission_file_list': submission_file_list,
        'task_grading_status_list': task_grading_status_list,
    }
    return render(request, 'serapis/submission.html', template_context)


@login_required(login_url='/login/')
def task_grading_detail(request, task_grading_id):
    try:
        task_grading_status = TaskGradingStatus.objects.get(id=task_grading_id)
    except Submission.DoesNotExist:
        return HttpResponse("Task grading detail cannot be found")

    user = User.objects.get(username=request.user)
    submission = task_grading_status.submission_id
    assignment = submission.assignment_id
    course = assignment.course_id
    if not user.has_perm('view_assignment', course):
        return HttpResponse("Not enough privilege")

    author = submission.student_id
    if not user.has_perm('modify_assignment', course):
        if author != user:
            return HttpResponse("Not enough privilege")

    assignment_task = task_grading_status.assignment_task_id
    task_grading_status.points = round(task_grading_status.points, 2)

    output_files = file_schema.get_task_grading_status_files(task_grading_status)
    output_full_log = []  # A list of {field_name, content}

    for f in output_files:
        raw_content = output_files[f].file.read()
        if len(raw_content) == 0:
            content = '(Empty file)'
        else:
            try:
                content = raw_content.decode('ascii')
            except:
                content = '(The file includes non-ascii characters)'
        output_full_log.append({
            'field_name': f,
            'content': content,
        })

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

    template_context = {
        'myuser': request.user,
        'course': course,
        'assignment': assignment,
        'submission': submission,
        'author': author,
        'grading': task_grading_status,
        'assignment_task': assignment_task,
        'output_log': output_full_log,
        'feedback': feedback,
        # 'js_plot_pack_string': js_plot_pack_string,
    }

    return render(request, 'serapis/task_grading_detail.html', template_context)


@login_required(login_url='/login/')
def submissions_full_log(request):
    user = User.objects.get(username=request.user)

    submission_list = Submission.objects.filter(student_id = user).order_by('-submission_time')
    submissions_count = len(submission_list)

    course_list = [];
    assignment_list = [];
    score_list = [];
    score_percentage_list = [];
    now = timezone.now()
    for s in submission_list:
        course = s.assignment_id.course_id
        course_list.append(course)

        assignment = s.assignment_id;
        assignment_list.append(assignment)

        gradings = TaskGradingStatus.objects.filter(submission_id=s.id).order_by('assignment_task_id')
        score = 0;
        for task in gradings:
            if user.has_perm('modify_assignment', course) or task.assignment_task_id.mode != AssignmentTask.MODE_HIDDEN or now > assignment.deadline:
                if task.grading_status == TaskGradingStatus.STAT_FINISH:
                    score += task.points
        score = round(score, 2)

        if user.has_perm('modify_assignment', course) or now > assignment.deadline:
            assignment_tasks = AssignmentTask.objects.filter(assignment_id=s.assignment_id).order_by('id')
        else:
            assignment_tasks = AssignmentTask.objects.filter(assignment_id=s.assignment_id).exclude(mode=2).order_by('id')

        total_points = 0
        for a in assignment_tasks:
            total_points += a.points

        if total_points == 0:
            score_percentage = 100
        else:
            score_percentage = (score/total_points)*100
        score_percentage_list.append(round(score_percentage,2))

    submission_full_log_list = list(zip(submission_list, course_list, score_percentage_list))

    #TODO: should only keep either user or myuser
    template_context = {
        'user': user,
        'submission_full_log': submission_full_log_list,
        'myuser': request.user,
        'now': timezone.now().replace(microsecond=0)
    }

    return render(request, 'serapis/submissions_full_log.html', template_context)

@login_required(login_url='/login/')
def student_submission_full_log(request):
    user = User.objects.get(username=request.user)
    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponse("Not enough privilege")
    courses_as_instructor = CourseUserList.objects.filter(user_id=user).exclude(role=ROLE_STUDENT)

    assignment_list = []
    for course in courses_as_instructor:
        course_assignments = Assignment.objects.filter(course_id=course.course_id)
        for assign in course_assignments:
            assignment_list.append(assign)

    students_submission_log = []
    course_list = []
    score_percentage_list = []
    name_list = []
    for assign in assignment_list:
        assign_submissions = Submission.objects.filter(assignment_id=assign).exclude(student_id=user)
        for s in assign_submissions:
            course_list.append(s.assignment_id.course_id)
            students_submission_log.append(s)

            student = User.objects.get(username = s.student_id)
            name_list.append(student.first_name + " " + student.last_name)

            gradings = TaskGradingStatus.objects.filter(submission_id=s.id).order_by('assignment_task_id')
            score = 0;
            for task in gradings:
                if task.grading_status == TaskGradingStatus.STAT_FINISH:
                    score += task.points
            score=round(score, 2)

            assignment_tasks = AssignmentTask.objects.filter(assignment_id=s.assignment_id).order_by('id')
            total_points = 0
            for a in assignment_tasks:
                total_points += a.points
            if total_points == 0:
                score_percentage = 100
            else:
                score_percentage = (score/total_points)*100
            score_percentage_list.append(round(score_percentage,2))

    submission_full_log_list = list(zip(students_submission_log, course_list, score_percentage_list, name_list))

    template_context = {
        'user':user,
        'myuser':request.user,
        'submission_full_log':submission_full_log_list
    }
    return render(request, 'serapis/student_submission_full_log.html', template_context)
