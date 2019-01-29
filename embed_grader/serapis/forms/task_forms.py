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
from serapis.utils import file_schema

from datetime import timedelta


class AssignmentTaskForm(ModelForm):
    class Meta:
        model = AssignmentTask
        fields = ['brief_description', 'mode', 'points', 'description', 'execution_duration', 'grading_script']

    def __init__(self, *args, **kwargs):
        assignment = kwargs.pop('assignment')
        super(AssignmentTaskForm, self).__init__(*args, **kwargs)

        assignment_task = kwargs.get('instance')  # None if in creating mode, otherwise updating
        assignment_task_files = (file_schema.get_dict_schema_name_to_assignment_task_schema_files(
            assignment_task) if assignment_task else None)

        schema_names = file_schema.get_assignment_task_file_schema_names(assignment)
        form_file_fields = []
        for schema_name in schema_names:
            form_field_name = "file_" + schema_name  # put 'file_' as a prefix of field names
            form_file_fields.append(form_field_name)
            if not assignment_task:  # creating mode
                self.fields[form_field_name] = forms.FileField()
            else:  # updating mode
                #TODO: Pass an initial value to the FileField. The following line doesn't work now.
                #      (http://stackoverflow.com/questions/42063858/how-should-i-show-a-link-of-existing-file-in-form-filefield-from-a-model-but-not)
                self.fields[form_field_name] = forms.FileField(initial={
                    'FileField': assignment_task_files[schema_name].file,
                })

        # set up variables to be used
        self.assignment = assignment
        self.form_file_fields = form_file_fields

    def clean(self):
        super(AssignmentTaskForm, self).clean()

        for form_field_name in self.form_file_fields:
            file_field = self.cleaned_data.get(form_field_name)
            if file_field:
                binary = file_field.read()
                #TODO: here we assume all files are (input) waveform files, which may not be true in
                #      the future
                #res, msg = grading.check_format(binary)
                #if not res:
                #    self.add_error(form_field_name, ValidationError(_(msg), code='invalid'))

    def save(self, commit=True):
        raise Exception('Deprecated method')

    def save_and_commit(self):
        assignment_task = super(AssignmentTaskForm, self).save(commit=False)
        assignment_task.assignment_fk = self.assignment
        assignment_task.save()

        schema_name_to_files = {}
        for form_field_name in self.form_file_fields:
            schema_name = form_field_name[5:]  # remove the prefix 'file_'
            schema_name_to_files[schema_name] = self.cleaned_data[form_field_name]
        file_schema.save_dict_schema_name_to_assignment_task_files(
                assignment_task, schema_name_to_files)

        return assignment_task
