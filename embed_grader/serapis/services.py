from django.views.decorators.csrf import csrf_exempt

from django.utils import timezone
from datetime import datetime, timedelta

from serapis.models import *
from serapis.model_forms import *

from ipware.ip import get_ip


@csrf_exempt
def testbed_summary_report(request):
    print(request.POST)
    print(request)
    ip = get_ip(request)
    print(ip)
    #port
    testbed = Testbed()
    #TODO: choose the correct testbed type, as right now just assign a dummy type
    testbed.testbed_type = TestbedType.objects.first()
    #testbed.ip_address =
    #testbed.report_status = 
    testbed.report_time = datetime.now()
    #testbed.status = 
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
