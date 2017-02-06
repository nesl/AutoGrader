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

from datetime import timedelta


class RegradeForm(Form):
    AUTHOR_OPTION_ALL = 0
    AUTHOR_OPTION_CUSTOMIZED = 1
    AUTHOR_SCOPE_CHOICES = (
            (AUTHOR_OPTION_ALL, 'All students in the course'),
            (AUTHOR_OPTION_CUSTOMIZED, 'Specify a student'),
    )

    SUBMISSION_OPTION_LAST_ONES = 10
    SUBMISSION_OPTION_CUSTOMIZED = 11
    SUBMISSION_SCOPE_CHOICES = (
            (SUBMISSION_OPTION_LAST_ONES, 'Last submission of all users'),
            (SUBMISSION_OPTION_CUSTOMIZED, 'Specify submission IDs'),
    )

    def __init__(self, *args, **kwargs):
        assignment = kwargs.pop('assignment')
        super(RegradeForm, self).__init__(*args, **kwargs)

        course = assignment.course_id

        self.fields['author_scope'] = forms.ChoiceField(
                required=True,
                widget=forms.RadioSelect,
                choices=RegradeForm.AUTHOR_SCOPE_CHOICES,
                initial=RegradeForm.AUTHOR_OPTION_ALL,
        )
        self.fields['submission_scope'] = forms.ChoiceField(
                required=True,
                widget=forms.RadioSelect,
                choices=RegradeForm.SUBMISSION_SCOPE_CHOICES,
                initial=RegradeForm.SUBMISSION_OPTION_LAST_ONES,
        )

        authors = [o.user_id for o in CourseUserList.objects.filter(course_id=course)]
        author_choices = [(u.id, UserProfile.objects.get(user=u).__str__()) for u in authors]
        self.fields['author_choice'] = forms.ChoiceField(
                required=True,
                widget=forms.Select,
                choices=author_choices,
        )
        
        self.fields['submission_range'] = forms.CharField(
                required=False,
                widget=forms.TextInput,
        )

        assignment_tasks = AssignmentTask.objects.filter(assignment_id=assignment)
        assignment_task_choices = [(a.id, a.brief_description) for a in assignment_tasks]
        assignment_task_choices_id = [t[0] for t in assignment_task_choices]
        self.fields['assignment_task_choice'] = forms.MultipleChoiceField(
                widget=forms.CheckboxSelectMultiple,
                choices=assignment_task_choices,
                initial=assignment_task_choices_id,
        )
        
        # set up variables to be used
        self.assignment = assignment
        self.course = course

    def clean(self):
        super(RegradeForm, self).clean()

        # if customized submission range is set, parse the range
        if int(self.cleaned_data['submission_scope']) == RegradeForm.SUBMISSION_OPTION_CUSTOMIZED:
            submission_range_str = self.cleaned_data['submission_range']
            terms = [t.strip() for t in submission_range_str.split(',')]
            submission_ids = set()
            for t in terms:
                split_idx = t.find('-')
                if split_idx < 0:
                    try:
                        n = int(t)
                        submission_ids.add(n)
                    except:
                        raise ValidationError(_('Invalid submission range'), code='invalid_sub_range')
                else:
                    try:
                        n1, n2 = int(t[:split_idx]), int(t[split_idx+1:])
                        for i in range(n1, n2+1):
                            submission_ids.add(i)
                    except:
                        raise ValidationError(_('Invalid submission range'), code='invalid_sub_range')
            self.cleaned_data['submission_range'] = submission_ids
    
    def save_and_commit(self):
        # finalize the author list
        if int(self.cleaned_data['author_scope']) == RegradeForm.AUTHOR_OPTION_ALL:
            authors = [o.user_id for o in CourseUserList.objects.filter(course_id=self.course)]
        else:
            authors = [self.cleaned_data['author_choice']]

        # finalize the submission list
        submission_list = []
        if int(self.cleaned_data['submission_scope']) == RegradeForm.SUBMISSION_OPTION_LAST_ONES:
            for a in authors:
                query = Submission.objects.filter(student_id=a, assignment_id=self.assignment)
                if query.count() > 0:
                    submission_list.append(query.latest('id'))
        else:
            author_set = set(authors)
            for sid in self.cleaned_data['submission_range']:
                s_list = Submission.objects.filter(id=sid)
                if s_list:
                    s = s_list[0]
                    if s.student_id in author_set:
                        submission_list.append(s)

        num_affected_submissions = len(submission_list)
        num_affected_task_grading_status = 0
        assignment_tasks = [AssignmentTask.objects.get(id=atid)
                for atid in self.cleaned_data['assignment_task_choice']]
        assignment_task_set = set(assignment_tasks)
        
        # change TaskGradingStatus records
        for s in submission_list:
            task_grading_status_list = TaskGradingStatus.objects.filter(submission_id=s)
            for task_grading in task_grading_status_list:
                if task_grading.assignment_task_id in assignment_task_set:
                    task_grading.grading_status = TaskGradingStatus.STAT_PENDING
                    task_grading.points = 0.
                    task_grading.save()
                    num_affected_task_grading_status += 1

        return (num_affected_submissions, num_affected_task_grading_status)

