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

import os
from zipfile import ZipFile
from io import BytesIO

from serapis.models import *
from serapis.forms.task_forms import *
from serapis.utils.visualizer_manager import VisualizerManager
from serapis.utils import file_schema

def _create_or_modify_assignment_task(request, assignment_id, assignment_task):
    """
    if assignment_task is None, it is creating mode, otherwise it is updating mode
    """

    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponseBadRequest("Assignment cannot be found")

    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    course = assignment.course_fk

    if not user.has_perm('modify_assignment', course):
        return HttpResponseBadRequest("Not enough privilege")

    mode = 'modify' if assignment_task else 'create'

    if request.method == 'POST':
        form = AssignmentTaskForm(request.POST, request.FILES,
                assignment=assignment, instance=assignment_task)
        if form.is_valid():
            form.save_and_commit()
            return HttpResponseRedirect(reverse('assignment',
                    kwargs={'assignment_id': assignment_id}))
    else:
        form = AssignmentTaskForm(assignment=assignment, instance=assignment_task)

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'mode': mode,
            'form': form,
            'course': course,
            'assignment': assignment,
            'assignment_task': assignment_task,
    }
    return render(request, 'serapis/create_or_modify_assignment_task.html', template_context)


@login_required(login_url='/login/')
def create_assignment_task(request, assignment_id):
    return _create_or_modify_assignment_task(
            request=request,
            assignment_id=assignment_id,
            assignment_task=None,
    )


@login_required(login_url='/login/')
def modify_assignment_task(request, task_id):
    try:
        task = AssignmentTask.objects.get(id=task_id)
    except AssignmentTask.DoesNotExist:
        return HttpResponseBadRequest("Assignment task cannot be found")

    return _create_or_modify_assignment_task(
            request=request,
            assignment_id=task.assignment_fk.id,
            assignment_task=task,
    )


@login_required(login_url='/login/')
def delete_assignment_task(request):
    if request.method != 'POST':
        HttpResponse("Not enough privilege", status=404)

    try:
        task = AssignmentTask.objects.get(id=request.POST.get('task_id'))
    except AssignmentTask.DoesNotExist:
        return HttpResponseBadRequest("Assignment task cannot be found")

    assignment = task.assignment_fk
    course = assignment.course_fk

    user = User.objects.get(username=request.user)

    if not user.has_perm('modify_assignment', course):
        return HttpResponse("Not enough privilege")

    task.delete()

    return HttpResponseRedirect(
            reverse('assignment', kwargs={'assignment_id': assignment.id}))


@login_required(login_url='/login/')
def zip_input_files(request, task_id):
    try:
        task = AssignmentTask.objects.get(id=task_id)
    except AssignmentTask.DoesNotExist:
        return HttpResponseBadRequest("Assignment task cannot be found")

    user = User.objects.get(username=request.user)
    assignment = task.assignment_fk
    course = assignment.course_fk
    if not user.has_perm('view_assignment', course):
        return HttpResponseBadRequest("Not enough privilege")

    # retrieve task status
    in_memory = BytesIO()
    input_zip = ZipFile(in_memory, "w")
    task_files = task.retrieve_assignment_task_files(user)

    if not task_files:
        return HttpResponseBadRequest("Not enough privilege")

    for f_obj in task_files:
        _, fname = os.path.split(f_obj.file.url)
        raw_content = f_obj.file.read()
        input_zip.writestr(fname, raw_content)

    # for Linux zip files read in Windows
    for f in input_zip.filelist:
        f.create_system = 0
    input_zip.close()

    response = HttpResponse(in_memory.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename={0}_{1}_input.zip".format(assignment, task)

    return response


@login_required(login_url='/login/')
def view_task_input_files(request, task_id):
    try:
        task = AssignmentTask.objects.get(id=task_id)
    except AssignmentTask.DoesNotExist:
        return HttpResponseBadRequest("Assignment task cannot be found")

    user = User.objects.get(username=request.user)
    assignment = task.assignment_fk
    course = assignment.course_fk
    if not user.has_perm('view_assignment', course):
        return HttpResponseBadRequest("Not enough privilege")

    task_files = task.retrieve_assignment_task_files(user)
    if not task_files:
        return HttpResponseBadRequest("Not enough privilege")

    input_files = file_schema.get_dict_schema_name_to_assignment_task_schema_files(task, enforce_check=True)

    visualizer_manager = VisualizerManager()

    for field_name in input_files:
        file = input_files[field_name].file
        raw_content = file.read()
        url = file.url
        visualizer_manager.add_file(field_name, raw_content, url)

    template_context = {
            'myuser': request.user,
            'course': course,
            'assignment': assignment,
            'task': task,
            'visualizer_manager': visualizer_manager,
    }
    return render(request, 'serapis/view_task_input.html', template_context)
