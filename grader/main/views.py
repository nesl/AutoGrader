from django.http import *
from django.shortcuts import render
from django.template import RequestContext
from main.models import *
from main.admin import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, context_processors

"""def login_user(request):
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

def login_user(request):
    template_response = views.login(request)
    # Do something with `template_response`
    return template_response
"""

@login_required(login_url='/login/')
def homepage(request):
    return render(request, 'main/homepage.html', {'myuser':request.user})

def registration(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = UserCreationForm(request.POST)
        print form.errors
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            form.save()
            return HttpResponse("Thanks.")
    # if a GET (or any other method) we'll create a blank form
    else:
        form = UserCreationForm()
    return render(request, 'main/registration.html', {'form':form})

def logout_view(request):
    logout(request)

#def successfully_logged_out(request):
   # return HttpResponse("Goodbye.")
