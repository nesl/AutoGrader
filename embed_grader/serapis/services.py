import json
import requests

from django.views.decorators.csrf import csrf_exempt

from django.utils import timezone
from django.http import *
from django.utils.datastructures import MultiValueDictKeyError
from django.utils import timezone

from datetime import datetime, timedelta
from serapis.models import *
from serapis.model_forms import *
from serapis.service_forms import *

from ipware.ip import get_ip


@csrf_exempt
def testbed_show_summary_report(request):
    #print(request.POST)
    ip = get_ip(request)
    #print(ip)
    try:
        info_json_string = request.POST['summary']
    except MultiValueDictKeyError:
        return HttpResponseBadRequest('Bad request')

    try:
        info = json.loads(info_json_string)
    except JSONDecodeError:
        return HttpResponseBadRequest('Bad request')

    try:
        port = info['localport']
        testbed_id = info['id']
    except KeyError:
        return HttpResponseBadRequest('Bad request')
    
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
        #TODO: choose the correct testbed type, as right now just assign a dummy type
        testbed.testbed_type = TestbedType.objects.first()
        flag_ask_status = True
    ip_port_address = '%s:%d' % (ip, port)
    testbed.ip_address = ip_port_address
    if flag_ask_status:
        try:
            r = requests.get('http://' + ip_port_address + '/tester/status/')
            if r.text == 'IDLE':
                testbed.report_status = Testbed.STATUS_AVAILABLE
                testbed.status = Testbed.STATUS_AVAILABLE
            elif r.text == 'TESTING':
                testbed.report_status = Testbed.STATUS_BUSY
                testbed.status = Testbed.STATUS_BUSY
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
        return HttpResponseBadRequest('Bad request')
    
    form = ReturnDutOutputForm(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseBadRequest('Bad form request')

    #TODO: should use use formset_factory to populate ReturnDutOutputForm,
    #from django.forms import formset_factory
    #du_output_forms = formset_factory(ReturnDutOutputForm)
    unique_hardware_id = form.cleaned_data['id']
    waveform = form.cleaned_data['dut0_waveform']
    serial_log = form.cleaned_data['dut0_serial_log']
    
    testbed_list = Testbed.objects.filter(unique_hardware_id=unique_hardware_id)
    if not testbed_list:
        return HttpResponseBadRequest('Bad request')
    testbed = testbed_list[0]

    now = timezone.now()

    task = testbed.task_being_graded
    if not task:
        return HttpResponseBadRequest('Bad request')

    task.grading_status = TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED
    task.execution_status = TaskGradingStatus.EXEC_OK
    task.output_file = waveform
    task.DUT_serial_output = serial_log
    task.status_update_time = now
    task.save()

    testbed.task_being_graded = None
    testbed.report_time = now
    testbed.report_status = Testbed.STATUS_AVAILABLE
    testbed_status = Testbed.STATUS_AVAILABLE
    testbed.save()
    
    return HttpResponse("Gotcha!")
