from django.forms import ModelForm
from datetimewidget.widgets import DateTimeWidget

from serapis.models import *


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
