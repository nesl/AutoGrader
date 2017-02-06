from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm

from django import forms
from django.forms import Form, ModelForm
from django.forms import modelformset_factory
from django.forms import formset_factory
from django.forms import Textarea
from django.forms.widgets import HiddenInput
from django.core.exceptions import ValidationError

from django.utils.translation import gettext as _

from datetimewidget.widgets import DateTimeWidget, DateWidget, TimeWidget

from serapis.models import *
from serapis.utils import grading

from datetime import timedelta


class UserRegistrationForm(UserCreationForm):
    PASSWORD_MIN_LENGTH = 8
    UID_LENGTH = 9

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    error_messages = {
        'password_mismatch': "The two password fields didn't match.",
        'email_not_unique': "This email has been registered."
    }
    uid = forms.CharField(label="University ID", required=True, max_length=UID_LENGTH,
            min_length=UID_LENGTH)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput,
            min_length=PASSWORD_MIN_LENGTH)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput,
            help_text="Enter the same password as above, for verification.")

    def clean_uid(self):
        uid = self.cleaned_data.get('uid')
        if not all(c.isdigit() for c in uid):
            raise forms.ValidationError('UID should only contain digits', code='invalid_uid')
        if UserProfile.objects.filter(uid=uid).count() > 0:
            raise forms.ValidationError('UID already exists', code='duplicate_uid')
        return uid

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).count() > 0:
            raise forms.ValidationError(self.error_messages['email_not_unique'],
                code='email_not_unique')
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")

        # At least one letter and one digit
        first_isalpha = password1[0].isalpha()
        if not any(c.isalpha() for c in password1):
            raise forms.ValidationError("The new password must contain at least one letter",
                    code='no_letter_in_password')
        if not any(c.isdigit() for c in password1):
            raise forms.ValidationError("The new password must contain at least one digit",
                    code='no_digit_in_password')
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password1 != password2:
            raise forms.ValidationError(self.error_messages['password_mismatch'],
                code='password_mismatch')
        return password2

    def save_and_commit(self, activation_key):
        user = super(UserRegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False
        user.save()

        user_profile = UserProfile(user=user, uid=self.cleaned_data['uid'],
                activation_key=activation_key,
                key_expires=(timezone.now() + timedelta(days=2))
        )
        user_profile.save()

        return user, user_profile


