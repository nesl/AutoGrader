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


class AssignmentTaskForm(ModelForm):
    class Meta:
        model = AssignmentTask
        fields = ['brief_description', 'mode', 'points', 'description', 'execution_duration', 'grading_script']

    def __init__(self, *args, **kwargs):
        assignment = kwargs.pop('assignment')
        super(AssignmentTaskForm, self).__init__(*args, **kwargs)

        schema = AssignmentTaskFileSchema.objects.filter(assignment_id=assignment).order_by('id')
        file_fields = []
        for field in schema:
            field_name = "file_" + field.field  # put 'file_' as a prefix of field names
            file_fields.append(field_name)
            self.fields[field_name] = forms.FileField()

        # set up variables to be used
        self.assignment = assignment
        self.file_fields = file_fields

    def clean(self):
        super(AssignmentTaskForm, self).clean()

        for field_name in self.file_fields:
            #TODO: assume all files are (input) waveform files, which may not be true in the future
            file_field = self.cleaned_data.get(field_name)
            if file_field:
                binary = file_field.read()
                res, msg = grading.check_format(binary)
                if not res:
                    self.add_error(field_name, ValidationError(_(msg), code='invalid'))

    def save_and_commit(self):
        assignment_task = AssignmentTask(
                assignment_id=self.assignment,
                brief_description=self.cleaned_data['brief_description'],
                mode=self.cleaned_data['mode'],
                points=self.cleaned_data['points'],
                description=self.cleaned_data['description'],
                grading_script=self.cleaned_data['grading_script'],
                execution_duration=self.cleaned_data['execution_duration'],
        )
        assignment_task.save()

        assignment_task_files = []
        for field_name in self.file_fields:
            field = field_name[5:]  # remove the prefix 'file_'
            print(field_name, field)
            schema = AssignmentTaskFileSchema.objects.get(
                    assignment_id=self.assignment,
                    field=field,
            )
            assignment_task_file = AssignmentTaskFile(
                    assignment_task_id=assignment_task,
                    file_schema_id=schema,
                    file=self.cleaned_data[field_name],
            )
            assignment_task_file.save()
            assignment_task_files.append(assignment_task_file)
            print(assignment_task_file.file.path)

        return (assignment_task, assignment_task_files)


class AssignmentTaskUpdateForm(Form):
    # class Meta:
    #     model = AssignmentTask
    #     fields = ['brief_description', 'mode', 'points', 'description', 'grading_script','execution_duration']
    MODE_PUBLIC = 0
    MODE_FEEDBACK = 1
    MODE_HIDDEN = 2
    EVAL_MODES = (
        (MODE_PUBLIC, 'Public'),
        (MODE_FEEDBACK, 'Feedback'),
        (MODE_HIDDEN, 'Hidden'),
    )

    def __init__(self, *args, **kwargs):
        task = kwargs.pop('instance')
        super(AssignmentTaskUpdateForm, self).__init__(*args, **kwargs)

        self.fields['brief_description'] = forms.CharField(
            required=True,
            widget=forms.TextInput,
            initial=task.brief_description
        )

        self.fields['mode'] = forms.ChoiceField(
            required=True,
            choices=self.EVAL_MODES,
            initial=task.mode
        )

        self.fields['points'] = forms.FloatField(
            required=True,
            initial=task.points
        )

        self.fields['description'] = forms.CharField(
            initial = task.description
        )

        self.fields['execution_duration'] = forms.FloatField(
            initial=task.execution_duration
        )

        self.fields['grading_script'] = forms.FileField(
            # upload_to='AssignmentTask_grading_script',
            initial=task.grading_script

        )

        assignment = task.assignment_id
        schema = AssignmentTaskFileSchema.objects.filter(assignment_id=assignment).order_by('id')
        file_fields = []
        for field in schema:
            field_name = "file_" + field.field  # put 'file_' as a prefix of field names
            file_fields.append(field_name)
            self.fields[field_name] = forms.FileField(
                 # initial=getattr(task, field.field)
            )

        # set up variables to be used
        # self.assignment = assignment
        # self.file_fields = file_fields

    # def save_and_commit(self):
    #     assignment_task = AssignmentTask(
    #             assignment_id=self.assignment,
    #             brief_description=self.cleaned_data['brief_description'],
    #             mode=self.cleaned_data['mode'],
    #             points=self.cleaned_data['points'],
    #             description=self.cleaned_data['description'],
    #             grading_script=self.cleaned_data['grading_script'],
    #             execution_duration=self.cleaned_data['execution_duration'],
    #     )
    #     assignment_task.save()
    
    #     assignment_task_files = []
    #     for field_name in self.file_fields:
    #         field = field_name[5:]  # remove the prefix 'file_'
    #         print(field_name, field)
    #         schema = AssignmentTaskFileSchema.objects.get(
    #                 assignment_id=self.assignment,
    #                 field=field,
    #         )
    #         assignment_task_file = AssignmentTaskFile(
    #                 assignment_task_id=assignment_task,
    #                 file_schema_id=schema,
    #                 file=self.cleaned_data[field_name],
    #         )
    #         assignment_task_file.save()
    #         assignment_task_files.append(assignment_task_file)
    #         print(assignment_task_file.file.path)
    
    #     return (assignment_task, assignment_task_files)


