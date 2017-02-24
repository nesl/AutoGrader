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

        schema_names = file_schema.get_task_grading_status_file_schema_names(assignment)
        for schema_name in schema_names:
            field_name = 'file_' + schema_name
            self.fields[field_name] = forms.FileField(allow_empty_file=True)

        # set up variables to be used
        self.testbed = testbed
        self.task = task
        self.schema_names = schema_names

    def save_and_commit(self):
        """
        Return:
          (task_grading_status, testbed)
        """
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

        schema_name_2_files = {}
        for schema_name in self.schema_names:
            field_name = 'file_' + schema_name
            schema_name_2_files[schema_name] = self.cleaned_data[field_name]
        file_schema.save_dict_schema_name_to_task_grading_status_files(
                self.task, schema_name_2_files)

        return (self.task, self.testbed)
