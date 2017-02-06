from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group

from django.shortcuts import render, get_object_or_404
from django.http import *
from django.core.exceptions import PermissionDenied

from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Max
from django.views.generic import TemplateView

from guardian.decorators import permission_required_or_403
from serapis.models import *


@login_required(login_url='/login/')
def homepage(request):
    username = request.user
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)

    course_user_list = CourseUserList.objects.filter(user_id=user)
    course_list = [cu.course_id for cu in course_user_list]
    template_context = {
            'user_profile': user_profile,
            'myuser': request.user,
            'course_list': course_list,
    }
    return render(request, 'serapis/homepage.html', template_context)


@login_required(login_url='/login/')
def about(request):
    user = User.objects.get(username=request.user)
    template_context = {'myuser': request.user}
    return render(request, 'serapis/about.html', template_context)
