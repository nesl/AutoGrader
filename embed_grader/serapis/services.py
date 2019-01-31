import json
import requests

from django.views.decorators.csrf import csrf_exempt

from django.http import *
from django.utils.datastructures import MultiValueDictKeyError
from django.utils import timezone

from datetime import timedelta
from serapis.models import *
from serapis.forms.service_forms import *

from ipware.ip import get_ip


TESTBED_REPLIED_STATUS_MSG_CONVERSION = {
    'IDLE': Testbed.STATUS_AVAILABLE,
    'TESTING': Testbed.STATUS_BUSY,
}


def _interpret_testbed_replied_status_msg(msg):
    if msg not in TESTBED_REPLIED_STATUS_MSG_CONVERSION:
        return Testbed.STATUS_UNKNOWN
    return TESTBED_REPLIED_STATUS_MSG_CONVERSION[msg]

def _get_ip_port(request):
    try:
        ip = get_ip(request)
        port = int(request.POST['localport'])
        return '%s:%d' % (ip, port)
    except MultiValueDictKeyError:
        print('No localport is provided')
    except ValueError:
        print('"port" is not an integer')
    return None

@csrf_exempt
def testbed_show_summary_report(request):
    if not request.method == 'POST':
        print('Error: not use post')
        return HttpResponseBadRequest('Bad request')

    # figure out IP and port
    ip_port = _get_ip_port(request)
    if not ip_port:
        return HttpResponseBadRequest('Bad request')
    
    # extract testbed type and check if the type can be recognized
    try:
        testbed_type_name = request.POST['testbed_type']
    except MultiValueDictKeyError:
        print('No testbed_type is provided')
        return HttpResponseBadRequest('Bad request')

    testbed_types = TestbedType.objects.filter(name=testbed_type_name)
    if not testbed_types:
        print('Invalid testbed type')
        return HttpResponseBadRequest('Bad request')
    testbed_type = testbed_types[0]

    # extract testbed status
    try:
        testbed_status_msg = request.POST['status']
    except MultiValueDictKeyError:
        print('No status is provided')
        return HttpResponseBadRequest('Bad request')

    # identify the testbed if a record in database can be found, otherwise create a new `Testbed`
    # object
    tmp_testbed_list = Testbed.objects.filter(ip_address=ip_port)
    if tmp_testbed_list.exists():
        testbed = tmp_testbed_list[0]
    else:
        testbed = Testbed()
        testbed.testbed_type_fk = testbed_type
        testbed.ip_address = ip_port
        testbed.task_being_graded = None
        testbed.grading_deadline = timezone.now()
        testbed.status = Testbed.STATUS_AVAILABLE
    
    #TODO: shall we do anything if testbed_type does not match what database remembers?
    testbed.testbed_type_fk = testbed_type

    # detemine testbed status
    testbed.report_status = _interpret_testbed_replied_status_msg(testbed_status_msg)
    testbed.report_time = timezone.now()

    if testbed.report_status == Testbed.STATUS_AVAILABLE:
        # if remote testbed reports available, make sure that AutoGrader recognize it as a free
        # resource (i.e., not tied to any task)
        if testbed.task_being_graded is None:
            testbed.status = Testbed.STATUS_AVAILABLE
    elif testbed.report_status == Testbed.STATUS_BUSY:
        # if remote testbed reports busy, then we believe the testbed is busy
        testbed.status = Testbed.STATUS_BUSY
    else:  # testbed.report_status == Testbed.STATUS_UNKNOWN:
        # if remote testbed reports bogus message (likely crashed), abort the task being graded by
        # this testbed
        if testbed.task_being_graded is not None:
            testbed_helper.abort_task(
                    testbed, set_status=testbed.status, check_task_status_is_executing=False)
        testbed.status = Testbed.STATUS_OFFLINE
        
    testbed.save()
    return HttpResponse("Gotcha!")


@csrf_exempt
def testbed_show_status_report(request):
    if not request.method == 'POST':
        print('Error: not use post')
        return HttpResponseBadRequest('Bad request')

    ip_port = _get_ip_port(request)
    if not ip_port:
        return HttpResponseBadRequest('Bad request')

    testbed_list = Testbed.objects.filter(ip_address=ip_port)
    if not testbed_list:
        return HttpResponseBadRequest('No such testbed')
    testbed = testbed_list[0]

    try:
        status = request.POST['status']
    except MultiValueDictKeyError:
        print('Error: no "status" field')
        return HttpResponseBadRequest('Bad request')

    if status == 'IDLE':
        testbed.report_status = Testbed.STATUS_AVAILABLE
        testbed.status = Testbed.STATUS_AVAILABLE
        testbed.report_time = timezone.now()
        testbed.save()
    elif status == 'TESTING':
        testbed.report_status = Testbed.STATUS_BUSY
        testbed.status = Testbed.STATUS_BUSY
        testbed.report_time = timezone.now()
        testbed.save()

    return HttpResponse("Gotcha!")


@csrf_exempt
def testbed_return_dut_output(request):
    if not request.method == 'POST':
        print('Error: not use post')
        return HttpResponseBadRequest('Bad request')
    
    ip_port = _get_ip_port(request)
    if not ip_port:
        return HttpResponseBadRequest('Bad request')

    testbed_list = Testbed.objects.filter(ip_address=ip_port)
    if not testbed_list:
        print('Error: testbed not found')
        return HttpResponseBadRequest('Bad request')
    testbed = testbed_list[0]

    task = testbed.task_being_graded
    if not task:
        print('Error: task not found')
        return HttpResponseBadRequest('Bad request')

    if not request.POST['secret_code']:
        print('Error: no secret code is returned')
        return HttpResponseBadRequest('Bad request')
    
    returned_secret_code = request.POST['secret_code']
    if returned_secret_code != testbed.secret_code:
        print('Error: secret code does not match')
        return HttpResponseBadRequest('Bad request')

    form = ReturnDutOutputForm(request.POST, request.FILES, testbed=testbed)
    if not form.is_valid():
        print('Error: form is incorrect', form.errors)
        return HttpResponseBadRequest('Bad form request')
    
    form.save_and_commit()
    return HttpResponse("Gotcha!")
