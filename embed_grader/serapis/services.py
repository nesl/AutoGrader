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

from ipware.ip import get_ip


@csrf_exempt
def testbed_summary_report(request):
    #print(request.POST)
    ip = get_ip(request)
    #print(ip)
    try:
        info_json_string = request.POST['summary']
    except MultiValueDictKeyError:
        return HttpResponseBadRequest('Bad request')

    info = json.loads(info_json_string)
    #for k in info:
    #    print('  field', k, info[k])
    port = info['localport']
    testbed_id = info['id']
    #print('A', 'localport', port)
    #print('----------')
    
    tmp_testbed_list = Testbed.objects.filter(unique_hardware_id=testbed_id)
    flag_ask_status = False
    if tmp_testbed_list:
        testbed = tmp_testbed_list[0]
        if testbed.status == Testbed.STATUS_OFFLINE:
            flag_ask_status = True
    else:
        testbed = Testbed()
        testbed.unique_hardware_id = testbed_id
        #TODO: choose the correct testbed type, as right now just assign a dummy type
        testbed.testbed_type = TestbedType.objects.first()
        #TODO: send a message to query the status instead of just assuming available
        flag_ask_status = True
    ip_port_address = '%s:%d' % (ip, port)
    testbed.ip_address = ip_port_address
    if flag_ask_status:
        r = requests.get('http://' + ip_port_address + '/tester/status/')
        if r.text == 'IDLE':
            testbed.report_status = Testbed.STATUS_AVAILABLE
            testbed.status = Testbed.STATUS_AVAILABLE
        elif r.text == 'BUSY':
            testbed.report_status = Testbed.STATUS_BUSY
            testbed.status = Testbed.STATUS_BUSY
    testbed.report_time = timezone.now()
    testbed.save()
    return HttpResponse("Gotcha!")


@csrf_exempt
def testbed_status_report(request):
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
    elif status == 'BUSY':
        testbed.report_status = Testbed.STATUS_BUSY
        testbed.status = Testbed.STATUS_BUSY
        testbed.report_time = timezone.now()
        testbed.save()

    return HttpResponse("Gotcha!")


@csrf_exempt
def testbed_return_output_waveform(request):
    if not request.method == 'POST':
        return HttpResponseBadRequest('Bad request')
    
    form = ReturningWaveformForm(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseBadRequest('Bad form request')

    unique_hardware_id = form.cleaned_data['id']
    waveform = form.cleaned_data['waveform']
    
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
    task.status_update_time = now
    task.save()

    testbed.task_being_graded = None
    testbed.report_time = now
    testbed_status = Testbed.STATUS_AVAILABLE
    testbed.status = Testbed.STATUS_AVAILABLE
    testbed.save()
    
    return HttpResponse("Gotcha!")
