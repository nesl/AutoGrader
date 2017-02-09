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
    class Meta:
        model = Course
        fields = ['course_code', 'name', 'description']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(CourseCreationForm, self).__init__(*args, **kwargs)
        
        now = timezone.now()
        cur_year = now.year 
        cur_month = now.month
        cur_quarter = (cur_month - 1) // 3
        cur_year_quarter = cur_year * 4 + cur_quarter
        year_quarter_choices_idx = [cur_year_quarter + offset for offset in range(5)]
        year_quarter_choices = [(yq, '%d %s' % (yq // 4, Course.QUARTER_DICT[yq % 4]))
                for yq in year_quarter_choices_idx]
        self.fields['year_quarter'] = forms.ChoiceField(
                required=True,
                widget=forms.Select,
                choices=year_quarter_choices,
        )
        self.order_fields(['course_code', 'name', 'year_quarter', 'description'])

    def clean(self):
        super(CourseCreationForm, self).clean()
        if 'course_code' in self.cleaned_data:
            self.cleaned_data['course_code'] = self.cleaned_data['course_code'].upper()
        return self.cleaned_data

    def save(self, commit=True):
        raise Exception('Deprecated method')

    def save_and_commit(self):
        year, quarter = divmod(int(self.cleaned_data['year_quarter']), 4)
        course = Course.objects.create(
                course_code=self.cleaned_data['course_code'],
                name=self.cleaned_data['name'],
                description=self.cleaned_data['description'],
                year=year,
                quarter=quarter,
        )
        course_user_list = CourseUserList.objects.create(
                user_id=self.user, course_id=course, role=CourseUserList.ROLE_INSTRUCTOR)

        # permission: create groups, add group permissions
        #TODO: don't hardcode strings here
        instructor_group_name = str(course.id) + "_Instructor_Group"
        student_group_name = str(course.id) + "_Student_Group"

        instructor_group = Group.objects.create(name=instructor_group_name)
        student_group = Group.objects.create(name=student_group_name)
        
        self.user.groups.add(instructor_group)

        #assign permissions
        assign_perm('serapis.view_hardware_type', instructor_group)
        assign_perm('view_course', instructor_group, course)
        assign_perm('view_course', student_group, course)
        assign_perm('serapis.create_course', instructor_group)
        assign_perm('modify_course', instructor_group, course)
        assign_perm('view_membership', instructor_group, course)
        assign_perm('view_assignment', instructor_group, course)
        assign_perm('view_assignment', student_group, course)
        assign_perm('modify_assignment', instructor_group, course)
        assign_perm('create_assignment', instructor_group, course)

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
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(CourseEnrollmentForm, self).__init__(*args, **kwargs)

        current_year = timezone.now().year
        self.fields['course_select'] = forms.ModelChoiceField(
            queryset=Course.objects.filter(year=current_year))

    def clean(self):
        course = self.cleaned_data.get("course_select")
        if CourseUserList.objects.filter(user_id=self.user, course_id=course).count():
            raise forms.ValidationError(self.error_messages['course_already_enrolled'],
                code='course_already_enrolled')
        return self.cleaned_data

    def save(self, commit=True):
        course = self.cleaned_data['course_select']
        course_user_list = CourseUserList(
                user_id=self.user,
                course_id=course,
                role=CourseUserList.ROLE_STUDENT
        )
        
        student_group_name = str(course.id) + "_Student_Group"
        student_group = Group.objects.get(name=student_group_name)
        user.groups.add(student_group)
        
        if commit:
            course_user_list.save()

        return course_user_list
        
