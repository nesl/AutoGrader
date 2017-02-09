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



def _get_submission_content_assignment(submission, _):
    return 'not support'

def _get_submission_content_status(submission, include_hidden):
    return 'not support'

def _get_submission_content_score(submission, include_hidden):
    (_, s_stu, s_all) = submission.retrieve_task_grading_status_and_score_sum(include_hidden)
    return show_score(s_stu, s_all)

def _get_submission_content_submission_time(submission, _):
    return submission.submission_time.astimezone(
            pytz.timezone('US/Pacific')).strftime("%Y-%m-%d %H:%M:%S")

def _get_submission_content_detail_button(submission, _):
    url_str = reverse('submission', kwargs={'submission_id': submission.id})
    return ('<a class="btn btn-primary" href="%s" style="font-size:12px; background:white; '
            + 'width:90px; color:SteelBlue; border-color:SteelBlue">'
            + '<span class="glyphicon glyphicon-file"></span>&nbsp;Detail</a>') % url_str

def _get_submission_content_author_name(submission, _):
    return user_info_helper.get_first_last_name(submission.student_id)


@register.simple_tag
def submission_table_row(table_schema, submission, user):
    schema_to_function = {
            SubmissionTableSchemaNode.SCHEMA_ASSIGNMENT: _get_submission_content_assignment,
            SubmissionTableSchemaNode.SCHEMA_STATUS: _get_submission_content_status,
            SubmissionTableSchemaNode.SCHEMA_SCORE: _get_submission_content_score,
            SubmissionTableSchemaNode.SCHEMA_SUBMISSION_TIME: _get_submission_content_submission_time,
            SubmissionTableSchemaNode.SCHEMA_DETAIL_BUTTON: _get_submission_content_detail_button,
            SubmissionTableSchemaNode.SCHEMA_AUTHOR_NAME: _get_submission_content_author_name,
    }
    include_hidden = (
            submission.assignment_id.viewing_scope_by_user(user) == Assignment.VIEWING_SCOPE_FULL)

    return format_html(''.join(['<td>' + schema_to_function[sch](submission, include_hidden) + '</td>'
            for sch in table_schema]))
