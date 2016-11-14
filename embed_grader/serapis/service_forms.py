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
            field_name = 'file_' + field.field
            self.fields[field_name] = forms.FileField(allow_empty_file=True)

        # set up variables to be used
        self.testbed = testbed
        self.task = task
        self.task_files = task_files

    def save_and_commit(self):
        now = timezone.now()

        self.task.update(
                grading_status=TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED,
                execution_status=TaskGradingStatus.EXEC_OK,
                status_update_time=now,
        )
        self.testbed.update(
                task_being_graded=None,
                report_time=now,
                report_status=Testbed.STATUS_AVAILABLE,
                status=Testbed.STATUS_AVAILABLE,
        )

        grading_task_status_files = []
        for field_name in self.task_files:
            task_file = self.task_files[field_name]
            task_file.update(file=self.cleaned_data[field_name])
            grading_task_status_files.append(task_file)

        return (self.task, self.testbed, grading_task_status_files)
