from django.forms import ModelForm

from serapis.models import *


class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = ['instructor_id', 'course_code', 'name', 'description']
