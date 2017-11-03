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
from serapis.utils import file_schema
from serapis.utils import user_info_helper
from serapis.utils import team_helper
from serapis.utils import submission_helper

from django.utils import timezone
from datetime import timedelta


class AssignmentForm(ModelForm):
    error_messages = {
        'time_conflict': 'Release time must be earlier than deadline.',
        'invalid_num_members': 'Number of team members has to be more than or equal to 2.',
        'invalid_num_submissions': 'Number of submissions has to be a postive integer.',
        'invalid_schema': 'Schema can only contain 0-9, a-z, \'.\', and \'_\'.',
    }

    class Meta:
        model = Assignment
        fields = ['name', 'release_time', 'deadline', 'problem_statement', 'testbed_type_fk',
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

    TEAM_OPTION_INDIVIDUAL = '0'
    TEAM_OPTION_TEAM = '1'
    TEAM_CHOICES = (
            (TEAM_OPTION_INDIVIDUAL, 'Individual assignment'),
            (TEAM_OPTION_TEAM, 'Team assignment'),
    )

    SUBMISSION_LIMIT_OPTION_INFINITE = '0'
    SUBMISSION_LIMIT_OPTION_FINITE = '1'
    SUBMISSION_LIMIT_CHOICES = (
            (SUBMISSION_LIMIT_OPTION_INFINITE, 'No limit'),
            (SUBMISSION_LIMIT_OPTION_FINITE, 'Set a limit for number of submissions'),
    )

    def __init__(self, *args, **kwargs):
        """
        Constructor:
          - course: the course object this assignment belongs to
        """
        self.course = kwargs.pop('course')
        super(AssignmentForm, self).__init__(*args, **kwargs)

        assignment = kwargs.get('instance')  # None if in creating mode, otherwise updating mode
        if assignment and assignment.course_fk != self.course:
            raise Exception('The passed assignment does not belong to the course')

        self.mode = 'modify' if assignment else 'create'

        # add three more input boxes for schema
        schema_file_info = [
                ('assignment_task_file_schema', 'Input file schema', 
                    file_schema.get_assignment_task_file_schema_names),
                ('submission_file_schema', 'Submission file schema',
                    file_schema.get_submission_file_schema_names),
                ('task_grading_status_file_schema', 'Output file schema',
                    file_schema.get_task_grading_status_file_schema_names),
        ]
        for form_field_name, label_text, retrieve_func in schema_file_info:
            initial_val = '; '.join(retrieve_func(assignment)) if assignment else ''
            self.fields[form_field_name] = forms.CharField(
                    required=False,
                    max_length=500,
                    label=label_text,
                    help_text="Use ; to separate multiple schema names.",
                    initial=initial_val,
            )
        
        # add team_choice radio button and max_num_team_members input field
        max_num_team_members = assignment.max_num_team_members if assignment else 1
        initial_team_choice_val, initial_num_member_val = (
                (AssignmentForm.TEAM_OPTION_INDIVIDUAL, 2) if max_num_team_members == 1
                else (AssignmentForm.TEAM_OPTION_TEAM, max_num_team_members))

        self.fields['team_choice'] = forms.ChoiceField(
                required=True,
                widget=forms.RadioSelect,
                choices=AssignmentForm.TEAM_CHOICES,
                initial=initial_team_choice_val,
        )
        self.fields['max_num_team_members'] = forms.IntegerField(
                required=False,
                initial=initial_num_member_val,
                validators=[MinValueValidator(2)]
        )

        # add submission_limit_choice radio button and max_num_submissions input field
        max_num_submissions = (assignment.max_num_submissions if assignment
                else Assignment.SUBMISSION_LIMIT_INFINITE)

        is_no_limit = (max_num_submissions == Assignment.SUBMISSION_LIMIT_INFINITE)
        initial_submission_limit_choice_val, initial_num_submission_val = (
                (AssignmentForm.SUBMISSION_LIMIT_OPTION_INFINITE, 10) if is_no_limit
                else (AssignmentForm.SUBMISSION_LIMIT_OPTION_INFINITE, max_num_submissions))

        self.fields['submission_limit_choice'] = forms.ChoiceField(
                required=True,
                widget=forms.RadioSelect,
                choices=AssignmentForm.SUBMISSION_LIMIT_CHOICES,
                initial=initial_submission_limit_choice_val,
        )
        self.fields['max_num_submissions'] = forms.IntegerField(
                required=False,
                initial=initial_num_submission_val,
                validators=[MinValueValidator(1)]
        )

        #TODO: field order
        

    def clean(self):
        # the order release time and deadline should be in order
        rt = self.cleaned_data.get("release_time")
        dl = self.cleaned_data.get("deadline")
        if rt and dl and rt >= dl:
            raise forms.ValidationError(self.error_messages['time_conflict'],
                code='time_conflict')

        # team choice
        if self.cleaned_data['team_choice'] == AssignmentForm.TEAM_OPTION_INDIVIDUAL:
            self.cleaned_data['max_num_team_members'] = 1
        else:
            if 'max_num_team_members' not in self.cleaned_data:
                # Since 'max_num_team_members' field is optional, it will not be inserted to
                # self.cleaned_data if user input is invalid
                raise forms.ValidationError(self.error_messages['invalid_num_members'],
                    code='invalid_num_members')
            
            self.cleaned_data['max_num_team_members'] = int(
                    self.cleaned_data['max_num_team_members'])


        # submission limit
        if (self.cleaned_data['submission_limit_choice']
                == AssignmentForm.SUBMISSION_LIMIT_OPTION_INFINITE):
            self.cleaned_data['max_num_submissions'] = Assignment.SUBMISSION_LIMIT_INFINITE
        else:
            if 'max_num_submissions' not in self.cleaned_data:
                # Since 'max_num_submissions' field is optional, it will not be inserted to
                # self.cleaned_data if user input is invalid
                raise forms.ValidationError(self.error_messages['invalid_num_submissions'],
                    code='invalid_num_submissions')

            self.cleaned_data['max_num_submissions'] = int(
                    self.cleaned_data['max_num_submissions'])

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

        qualified_chars = string.digits + string.ascii_lowercase + '_.'
            
        # if not all the schema name are composed only by letters, digits, and underscores
        if not all([all([(c in qualified_chars) for c in s]) for s in schema_name_list]):
            return None
        return schema_name_list

    def save(self, commit=True):
         raise Exception('Deprecated method')

    def save_and_commit(self):
        """
        Return:
          assignment
        """
        assignment = super(AssignmentForm, self).save(commit=False)
        assignment.course_fk = self.course
        assignment.max_num_team_members = self.cleaned_data['max_num_team_members']
        assignment.max_num_submissions = self.cleaned_data['max_num_submissions']
        assignment.save()

        # file schemas
        SchemaClass_n_new_schema_name = [
                (AssignmentTaskFileSchema, self.cleaned_data['assignment_task_file_schema']),
                (SubmissionFileSchema, self.cleaned_data['submission_file_schema']),
                (TaskGradingStatusFileSchema, self.cleaned_data['task_grading_status_file_schema']),
        ]
        for SchemaClass, new_schema_name_list in SchemaClass_n_new_schema_name:
            old_schema = SchemaClass.objects.filter(assignment_fk=assignment)
            old_schema_name_list = [sch.field for sch in old_schema]

            # remove out-dated schema in database
            for o_sch in old_schema:
                if o_sch.field not in new_schema_name_list:
                    o_sch.delete()

            # add new schema to database
            for n_name in new_schema_name_list:
                if n_name not in old_schema_name_list:
                    SchemaClass.objects.create(assignment_fk=assignment, field=n_name)

        return assignment


class AssignmentSubmissionForm(Form):
    error_messages = {
        'pass_deadline': 'Assignment deadline has already passed.',
        'submission_in_queue': 'Previous submission is still grading.'
    }

    def __init__(self, *args, **kwargs):
        """
        Constructor:
          - user: the user who submits the codes
          - assignment: which assignment the user submit the codes to
        """
        user = kwargs.pop('user')
        team = kwargs.pop('team')
        assignment = kwargs.pop('assignment')
        super(AssignmentSubmissionForm, self).__init__(*args, **kwargs)

        execution_scope_choice = [
                (AssignmentTask.MODE_DEBUG, 'Debug'),
                (AssignmentTask.MODE_PUBLIC, 'Debug+Public'),
                (AssignmentTask.MODE_FEEDBACK, 'Debug+Public+Feedback'),
        ]
        if user.has_perm('modify_assignment', assignment.course_fk):  # an instructor
            execution_scope_choice.append(
                    (AssignmentTask.MODE_HIDDEN, 'Debug+Public+Feedback+Hidden'))
        self.fields['execution_scope'] = forms.ChoiceField(
                required=True,
                widget=forms.Select,
                choices=execution_scope_choice,
                initial=AssignmentTask.MODE_DEBUG,
        )

        file_fields = []
        for schema_name in file_schema.get_submission_file_schema_names(assignment):
            field_name = 'file_' + schema_name
            self.fields[field_name] = forms.FileField()
            file_fields.append(field_name)

        # set up variables to be used
        self.user = user
        self.team = team
        self.assignment = assignment
        self.file_fields = file_fields

    def clean(self):
        if not self.user.has_perm('modify_assignment', self.assignment.course_fk):  # a student
            # a student cannot submit after passing the deadline
            if self.assignment.is_deadline_passed():
                raise forms.ValidationError(self.error_messages['pass_deadline'],
                        code='pass_deadline')

            # a student can submit only if the previous submission is done
            if not user_info_helper.all_submission_graded_on_assignment(self.user, self.assignment):
                raise forms.ValidationError(self.error_messages['submission_in_queue'],
                        code='submission_in_queue')

        return self.cleaned_data

    def save_and_commit(self):
        """
        Return:
          - submission
        """
        submission = Submission(
                student_fk=self.user,
                team_fk=self.team,
                assignment_fk=self.assignment,
                submission_time=timezone.now(),
                grading_result=0.,
                status=Submission.STAT_GRADING,
                task_scope=self.cleaned_data['execution_scope'],
                num_graded_tasks=0,
                num_total_tasks=0,
        )
        submission.save()

        dict_schema_name_2_files = {}
        for field_name in self.file_fields:
            schema_name = field_name[5:]  # remove prefix 'file_'
            dict_schema_name_2_files[schema_name] = self.cleaned_data[field_name]
        file_schema.save_dict_schema_name_to_submission_files(submission, dict_schema_name_2_files)

        # dispatch grading tasks
        assignment_tasks = self.assignment.retrieve_assignment_tasks_by_accumulative_scope(
                self.cleaned_data['execution_scope'])
        for assignment_task in assignment_tasks:
            grading_task= submission_helper.create_task_grading_status(submission, assignment_task)
            file_schema.create_empty_task_grading_status_schema_files(grading_task)

        return submission


class JoinTeamForm(Form):
    """
    JoinTeamForm receives the passcode and put the user to that team. Since the validation and
    the save logic (i.e., putting the user in the team) cannot be decoupled, the save() method
    will be a no-operation.
    """

    error_messages = {
        'wrong_passcode': 'Incorrect passcode.',
        'pass_deadline': 'Assignment deadline has already passed.',
        'no_capacity': 'No empty spot in the team.',
    }

    def __init__(self, *args, **kwargs):
        """
        Constructor:
          - user: the user who submits the codes
          - assignment: which assignment the user submit the codes to
        """
        user = kwargs.pop('user')
        assignment = kwargs.pop('assignment')
        super(JoinTeamForm, self).__init__(*args, **kwargs)

        self.fields['team_passcode'] = forms.CharField(required=True, max_length=20)

        # set up variables to be used
        self.user = user
        self.assignment = assignment

    def clean(self):
        # check passcode
        team = team_helper.check_passcode(self.cleaned_data['team_passcode'])
        if team is None:
            raise forms.ValidationError(self.error_messages['wrong_passcode'],
                    code='wrong_passcode')

        # a student cannot join a team after passing the deadline
        if self.assignment.is_deadline_passed():
            raise forms.ValidationError(self.error_messages['pass_deadline'],
                    code='pass_deadline')

        if not team_helper.add_users_to_team(team, [self.user]):
            raise forms.ValidationError(self.error_messages['no_capacity'],
                    code='no_capacity')

        return self.cleaned_data

    def save(self):
        pass
