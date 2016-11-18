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
    form = UserRegistrationForm()
    datas = {}
    user = User.objects.get(id=user_id)
    if not user.is_active:
        datas['uid'] = user.uid
        datas['email'] = user.email
        datas['email_path'] = "serapis/activation_email_resend.html"
        datas['email_subject'] = "Account Activation Resend"

        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        usernamesalt = datas['uid']
        if isinstance(usernamesalt, unicode):
            usernamesalt = usernamesalt.encode('utf8')
        datas['activation_key'] = hashlib.sha1(salt+usernamesalt).hexdigest()

        user_profile = UserProfile.objects.get(user=user)
        user_profile.activation_key = datas['activation_key']
        user_profile.key_expires = datetime.strftime(timezone.now() + timedelta(days=2), "%Y-%m-%d %H:%M:%S")
        user_profile.save()
        form.sendEmail(datas)
        request.session['new_link'] = True  # Display : new link send

    return HttpResponse("The new verification link has been sent to your email. Please check.")


def logout_view(request):
    logout(request)
