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
from django.views.decorators.csrf import csrf_exempt

from django.utils import timezone
from datetime import datetime, timedelta

from serapis.models import *
from serapis.model_forms import *

import hashlib, random, pytz


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
    course_list = [Course.objects.filter(id=cu.course_id.id)[0] for cu in course_user_list]
    template_context = {
            'user_profile': user_profile,
            'myuser': request.user,
            'course_list': course_list,
    }
    return render(request, 'serapis/homepage.html', template_context)


@login_required(login_url='/login/')
def create_course(request):
    #TODO:how to check user role here?
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    if request.method == 'POST':
        form = CourseCreationForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
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
    error_message = ''
    if request.method == 'POST':
        form = CourseEnrollmentForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/homepage/')
        error_message = "You have already enrolled in this course."
    else:
        form = CourseEnrollmentForm(user=request.user)

    return render(request, 'serapis/enroll_course.html', {'form': form, 'error_message': error_message})


@login_required(login_url='/login/')
def course(request, course_id):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)
    course = Course.objects.get(id=course_id)

    if not course:
        return HttpResponse("Course cannot be found")

    current_cu = CourseUserList.objects.filter(course_id=course, user_id=user)
    if not current_cu:
        raise PermissionDenied

    assignment_list = Assignment.objects.filter(course_id=course_id)

    if current_cu[0].role == ROLE_STUDENT:
        for assignment in assignment_list:
            now = datetime.now(tz=pytz.timezone('UTC'))
            if now < assignment.release_time:
                assignment_list = Assignment.objects.filter(course_id=course_id, release_time__lte = now)


    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'course': course,
            'assignment_list': assignment_list,
            'role': current_cu[0].role
    }
    return render(request, 'serapis/course.html', template_context)

@login_required(login_url='/login/')
def modify_course(request, course_id):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)
    course = Course.objects.get(id=course_id)

    if not course:
        return HttpResponse("Course cannot be found")

    courseUserObj = CourseUserList.objects.filter(course_id=course, user_id=user)
    # if not courseUserObj or (courseUserObj[0].role != ROLE_INSTRUCTOR or courseUserObj[0].role != ROLE_SUPER_USER):
    #     raise PermissionDenied

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
    # user_profile = UserProfile.objects.get(user=user)
    course = Course.objects.get(id=course_id)

    if not course:
        return HttpResponse("Course cannot be found")

    courseUserObj = CourseUserList.objects.filter(course_id=course, user_id=user)
    #students don't have access to view student list
    if not courseUserObj or courseUserObj[0].role == ROLE_STUDENT:
        raise PermissionDenied

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
            'course': course,
            'user_enrolled': user_enrolled,
            'students': students,
            'teaching_assistants': assistants,
            'instructors': instructors,
            'role':courseUserObj[0].role
        }

    return render(request, 'serapis/roster.html', template_context)


@login_required(login_url='/login/')
#Only super user has access to create a course
def create_assignment(request, course_id):
    course = Course.objects.get(id=course_id)
    if not course:
        return HttpResponse("Course cannot be found")

    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)
    courseUserObj=CourseUserList.objects.filter(course_id=course, user_id=user)

    if not courseUserObj or (courseUserObj[0].role != ROLE_INSTRUCTOR and courseUserObj[0].role != ROLE_SUPER_USER):
        raise PermissionDenied

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
            'role': courseUserObj[0].role,
            'form': form,
    }
    return render(request, 'serapis/create_assignment.html', template_context)


@login_required(login_url='/login/')
def assignment(request, assignment_id):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    assignment = Assignment.objects.get(id=assignment_id)
    if not assignment:
        return HttpResponse("Assignment cannot be found")

    now = datetime.now(tz=pytz.timezone('UTC'))
    time_remaining = assignment.deadline - now

    course = assignment.course_id

    courseUserObj = CourseUserList.objects.filter(course_id=course, user_id=user)
    if not courseUserObj:
        raise PermissionDenied

    # Assignment Submission
    assignment_tasks = AssignmentTask.objects.filter(assignment_id=assignment)
    total_points = 0
    public_points = 0
    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.student_id = user
            submission.assignment_id = assignment
            submission.submission_time = timezone.now()
            submission.grading_result = 0.
            submission.status = Submission.STAT_GRADING
            submission.save()

            for assignment_task in assignment_tasks:
                grading_task = TaskGradingStatus()
                grading_task.submission_id = submission
                grading_task.assignment_task_id = assignment_task
                grading_task.grading_status = TaskGradingStatus.STAT_PENDING
                grading_task.execution_status = TaskGradingStatus.EXEC_UNKNOWN
                grading_task.status_update_time = timezone.now()
                grading_task.save()

    for assignment_task in assignment_tasks:
        total_points += assignment_task.points
        if assignment_task.mode != 2:
            public_points += assignment_task.points

    submission_form = AssignmentSubmissionForm()

    if courseUserObj[0].role == ROLE_STUDENT:
        submission_list = Submission.objects.filter(student_id=user, assignment_id=assignment).order_by('-submission_time')
    else:
        submission_list = Submission.objects.filter(assignment_id=assignment).order_by('-submission_time')

    num_display = min(5, len(submission_list))
    submission_short_list = submission_list[:num_display]

    submission_grading_detail = []
    student_list = []
    for submission in submission_short_list:
        student = User.objects.get(username = submission.student_id)
        student_name = student.first_name + ", " + student.last_name
        student_list.append(student_name)

        task_symbols = []
        tasks = TaskGradingStatus.objects.filter(submission_id=submission).order_by('assignment_task_id')
        for task in tasks:
            if task.grading_status == TaskGradingStatus.STAT_PENDING:
                task_symbols.append('(P)')
            elif task.grading_status == TaskGradingStatus.STAT_EXECUTING:
                task_symbols.append('(E)')
            elif task.grading_status == TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED:
                task_symbols.append('(C)')
            elif task.grading_status == TaskGradingStatus.STAT_FINISH:
                task_symbols.append(str(task.points))
            elif task.grading_status == TaskGradingStatus.STAT_INTERNAL_ERROR:
                task_symbols.append('Error')
        submission_grading_detail.append(','.join(task_symbols))

    gradings = []
    for grading in submission_grading_detail:
        total = 0
        scoreList = grading.split(',')

        for score in scoreList:
            if score[0].isnumeric():
                total += float(score)
        gradings.append(round(total,2))


    # print(submission_short_list[0].student_id)
    submission_n_detail_short_list = zip(submission_short_list, submission_grading_detail, gradings, student_list)

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'assignment': assignment,
            'course': course,
            'submission_form': submission_form,
            'submission_n_detail_short_list': submission_n_detail_short_list,
            'tasks': assignment_tasks,
            'role':courseUserObj[0].role,
            'total_points':total_points,
            'public_points':public_points,
            'time_remaining':time_remaining,
            'now':now
    }

    return render(request, 'serapis/assignment.html', template_context)


@login_required(login_url='/login/')
def modify_assignment(request, assignment_id):
    assignment = Assignment.objects.get(id=assignment_id)
    if not assignment:
        return HttpResponse("Assignment cannot be found")

    course = assignment.course_id
    if not course:
        return HttpResponse("Course cannot be found")

    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)
    courseUserObj = CourseUserList.objects.filter(course_id=course, user_id=user)
    if not courseUserObj or courseUserObj == ROLE_STUDENT:
        raise PermissionDenied

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
        tasks = AssignmentTask.objects.filter(assignment_id=assignment)

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

    assignment = Assignment.objects.get(id=assignment_id)
    if not assignment:
        return HttpResponse("Assignment cannot be found")

    course = assignment.course_id
    courseUserObj = CourseUserList.objects.filter(course_id=course, user_id=user)

    if not courseUserObj or courseUserObj[0].role == ROLE_STUDENT:
        raise PermissionDenied

    if request.method == 'POST':
        form = AssignmentTaskForm(request.POST, request.FILES)
        if form.is_valid():
            assignment_task = form.save(commit=False)
            assignment_task.assignment_id = assignment
            assignment_task.save()
            return HttpResponseRedirect(reverse('modify-assignment', args=(assignment_id)))
    else:
        form = AssignmentTaskForm()

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form,
            'course': course,
            'role':courseUserObj[0].role,
            'assignment': assignment,
    }
    return render(request, 'serapis/create_assignment_task.html', template_context)

@login_required(login_url='/login/')
def modify_assignment_task(request, task_id):
    task = AssignmentTask.objects.get(id=task_id)
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    assignment = Assignment.objects.get(id=task.assignment_id.id)
    if not assignment:
        return HttpResponse("Assignment cannot be found")

    course = assignment.course_id
    courseUserObj = CourseUserList.objects.filter(course_id=course, user_id=user)

    if not courseUserObj or courseUserObj[0].role == ROLE_STUDENT:
        raise PermissionDenied

    if request.method == 'POST':
        form = AssignmentTaskCompleteForm(request.POST, instance=task)
        if form.is_valid():
            assignment_task = form.save()
            return HttpResponseRedirect('/assignment/' + str(assignment.id))
    else:
        form = AssignmentTaskCompleteForm(instance=task)

    template_context = {
            'myuser': request.user,
            'user_profile': user_profile,
            'form': form,
            'course': course,
            'role':courseUserObj[0].role,
            'assignment': assignment,
    }
    return render(request, 'serapis/modify_assignment_task.html', template_context)

def submission(request, submission_id):
    submission = Submission.objects.get(id=submission_id)
    if not submission:
        return HttpResponse("Submission cannot be found")

    user = User.objects.get(username=request.user)
    assignment = submission.assignment_id
    course = assignment.course_id
    courseUserObj = CourseUserList.objects.filter(course_id=course, user_id=user)

    if not courseUserObj:
        raise PermissionDenied

    author = User.objects.get(username=submission.student_id)
    if courseUserObj[0].role == ROLE_STUDENT:
        if author.username != user.username:
            print(author.username)
            print(user.username)
            raise PermissionDenied

    gradings = TaskGradingStatus.objects.filter(submission_id=submission_id).order_by('assignment_task_id')
    if courseUserObj[0].role == ROLE_STUDENT:
        assignment_tasks = AssignmentTask.objects.filter(assignment_id=assignment).exclude(mode=2).order_by('id')
    else:
        assignment_tasks = AssignmentTask.objects.filter(assignment_id=assignment).order_by('id')

    task_symbols = []
    score = 0;
    for task in gradings:
        if task.grading_status == TaskGradingStatus.STAT_PENDING:
            task_symbols.append('Pending')
        elif task.grading_status == TaskGradingStatus.STAT_EXECUTING:
            task_symbols.append('Executing')
        elif task.grading_status == TaskGradingStatus.STAT_OUTPUT_TO_BE_CHECKED:
            task_symbols.append('Checking')
        elif task.grading_status == TaskGradingStatus.STAT_FINISH:
            score += task.points
            task.points = round(task.points, 2)
            task_symbols.append('Finalized')
        elif task.grading_status == TaskGradingStatus.STAT_INTERNAL_ERROR:
            task_symbols.append('Error')

    total_points = 0
    for a in assignment_tasks:
        total_points += a.points

    score = round(score, 2)

    submission_n_detail_short_list = zip(gradings, task_symbols, assignment_tasks)

    template_context = {
        'submission':submission,
        'assignment': assignment,
        'course': course,
        'author':author,
        'submission_n_detail_short_list':submission_n_detail_short_list,
        'score':score,
        'total_points':total_points
    }
    return render(request, 'serapis/submission.html', template_context)

@login_required(login_url='/login/')
def testbed_type_list(request):
    user = User.objects.get(username=request.user)
    user_profile = UserProfile.objects.get(user=user)

    # TODO: should do permission check
    # if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
    #     return HttpResponse("Not enough privilege")

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

    testbed_type = TestbedType.objects.get(id=testbed_type_id)
    if not testbed_type:
        return HttpResponse("Testbed type not found")

    testbed_type_form = TestbedTypeForm()

    template_context = { "myuser": request.user, "testbed_type_form": testbed_type_form }

    return HttpResponse("Under construction")


@login_required(login_url='/login/')
def create_testbed_type(request):
    username = request.user
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)

    # TODO: should do permission check
    # if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
    #     return HttpResponse("Not enough privilege")

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

    # TODO: should do permission check
    # if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
    #     return HttpResponse("Not enough privilege")

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

    # TODO: should do permission check
    # if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
    #     return HttpResponse("Not enough privilege")


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

    # TODO: should do permission check
    # if not user_profile.user_role == user_profile.ROLE_SUPER_USER and not user_profile.user_role == user_profile.ROLE_INSTRUCTOR and not user_profile.user_role == user_profile.ROLE_TA:
    #     return HttpResponse("Not enough privilege")

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
            task = TaskGradingStatus.objects.filter(id=request.POST['id'])[0]
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
