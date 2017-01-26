import hashlib
import random
import pytz
import json
from datetime import timedelta

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

from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from guardian.decorators import permission_required_or_403
from guardian.compat import get_user_model
from guardian.shortcuts import assign_perm

from serapis.models import *
from serapis.model_forms import *


@login_required(login_url='/login/')
def create_assignment_task(request, assignment_id):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found")

    course = assignment.course_id

    if not user.has_perm('modify_assignment',course):
    	return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        form = AssignmentTaskForm(request.POST, request.FILES, assignment=assignment)
        if form.is_valid():
            form.save_and_commit()
            return HttpResponseRedirect(reverse('modify-assignment',
                    kwargs={'assignment_id': assignment_id}))
    else:
        form = AssignmentTaskForm(assignment=assignment)

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form,
            'course': course,
            'assignment': assignment,
    }
    return render(request, 'serapis/create_assignment_task.html', template_context)

@login_required(login_url='/login/')
def modify_assignment_task(request, task_id):
    try:
        task = AssignmentTask.objects.get(id=task_id)
    except AssignmentTask.DoesNotExist:
        return HttpResponse("Assignment task cannot be found")

    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    try:
        assignment = Assignment.objects.get(id=task.assignment_id.id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found")

    course = assignment.course_id

    if not user.has_perm('modify_assignment',course):
    	return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        form = AssignmentTaskUpdateForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            assignment_task = form.save(commit=False)
            assignment_task.assignment_id = assignment
            binary = assignment_task.grading_script.read()
            # res, msg = grading.check_format(binary)
            res = True
            if res:
                # assignment_task.execution_duration = float(grading.get_length(binary)) / 5000.0
                assignment_task.save()
                return HttpResponseRedirect('/assignment/' + str(assignment.id))
            else:
                #TODO(timestring): display why failed
                print("modify assignment task failed")
                pass
    else:
        form = AssignmentTaskUpdateForm(instance=task)

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form,
            'course': course,
            'assignment': assignment,
    }
    return render(request, 'serapis/modify_assignment_task.html', template_context)


@login_required(login_url='/login/')
def debug_task_grading_status(request):
    username = request.user
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)

    if request.method == 'POST':
        form = TaskGradingStatusDebugForm(request.POST, request.FILES)
        if form.is_valid():
            #task = form.save(commit=False)
            task = TaskGradingStatus.objects.get(id=request.POST['id'])
            task.grading_status = form.cleaned_data['grading_status']
            task.execution_status = form.cleaned_data['execution_status']
            task.output_file = form.cleaned_data['output_file']
            task.status_update_time = timezone.now()
            task.save()

    form = TaskGradingStatusDebugForm()

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form,
    }
    return render(request, 'serapis/debug_task_grading_status.html', template_context)
