from django import forms
from django.utils import timezone

from serapis.models import *
from serapis.utils import file_schema


class ReturnDutOutputForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        testbed = kwargs.pop('testbed')
        super(ReturnDutOutputForm, self).__init__(*args, **kwargs)

        # services.py has checked the graded task is valid
        task = testbed.task_being_graded
        assignment = task.assignment_task_id.assignment_id

        task_files = file_schema.get_task_grading_status_files(assignment, task)
        for field in task_files:
            field_name = 'file_' + field
            self.fields[field_name] = forms.FileField(allow_empty_file=True)

        # set up variables to be used
        self.testbed = testbed
        self.task = task
        self.task_files = task_files

    def save_and_commit(self):
        now = timezone.now()

        self.task.grading_status = TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED
        self.task.execution_status = TaskGradingStatus.EXEC_OK
        self.task.status_update_time = now
        self.task.save()
        
        self.testbed.task_being_graded = None
        self.testbed.report_time = now
        self.testbed.report_status = Testbed.STATUS_AVAILABLE
        self.testbed.status = Testbed.STATUS_AVAILABLE
        self.testbed.save()

        grading_task_status_files = []
        for field in self.task_files:
            field_name = 'file_' + field
            task_file = self.task_files[field]
            task_file.file = self.cleaned_data[field_name]
            task_file.save()
            grading_task_status_files.append(task_file)

        return (self.task, self.testbed, grading_task_status_files)
