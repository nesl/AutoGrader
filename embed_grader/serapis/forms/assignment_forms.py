import string

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
from serapis.utils import user_info_helper

from django.utils import timezone
from datetime import timedelta


class AssignmentForm(ModelForm):
    error_messages = {
        'time_conflict': 'Release time must be earlier than deadline.',
        'invalid_schema': 'Schema can only contain 0-9, a-z, and \'_\'.',
    }

    class Meta:
        model = Assignment
        fields = ['name', 'release_time', 'deadline', 'problem_statement', 'testbed_type_id',
                'num_testbeds']
        date_time_options = {
                'format': 'mm/dd/yyyy hh:ii',
                'autoclose': True,
                'showMeridian' : False,
        }
        widgets = {
            'release_time': DateTimeWidget(bootstrap_version=3, options=date_time_options),
            'deadline': DateTimeWidget(bootstrap_version=3, options=date_time_options),
        }

    def __init__(self, *args, **kwargs):
        """
        Constructor:
          - course: the course object this assignment belongs to
        """
        self.course = kwargs.pop('course')
        super(AssignmentForm, self).__init__(*args, **kwargs)

        # add three more input boxes for schema
        self.fields['assignment_task_file_schema'] = forms.CharField(
                required=False,
                max_length=500,
                label='Input file schema',
                help_text="Use ; to separate multiple schema names.",
        )
        self.fields['submission_file_schema'] = forms.CharField(
                required=False,
                max_length=500,
                label='Submission file schema',
                help_text="Use ; to separate multiple schema names.",
        )
        self.fields['task_grading_status_file_schema'] = forms.CharField(
                required=False,
                max_length=500,
                label='Output file schema',
                help_text="Use ; to separate multiple schema names.",
        )

    def clean(self):
        # the order release time and deadline should be in order
        rt = self.cleaned_data.get("release_time")
        dl = self.cleaned_data.get("deadline")
        if rt and dl and rt >= dl:
            raise forms.ValidationError(self.error_messages['time_conflict'],
                code='time_conflict')

        return self.cleaned_data

    def clean_assignment_task_file_schema(self):
         schema_string = self.cleaned_data.get('assignment_task_file_schema')
         schema_name_list = self._parse_schema_string(schema_string)
         if schema_name_list is None:
             raise forms.ValidationError(self.error_messages['invalid_schema'],
                     code='invalid_schema')
         return schema_name_list

    def clean_submission_file_schema(self):
         schema_string = self.cleaned_data.get('submission_file_schema')
         schema_name_list = self._parse_schema_string(schema_string)
         if schema_name_list is None:
             raise forms.ValidationError(self.error_messages['invalid_schema'],
                     code='invalid_schema')
         return schema_name_list

    def clean_task_grading_status_file_schema(self):
         schema_string = self.cleaned_data.get('task_grading_status_file_schema')
         schema_name_list = self._parse_schema_string(schema_string)
         if schema_name_list is None:
             raise forms.ValidationError(self.error_messages['invalid_schema'],
                     code='invalid_schema')
         return schema_name_list

    def _parse_schema_string(self, schema_str):
        schema_name_list = [s.strip().lower() for s in schema_str.split(';')]
        schema_name_list = [s for s in schema_name_list if s]  # remove empty strings
        idx = 1
        while idx < len(schema_name_list):
            if schema_name_list[idx] in schema_name_list[:idx]:
                schema_name_list.pop(idx)
            else:
                idx += 1

        qualified_chars = string.digits + string.ascii_lowercase + '_'
            
        # if not all the schema name are composed only by letters, digits, and underscores
        if not all([all([(c in qualified_chars) for c in s]) for s in schema_name_list]):
            return None
        return schema_name_list

    def save(self, commit=True):
        assignment = super(AssignmentForm, self).save(commit=False)
        assignment.course_id = self.course
        if commit:
            assignment.save()
        
        SchemaClass_n_new_schema_name = [
                (AssignmentTaskFileSchema, self.cleaned_data['assignment_task_file_schema']),
                (SubmissionFileSchema, self.cleaned_data['submission_file_schema']),
                (TaskGradingStatusFileSchema, self.cleaned_data['task_grading_status_file_schema']),
        ]
        for SchemaClass, new_schema_name_list in SchemaClass_n_new_schema_name:
            old_schema = SchemaClass.objects.filter(assignment_id=assignment)
            old_schema_name_list = [sch.field for sch in old_schema]

            # remove out-dated schema in database
            for o_sch in old_schema:
                if o_sch.field not in new_schema_name_list:
                    o_sch.delete()

            # add new schema to database
            for n_name in new_schema_name_list:
                if n_name not in old_schema_name_list:
                    SchemaClass.objects.create(assignment_id=assignment, field=n_name)

        return assignment


class AssignmentSubmissionForm(Form):
    error_messages = {
        'pass_deadline': 'Assignment deadline has already passed.',
        'submission_in_queue': 'Previous submission is still grading.'
    }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        assignment = kwargs.pop('assignment')
        super(AssignmentSubmissionForm, self).__init__(*args, **kwargs)

        schema_list = SubmissionFileSchema.objects.filter(assignment_id=assignment).order_by('id')
        for schema in schema_list:
            self.fields[schema.field] = forms.FileField()

        # set up variables to be used
        self.user = user
        self.assignment = assignment

    def clean(self):
        if not self.user.has_perm('modify_assignment', course):  # a student
            # a student cannot submit after passing the deadline
            if self.assignment.is_deadline_passed():
                raise forms.ValidationError(self.error_messages['pass_deadline'],
                        code='pass_deadline')

            # a student can submit only if the previous submission is done
            if not user_info_helper.can_submit_on_assignment(user, assignment):
                raise forms.ValidationError(self.error_messages['submission_in_queue'],
                        code='submission_in_queue')

        return self.cleaned_data

    def save_and_commit(self, student):
        """
        Return:
          - (submission, submission_files)
        """
        submission = Submission(
                student_id=student,
                assignment_id=self.assignment,
                submission_time=timezone.now(),
                grading_result=0.,
                status=Submission.STAT_GRADING,
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

        # dispatch grading tasks
        #TODO: dispatched tasks should be based on the execution scope
        (assignment_tasks, _) = self.assignment.retrieve_assignment_tasks_and_score_sum(True)
        now = timezone.now()
        for assignment_task in assignment_tasks:
            grading_task = TaskGradingStatus.objects.create(
                submission_id=submission,
                assignment_task_id=assignment_task,
                grading_status=TaskGradingStatus.STAT_PENDING,
                execution_status=TaskGradingStatus.EXEC_UNKNOWN,
                status_update_time=now,
            )

            # create file records for each task
            schema_list = TaskGradingStatusFileSchema.objects.filter(
                    assignment_id=assignment)
            for sch in schema_list:
                TaskGradingStatusFile.objects.create(
                    task_grading_status_id=grading_task,
                    file_schema_id=sch,
                    file=None,
                )

        return (submission, submission_files)
