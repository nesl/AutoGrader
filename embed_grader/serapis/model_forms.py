from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm

from django import forms
from django.forms import Form, ModelForm
from django.forms import modelformset_factory
from django.forms import formset_factory
from django.forms import Textarea
from django.forms.widgets import HiddenInput
from datetimewidget.widgets import DateTimeWidget, DateWidget, TimeWidget
from django.template.loader import get_template
from django.template import Context
from django.core.mail import send_mail

from serapis.models import *
from serapis.utils import grading

#TODO: shouldn't use datetime.datetime
from datetime import datetime, timedelta


class UserCreateForm(UserCreationForm):
    MIN_LENGTH = 8
    error_messages = {
        'password_mismatch': "The two password fields didn't match.",
        'email_not_unique': "This email has been registered."
     }
    uid = forms.CharField(label="University ID",
        widget=forms.TextInput)
    password1 = forms.CharField(label="Password",
        widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation",
        widget=forms.PasswordInput,
        help_text="Enter the same password as above, for verification.")
    # user_role = forms.ChoiceField(widget=forms.RadioSelect(), choices=USER_ROLES)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def clean_email(self):
        email = self.cleaned_data.get("email")
        username = self.cleaned_data.get("username")
        if not email:
            raise forms.ValidationError("This field is required.")
        if email and User.objects.filter(email=email).count():
            raise forms.ValidationError(
                self.error_messages['email_not_unique'],
                code='email_not_unique')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        # At least MIN_LENGTH
        elif len(password1) < self.MIN_LENGTH:
            raise forms.ValidationError("The new password must be at least %d characters long." % self.MIN_LENGTH)

        # At least one letter and one non-letter
        first_isalpha = password1[0].isalpha()
        if all(c.isalpha() == first_isalpha for c in password1):
            raise forms.ValidationError("The new password must contain at least one letter and at least one digit or" \
                                        " punctuation character.")
        return password2

    def sendEmail(self, datas):
        link="https://autograder.nesl.ucla.edu/activate/"+datas['activation_key']
        template = get_template(datas['email_path'])
        context = Context({'activation_link':link,'uid':datas['uid']})
        message = template.render(context)
        #print unicode(message).encode('utf8')
        send_mail(datas['email_subject'], message, 'NESL Embed AutoGrader', [datas['email']], fail_silently=False)

    def save(self, datas, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False
        if commit:
            user.save()

        # role = self.cleaned_data['user_role']
        # role_string = dict(self.USER_ROLES).get(int(role))

        user_profile = UserProfile(user=user,
                                   uid=self.cleaned_data['uid'],
                                #    user_role=role,
                                   activation_key=datas['activation_key'],
                                   key_expires=datetime.strftime(datetime.now() + timedelta(days=2), "%Y-%m-%d %H:%M:%S")
                                  )
        user_profile.save()
        # group = Group.objects.get(name=role_string)
        # group.user_set.add(user)
        return user, user_profile


class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = ['course_code', 'name', 'description']


class CourseCreationForm(ModelForm):
    error_messages = {
        'course_already_created': "Course already exists. Please modify the existing course or ask admin to delete it.",
    }

    class Meta:
        model = Course
        fields = ['course_code', 'name', 'quarter', 'year', 'description']
        YEAR_CHOICES = []
        for r in range(2015, (datetime.now().year+2)):
            YEAR_CHOICES.append((r,r))
        QUARTER_CHOICES = ((1, 'Fall'), (2, 'Winter'), (3, 'Spring'), (4, 'Summer'))
        widgets = {
                'description': forms.Textarea(attrs={'cols': 40, 'rows': 5}),
                'year': forms.Select(choices=YEAR_CHOICES),
                'quarter': forms.Select(choices=QUARTER_CHOICES)
        }

    #TODO(Meng): Do we really need this constructor?
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
        YEAR_CHOICES = []
        for r in range(2015, (datetime.now().year+2)):
            YEAR_CHOICES.append((r,r))
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
    current_year = datetime.now().year
    course_select = forms.ModelChoiceField(queryset=Course.objects.filter(year=current_year))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CourseEnrollmentForm, self).__init__(*args, **kwargs)

    def clean(self):
        course=self.cleaned_data.get("course_select")
        if CourseUserList.objects.filter(user_id=self.user, course_id=course).count():
            raise forms.ValidationError(self.error_messages['course_already_enrolled'],
                code='course_already_enrolled')
        return self.cleaned_data

    def save(self, commit=True):
        course=self.cleaned_data['course_select']
        course_user_list = CourseUserList.objects.create(user_id=self.user, course_id=course)

class AssignmentBasicForm(ModelForm):
    error_messages = {
        'time_conflict': "Release time must be earlier than deadline.",
    }

    class Meta:
        model = Assignment
        fields = ['course_id', 'name', 'release_time', 'deadline', 'problem_statement', 'input_statement', 'output_statement']
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
        rt=self.cleaned_data.get("release_time")
        dl=self.cleaned_data.get("deadline")
        if rt>=dl:
            raise forms.ValidationError(self.error_messages['time_conflict'],
                code='time_conflict')
        return self.cleaned_data


class AssignmentCompleteForm(ModelForm):
    class Meta:
        model = Assignment
        fields = ['course_id', 'name', 'release_time', 'deadline', 'problem_statement', 'input_statement', 'output_statement',
                'testbed_type_id', 'num_testbeds']
        date_time_options = {
                'format': 'mm/dd/yyyy hh:ii',
                'autoclose': True,
                'showMeridian' : False,
        }
        widgets = {
            'release_time': DateTimeWidget(bootstrap_version = 3, options = date_time_options),
            'deadline': DateTimeWidget(bootstrap_version = 3, options = date_time_options),
        }


class AssignmentTaskForm(ModelForm):
    class Meta:
        model = AssignmentTask
        fields = ['brief_description', 'mode', 'points', 'description', 'grading_script',
                'execution_duration']
    
    def __init__(self, *args, **kwargs):
        assignment = kwargs.pop('assignment')
        super(AssignmentTaskForm, self).__init__(*args, **kwargs)

        schema = AssignmentTaskFileSchema.objects.filter(assignment_id=assignment).order_by('id')
        file_fields = []
        for field in schema:
            field_name = "file_" + field.field
            file_fields.append(field_name)
            self.fields[field_name] = forms.FileField()
        
        # set up variables to be used
        self.assignment = assignment
        self.file_fields = file_fields
    
    def clean(self):
        super(AssignmentTaskForm, self).clean()
        
        for field_name in self.file_fields:
            #TODO: assume all files are (input) waveform files, which may not be true in the future
            print('check %s' % field_name)
            file_field = self.cleaned_data.get(field_name)
            if file_field:
                binary = file_field.read()
                res, msg = grading.check_format(binary)
                if not res:
                    self.add_error(field_name, ValidationError(_(msg), code='invalid'))

    def save_and_commit(self):
        assignment_task = AssignmentTask(
                assignment_id=self.assignment,
                brief_descripton=self.cleaned_data['brief_description'],
                mode=self.cleaned_data['mode'],
                points=self.cleaned_data['points'],
                description=self.cleaned_data['description'],
                grading_script=self.cleaned_data['grading_script'],
                execution_duration=self.cleaned_data['execution_duration'],
        )

        assignment_task_files = []
        for field_name in self.file_fields:
            field = field_name[5:]  # remove the prefix 'file_'
            schema = AssignmentTaskFileSchema.objects.get(
                    assignment_id=self.assignment,
                    field=field,
            )
            assignment_task_file = AssignmentTaskFile(
                    assignment_task_id=assignment_task,
                    file_schema_id=schema,
                    file=self.cleaned_data[field],
            )
            assignment_task_file.save()
            assignment_task_files.append(assignment_task_file)
            print(assignment_task_file.file.path)

        return (submission, submission_files)


class TestbedTypeForm(ModelForm):
    class Meta:
        model = TestbedType
        fields = ['name']


class TestbedTypeWiringForm(ModelForm):
    class Meta:
        model = TestbedTypeWiring
        fields = ['dev_1_index', 'dev_1_pin', 'dev_2_index', 'dev_2_pin']
        widgets = {
                'dev_1_index': forms.Select(),
                'dev_1_pin': forms.Select(),
                'dev_2_index': forms.Select(),
                'dev_2_pin': forms.Select(),
        }


class TestbedTypeWiringFormSet(formset_factory(TestbedTypeWiringForm)):
    def clean(self):
        if any(self.errors):
            return


# TODO: Refactor the TestbedHardwareList{HE/DUT}Form classes and TestbedHardwareList{HE/DUT}FormSet classes
#       as they are basically duplicated
class TestbedHardwareListHEForm(ModelForm):
    class Meta:
        model = TestbedHardwareList
        fields = ['hardware_type']

    def __init__(self, *args, **kwargs):
        super(TestbedHardwareListHEForm, self).__init__(*args, **kwargs)
        self.fields['hardware_type'].queryset = HardwareType.objects.filter(hardware_role=HardwareType.HARDWARE_ENGINE)
        self.fields['hardware_type'].label_from_instance = lambda obj: obj.name


class TestbedHardwareListDUTForm(ModelForm):
    class Meta:
        model = TestbedHardwareList
        fields = ['hardware_type']

    def __init__(self, *args, **kwargs):
        super(TestbedHardwareListDUTForm, self).__init__(*args, **kwargs)
        self.fields['hardware_type'].queryset = HardwareType.objects.filter(hardware_role=HardwareType.DEVICE_UNDER_TEST)
        self.fields['hardware_type'].label_from_instance = lambda obj: obj.name


class TestbedHardwareListHEFormSet(formset_factory(TestbedHardwareListHEForm)):
    def clean(self):
        if any(self.errors):
            return


class TestbedHardwareListDUTFormSet(formset_factory(TestbedHardwareListDUTForm)):
    def clean(self):
        if any(self.errors):
            return


class TestbedHardwareListAllForm(ModelForm):
    class Meta:
        model = TestbedHardwareList
        fields = ['hardware_type', 'hardware_index']

    def __init__(self, *args, **kwargs):
        super(TestbedHardwareListAllForm, self).__init__(*args, **kwargs)
        self.fields['hardware_type'].widget = HiddenInput()
        self.fields['hardware_index'].widget = HiddenInput()


class TestbedHardwareListAllFormSet(formset_factory(TestbedHardwareListAllForm)):
    def clean(self):
        if any(self.errors):
            return


class HardwareTypeForm(ModelForm):
    class Meta:
        model = HardwareType
        fields = ['name', 'pinout', 'link_to_manual', 'hardware_role']


class HardwareTypePinFormSet(modelformset_factory(HardwareTypePin, fields=['pin_name'])):
    def clean(self):
        if any(self.errors):
            return

        pin_names = set()
        for form in self.forms:
            if not form.cleaned_data:
                raise forms.ValidationError('Pin names cannot be an empty string.',
                        code='missing_pin_name')
            else:
                pin_name = form.cleaned_data['pin_name']
                if pin_name in pin_names:
                    raise forms.ValidationError('No two pin names should be identical.',
                            code='duplicated_pin_names')
                pin_names.add(pin_name)


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


class TaskGradingStatusDebugForm(ModelForm):
    id = forms.IntegerField(widget=forms.NumberInput)
    class Meta:
        model = TaskGradingStatus
        fields = ['id', 'grading_status', 'execution_status']
        #TODO: wire output files


