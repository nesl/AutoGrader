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
from serapis.forms.task_forms import *

import os
from zipfile import ZipFile
from io import BytesIO


def _create_or_modify_assignment_task(request, assignment_id, assignment_task):
    """
    if assignment_task is None, it is creating mode, otherwise it is updating mode
    """

    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found")

    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    course = assignment.course_fk

    if not user.has_perm('modify_assignment', course):
        return HttpResponse("Not enough privilege")

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
        return HttpResponse("Assignment task cannot be found")

    return _create_or_modify_assignment_task(
            request=request,
            assignment_id=task.assignment_fk.id,
            assignment_task=task,
    )


@login_required(login_url='/login/')
def delete_assignment_task(request, task_id):
    try:
        task = AssignmentTask.objects.get(id=task_id)
    except AssignmentTask.DoesNotExist:
        return HttpResponse("Assignment task cannot be found")

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
        return HttpResponse("Assignment task cannot be found")

    user = User.objects.get(username=request.user)
    assignment = task.assignment_fk

    # retrieve task status
    # can_see_hidden_cases = (assignment.viewing_scope_by_user(user) == Assignment.VIEWING_SCOPE_FULL)
    in_memory = BytesIO()
    input_zip = ZipFile(in_memory, "w")
    task_files = task.retrieve_assignment_task_files_obj(user)

    for f_obj in task_files:
        fdir, fname = os.path.split(f_obj.file.url)
        raw_content = f_obj.file.read()
        input_zip.writestr(fname, raw_content)

    # for Linux zip files read in Windows
    for f in input_zip.filelist:
        f.create_system = 0
    input_zip.close()


    response = HttpResponse(in_memory.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename={0}_{1}_input.zip".format(assignment, task)

    return response
