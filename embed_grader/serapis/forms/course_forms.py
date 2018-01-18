from django.contrib.auth.models import User, Group

from django import forms
from django.forms import Form, ModelForm
from django.forms import modelformset_factory
from django.forms import formset_factory
from django.forms import Textarea
from django.forms.widgets import HiddenInput
from django.core.exceptions import ValidationError

from django.db import transaction

from django.utils.translation import gettext as _

from datetimewidget.widgets import DateTimeWidget, DateWidget, TimeWidget

from serapis.models import *
from serapis.utils import grading
from serapis.utils import team_helper

from datetime import timedelta


class CourseCreationForm(ModelForm):
    class Meta:
        model = Course
        fields = ['course_code', 'name', 'description']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(CourseCreationForm, self).__init__(*args, **kwargs)

        course = kwargs.get('instance')  # None if in creating mode, otherwise updating

        now = timezone.now()
        cur_year = now.year
        cur_month = now.month
        cur_quarter = (cur_month - 1) // 3
        cur_year_quarter = cur_year * 4 + cur_quarter
        year_quarter_choices_idx = [cur_year_quarter + offset for offset in range(5)]
        year_quarter_choices = [(yq, '%d %s' % (yq // 4, Course.QUARTER_DICT[yq % 4]))
                for yq in year_quarter_choices_idx]

        if not course:
            initial_year_quarter_value = year_quarter_choices_idx[0]
        else:
            initial_year_quarter_value = course.year * 4 + course.quarter
            if initial_year_quarter_value not in year_quarter_choices_idx:
                initial_year_quarter_value = year_quarter_choices_idx[0]

        self.fields['year_quarter'] = forms.ChoiceField(
                required=True,
                widget=forms.Select,
                choices=year_quarter_choices,
                initial=initial_year_quarter_value,
        )
        self.order_fields(['course_code', 'name', 'year_quarter', 'description'])

        # set up variables to be used
        self.course = course

    def clean(self):
        super(CourseCreationForm, self).clean()
        if 'course_code' in self.cleaned_data:
            self.cleaned_data['course_code'] = self.cleaned_data['course_code'].upper()
        return self.cleaned_data

    def save(self, commit=True):
        raise Exception('Deprecated method')

    def save_and_commit(self):
        year, quarter = divmod(int(self.cleaned_data['year_quarter']), 4)

        if not self.course:  # creating mode
            course = Course.objects.create(
                    course_code=self.cleaned_data['course_code'],
                    name=self.cleaned_data['name'],
                    description=self.cleaned_data['description'],
                    year=year,
                    quarter=quarter,
            )
            course_user_list = CourseUserList.objects.create(
                    user_fk=self.user, course_fk=course, role=CourseUserList.ROLE_INSTRUCTOR)

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
            assign_perm('download_csv', instructor_group, course)
        else:  # updating mode
            course = self.course
            course.course_code = self.cleaned_data['course_code']
            course.name = self.cleaned_data['name']
            course.description = self.cleaned_data['description']
            course.year = year
            course.quarter = quarter
            course.save()

        return course


class CourseEnrollmentForm(Form):
    error_messages = {
        'course_already_enrolled': "You have already enrolled in this course.",
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(CourseEnrollmentForm, self).__init__(*args, **kwargs)

        now = timezone.now()
        cur_year = now.year
        cur_month = now.month
        cur_quarter = (cur_month - 1) // 3
        cur_year_quarter = cur_year * 4 + cur_quarter

        self.fields['course_select'] = forms.ModelChoiceField(
            queryset=Course.objects.filter(year=cur_year, quarter=cur_quarter))

    def clean(self):
        course = self.cleaned_data.get("course_select")
        if CourseUserList.objects.filter(user_fk=self.user, course_fk=course).count():
            raise forms.ValidationError(self.error_messages['course_already_enrolled'],
                code='course_already_enrolled')
        return self.cleaned_data

    def save(self, commit=True):
        course = self.cleaned_data['course_select']
        course_user_list = CourseUserList(
                user_fk=self.user,
                course_fk=course,
                role=CourseUserList.ROLE_STUDENT
        )

        student_group_name = str(course.id) + "_Student_Group"
        student_group = Group.objects.get(name=student_group_name)
        self.user.groups.add(student_group)

        if commit:
            course_user_list.save()

        return course_user_list

class CourseDropForm(Form):
    """
    CourseDropForm assumes that the passed user and course instances are valid, meaning that
    it is expected the check of the user belongs to the course has been proceeded in views.
    """

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.course = kwargs.pop('course')
        super(CourseDropForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        raise Exception('Deprecated method')

    def save_and_commit(self):
        with transaction.atomic():
            assignment_list = Assignment.objects.filter(course_fk=self.course)
            for assignment in assignment_list:
                team = team_helper.get_belonged_team(self.user, assignment)
                if team is not None:
                    team_helper.remove_users_from_team(team=team, users=[self.user])

            CourseUserList.objects.filter(user_fk=self.user, course_fk=self.course).delete()

        #TODO: remove instruction privileges
        # if len(cu_list) > 0 && cu_list[0].role < 20:
        #     instructor_group_name = str(course.id) + "_Instructor_Group"

        # remove user from course group also
        student_group_name = str(self.course.id) + "_Student_Group"
        student_group = Group.objects.get(name=student_group_name)
        self.user.groups.remove(student_group)
