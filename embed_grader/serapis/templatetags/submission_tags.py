from django import template
from django.utils.html import format_html


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
