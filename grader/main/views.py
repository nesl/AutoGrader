from django.http import *
from django.shortcuts import render
from django.template import RequestContext
from main.models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

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
    return render(request, 'homepage.html', {'myuser':request.myuser})
