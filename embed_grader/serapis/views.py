from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, context_processors
from django.template import RequestContext

from serapis.models import *

def index(request):
    return HttpResponse("Hello World!")

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

def registration(request):
    if request.method == 'POST':
    # if this is a POST request we need to process the form data
        return HttpResponse("Thanks.")
    else:
    # if a GET (or any other method) we'll create a blank form
        form = UserCreationForm()
    return render(request, 'main/registration.html', {'form':form})

def logout_view(request):
    logout(request)

@login_required(login_url='/login/')
def course(request, course_id):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    course_list = Course.objects.filter(id=course_id)
    print(course_list)
    if not course_list:
        return HttpResponse("Course cannot be found")

    course = course_list[0]
    return render(request, 'serapis/homepage.html', {'user_profile': user_profile, 'myuser': request.user})

