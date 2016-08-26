import json

from django.shortcuts import render, get_object_or_404
from django.http import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, context_processors
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied

from django.template import RequestContext
from django.forms import modelform_factory
from django import forms
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db import transaction

from django.utils import timezone
from datetime import datetime, timedelta

from serapis.models import *
from serapis.model_forms import *

import hashlib, random

def registration(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            datas={}
            datas['uid']=form.cleaned_data['uid']
            datas['email']=form.cleaned_data['email']
            datas['password1']=form.cleaned_data['password1']
            #We will generate a random activation key
            salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
            usernamesalt = datas['uid']
            if isinstance(usernamesalt, unicode):
                usernamesalt = usernamesalt.encode('utf8')
            datas['activation_key']= hashlib.sha1(salt+usernamesalt).hexdigest()
            datas['email_path']="serapis/activation_email.html"
            datas['email_subject']="Account Activation"

            form.sendEmail(datas) #Send validation email
            form.save(datas) #Save the user and his profile

            request.session['registered']=True #For display purposes
            return render(request, 'serapis/registration_done.html', locals())
    else:
        form = UserCreateForm()
    return render(request, 'serapis/registration.html', {'form':form})

#View called from activation email. Activate user if link didn't expire (48h default), or offer to
#send a second link if the first expired.
def activation(request, key):
    activation_expired = False
    already_active = False
    user_profile = get_object_or_404(UserProfile, activation_key=key)
    if user_profile.user.is_active == False:
        if timezone.now() > user_profil.key_expires:
            activation_expired = True 
            #Display : offer to user to have another activation link (a link in template sending to the view new_activation_link)
            id_user = user_profile.user.id
        else: #Activation successful
            user_profile.user.is_active = True
            user_profile.user.save()
    #If user is already active, simply display error message
    else:
        already_active = True #Display : error message
    return render(request, 'serapis/activation.html', locals())

def new_activation(request, user_id):
    form = UserCreationForm()
    datas={}
    user = User.objects.get(id=user_id)
    if user is not None and not user.is_active:
        datas['uid']=user.uid
        datas['email']=user.email
        datas['email_path']="serapis/activation_email_resend.html"
        datas['email_subject']="Account Activation Resend"

        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        usernamesalt = datas['uid']
        if isinstance(usernamesalt, unicode):
            usernamesalt = usernamesalt.encode('utf8')
        datas['activation_key']= hashlib.sha1(salt+usernamesalt).hexdigest()

        user_profile = UserProfile.objects.get(user=user)
        user_profile.activation_key = datas['activation_key']
        user_profile.key_expires = datetime.strftime(datetime.now() + timedelta(days=2), "%Y-%m-%d %H:%M:%S")
        user_profile.save()
        form.sendEmail(datas)
        request.session['new_link']=True #Display : new link send

    return HttpResponse("The new verification link has been sent to your email. Please check.")


def logout_view(request):
    logout(request)


@login_required(login_url='/login/')
def homepage(request):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]

    course_list = Course.objects.filter(instructor_id=user_profile)
    template_context = {
            'user_profile': user_profile,
            'myuser': request.user,
            'course_list': course_list,
    }
    return render(request, 'serapis/homepage.html', template_context)


@login_required(login_url='/login/')
def create_course(request):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    
    if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
        return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            course.save()
            return HttpResponseRedirect(reverse('homepage'))
    else:
        form = CourseForm(initial={'instructor_id': user_profile})
    
    form.fields['instructor_id'].widget = forms.NumberInput(attrs={'readonly':'readonly'})

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form.as_p(),
    }
    return render(request, 'serapis/create_course.html', template_context)


@login_required(login_url='/login/')
def modify_course(request, course_id):
    return HttpResponse("Under construction")


@login_required(login_url='/login/')
def course(request, course_id):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    course_list = Course.objects.filter(id=course_id)
    if not course_list:
        return HttpResponse("Course cannot be found")
    course = course_list[0]
    assignment_list = Assignment.objects.filter(course_id=course_id)
    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'course': course,
            'assignment_list': assignment_list,
    }
    return render(request, 'serapis/course.html', template_context)


@login_required(login_url='/login/')
def create_assignment(request, course_id):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    
    if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
        return HttpResponse("Not enough privilege")

    course_list = Course.objects.filter(id=course_id)
    if not course_list:
        return HttpResponse("Course cannot be found")
    course = course_list[0]

    if request.method == 'POST':
        form = AssignmentBasicForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            assignment.save()
            return HttpResponseRedirect(reverse('course', args=(course_id)))
    else:
        form = AssignmentBasicForm(initial={'course_id': course_id})
    
    form.fields['course_id'].widget = forms.NumberInput(attrs={'readonly':'readonly'})
    
    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form.as_p(),
    }
    return render(request, 'serapis/create_assignment.html', template_context)


@login_required(login_url='/login/')
def assignment(request, course_id):
    return HttpResponse("Under construction")


@login_required(login_url='/login/')
def modify_assignment(request, assignment_id):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    
    if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
        return HttpResponse("Not enough privilege")

    assignment_list = Assignment.objects.filter(id=assignment_id)
    if not assignment_list:
        return HttpResponse("Assignment cannot be found")
    assignment = assignment_list[0]

    if request.method == 'POST':
        print(request.POST)
        for key in request.POST:
            print(key, request.POST[key])
    #    form = AssignmentBasicForm(request.POST)
    #    #if form.is_valid():
    #    #    assignment = form.save()
    #    #    assignment.save()
    #    #    return HttpResponseRedirect(reverse('course', args=(course_id)))
    else:
        form = AssignmentCompleteForm(instance = assignment)
    
    if not assignment.testbed_type_id:
        form.fields.pop('testbed_type_id')
        form.fields.pop('num_testbeds')

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form.as_p(),
    }
    return render(request, 'serapis/modify_assignment.html', template_context)


@login_required(login_url='/login/')
def testbed_type_list(request):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    
    if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
        return HttpResponse("Not enough privilege")

    testbed_type_list = TestbedType.objects.all()
    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'testbed_type_list': testbed_type_list,
    }
    return render(request, 'serapis/testbed_type_list.html', template_context)


@login_required(login_url='/login/')
def testbed_type(request, testbed_type_id):
    return HttpResponse("Under construction")


@login_required(login_url='/login/')
def create_testbed_type(request):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    
    if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
        return HttpResponse("Not enough privilege")

    was_in_stage = 1
    if request.method == 'POST' and 'stage2' in request.POST:
        was_in_stage = 2

    if was_in_stage == 1:
        render_stage = 1
        if request.method == 'POST':
            testbed_form = TestbedTypeForm(request.POST, prefix='testbed')
            he_formset = TestbedHardwareListHEFormSet(request.POST, prefix='he')
            dut_formset = TestbedHardwareListDUTFormSet(request.POST, prefix='dut')
            #request.POST = QueryDict('people=Aaron&people=Randy&people=Chris&people=Andrew&message=Hello!')
            #print(request.POST)
            
            #dict = {'a': 'one', 'b': 'two', }
            #qdict = QueryDict('', mutable=True)
            #qdict.update(dict)
            #request.POST = qdict
            #print(request.POST)

            print(testbed_form.is_valid(), he_formset.is_valid(), dut_formset.is_valid())
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
                render_stage = 2
                print(request.POST)
                #assignment = form.save()
                #assignment.save()
                #return HttpResponseRedirect(reverse('course', args=(course_id)))
    elif was_in_stage == 2:
        render_stage = 2
        # if everything is valid
        #     return HttpResponseRedirect(reverse('testbed-type-list'))
        
    if render_stage == 1:
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
        testbed_form = TestbedTypeForm(request.POST, prefix='testbed')
        hardware_formset = TestbedHardwareListAllFormSet(request.POST, prefix='hardware')
        print(hardware_formset)
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
        js_dev_string = json.dumps(js_dev_options)
        js_pin_string = json.dumps(js_pin_options)
        wiring_form = TestbedTypeWiringForm()
        print(wiring_form)
        template_context = {
                'myuser': request.user,
                'user_profile': user_profile,
                'testbed_form': testbed_form,
                'hardware_formset': hardware_formset,
                'zip_hardware_form_dev': zip_hardware_form_dev,
                'js_dev_string': js_dev_options,
                'js_pin_string': js_pin_options,
        }
        return render(request, 'serapis/create_testbed_type_stage2.html', template_context)


@login_required(login_url='/login/')
def hardware_type_list(request):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    
    if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
        return HttpResponse("Not enough privilege")
    
    hardware_type_list = HardwareType.objects.all()
    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'hardware_type_list': hardware_type_list,
    }
    return render(request, 'serapis/hardware_type_list.html', template_context)


@login_required(login_url='/login/')
def hardware_type(request, hardware_type_id):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    
    if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
        return HttpResponse("Not enough privilege")
    
    hardware_type_list = HardwareType.objects.filter(id=hardware_type_id)
    if not hardware_type_list:
        return HttpResponse("Hardware type cannot be found")
    hardware_type = hardware_type_list[0]

    hardware_type_pins = HardwareTypePin.objects.filter(hardware_type=hardware_type)

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'hardware_type': hardware_type,
            'hardware_type_pins': hardware_type_pins
    }
    return render(request, 'serapis/hardware_type.html', template_context)


@login_required(login_url='/login/')
def create_hardware_type(request):
    username = request.user
    user = User.objects.filter(username=username)[0]
    user_profile = UserProfile.objects.filter(user=user)[0]
    
    if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
        return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        hardware_form = HardwareTypeForm(request.POST, request.FILES)
        pin_formset = HardwareTypePinFormSet(request.POST)
        if hardware_form.is_valid() and pin_formset.is_valid():
            hardware = hardware_form.save()
            hardware.save()
            
            hardware_pins = []
            for form in pin_formset:
                pin_name = form.cleaned_data.get('pin_name')
                hardware_pins.append(HardwareTypePin(hardware_type=hardware, pin_name=pin_name))

            try:
                with transaction.atomic():
                    HardwareTypePin.objects.filter(hardware_type=hardware).delete()
                    HardwareTypePin.objects.bulk_create(hardware_pins)

            except IntegrityError: #If the transaction failed
                messages.error(request, 'There was an error saving your profile.')
            return HttpResponseRedirect(reverse('hardware-type-list'))
    else:
        hardware_form = HardwareTypeForm()
        pin_formset = HardwareTypePinFormSet(queryset=HardwareTypePin.objects.none())

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'hardware_form': hardware_form,
            'pin_formset': pin_formset,
    }
    return render(request, 'serapis/create_hardware_type.html', template_context)


@login_required(login_url='/login/')
def modify_hardware_type(request, hardware_id):
    return HttpResponse("Under construction")
