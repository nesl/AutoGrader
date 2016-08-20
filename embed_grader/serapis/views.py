from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, context_processors
from django.template import RequestContext
from django.forms import modelform_factory

from serapis.models import *


def registration(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = UserCreateForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            form.save()
            return HttpResponse("Thanks.")
    # if a GET (or any other method) we'll create a blank form
    else:
        form = UserCreateForm()
    return render(request, 'serapis/registration.html', {'form':form})


def logout_view(request):
    logout(request)


@login_required(login_url='/login/')
def homepage(request):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]

    #TODO: Check if user is student or instructor
    course_list = Course.objects.filter(instructor_id=user_profile)
    template_context = {
            'user_profile': user_profile,
            'myuser': request.user,
            'course_list': course_list,
    }
    return render(request, 'serapis/homepage.html', template_context)


@login_required(login_url='/login/')
def course(request, course_id):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    course_list = Course.objects.filter(id=course_id)
    if not course_list:
        return HttpResponse("Course cannot be found")
    course = course_list[0]
    #assignments = Assignment.objects.filter(course)
    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'course': course
    }
    return render(request, 'serapis/course.html', template_context)


@login_required(login_url='/login/')
def create_course(request):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    
    if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
        return HttpResponse("Not enough privilege")

    form = modelform_factory(Course, fields=('course_code', 'name', 'description'))
    print(form)

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form
    }
    return render(request, 'serapis/create_course.html', template_context)


@login_required(login_url='/login/')
def create_assignment(request, course_id):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    
    if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
        return HttpResponse("Not enough privilege")

    form = modelform_factory(Assignment, fields=('description', 'release_time', 'deadline', 'DUT_count', 'num_testbenches'))
    print(form.as_table())
    print('hello')
    course_list = Course.objects.filter(id=course_id)
    if not course_list:
        return HttpResponse("Course cannot be found")
    course = course_list[0]

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'course': course
    }
    return render(request, 'serapis/create_assignment.html', template_context)
