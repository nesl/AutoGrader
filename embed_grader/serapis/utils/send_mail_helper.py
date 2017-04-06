from django.template.loader import get_template
from django.template import Context
from django.core.mail import send_mail


def send_by_template(subject, recipient_email_list, template_path, context_dict,
        fail_silently=False):
    template = get_template(template_path)
    context = Context(context_dict)
    message = template.render(context)
    send_mail(
            subject=subject,
            message=message,
            from_email='NESL Embed AutoGrader',
            recipient_list=recipient_email_list,
            fail_silently=fail_silently,
    )
