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
from serapis.forms.assignment_forms import *


@login_required(login_url='/login/')
#Only super user has access to create a course
def create_assignment(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return HttpResponse("Course cannot be found.")

    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('create_assignment', course):
    	return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        form = AssignmentBasicForm(request.POST)
        if form.is_valid():
            assignment = form.save()

            # create schema object accordingly
            assignmentTaskFileSchema = get_schema_list(assignment.assignent_task_file_schema)
            for s in assignmentTaskFileSchema:
                if s != '' and len(s) > 0:
                    AssignmentTaskFileSchema.objects.create(assignment_id=assignment, field=s)

            submissionFileSchema = get_schema_list(assignment.task_grading_schema)
            for s in submissionFileSchema:
                if s != '' and len(s) > 0:
                    SubmissionFileSchema.objects.create(assignment_id=assignment, field=s)
            
            taskGradingStatusFileSchema = get_schema_list(assignment.submission_file_schema)
            for s in taskGradingStatusFileSchema:
                if s != '' and len(s) > 0:
                    TaskGradingStatusFileSchema.objects.create(assignment_id=assignment, field=s)

            return HttpResponseRedirect(reverse('course', args=(course_id)))
    else:
        form = AssignmentBasicForm(initial={'course_id': course_id})

    form.fields['course_id'].widget = forms.NumberInput(attrs={'readonly':'readonly'})

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'course':course,
            'form': form,
    }
    return render(request, 'serapis/create_assignment.html', template_context)


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
        submission_list = Submission.objects.filter(assignment_id=assignment).values('student_id').annotate(submission_time=Max('submission_time'))
        for s in submission_list:
            submission_short_list.append(Submission.objects.get(student_id = s['student_id'], submission_time=s['submission_time']))
        submission_short_list.sort(key=lambda x:x.submission_time, reverse=True)
    else:
        submission_list = Submission.objects.filter(student_id=user, assignment_id=assignment).order_by('-submission_time')
        num_display = min(10, len(submission_list))
        submission_short_list = submission_list[:num_display]

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


@login_required(login_url='/login/')
def modify_assignment(request, assignment_id):
    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found")

    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    course = assignment.course_id
    if not user.has_perm('modify_assignment', course):
        return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        form = AssignmentBasicForm(request.POST, instance=assignment)
        if form.is_valid():
            # update schema info
            updated_assignment = form.save()
            update_schema_lists(assignment, updated_assignment)

            return HttpResponseRedirect('/assignment/' + assignment_id)
    else:
        form = AssignmentBasicForm(instance=assignment)

    tasks = None
    if assignment.testbed_type_id:
        form.fields['testbed_type_id'].widget = forms.NumberInput(attrs={'readonly':'readonly'})
        tasks = AssignmentTask.objects.filter(assignment_id=assignment).order_by('id')

    form.fields['course_id'].widget = forms.NumberInput(attrs={'readonly':'readonly'})

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'assignment': assignment,
            'form': form,
            'tasks': tasks,
            'course': course
    }
    return render(request, 'serapis/modify_assignment.html', template_context)


def get_schema_list(schemaString):
    schema_list = [s.strip() for s in schemaString.split(';')]
    return schema_list

def update_schema_lists(assignment, updated_assignment):
    # Update AssignmentTaskFileSchema
    assignmentTaskFileSchema = AssignmentTaskFileSchema.objects.filter(assignment_id=assignment)
    updated_assignmentTaskFileSchema = get_schema_list(updated_assignment.assignent_task_file_schema)

    # detele out-of-date schema
    field_list1 = []
    for schema in assignmentTaskFileSchema:
        if schema.field not in updated_assignmentTaskFileSchema:
            schema.delete()
            print("[AssignmentTaskFileSchema deleted]: " + schema.field)
        else:
            field_list1.append(schema.field)

    # add new schema
    for schema in updated_assignmentTaskFileSchema:
        if schema not in field_list1 and schema != '' and len(schema) > 0:
            AssignmentTaskFileSchema.objects.create(assignment_id=updated_assignment, field=schema)
            print("[AssignmentTaskFileSchema created]: " + schema)
    
    # Update SubmissionFileSchema
    submissionFileSchema = SubmissionFileSchema.objects.filter(assignment_id=assignment)
    updated_submissionFileSchema = get_schema_list(updated_assignment.submission_file_schema)

    # detele out-of-date schema
    field_list2 = []
    for schema in submissionFileSchema:
        if schema.field not in updated_submissionFileSchema:
            schema.delete()
            print("[SubmissionFileSchema deleted]: " + schema.field)
        else:
            field_list2.append(schema.field)

    # add new schema
    for schema in updated_submissionFileSchema:
        if schema not in field_list2 and schema != '' and len(schema) > 0:
            SubmissionFileSchema.objects.create(assignment_id=updated_assignment, field=schema)
            print("[SubmissionFileSchema created]: " + schema)


    # Update TaskGradingStatusFileSchema
    taskGradingStatusFileSchema = TaskGradingStatusFileSchema.objects.filter(assignment_id=assignment)
    updated_taskGradingStatusFileSchema = get_schema_list(updated_assignment.task_grading_schema)
 
    # detele out-of-date schema
    field_list3 = []
    for schema in taskGradingStatusFileSchema:
        if schema.field not in updated_taskGradingStatusFileSchema:
            schema.delete()
            print("[TaskGradingStatusFileSchema deleted]: " + schema.field)
        else:
            field_list3.append(schema.field)

    # add new schema
    for schema in updated_taskGradingStatusFileSchema:
        if schema not in field_list3 and schema != '' and len(schema) > 0:
            TaskGradingStatusFileSchema.objects.create(assignment_id=updated_assignment, field=schema)
            print("[TaskGradingStatusFileSchema create]: " + schema)

