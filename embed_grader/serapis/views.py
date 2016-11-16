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
from django.db.models import Max

from django.utils import timezone
from datetime import datetime, timedelta

from serapis.models import *
from serapis.model_forms import *
from serapis.utils import grading

from django.contrib.auth.models import User, Group
from guardian.decorators import permission_required_or_403
from guardian.compat import get_user_model
from guardian.shortcuts import assign_perm

import hashlib, random, pytz

from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
#TODO(timestring): recheck whether I should use disabled instead of readonly to enforce data integrity


def registration(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            datas = {}
            datas['uid'] = form.cleaned_data['uid']
            datas['email'] = form.cleaned_data['email']
            datas['password1'] = form.cleaned_data['password1']
            # We will generate a random activation key
            random_string = str(random.random())
            salt = hashlib.sha1(random_string.encode('utf-8')).hexdigest()[:5]
            usernamesalt = datas['uid']
            activation_string = (salt+usernamesalt).encode('utf-8')
            datas['activation_key'] = hashlib.sha1(activation_string).hexdigest()
            datas['email_path'] = "serapis/activation_email.html"
            datas['email_subject'] = "Account Activation"

            form.sendEmail(datas)  #Send validation email
            form.save(datas)  #Save the user and his profile

            request.session['registered'] = True  # For display purposes
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
        if timezone.now() > user_profile.key_expires:
            activation_expired = True
            # Display : offer to user to have another activation link (a link in template sending to the view new_activation_link)
            id_user = user_profile.user.id
        else:  # Activation successful
            user_profile.user.is_active = True
            user_profile.user.save()
    # If user is already active, simply display error message
    else:
        already_active = True  # Display : error message
    return render(request, 'serapis/activation.html', locals())


def new_activation(request, user_id):
    form = UserCreationForm()
    datas = {}
    user = User.objects.get(id=user_id)
    if user is not None and not user.is_active:
        datas['uid'] = user.uid
        datas['email'] = user.email
        datas['email_path'] = "serapis/activation_email_resend.html"
        datas['email_subject'] = "Account Activation Resend"

        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        usernamesalt = datas['uid']
        if isinstance(usernamesalt, unicode):
            usernamesalt = usernamesalt.encode('utf8')
        datas['activation_key'] = hashlib.sha1(salt+usernamesalt).hexdigest()

        user_profile = UserProfile.objects.get(user=user)
        user_profile.activation_key = datas['activation_key']
        user_profile.key_expires = datetime.strftime(timezone.now() + timedelta(days=2), "%Y-%m-%d %H:%M:%S")
        user_profile.save()
        form.sendEmail(datas)
        request.session['new_link'] = True  # Display : new link send

    return HttpResponse("The new verification link has been sent to your email. Please check.")


def logout_view(request):
    logout(request)


@login_required(login_url='/login/')
def homepage(request):
    username = request.user
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)

    course_user_list = CourseUserList.objects.filter(user_id=user)
    course_list = [cu.course_id for cu in course_user_list]
    template_context = {
            'user_profile': user_profile,
            'myuser': request.user,
            'course_list': course_list,
    }
    return render(request, 'serapis/homepage.html', template_context)


@login_required(login_url='/login/')
def about(request):
    user = User.objects.get(username=request.user)
    template_context = {'myuser': request.user}
    return render(request, 'serapis/about.html', template_context)


@login_required(login_url='/login/')
def create_course(request):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('serapis.create_course'):
        return HttpResponse("Not enough privilege.")

    if request.method == 'POST':
        form = CourseCreationForm(request.POST, user=request.user)
        if form.is_valid():
            # database
            course = form.save()

            # permission: create groups, add group permissions
            instructor_group_name = str(course.id) + "_Instructor_Group"
            student_group_name = str(course.id) + "_Student_Group"

            instructor_group = Group.objects.get_or_create(name=instructor_group_name)
            student_group = Group.objects.get_or_create(name=student_group_name)

            #assign permissions
            assign_perm('serapis.view_hardware_type', instructor_group)
            assign_perm('view_course', instructor_group, course)
            assign_perm('view_course', student_group, course)
            assign_perm('serapis.create_course', instructor_group)
            assign_perm('modify_course', instructor_group, course)
            assign_perm('view_membership', instructor_group, course)
            assign_perm('view_assignment', instructor_group, course)
            assign_perm('view_assignment', student_group, course)
            assign_perm('modify_assignment', instructor_group, course)
            assign_perm('create_assignment', instructor_group, course)

            return HttpResponseRedirect(reverse('homepage'))
    else:
        form = CourseCreationForm()

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form,
    }
    return render(request, 'serapis/create_course.html', template_context)


@login_required(login_url='/login/')
def enroll_course(request):
    user = User.objects.get(username=request.user)
    error_message = ''
    if request.method == 'POST':
        form = CourseEnrollmentForm(request.POST, user=request.user)
        if form.is_valid():
            # database
            form.save()

            # add user to belonged group
            course = form.cleaned_data['course_select']
            student_group_name = str(course.id) + "_Student_Group"
            student_group = Group.objects.get(name=student_group_name)
            user.groups.add(student_group)

            return HttpResponseRedirect(reverse('homepage'))
        error_message = "You have already enrolled in this course."
    else:
        form = CourseEnrollmentForm(user=request.user)

    template_context = {
        'form': form,
        'error_message': error_message,
        'myuser': request.user
    }

    return render(request, 'serapis/enroll_course.html', template_context)


@login_required(login_url='/login/')
def course(request, course_id):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return HttpResponse("Course cannot be found.")

    if not user.has_perm('view_course', course):
        return HttpResponse("Not enough privilege.")

    assignment_list = Assignment.objects.filter(course_id=course_id)

    if not user.has_perm('modify_course',course):
        for assignment in assignment_list:
            now = datetime.now(tz=pytz.timezone('UTC'))
            if now < assignment.release_time:
                assignment_list = Assignment.objects.filter(course_id=course_id, release_time__lte = now)

    template_context = {
        'myuser': request.user,
        'course': course,
        'assignment_list': assignment_list,
    }
    return render(request, 'serapis/course.html', template_context)

@login_required(login_url='/login/')
def modify_course(request, course_id):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return HttpResponse("Course cannot be found.")

    if not user.has_perm('modify_course', course):
        return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        form = CourseCompleteForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            return HttpResponseRedirect('/course/'+course_id)
    else:
        form = CourseCompleteForm(instance=course)

    template_context = {
        'myuser': request.user,
        'user_profile': user_profile,
        'course':course,
        'form': form
    }

    return render(request, 'serapis/modify_course.html', template_context)

@login_required(login_url='/login/')
def membership(request, course_id):
    user = User.objects.get(username=request.user)

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return HttpResponse("Course cannot be found.")

    if not user.has_perm('view_membership', course):
        return HttpResponse("Not enough privilege")

    students = []
    instructors = []
    assistants = []
    user_enrolled = []
    cu_list = CourseUserList.objects.filter(course_id=course)
    for cu in cu_list:
        member = UserProfile.objects.get(user=cu.user_id)

        if cu.role == ROLE_INSTRUCTOR:
            instructors.append(member)
        elif cu.role == ROLE_TA:
            assistants.append(member)
        elif cu.role == ROLE_STUDENT:
            students.append(member)
        user_enrolled.append(member)

    template_context = {
        'myuser': request.user,
        'course': course,
        'user_enrolled': user_enrolled,
        'students': students,
        'teaching_assistants': assistants,
        'instructors': instructors,
    }

    return render(request, 'serapis/roster.html', template_context)


@login_required(login_url='/login/')
#Only super user has access to create a course
def create_assignment(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return HttpResponse("Course cannot be found.")

    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('create_assignment', course):
    	return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        form = AssignmentBasicForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('course', args=(course_id)))
    else:
        form = AssignmentBasicForm(initial={'course_id': course_id})

    form.fields['course_id'].widget = forms.NumberInput(attrs={'readonly':'readonly'})

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'course':course,
            'form': form,
    }
    return render(request, 'serapis/create_assignment.html', template_context)


@login_required(login_url='/login/')
def assignment(request, assignment_id):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found.")

    course = assignment.course_id
    if not user.has_perm('view_assignment', course):
        return HttpResponse("Not enough privilege")

    now = datetime.now(tz=pytz.timezone('UTC'))
    time_remaining = str(assignment.deadline - now)

    # Handle POST the request
    assignment_tasks = AssignmentTask.objects.filter(assignment_id=assignment).order_by('id')
    total_points = 0
    public_points = 0
    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES, assignment=assignment)
        if form.is_valid():
            if assignment.is_deadline_passed() and not user.has_perm('modify_assignment', course):
                #TODO: Show error message: deadline is passed
                print('Silent error msg: deadline is passed')
            else:
                submission, _ = form.save_and_commit(student=user)

                # dispatch grading tasks
                for assignment_task in assignment_tasks:
                    grading_task = TaskGradingStatus.objects.create(
                        submission_id=submission,
                        assignment_task_id=assignment_task,
                        grading_status=TaskGradingStatus.STAT_PENDING,
                        execution_status=TaskGradingStatus.EXEC_UNKNOWN,
                        status_update_time=timezone.now()
                    )

                    # create file records for each task
                    schema_list = TaskGradingStatusFileSchema.objects.filter(
                            assignment_id=assignment)
                    for sch in schema_list:
                        TaskGradingStatusFile.objects.create(
                            task_grading_status_id=grading_task,
                            file_schema_id=sch,
                            file=None,
                        )

    # get true total points and total points to students
    for assignment_task in assignment_tasks:
        total_points += assignment_task.points
        if assignment_task.mode != AssignmentTask.MODE_HIDDEN or now > assignment.deadline:
            public_points += assignment_task.points

    submission_form = AssignmentSubmissionForm(assignment=assignment)
    submission_short_list = []
    if user.has_perm('modify_assignment', course):
        submission_list = Submission.objects.filter(assignment_id=assignment).values('student_id').annotate(submission_time=Max('submission_time'))
        for s in submission_list:
            submission_short_list.append(Submission.objects.get(student_id = s['student_id'], submission_time=s['submission_time']))
        submission_short_list.sort(key=lambda x:x.submission_time, reverse=True)
    else:
        submission_list = Submission.objects.filter(student_id=user, assignment_id=assignment).order_by('-submission_time')
        num_display = min(10, len(submission_list))
        submission_short_list = submission_list[:num_display]

    submission_grading_detail = []
    student_list = []
    gradings = []
    for submission in submission_short_list:
        student = User.objects.get(username = submission.student_id)
        #TODO: is there a function for this?
        student_name = student.first_name + " " + student.last_name
        student_list.append(student_name)

        total_submission_points = 0.
        tasks = TaskGradingStatus.objects.filter(
                submission_id=submission, grading_status=TaskGradingStatus.STAT_FINISH)


        for task in tasks:
            if task.grading_status == TaskGradingStatus.STAT_FINISH:
                if user.has_perm('modify_assignment', course) or task.assignment_task_id.mode != AssignmentTask.MODE_HIDDEN or now > assignment.deadline:
                    total_submission_points += task.points

        submission_grading_detail.append(total_submission_points)
        gradings.append(round(total_submission_points, 2))


    recent_submission_list = list(zip(submission_short_list, submission_grading_detail, gradings, student_list))

    # page = request.GET.get('page',1)
    # paginator = Paginator(recent_submission_list, 5)
    # try:
    #     submission_log = paginator.page(page)
    # except PageNotAnInteger:
    #     submission_log = paginator.page(1)
    # except EmptyPage:
    #     submission_log = paginator.page(paginator.num_pages)

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'assignment': assignment,
            'course': course,
            'submission_form': submission_form,
            'submission_n_detail_short_list': recent_submission_list,
            'tasks': assignment_tasks,
            'total_points': total_points,
            'public_points': public_points,
            'time_remaining': time_remaining,
            'now': now
    }

    return render(request, 'serapis/assignment.html', template_context)


@login_required(login_url='/login/')
def modify_assignment(request, assignment_id):
    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found")

    course = assignment.course_id
    if not course:
        return HttpResponse("Course cannot be found")

    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('modify_assignment',course):
        return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        form = AssignmentCompleteForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save()
            return HttpResponseRedirect('/assignment/' + assignment_id)
    else:
        form = AssignmentCompleteForm(instance=assignment)

    tasks = None
    if assignment.testbed_type_id:
        form.fields['testbed_type_id'].widget = forms.NumberInput(attrs={'readonly':'readonly'})
        tasks = AssignmentTask.objects.filter(assignment_id=assignment).order_by('id')

    form.fields['course_id'].widget = forms.NumberInput(attrs={'readonly':'readonly'})

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'assignment': assignment,
            'form': form,
            'tasks': tasks,
            'course': course
    }
    return render(request, 'serapis/modify_assignment.html', template_context)


@login_required(login_url='/login/')
def create_assignment_task(request, assignment_id):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found")

    course = assignment.course_id

    if not user.has_perm('modify_assignment',course):
    	return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        form = AssignmentTaskForm(request.POST, request.FILES, assignment=assignment)
        if form.is_valid():
            form.save_and_commit()
            return HttpResponseRedirect(reverse('modify-assignment', args=(assignment_id)))
    else:
        form = AssignmentTaskForm(assignment=assignment)

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form,
            'course': course,
            'assignment': assignment,
    }
    return render(request, 'serapis/create_assignment_task.html', template_context)

@login_required(login_url='/login/')
def modify_assignment_task(request, task_id):
    try:
        task = AssignmentTask.objects.get(id=task_id)
    except AssignmentTask.DoesNotExist:
        return HttpResponse("Assignment task cannot be found")

    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    try:
        assignment = Assignment.objects.get(id=task.assignment_id.id)
    except Assignment.DoesNotExist:
        return HttpResponse("Assignment cannot be found")

    course = assignment.course_id

    if not user.has_perm('modify_assignment',course):
    	return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        form = AssignmentTaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            assignment_task = form.save(commit=False)
            assignment_task.assignment_id = assignment
            binary = assignment_task.test_input._file.file.read()
            res, msg = grading.check_format(binary)
            if res:
                assignment_task.execution_duration = float(grading.get_length(binary)) / 5000.0
                assignment_task.save()
                #return HttpResponseRedirect(reverse('modify-assignment', args=(assignment_id)))
                return HttpResponseRedirect('/assignment/' + str(assignment.id))
            else:
                #TODO(timestring): display why failed
                print("Create assignment task failed")
                pass
    else:
        form = AssignmentTaskForm(instance=task)

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form,
            'course': course,
            'assignment': assignment,
    }
    return render(request, 'serapis/modify_assignment_task.html', template_context)

@login_required(login_url='/login/')
def testbed_type_list(request):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('serapis.view_hardware_type'):
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
    username=request.user

    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponse("Not enough privilege")

    try:
        testbed_type = TestbedType.objects.get(id=testbed_type_id)
    except TestbedType.DoesNotExist:
        return HttpResponse("Testbed type not found")

    testbed_type_form = TestbedTypeForm()

    template_context = { "myuser": request.user, "testbed_type_form": testbed_type_form }

    return HttpResponse("Under construction")


@login_required(login_url='/login/')
def create_testbed_type(request):
    username = request.user
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponse("Not enough privilege")

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
def hardware_type_list(request):
    username = request.user
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('serapis.view_hardware_type'):
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
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponse("Not enough privilege")

    hardware_type = HardwareType.objects.get(id=hardware_type_id)
    if not hardware_type:
        return HttpResponse("Hardware type cannot be found")

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
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)

    if not user.has_perm('serapis.view_hardware_type'):
        return HttpResponse("Not enough privilege")

    if request.method == 'POST':
        hardware_form = HardwareTypeForm(request.POST, request.FILES)
        pin_formset = HardwareTypePinFormSet(request.POST)
        if hardware_form.is_valid() and pin_formset.is_valid():
            hardware = hardware_form.save()

            hardware_pins = []
            for form in pin_formset:
                pin_name = form.cleaned_data.get('pin_name')
                hardware_pins.append(HardwareTypePin(hardware_type=hardware, pin_name=pin_name))

            try:
                with transaction.atomic():
                    HardwareTypePin.objects.filter(hardware_type=hardware).delete()
                    HardwareTypePin.objects.bulk_create(hardware_pins)
            except IntegrityError:  # if the transaction failed
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
    return HttpResponse("under construction")


@login_required(login_url='/login/')
def debug_task_grading_status(request):
    username = request.user
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)

    if request.method == 'POST':
        form = TaskGradingStatusDebugForm(request.POST, request.FILES)
        if form.is_valid():
            #task = form.save(commit=False)
            task = TaskGradingStatus.objects.get(id=request.POST['id'])
            task.grading_status = form.cleaned_data['grading_status']
            task.execution_status = form.cleaned_data['execution_status']
            task.output_file = form.cleaned_data['output_file']
            task.status_update_time = timezone.now()
            task.save()

    form = TaskGradingStatusDebugForm()

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form,
    }
    return render(request, 'serapis/debug_task_grading_status.html', template_context)
