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


def login_user(request):
    logout(request)
    uid = password = ''
    if request.POST:
        uid = request.POST['username']
        password = request.POST['password']

        myuser = authenticate(username=uid, password=password)
        #print('myuser')
        #print(myuser)
        #print("fatal error", file=sys.stderr)
        logger.error('myuser')
        if myuser is not None:
            if myuser.is_active:
                login(request, myuser)
                return HttpResponseRedirect('/homepage/')
    return render_to_response('login.html', context_instance=RequestContext(request))

@login_required(login_url='/login/')
def homepage(request):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    return render(request, 'serapis/homepage.html', {'user_profile': user_profile, 'myuser': request.user})


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
