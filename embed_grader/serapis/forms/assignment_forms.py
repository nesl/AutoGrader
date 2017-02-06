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


class AssignmentBasicForm(ModelForm):
    error_messages = {
        'time_conflict': "Release time must be earlier than deadline.",
    }

    class Meta:
        model = Assignment
        fields = ['course_id', 'name', 'release_time', 'deadline', 'problem_statement']
        date_time_options = {
                'format': 'mm/dd/yyyy hh:ii',
                'autoclose': True,
                'showMeridian' : False,
        }
        widgets = {
            'release_time': DateTimeWidget(bootstrap_version = 3, options = date_time_options),
            'deadline': DateTimeWidget(bootstrap_version = 3, options = date_time_options),
        }

    def clean(self):
        rt = self.cleaned_data.get("release_time")
        dl = self.cleaned_data.get("deadline")
        if rt and dl and rt >= dl:
            raise forms.ValidationError(self.error_messages['time_conflict'],
                code='time_conflict')
        return self.cleaned_data


class AssignmentCompleteForm(ModelForm):
    class Meta:
        model = Assignment
        fields = ['course_id', 'name', 'release_time', 'deadline', 'problem_statement',
                 'testbed_type_id', 'num_testbeds']
        date_time_options = {
                'format': 'mm/dd/yyyy hh:ii',
                'autoclose': True,
                'showMeridian' : False,
        }
        widgets = {
            'release_time': DateTimeWidget(bootstrap_version=3, options=date_time_options),
            'deadline': DateTimeWidget(bootstrap_version=3, options=date_time_options),
        }


class AssignmentSubmissionForm(Form):
    def __init__(self, *args, **kwargs):
        assignment = kwargs.pop('assignment')
        super(AssignmentSubmissionForm, self).__init__(*args, **kwargs)

        schema = SubmissionFileSchema.objects.filter(assignment_id=assignment).order_by('id')
        for field in schema:
            self.fields[field.field] = forms.FileField()

        # set up variables to be used
        self.assignment = assignment

    def save_and_commit(self, student):
        submission = Submission(
                student_id=student,
                assignment_id=self.assignment,
                submission_time=timezone.now(),
                grading_result=0.,
                status=Submission.STAT_GRADING
        )
        submission.save()

        submission_files = []
        for field in self.fields:
            schema = SubmissionFileSchema.objects.get(
                    assignment_id=self.assignment,
                    field=field,
            )
            submission_file = SubmissionFile(
                    submission_id=submission,
                    file_schema_id=schema,
                    file=self.cleaned_data[field],
            )
            submission_file.save()
            submission_files.append(submission_file)

        return (submission, submission_files)
