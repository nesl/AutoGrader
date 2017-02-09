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
from serapis.forms.course_forms import *


def _create_or_modify_course(request, course):
    """
    if course is None, it is creating mode, otherwise it is in updating mode
    """
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('serapis.create_course'):
        return HttpResponse("Not enough privilege.")
    
    if request.method == 'POST':
        form = CourseCreationForm(request.POST, instance=course, user=user)
        if form.is_valid():
            course = form.save_and_commit()
            return HttpResponseRedirect(reverse('course', kwargs={'course_id': course.id}))
    else:
        form = CourseCreationForm(instance=course, user=user)

    mode = 'modify' if course else 'create'

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'mode': mode,
            'course': course,
            'form': form,
    }
    return render(request, 'serapis/create_or_modify_course.html', template_context)


@login_required(login_url='/login/')
def create_course(request):
    return _create_or_modify_course(request, None)


@login_required(login_url='/login/')
def modify_course(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return HttpResponse("Course cannot be found.")

    return _create_or_modify_course(request, course)


@login_required(login_url='/login/')
def course(request, course_id):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return HttpResponse("Course cannot be found.")

    if not user.has_perm('view_course', course):
        return HttpResponse("Not enough privilege.")

    assignment_list = Assignment.objects.filter(course_id=course_id)

    if not user.has_perm('modify_course', course):
        assignment_list = [a for a in assignment_list if a.is_released()]

    template_context = {
        'myuser': request.user,
        'course': course,
        'assignment_list': assignment_list,
    }
    return render(request, 'serapis/course.html', template_context)


@login_required(login_url='/login/')
def enroll_course(request):
    user = User.objects.get(username=request.user)

    if request.method == 'POST':
        form = CourseEnrollmentForm(request.POST, user=user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('homepage'))
    else:
        form = CourseEnrollmentForm(user=user)

    template_context = {
        'myuser': user,
        'form': form,
    }

    return render(request, 'serapis/enroll_course.html', template_context)


@login_required(login_url='/login/')
def membership(request, course_id):
    user = User.objects.get(username=request.user)

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return HttpResponse("Course cannot be found.")

    if not user.has_perm('view_membership', course):
        return HttpResponse("Not enough privilege")

    students = []
    instructors = []
    assistants = []
    user_enrolled = []
    cu_list = CourseUserList.objects.filter(course_id=course)
    for cu in cu_list:
        member = UserProfile.objects.get(user=cu.user_id)

        if cu.role == ROLE_INSTRUCTOR:
            instructors.append(member)
        elif cu.role == ROLE_TA:
            assistants.append(member)
        elif cu.role == ROLE_STUDENT:
            students.append(member)
        user_enrolled.append(member)

    template_context = {
        'myuser': request.user,
        'course': course,
        'user_enrolled': user_enrolled,
        'students': students,
        'teaching_assistants': assistants,
        'instructors': instructors,
    }

    return render(request, 'serapis/roster.html', template_context)
