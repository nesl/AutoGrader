import hashlib
import random

from django.contrib.auth import authenticate, login, logout, context_processors
from django.contrib.auth.models import Permission

from django.utils import timezone
from datetime import timedelta

from django.conf import settings

from django.core.urlresolvers import reverse
from django.http import *
from django.shortcuts import render, get_object_or_404

from serapis.models import *
from serapis.utils import send_email_helper
from serapis.forms.registration_forms import *


def _generate_activation_key(uid):
    random_string = str(random.random())
    salt = hashlib.sha1(random_string.encode('utf-8')).hexdigest()[:5] + uid
    return hashlib.sha1(salt.encode('utf-8')).hexdigest()

def _send_activation_email(activation_link, email):
    context = {
        'activation_link': activation_link,
        'site_name': settings.SITE_NAME,
    }
    send_email_helper.send_by_template(
            subject='Account Activation',
            recipient_email_list=[email],
            template_path='serapis/email/activation_email.html',
            context_dict=context,
    )

def registration(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            activation_key = _generate_activation_key(form.cleaned_data['uid'])
            form.save_and_commit(activation_key)  # Save the user and her profile
            activation_link = request.build_absolute_uri(
                    reverse('activation', kwargs={'key': activation_key}))
            _send_activation_email(activation_link, form.cleaned_data['email'])

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
        activation_link = request.build_absolute_uri(
                reverse('activation', kwargs={'key': activation_key}))
        _send_activation_email(activation_link, user.email)
        return HttpResponse("The new verification link has been sent to your email. Please check.")


def logout_view(request):
    logout(request)
