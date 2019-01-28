import json

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.shortcuts import render, get_object_or_404
from django.http import *
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.core import serializers
from django.template import RequestContext
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Max
from django.views.generic import TemplateView

from guardian.decorators import permission_required_or_403
from guardian.compat import get_user_model
from guardian.shortcuts import assign_perm

from serapis.models import *
from serapis.forms.testbed_forms import *
from serapis.utils import testbed_helper
from serapis.utils.grading_scheduler_heartbeat import GradingSchedulerHeartbeat
from django.views.decorators.csrf import csrf_exempt
from django.utils.formats import get_format


@login_required(login_url='/login/')
def create_testbed_type(request):
    username = request.user
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponseBadRequest("Not enough privilege")

    was_in_stage = 1
    if request.method == 'POST' and 'stage2' in request.POST:
        was_in_stage = 2

    if was_in_stage == 1:
        render_stage, render_first_time = 1, True
        if request.method == 'POST':
            render_first_time = False
            testbed_form = TestbedTypeForm(request.POST, prefix='testbed')
            he_formset = TestbedHardwareListHEFormSet(request.POST, prefix='he')
            dut_formset = TestbedHardwareListDUTFormSet(request.POST, prefix='dut')

            if testbed_form.is_valid() and he_formset.is_valid() and dut_formset.is_valid():
                tmp_dict = request.POST.dict()
                num_he = int(tmp_dict['he-TOTAL_FORMS'])
                num_dut = int(tmp_dict['dut-TOTAL_FORMS'])
                num_hardware = 0
                for prefix, num_dev in [('he', num_he), ('dut', num_dut)]:
                    for i in range(num_dev):
                        t_src_k = '%s-%d-hardware_type' % (prefix, i)
                        t_dst_k = 'hardware-%d-hardware_type' % num_hardware
                        tmp_dict[t_dst_k] = tmp_dict[t_src_k]
                        t_dst_k = 'hardware-%d-hardware_index' % num_hardware
                        tmp_dict[t_dst_k] = str(num_hardware)
                        num_hardware += 1
                tmp_dict['hardware-INITIAL_FORMS'] = '0'
                tmp_dict['hardware-TOTAL_FORMS'] = str(num_hardware)
                tmp_dict['hardware-MIN_NUM_FORMS'] = '0'
                tmp_dict['hardware-MAX_NUM_FORMS'] = str(num_hardware)
                qdict = QueryDict('', mutable=True)
                qdict.update(tmp_dict)
                request.POST = qdict
                hardware_formset = TestbedHardwareListAllFormSet(request.POST, prefix='hardware')
                render_stage, render_first_time = 2, True
    elif was_in_stage == 2:
        render_stage, render_first_time = 2, False
        testbed_form = TestbedTypeForm(request.POST, prefix='testbed')
        hardware_formset = TestbedHardwareListAllFormSet(request.POST, prefix='hardware')
        wiring_formset = TestbedTypeWiringFormSet(request.POST, prefix='wire')
        if testbed_form.is_valid() and hardware_formset.is_valid() and wiring_formset.is_valid():
            testbed = testbed_form.save()

            testbed_hardware_list = []
            for form in hardware_formset:
                testbed_hardware_list.append(TestbedHardwareList(
                        testbed_type=testbed,
                        hardware_type=form.cleaned_data.get('hardware_type'),
                        hardware_index=form.cleaned_data.get('hardware_index')))

            wiring_list = []
            for form in wiring_formset:
                wiring_list.append(TestbedTypeWiring(
                        testbed_type=testbed,
                        dev_1_index=form.cleaned_data.get('dev_1_index'),
                        dev_1_pin=form.cleaned_data.get('dev_1_pin'),
                        dev_2_index=form.cleaned_data.get('dev_2_index'),
                        dev_2_pin=form.cleaned_data.get('dev_2_pin')))

            try:
                with transaction.atomic():
                    TestbedHardwareList.objects.filter(testbed_type=testbed).delete()
                    TestbedHardwareList.objects.bulk_create(testbed_hardware_list)
                    TestbedTypeWiring.objects.filter(testbed_type=testbed).delete()
                    TestbedTypeWiring.objects.bulk_create(wiring_list)
            except IntegrityError:  # if the transaction failed
                messages.error(request, 'There was an error saving your profile.')
            return HttpResponseRedirect(reverse('testbed-type-list'))

    if render_stage == 1:
        if render_first_time:
            testbed_form = TestbedTypeForm(prefix='testbed')
            he_formset = TestbedHardwareListHEFormSet(prefix='he')
            dut_formset = TestbedHardwareListDUTFormSet(prefix='dut')
        template_context = {
                'myuser': request.user,
                'user_profile': user_profile,
                'testbed_form': testbed_form,
                'he_formset': he_formset,
                'dut_formset': dut_formset,
        }
        return render(request, 'serapis/create_testbed_type_stage1.html', template_context)
    elif render_stage == 2:
        if not hardware_formset.is_valid():
            return HttpResponse('Something is wrong or system is being hacked /__\\')

        zip_hardware_form_dev = []
        js_dev_options = []
        js_pin_options = []
        for idx, form in enumerate(hardware_formset):
            hardware = form.cleaned_data.get('hardware_type')
            zip_hardware_form_dev.append((form, hardware))
            js_dev_options.append({'val': idx, 'text': hardware.name})
            pins = HardwareTypePin.objects.filter(hardware_type=hardware)
            js_pin_options.append([{'val': p.id, 'text': p.pin_name} for p in pins])
        js_dev_opt_string = json.dumps(js_dev_options)
        js_pin_opt_string = json.dumps(js_pin_options)
        if render_first_time:
            wiring_formset = TestbedTypeWiringFormSet(prefix='wire')
        js_pin_init_val = []
        # TODO: data integrity checking
        if 'wire-TOTAL_FORMS' in request.POST:
            for i in range(int(request.POST['wire-TOTAL_FORMS'])):
                row = []
                for field in ['dev_1_index', 'dev_1_pin', 'dev_2_index', 'dev_2_pin']:
                    k = 'wire-%d-%s' % (i, field)
                    row.append(request.POST[k])
                js_pin_init_val.append(row)
        js_pin_init_val_string = json.dumps(js_pin_init_val)
        template_context = {
                'myuser': request.user,
                'user_profile': user_profile,
                'testbed_form': testbed_form,
                'hardware_formset': hardware_formset,
                'zip_hardware_form_dev': zip_hardware_form_dev,
                'js_dev_opt_string': js_dev_opt_string,
                'js_pin_opt_string': js_pin_opt_string,
                'js_pin_init_val_string': js_pin_init_val_string,
                'wiring_formset': wiring_formset,
        }
        return render(request, 'serapis/create_testbed_type_stage2.html', template_context)

@login_required(login_url='/login/')
def testbed_type(request, testbed_type_id):
    user = User.objects.get(username=request.user)
    username=request.user

    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponseBadRequest("Not enough privilege")

    try:
        testbed_type = TestbedType.objects.get(id=testbed_type_id)
    except TestbedType.DoesNotExist:
        return HttpResponseBadRequest("Testbed type not found")

    testbed_type_form = TestbedTypeForm()
    template_context = {
            "myuser": request.user,
            "testbed_type_form": testbed_type_form,
    }

    return HttpResponseBadRequest("Under construction")


@login_required(login_url='/login/')
def testbed_type_list(request):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponseBadRequest("Not enough privilege")

    testbed_type_list = TestbedType.objects.all()
    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'testbed_type_list': testbed_type_list,
    }
    return render(request, 'serapis/testbed_type_list.html', template_context)


@login_required(login_url='/login/')
def testbed_status_list(request):
    user = User.objects.get(username=request.user)
    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponseBadRequest("Not enough privilege", status=404)

    #TODO: The following code that displays grading scheduler status is experimental and should be
    #      reorganized. Instead of showing as part of the content, it should be moved to the side
    #      bar.
    is_scheduler_running = GradingSchedulerHeartbeat.is_scheduler_running()
    if is_scheduler_running is None:
        schedluer_status_msg = "The scheduler has never been started."
    elif is_scheduler_running:
        scheduler_status_msg = "The scheduler is running."
    else:
        time_been_down = GradingSchedulerHeartbeat.get_time_since_last_scheduler_crash()
        total_seconds = time_been_down.days * 86400 + time_been_down.seconds
        scheduler_status_msg = "The scheduler has been down for %d seconds." % total_seconds

    template_context = {
        'myuser': request.user,
        'is_scheduler_running': is_scheduler_running,
        'scheduler_status_msg': scheduler_status_msg,
    }
    return render(request, 'serapis/testbed_status_list.html', template_context)

        
def _convert_task_grading_status_to_JSON(task):
    if task is None:
        return None

    assignment_task = task.assignment_task_fk
    assignment = assignment_task.assignment_fk
    return {
            "course": assignment.course_fk.name,
            "assignment": assignment.name,
            "task_name": assignment_task.brief_description,
            "submission_id": task.submission_fk.id,
    }

def _convert_testbed_to_JSON(testbed):
    return {
            "id": testbed.id,
            "ip_address": testbed.ip_address,
            "status": testbed.get_status_display(),
            "report_time": testbed.report_time,
            "report_status": testbed.get_report_status_display(),
            "task": _convert_task_grading_status_to_JSON(testbed.task_being_graded),
    }

@login_required(login_url='/login/')
def ajax_get_testbeds(request):
    if not request.is_ajax():
        return HttpResponseBadRequest("Not enough privilege", status=404)

    user = User.objects.get(username=request.user)
    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponseBadRequest("Not enough privilege", status=404)

    testbed_list = Testbed.objects.all()
    ajax_json = list(map(_convert_testbed_to_JSON, testbed_list))

    return JsonResponse(ajax_json, safe=False)


@login_required(login_url='/login/')
def ajax_abort_testbed_task(request):
    if not request.is_ajax():
        return HttpResponseBadRequest("Not enough privilege", status=404)
    
    if request.method != 'POST':
        return HttpResponseBadRequest("Not enough privilege", status=404)

    try:
        testbed = Testbed.objects.get(id=request.POST['id'])
    except:
        return HttpResponseBadRequest("Not enough privilege", status=404)

    testbed_helper.abort_task(testbed, set_status=Testbed.STATUS_AVAILABLE,
            tolerate_task_is_not_present=True, check_task_status_is_executing=False)
    return JsonResponse({"done": "success"}, safe=False)
