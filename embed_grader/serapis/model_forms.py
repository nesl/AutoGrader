from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm

from django import forms
from django.forms import Form, ModelForm, Textarea
from django.forms import modelformset_factory
from django.forms import formset_factory
from django.forms.widgets import HiddenInput
from datetimewidget.widgets import DateTimeWidget, DateWidget, TimeWidget
from django.template.loader import get_template
from django.template import Context
from django.core.mail import send_mail

from serapis.models import *

from datetime import datetime, timedelta


class UserCreateForm(UserCreationForm):
    ROLE_INSTRUCTOR = 10
    ROLE_TA = 11
    ROLE_STUDENT = 20
    USER_ROLES = (
            (ROLE_INSTRUCTOR, 'Instructor'),
            (ROLE_TA, 'TA'),
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
        link="http://128.97.93.16:8000/activate/"+datas['activation_key']
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
        role = self.cleaned_data['user_role']
        role_string = dict(self.USER_ROLES).get(int(role))
        user_profile = UserProfile(user=user, 
                                   uid=self.cleaned_data['uid'],
                                   user_role=role,
                                   activation_key=datas['activation_key'],
                                   key_expires=datetime.strftime(datetime.now() + timedelta(days=2), "%Y-%m-%d %H:%M:%S") 
                                  )
        user_profile.save()
        group = Group.objects.get(name=role_string)
        group.user_set.add(user)
        return user, user_profile



class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = ['owner_id', 'course_code', 'name', 'description']

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
        QUARTER_CHOICES = ((1, 'Fall'), (2, 'Winter'), (3, 'Fall'), (4, 'Summer'))
        widgets = {
                'description': forms.Textarea(attrs={'cols': 40, 'rows': 5}),
                'year': forms.Select(choices=YEAR_CHOICES),
                'quarter': forms.Select(choices=QUARTER_CHOICES)
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CourseCreationForm, self).__init__(*args, **kwargs)

    def clean(self):
        a = self.cleaned_data.get("course_code")
        b = str(self.cleaned_data.get("quarter"))
        c = str(self.cleaned_data.get("year"))
        if Group.objects.filter(name=a+'_'+b+'_'+c).count():
            raise forms.ValidationError(self.error_messages['course_already_created'],
                code='course_already_created')
        return self.cleaned_data

    def save(self, commit=True):
        a = self.cleaned_data['course_code']
        b = str(self.cleaned_data['quarter'])
        c = str(self.cleaned_data['year'])
        course = super(CourseCreationForm, self).save(commit=False)
        group = Group.objects.create(name=a+'_'+b+'_'+c)
        group.user_set.add(self.user)
        course_user_list = CourseUserList.objects.create(user_id=self.user, course_id=course)
        if commit:
          course.save()
        return course


class CourseEnrollForm(Form):
    current_year = datetime.now().year
    course_select = forms.ModelChoiceField(queryset=Course.objects.filter(year=current_year))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CourseEnrollmentForm, self).__init__(*args, **kwargs)
    
    def save(self, commit=True):
        course=self.cleaned_data['course_select'] 
        group = Groups.objects.get(name=course.course_code+'_'+course.quarter+'_'+course.year)
        group.user_set.add(self.user)
        course_user_list = CourseUserList.objects.create(user_id=self.user, course_id=course)


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

