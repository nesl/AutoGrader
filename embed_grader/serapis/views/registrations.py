import hashlib
import random
import pytz
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout, context_processors
from django.contrib.auth.models import Permission

from django.utils import timezone

from django.core.urlresolvers import reverse
from django.http import *
from django.shortcuts import render, get_object_or_404

from django.template.loader import get_template
from django.template import Context
from django.core.mail import send_mail

from serapis.models import *
from serapis.model_forms import *


def _generate_activation_key(uid):
    random_string = str(random.random())
    salt = hashlib.sha1(random_string.encode('utf-8')).hexdigest()[:5] + uid
    return hashlib.sha1(salt.encode('utf-8')).hexdigest()

def _send_email(activation_key, email):
    link = reverse('activation', kwargs={'key': '123'})
    template = get_template("serapis/activation_email.html")
    context = Context({'activation_link': link})
    message = template.render(context)
    send_mail(subject='Account Activation',
            message=message,
            from_email='NESL Embed AutoGrader',
            recipient_list=[email],
            fail_silently=False,
    )

def registration(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            activation_key = _generate_activation_key(form.cleaned_data['uid'])
            form.save_and_commit(activation_key)  # Save the user and her profile
            _send_email(activation_key, form.cleaned_data['email'])

            request.session['registered'] = True  # For display purposes
            return render(request, 'serapis/registration_done.html', locals())
    else:
        form = UserRegistrationForm()
    return render(request, 'serapis/registration.html', {'form': form})


# View called from activation email. Activate user if link didn't expire (48h default), or offer to
# send a second link if the first expired.
def activation(request, key):
    activation_expired = False
    already_active = False
    user_profile = get_object_or_404(UserProfile, activation_key=key)
    user = user_profile.user
    if user_profile.user.is_active:
        already_active = True  # for displaying already-active message
    elif timezone.now() > user_profile.key_expires:
        activation_expired = True  # offer a new activation link
    else:  # Activation successful
        user_profile.user.is_active = True
        user_profile.user.save()
    return render(request, 'serapis/activation.html', locals())


def new_activation(request, user_id):
    user = User.objects.get_object_or_404(id=user_id)
    user_profile = UserProfile.objects.get_object_or_404(user=user)
    if user.is_active:
        return HttpResponse("The user has been activated")
    else:
        activation_key = _generate_activation_key(user_profile.uid)
        _send_email(activation_key, user.email)
        return HttpResponse("The new verification link has been sent to your email. Please check.")


def logout_view(request):
    logout(request)
