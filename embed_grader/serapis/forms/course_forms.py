from django.contrib.auth.models import User, Group

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


class CourseCreationForm(ModelForm):
    error_messages = {
        'course_already_created': "Course already exists. Please modify the existing course or ask admin to delete it.",
    }

    class Meta:
        model = Course
        fields = ['course_code', 'name', 'quarter', 'year', 'description']
        YEAR_CHOICES = [(timezone.now().year + i, timezone.now().year + i) for i in range(3)]
        QUARTER_CHOICES = ((1, 'Fall'), (2, 'Winter'), (3, 'Spring'), (4, 'Summer'))
        widgets = {
                'description': forms.Textarea(attrs={'cols': 40, 'rows': 5}),
                'year': forms.Select(choices=YEAR_CHOICES),
                'quarter': forms.Select(choices=QUARTER_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CourseCreationForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        course = super(CourseCreationForm, self).save(commit=False)
        if commit:
            course.save()
        course_user_list = CourseUserList.objects.create(user_id=self.user, course_id=course)
        return course


class CourseCompleteForm(ModelForm):
    class Meta:
        model = Course
        fields = ['course_code', 'name', 'quarter', 'year', 'description']
        YEAR_CHOICES = [(timezone.now().year + i, timezone.now().year + i) for i in range(3)]
        QUARTER_CHOICES = ((1, 'Fall'), (2, 'Winter'), (3, 'Spring'), (4, 'Summer'))
        widgets = {
                'description': forms.Textarea(attrs={'cols': 40, 'rows': 5}),
                'year': forms.Select(choices=YEAR_CHOICES),
                'quarter': forms.Select(choices=QUARTER_CHOICES)
        }


class CourseEnrollmentForm(Form):
    error_messages = {
        'course_already_enrolled': "You have already enrolled in this course.",
    }
    current_year = timezone.now().year
    course_select = forms.ModelChoiceField(queryset=Course.objects.filter(year=current_year))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CourseEnrollmentForm, self).__init__(*args, **kwargs)

    def clean(self):
        course = self.cleaned_data.get("course_select")
        if CourseUserList.objects.filter(user_id=self.user, course_id=course).count():
            raise forms.ValidationError(self.error_messages['course_already_enrolled'],
                code='course_already_enrolled')
        return self.cleaned_data

    def save(self, commit=True):
        course=self.cleaned_data['course_select']
        course_user_list = CourseUserList.objects.create(user_id=self.user, course_id=course)


