import json

from django.views.decorators.csrf import csrf_exempt

from django.utils import timezone
from django.http import *
from datetime import datetime, timedelta

from serapis.models import *
from serapis.model_forms import *

from ipware.ip import get_ip


@csrf_exempt
def testbed_summary_report(request):
    #print(request.POST)
    ip = get_ip(request)
    #print(ip)
    info_json_string = request.POST['testbench']
    info = json.loads(info_json_string)
    for k in info:
        print('  field', k, info[k])
    port = info['localport']
    #print('A', 'localport', port)
    print('----------')
    
    testbed = Testbed()
    #TODO: choose the correct testbed type, as right now just assign a dummy type
    testbed.testbed_type = TestbedType.objects.first()
    testbed.ip_address = '%s:%d' % (ip, port)
    #TODO: report_status should be based on request
    testbed.report_status = Testbed.STATUS_AVAILABLE
    testbed.report_time = datetime.now()
    #TODO: status should be based on request
    testbed.status = Testbed.STATUS_AVAILABLE
    testbed.save()
    return HttpResponse("Gotcha!")


@csrf_exempt
def testbed_status_report(request):
    print(request.POST)
    return HttpResponse("Gotcha!")


@csrf_exempt
def testbed_task_return_output_waveform(request):
    #grading_task_id =
    grading_task = TaskGradingStatus.objects.filter(id=grading_task_id)[0]
    grading_task.grading_status = TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED
    grading_task.status_update_time = datetime.now()
    #file
    #write file to disk
    #grading_task.output_file
    return HttpResponse("Gotcha!")
