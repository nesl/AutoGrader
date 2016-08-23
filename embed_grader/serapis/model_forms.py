from django.forms import ModelForm
from datetimewidget.widgets import DateTimeWidget

from serapis.models import *


class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = ['instructor_id', 'course_code', 'name', 'description']


class AssignmentForm(ModelForm):
    class Meta:
        model = Assignment
        fields = ['course_id', 'description', 'release_time', 'deadline', 'DUT_count', 'num_testbenches']
        date_time_options = {
                'format': 'dd/mm/yyyy HH:ii P',
                'autoclose': True,
                'showMeridian' : True,
        }
        widgets = {
            'release_time': DateTimeWidget(bootstrap_version = 3, options = date_time_options),
            'deadline': DateTimeWidget(bootstrap_version = 3, options = date_time_options),
        }
