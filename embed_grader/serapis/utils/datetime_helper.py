import pytz

from embed_grader import settings


def print_datetime(datetime_obj, format):
    return datetime_obj.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime(format)
