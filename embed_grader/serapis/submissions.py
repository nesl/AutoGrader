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

    submission_files = file_schema.get_submission_files(assignment, submission)

    submission_filename_list = []
    submission_file_path_list = []
    for s in submission_files:
        if submission_files[s].file:
            submission_filename_list.append(s)
            submission_file_path_list.append(submission_files[s].file)

    submission_file_list = list(zip(submission_filename_list, submission_file_path_list))

    template_context = {
        'submission':submission,
        'assignment': assignment,
        'course': course,
        'author':author,
        'submission_n_detail_short_list':submission_n_detail_short_list,
        'score':score,
        'total_points':total_points,
        'myuser': request.user,
        'now':now,
        'submission_files':submission_file_list    
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

    task_grading_status = TaskGradingStatus.objects.filter(submission_id=submission, assignment_task_id=assignment_task)
    output_files = file_schema.get_task_grading_status_files(assignment, task_grading_status)
    output_field_list = []
    output_content_list = []
    for f in output_files:
        content = open(output_files[f].file.path, 'r').read()
        if content != '':
            output_field_list.append(f)
            output_content_list.append(content)

    output_full_log = list(zip(output_field_list, output_content_list))

    # if grading.grading_detail:
    #     feedback = open(grading.grading_detail.path, 'r').read()

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
        'grading': grading,
        'assignment_task': assignment_task,
        'output_log':output_full_log
        # 'feedback': feedback,
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
    now = datetime.now(tz=pytz.timezone('UTC'))
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

    template_context = {
        'user': user,
        'submission_full_log':submission_full_log_list,
        'myuser': request.user,
        'now':datetime.now().replace(microsecond=0)
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
