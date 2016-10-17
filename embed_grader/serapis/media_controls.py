import os.path

from django.conf import settings
from django.http import *
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.encoding import smart_str

from datetime import timedelta
from serapis.models import *

from django.contrib.auth.models import User, Group
from guardian.decorators import permission_required_or_403
from guardian.compat import get_user_model
from guardian.shortcuts import assign_perm



# Note: please keep the function name as in the convention of <model>_<attribute>.


def _get_query_file_name(request_full_path):
    skip = len(settings.MEDIA_URL)
    query_file_name = request_full_path[skip:]
    if query_file_name[-1] == '/':
        query_file_name = query_file_name[:-1]
    return query_file_name


def _make_http_response_for_file_download(file_path):
    response = HttpResponse(content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(os.path.basename(file_path))
    response['X-Sendfile'] = smart_str(file_path)
    return response


def hardware_type_pinout(request):
    query_file_name = _get_query_file_name(request.get_full_path())
    
    hardware_types = HardwareType.objects.filter(pinout=query_file_name)
    if len(hardware_types) == 0:
        return HttpResponseForbidden()

    if len(hardware_types) >= 2:
        print('Warning: find 2 or more records with this file name')

    hardware_type = hardware_types[0]

    return _make_http_response_for_file_download(hardware)


def submission_file(request):
    user = User.objects.get(username=request.user)
    query_file_name = _get_query_file_name(request.get_full_path())
    
    submissions = Submission.objects.filter(file=query_file_name)
    if len(submissions) == 0:
        return HttpResponseForbidden()
    
    if len(submissions) >= 2:
        print('Warning: find 2 or more records with this file name')

    submission = submissions[0]
    course = submission.assignment_id.course_id

    can_download = False
    if submission.student_id == user:
        can_download = True
    elif user.has_perm('modify_assignment', course):
        can_download = True

    if not can_download:
        return HttpResponseForbidden()
    else:
        return _make_http_response_for_file_download(submission.file.path)
