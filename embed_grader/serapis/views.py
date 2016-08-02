from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, context_processors
from django.template import RequestContext


# Create your views here.

def index(request):
    return HttpResponse("Hello World!")


def login_user(request):
    logout(request)
    uid = password = ''
    if request.POST:
        uid = request.POST['username']
        password = request.POST['password']

        myuser = authenticate(username=uid, password=password)
        if myuser is not None:
            if myuser.is_active:
                login(request, myuser)
                return HttpResponseRedirect('/homepage/')
    return render_to_response('login.html', context_instance=RequestContext(request))

@login_required(login_url='/login/')
def homepage(request):
    return render(request, 'serapis/homepage.html', {'myuser':request.user})


def registration(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
            return HttpResponse("Thanks.")
    # if a GET (or any other method) we'll create a blank form
    else:
        form = UserCreationForm()
    return render(request, 'main/registration.html', {'form':form})

def logout_view(request):
    logout(request)
