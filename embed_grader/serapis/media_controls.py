import os.path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import *
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.encoding import smart_str

from datetime import timedelta
from serapis.models import *

from wsgiref.util import FileWrapper

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
    #response = HttpResponse(content_type='application/force-download')
    wrapper = FileWrapper(open(file_path, 'rb'))
    response = HttpResponse(wrapper, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(os.path.basename(file_path))
    response['Content-Length'] = os.path.getsize(file_path)
    response['X-Sendfile'] = smart_str(file_path)
    return response


@login_required(login_url='/login/')
def hardware_type_pinout(request):
    query_file_name = _get_query_file_name(request.get_full_path())

    # Check file exists
    hardware_types = HardwareType.objects.filter(pinout=query_file_name)
    if len(hardware_types) == 0:
        return HttpResponseForbidden()

    if len(hardware_types) >= 2:
        print('Warning: find 2 or more records with this file name')

    hardware_type = hardware_types[0]

    return _make_http_response_for_file_download(hardware_type.pinout.path)


@login_required(login_url='/login/')
def testbed_hardware_list_firmware(request):
    query_file_name = _get_query_file_name(request.get_full_path())

    # Check file exists
    testbed_hardware_lists = TestbedHardwareList.objects.filter(firmware=query_file_name)
    if len(testbed_hardware_lists) == 0:
        return HttpResponseForbidden()

    if len(testbed_hardware_lists) >= 2:
        print('Warning: find 2 or more records with this file name')

    testbed_hardware_list = testbed_hardware_lists[0]

    return _make_http_response_for_file_download(testbed_hardware_list.firmware.path)


@login_required(login_url='/login/')
def assignment_task_test_input(request):
    user = User.objects.get(username=request.user)
    query_file_name = _get_query_file_name(request.get_full_path())

    # Check file exists
    assignment_tasks = AssignmentTask.objects.filter(test_input=query_file_name)
    if len(assignment_tasks) == 0:
        return HttpResponseForbidden()

    if len(assignment_tasks) >= 2:
        print('Warning: find 2 or more records with this file name')

    assignment_task = assignment_tasks[0]
    if assignment_task.can_access_test_input_by_user(user):
        return _make_http_response_for_file_download(assignment_task.test_input.path)
    else:
        return HttpResponseForbidden()


@login_required(login_url='/login/')
def assignment_task_grading_script(request):
    user = User.objects.get(username=request.user)
    query_file_name = _get_query_file_name(request.get_full_path())

    # Check file exists
    assignment_tasks = AssignmentTask.objects.filter(grading_script=query_file_name)
    if len(assignment_tasks) == 0:
        return HttpResponseForbidden()

    if len(assignment_tasks) >= 2:
        print('Warning: find 2 or more records with this file name')

    assignment_task = assignment_tasks[0]
    if assignment_task.can_access_grading_script_by_user(user):
        return _make_http_response_for_file_download(assignment_task.grading_script.path)
    else:
        return HttpResponseForbidden()


@login_required(login_url='/login/')
def submission_file(request):
    user = User.objects.get(username=request.user)
    query_file_name = _get_query_file_name(request.get_full_path())

    # Check file exists
    submissions = Submission.objects.filter(file=query_file_name)
    if len(submissions) == 0:
        return HttpResponseForbidden()

    if len(submissions) >= 2:
        print('Warning: find 2 or more records with this file name')

    submission = submissions[0]

    if submission.can_access_file_by_user(user):
        return _make_http_response_for_file_download(submission.file.path)
    else:
        return HttpResponseForbidden()


@login_required(login_url='/login/')
def submission_file2(request):
    user = User.objects.get(username=request.user)
    query_file_name = _get_query_file_name(request.get_full_path())

    # check if file exists
    submission_file = SubmissionFile.objects.filter(file=query_file_name)
    if len(submission_file) == 0:
        return HttpResponseForbidden()

    if len(submission_file) > 1:
        print('Warning: find 2 or more records with this file name')

    file_to_download = submission_file[0]

    return _make_http_response_for_file_download(file_to_download.file.path)


@login_required(login_url='/login/')
def task_grading_status_output_file(request):
    user = User.objects.get(username=request.user)
    query_file_name = _get_query_file_name(request.get_full_path())

    # Check file exists
    status_list = TaskGradingStatus.objects.filter(output_file=query_file_name)
    if len(status_list) == 0:
        return HttpResponseForbidden()

    if len(status_list) >= 2:
        print('Warning: find 2 or more records with this file name')

    status = status_list[0]
    if status.can_access_output_file_by_user(user):
        return _make_http_response_for_file_download(status.output_file.path)
    else:
        return HttpResponseForbidden()


@login_required(login_url='/login/')
def task_grading_status_grading_detail(request):
    user = User.objects.get(username=request.user)
    query_file_name = _get_query_file_name(request.get_full_path())

    # Check file exists
    status_list = TaskGradingStatus.objects.filter(grading_detail=query_file_name)
    if len(status_list) == 0:
        return HttpResponseForbidden()

    if len(status_list) >= 2:
        print('Warning: find 2 or more records with this file name')

    status = status_list[0]
    if status.can_access_output_file_by_user(user):
        return _make_http_response_for_file_download(status.grading_detail.path)
    else:
        return HttpResponseForbidden()


@login_required(login_url='/login/')
def task_grading_status_dut_serial_output(request):
    user = User.objects.get(username=request.user)
    query_file_name = _get_query_file_name(request.get_full_path())

    # Check file exists
    status_list = TaskGradingStatus.objects.filter(DUT_serial_output=query_file_name)
    if len(status_list) == 0:
        return HttpResponseForbidden()

    if len(status_list) >= 2:
        print('Warning: find 2 or more records with this file name')

    status = status_list[0]
    if status.can_access_output_file_by_user(user):
        return _make_http_response_for_file_download(status.DUT_serial_output.path)
    else:
        return HttpResponseForbidden()



def content_images(request):
    query_file_name = _get_query_file_name(request.get_full_path())
    return _make_http_response_for_file_download(settings.MEDIA_ROOT + query_file_name)
