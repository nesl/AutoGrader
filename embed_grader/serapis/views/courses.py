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


@login_required(login_url='/login/')
def create_course(request):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('serapis.create_course'):
        return HttpResponse("Not enough privilege.")

    if request.method == 'POST':
        form = CourseCreationForm(request.POST, user=request.user)
        if form.is_valid():
            # database
            course = form.save()

            # permission: create groups, add group permissions
            instructor_group_name = str(course.id) + "_Instructor_Group"
            student_group_name = str(course.id) + "_Student_Group"

            # get_or_create will raise error here
            # instructor_group = Group.objects.get_or_create(name=instructor_group_name)
            # student_group = Group.objects.get_or_create(name=student_group_name)
            instructor_group = Group.objects.create(name=instructor_group_name)
            student_group = Group.objects.create(name=student_group_name)
            user.groups.add(instructor_group)

            #assign permissions
            assign_perm('serapis.view_hardware_type', instructor_group)
            assign_perm('view_course', instructor_group, course)
            assign_perm('view_course', student_group, course)
            assign_perm('serapis.create_course', instructor_group)
            assign_perm('modify_course', instructor_group, course)
            assign_perm('view_membership', instructor_group, course)
            assign_perm('view_assignment', instructor_group, course)
            assign_perm('view_assignment', student_group, course)
            assign_perm('modify_assignment', instructor_group, course)
            assign_perm('create_assignment', instructor_group, course)

            return HttpResponseRedirect(reverse('homepage'))
    else:
        form = CourseCreationForm()

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form,
    }
    return render(request, 'serapis/create_course.html', template_context)


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

    if not user.has_perm('modify_course',course):
        for assignment in assignment_list:
            now = timezone.now()
            if now < assignment.release_time:
                assignment_list = Assignment.objects.filter(course_id=course_id, release_time__lte=now)

    template_context = {
        'myuser': request.user,
        'course': course,
        'assignment_list': assignment_list,
    }
    return render(request, 'serapis/course.html', template_context)


@login_required(login_url='/login/')
def modify_course(request, course_id):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return HttpResponse("Course cannot be found.")

    if not user.has_perm('modify_course', course):
        return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        form = CourseCompleteForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            return HttpResponseRedirect('/course/'+course_id)
    else:
        form = CourseCompleteForm(instance=course)

    template_context = {
        'myuser': request.user,
        'user_profile': user_profile,
        'course':course,
        'form': form
    }

    return render(request, 'serapis/modify_course.html', template_context)


@login_required(login_url='/login/')
def enroll_course(request):
    user = User.objects.get(username=request.user)
    error_message = ''
    if request.method == 'POST':
        form = CourseEnrollmentForm(request.POST, user=request.user)
        if form.is_valid():
            # database
            form.save()

            # add user to belonged group
            course = form.cleaned_data['course_select']
            student_group_name = str(course.id) + "_Student_Group"
            student_group = Group.objects.get(name=student_group_name)
            user.groups.add(student_group)

            return HttpResponseRedirect(reverse('homepage'))
        error_message = "You have already enrolled in this course."
    else:
        form = CourseEnrollmentForm(user=request.user)

    template_context = {
        'form': form,
        'error_message': error_message,
        'myuser': request.user
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
