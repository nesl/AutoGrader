from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from django import forms
from django.forms import ModelForm
from django.forms import modelformset_factory
from django.forms import formset_factory
from django.forms.widgets import HiddenInput
from datetimewidget.widgets import DateTimeWidget

from serapis.models import *


class UserCreateForm(UserCreationForm):
    ROLE_SUPER_USER = 0
    ROLE_INSTRUCTOR = 10
    ROLE_TA = 11
    ROLE_GRADER = 12
    ROLE_STUDENT = 20
    USER_ROLES = (
            (ROLE_SUPER_USER, 'Super user'),
            (ROLE_INSTRUCTOR, 'Instructor'),
            (ROLE_TA, 'TA'),
            (ROLE_GRADER, 'Grader'),
            (ROLE_STUDENT, 'Student'),
    )
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
    user_role = forms.ChoiceField(widget=forms.RadioSelect(), choices=USER_ROLES)

    class Meta:
        model = User
        fields = ['username', 'email']

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


class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = ['instructor_id', 'course_code', 'name', 'description']


class AssignmentBasicForm(ModelForm):
    class Meta:
        model = Assignment
        fields = ['course_id', 'description', 'release_time', 'deadline', 'problem_statement', 'input_statement', 'output_statement']
        date_time_options = {
                'format': 'mm/dd/yyyy hh:ii',
                'autoclose': True,
                'showMeridian' : False,
        }
        widgets = {
            'release_time': DateTimeWidget(bootstrap_version = 3, options = date_time_options),
            'deadline': DateTimeWidget(bootstrap_version = 3, options = date_time_options),
        }


class AssignmentCompleteForm(ModelForm):
    class Meta:
        model = Assignment
        fields = ['course_id', 'description', 'release_time', 'deadline', 'problem_statement', 'input_statement', 'output_statement',
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

        
class TestbedTypeForm(ModelForm):
    class Meta:
        model = TestbedType
        fields = ['name']


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

