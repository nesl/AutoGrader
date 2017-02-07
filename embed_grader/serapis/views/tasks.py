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


def _create_or_modify_assignment(request, assignment_id, assignment_task):
    """
    if assignment_task is None, it is creating mode, otherwise it is updating mode
    """

    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found")

    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)
    
    course = assignment.course_id

    if not user.has_perm('modify_assignment', course):
    	return HttpResponse("Not enough privilege")
    
    mode = 'update' if assignment_task else 'create'

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
    }
    return render(request, 'serapis/create_or_modify_assignment_task.html', template_context)


@login_required(login_url='/login/')
def create_assignment_task(request, assignment_id):
    return _create_or_modify_assignment(
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

    return _create_or_modify_assignment(
            request=request,
            assignment_id=task.assignment_id.id,
            assignment_task=task,
    )
