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


@csrf_exempt
def testbed_show_summary_report(request):
    ip = get_ip(request)
    try:
        info_json_string = request.POST['summary']
    except MultiValueDictKeyError:
        print('No summary field in POST request')
        return HttpResponseBadRequest('Bad request')

    try:
        info = json.loads(info_json_string)
    except JSONDecodeError:
        print('Not in JSON format')
        return HttpResponseBadRequest('Bad request')

    try:
        port = info['localport']
        testbed_id = info['id']
    except KeyError:
        print('No localport or id field in JSON')
        return HttpResponseBadRequest('Bad request')
    
    try:
        testbed_type_name = info['testbed_type']
    except JSONDecodeError:
        print('No testbed_type field in JSON')
        return HttpResponseBadRequest('Bad request')

    testbed_types = TestbedType.objects.filter(name=testbed_type_name)
    if not testbed_types:
        print('Invalid testbed type')
        return HttpResponseBadRequest('Bad request')
    testbed_type = testbed_types[0]

    tmp_testbed_list = Testbed.objects.filter(unique_hardware_id=testbed_id)
    flag_ask_status = False
    if tmp_testbed_list:
        testbed = tmp_testbed_list[0]
        if testbed.status == Testbed.STATUS_OFFLINE:
            flag_ask_status = True
    else:
        testbed = Testbed()
        testbed.unique_hardware_id = testbed_id
        testbed.grading_deadline = timezone.now()
        flag_ask_status = True
    ip_port_address = '%s:%d' % (ip, port)
    testbed.ip_address = ip_port_address
    testbed.testbed_type_id = testbed_type
    if flag_ask_status:
        try:
            r = requests.get('http://' + ip_port_address + '/tb/status/')
            if r.text == 'IDLE':
                testbed.report_status = Testbed.STATUS_AVAILABLE
                testbed.status = Testbed.STATUS_AVAILABLE
            elif r.text == 'TESTING':
                testbed.report_status = Testbed.STATUS_BUSY
                testbed.status = Testbed.STATUS_BUSY
            else:
                testbed.report_status = Testbed.STATUS_UNKNOWN
                testbed.status = Testbed.STATUS_OFFLINE
        except requests.exceptions.ConnectionError:
            testbed.report_status = Testbed.STATUS_UNKNOWN
            testbed.status = Testbed.STATUS_OFFLINE
    testbed.report_time = timezone.now()
    testbed.save()
    return HttpResponse("Gotcha!")


@csrf_exempt
def testbed_show_status_report(request):
    try:
        status = request.POST['status']
        unique_hardware_id = request.POST['id']
    except MultiValueDictKeyError:
        return HttpResponseBadRequest('Bad request')

    testbed_list = Testbed.objects.filter(unique_hardware_id=unique_hardware_id)
    if not testbed_list:
        return HttpResponseBadRequest('No such testbed')
    testbed = testbed_list[0]

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
    
    if not request.POST['id']:
        print('Error: unique hardware id is not provided')
        return HttpResponseBadRequest('Bad request')

    testbed_list = Testbed.objects.filter(unique_hardware_id=request.POST['id'])
    if not testbed_list:
        print('Error: testbed not found')
        return HttpResponseBadRequest('Bad request')
    testbed = testbed_list[0]

    task = testbed.task_being_graded
    if not task:
        print('Error: task not found')
        return HttpResponseBadRequest('Bad request')

    form = ReturnDutOutputForm(request.POST, request.FILES, testbed=testbed)
    if not form.is_valid():
        print('Error: form is incorrect', form.errors)
        return HttpResponseBadRequest('Bad form request')
    
    form.save_and_commit()
    return HttpResponse("Gotcha!")
