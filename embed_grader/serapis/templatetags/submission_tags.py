import re
import pytz

from django.core.urlresolvers import reverse

from django import template
from django.utils.html import format_html

from serapis.models import *
from serapis.utils import user_info_helper


register = template.Library()


@register.simple_tag
def show_score(achieved_score, total_score):
	try:
		achieved_score = str(round(float(achieved_score), 2))
	except:
		pass

	try:
		total_score = str(round(float(total_score), 2))
	except:
		pass
	
	background_color = ('green'
			if achieved_score != '0.0' and achieved_score == total_score else 'darkred')
	return format_html('<span class="badge" style="background:%s; width:100px;">%s / %s</span>' % (
			background_color, achieved_score, total_score))

def show_status(status):
    try:
        status = str(status)
    except:
        pass
    


class SubmissionTableSchemaNode(template.Node):
    SCHEMA_ASSIGNMENT = 'assignment'
    SCHEMA_STATUS = 'status'
    SCHEMA_SCORE = 'score'
    SCHEMA_SUBMISSION_TIME = 'submission_time'
    SCHEMA_DETAIL_BUTTON = 'detail_button'
    SCHEMA_AUTHOR_NAME = 'author_name'

    QUALIFIED_SCHEMA = [
            SCHEMA_ASSIGNMENT,
            SCHEMA_STATUS,
            SCHEMA_SCORE,
            SCHEMA_SUBMISSION_TIME,
            SCHEMA_DETAIL_BUTTON,
            SCHEMA_AUTHOR_NAME,
    ]

    def __init__(self, schema_list, width_attr_list, var_name):
        self.schema_list = schema_list
        self.width_attr_list = width_attr_list
        self.var_name = var_name
        print(self.schema_list)
        print(self.width_attr_list)
        print(self.var_name)

    def render(self, context):
        context[self.var_name] = self.schema_list
        return format_html(''.join([
            '<th style="wdith:%s">%s</th>' % (width, schema_name.replace('_', ' ').capitalize())
                for schema_name, width in zip(self.schema_list, self.width_attr_list)]))


@register.tag(name="submission_table_schema")
def do_submission_table_schema(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires arguments" % token.contents.split()[0]
        )
    
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError("%r tag had invalid arguments" % tag_name)
    
    format_string, var_name = m.groups()
    terms = [w.strip() for w in format_string.split()]
    terms = [w for w in terms if w]

    if len(terms) == 0 or len(terms) % 2 == 1:
        raise template.TemplateSyntaxError(
            "%r tag should have more than 0 and even number of arguments" % tag_name
        )
    
    schema_list = terms[::2]
    attr_list = terms[1::2]

    for sch in schema_list:
        if sch not in SubmissionTableSchemaNode.QUALIFIED_SCHEMA:
            raise template.TemplateSyntaxError(
                "%r tag does not support schema %s" % (tag_name, sch)
            )

    return SubmissionTableSchemaNode(schema_list, attr_list, var_name)


@register.simple_tag
def submission_table_row(table_schema, submission, user):
    return RenderSubmissionTableRow(table_schema, submission, user).render()


class RenderSubmissionTableRow:
    def __init__(self, table_schema, submission, user):
        schema_to_function = {
                SubmissionTableSchemaNode.SCHEMA_ASSIGNMENT: self._get_content_assignment,
                SubmissionTableSchemaNode.SCHEMA_STATUS: self._get_content_status,
                SubmissionTableSchemaNode.SCHEMA_SCORE: self._get_content_score,
                SubmissionTableSchemaNode.SCHEMA_SUBMISSION_TIME: self._get_content_submission_time,
                SubmissionTableSchemaNode.SCHEMA_DETAIL_BUTTON: self._get_content_detail_button,
                SubmissionTableSchemaNode.SCHEMA_AUTHOR_NAME: self._get_content_author_name,
        }
        self.submission = submission
        self.user = user
        self.include_hidden = (submission.assignment_id.viewing_scope_by_user(user)
                == Assignment.VIEWING_SCOPE_FULL)
        self.result = format_html(
                ''.join(['<td>' + schema_to_function[sch]() + '</td>'
                    for sch in table_schema]))

    def render(self):
        return self.result

    def _get_content_assignment(self):
        assignment = self.submission.assignment_id
        return '<a href="%s">%s</a>' % (
                reverse('assignment', kwargs={'assignment_id': assignment.id}), assignment.name)

    def _get_content_status(self):
        (all_assignment_tasks, _) = (self.submission.assignment_id
                .retrieve_assignment_tasks_and_score_sum(include_hidden=True))
        (task_grading_status_list, _, _) = (
                self.submission.retrieve_task_grading_status_and_score_sum(self.include_hidden))
        
        atid_2_task_grading_status = {}
        for task_grading_stataus in task_grading_status_list:
            atid = task_grading_status.assignment_id.id
            atid_2_task_grading_status[atid] = task_grading_status


        status_2_text = {
                TaskGradingStatus.STAT_PENDING: 'P',
                TaskGradingStatus.STAT_EXECUTING: 'E',
                TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED: 'C',
                TaskGradingStatus.STAT_FINISH: 'F',
                TaskGradingStatus.STAT_INTERNAL_ERROR: '!',
                TaskGradingStatus.STAT_SKIPPED: 'S',
        }
        status_2_style = {
                TaskGradingStatus.STAT_PENDING: 'color:#378',
                TaskGradingStatus.STAT_EXECUTING: 'color:#373',
                TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED: 'color:#373',
                TaskGradingStatus.STAT_FINISH: 'color:#863',
                TaskGradingStatus.STAT_INTERNAL_ERROR: 'color:red',
                TaskGradingStatus.STAT_SKIPPED: 'color:#aaa',
        }
        htmls = []
        for assignment_task in all_assignment_tasks:
            atid = assignment_task.id
            if atid not in atid_2_task_grading_status:
                htmls.append(self._render_task_status(' ', 'color:#aaa', None))
            else:
                task = atid_2_task_grading_status[atid]
                status = task.grading_status
                task_id_for_url = task.id if task.can_detail_be_viewed_by_user(self.user) else None
                htmls.append(self._render_task_status(status_2_text[status],
                    status_2_style[status], task_id_for_url))
        return ''.join(htmls)

    def _get_content_score(self):
        (_, student_score, total_score) = (
                self.submission.retrieve_task_grading_status_and_score_sum(self.include_hidden))
        return show_score(student_score, total_score)

    def _get_content_submission_time(self):
        return self.submission.submission_time.astimezone(
                pytz.timezone('US/Pacific')).strftime("%Y-%m-%d %H:%M:%S")

    def _get_content_detail_button(self):
        url_str = reverse('submission', kwargs={'submission_id': self.submission.id})
        return ('<a class="btn btn-primary" href="%s" style="font-size:12px; background:white; '
                + 'width:90px; color:SteelBlue; border-color:SteelBlue">'
                + '<span class="glyphicon glyphicon-file"></span>&nbsp;Detail</a>') % url_str

    def _get_content_author_name(self):
        return user_info_helper.get_first_last_name(self.submission.student_id)

    def _render_task_status(self, text, style, task_id_for_url):
        if not task_id_for_url:
            a_tag_prefix, a_tag_postfix = '', ''
        else:
            a_tag_prefix = '<a href="%s">' % reverse(
                    'task-grading-detail', kwargs={'task_grading_id': task_id_for_url})
            a_tag_postfix = '</a>'
        return '%s<span style="%s">[%s]</span>%s' % (a_tag_prefix, style, text, a_tag_postfix)
