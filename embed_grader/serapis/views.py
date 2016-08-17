from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, context_processors
from django.template import RequestContext

from serapis.models import *

# import the logging library
import logging, logging.config
import sys
"""
LOGGING = {
        'version': 1,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
                }
            },
        'root': {
            'handlers': ['console'],
            'level': 'INFO'
            }
        }
# Get an instance of a logger
logging.config.dictConfig(LOGGING)
"""
logger = logging.getLogger(__name__)

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
