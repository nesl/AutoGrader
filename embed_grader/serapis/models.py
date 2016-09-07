from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

import datetime

class UserProfile(models.Model):
    ROLE_SUPER_USER = 0
    ROLE_INSTRUCTOR = 10
    ROLE_TA = 11
    ROLE_GRADER = 12
    ROLE_STUDENT = 20
    USER_ROLES = (
            (ROLE_SUPER_USER, 'Super user'),
            (ROLE_INSTRUCTOR, 'Instructor'),
            (ROLE_TA, 'TA'),
            (ROLE_GRADER, 'Grader'),
            (ROLE_STUDENT, 'Student'),
    )
    
    #Connect to built-in User model, which already has firstname, lastname, email and password
    user = models.OneToOneField(User, on_delete = models.CASCADE)

    #TODO: We may want to use in-built "Groups" feature of Django to make permissions easier
    #TODO: The role of a user can change from TA to Student depending on a course
    user_role = models.IntegerField(choices = USER_ROLES, default = ROLE_STUDENT)
    uid = models.CharField(max_length=20, unique=True, verbose_name = "University ID")

    #for activation of user. One time use
    activation_key = models.CharField(max_length=40, null=True, blank=True)
    key_expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name


#Common model for both DUT and Hardware Engines
class HardwareType(models.Model):
    HARDWARE_ENGINE = 0
    DEVICE_UNDER_TEST = 1
    HARDWARE_ROLES = (
        (HARDWARE_ENGINE, 'Hardware Engine'),
        (DEVICE_UNDER_TEST, 'Device Under Test'),
    )
    name = models.CharField(max_length=50)
    pinout = models.FileField(upload_to='uploaded_files')
    link_to_manual = models.URLField()
    hardware_role = models.IntegerField(choices=HARDWARE_ROLES)


class HardwareTypePin(models.Model):
    hardware_type = models.ForeignKey(HardwareType, on_delete = models.CASCADE)
    pin_name = models.CharField(max_length=10)


# Model that encapsulates the entire Testbed, including the Hardware Engines and DUTs
class TestbedType(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self):
        return self.name


# Model that links the TestbedType to it's list of hardware types
class TestbedHardwareList(models.Model):
    testbed_type = models.ForeignKey(TestbedType, on_delete = models.CASCADE)
    hardware_type = models.ForeignKey(HardwareType, on_delete = models.CASCADE) 
    hardware_index = models.IntegerField()
    firmware = models.FileField(null=True, blank=True, upload_to='uploaded_files')


# Wiring for the TestbedType
class TestbedTypeWiring(models.Model):
    testbed_type = models.ForeignKey(TestbedType, on_delete = models.CASCADE)
    #The device index should match the index in TestbedHardwareList model
    dev_1_index = models.IntegerField()
    dev_1_pin = models.ForeignKey(HardwareTypePin, related_name = 'dev_1_pin', on_delete = models.CASCADE)
    #The device index should match the index in TestbedHardwareList model
    dev_2_index = models.IntegerField()
    dev_2_pin = models.ForeignKey(HardwareTypePin, related_name = 'dev_2_pin', on_delete = models.CASCADE)


class Course(models.Model):
    FALL = 0
    WINTER = 1
    SPRING = 2
    SUMMER = 3
    QUARTER_TYPES = (
        (FALL, 'Fall'),
        (WINTER, 'Winter'),
        (SPRING, 'Spring'),
        (SUMMER, 'Summer'),
    )

    # Django does not support years field by default. So this is a hack to get a list of valid years.
    YEAR_CHOICES = []
    for r in range(2015, (datetime.datetime.now().year+2)):
        YEAR_CHOICES.append((r,r))

    owner_id = models.ForeignKey(User, on_delete = models.CASCADE)
    course_code = models.CharField(max_length = 10, default = '')
    name = models.CharField(max_length = 100, default = '')
    description = models.TextField()
    quarter = models.IntegerField(choices=QUARTER_TYPES, default=FALL)
    year = models.IntegerField(choices=YEAR_CHOICES, default=datetime.datetime.now().year)

    def __str__(self):
        return '%s: %s %s %d' % (self.course_code, self.name, self.get_quarter_display(), self.year)


class CourseUserList(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    

class Assignment(models.Model):
    # basic information
    course_id = models.ForeignKey(Course, on_delete = models.CASCADE)
    # TODO: permission only for instructor
    name = models.CharField(max_length=50)
    release_time = models.DateTimeField()
    deadline = models.DateTimeField()
    problem_statement = models.TextField()
    input_statement = models.TextField()
    output_statement = models.TextField()

    # testbed related
    testbed_type_id = models.ForeignKey(TestbedType, on_delete = models.CASCADE, default = None, null = True)
    # Testbenches are reserved using AssignmentTestBenches table
    num_testbeds = models.IntegerField(default = None, null = True)
    
    # internal
    # TODO: status (completition of problem statement, is it ready to submit)

    def __str__(self):
        return self.name


class AssignmentTask(models.Model):
    MODE_PUBLIC = 0
    MODE_FEEDBACK = 1
    MODE_HIDDEN = 2
    EVAL_MODES = (
        (MODE_PUBLIC, 'Public'),
        (MODE_FEEDBACK, 'Feedback'),
        (MODE_HIDDEN, 'Hidden'),
    )

    assignment_id = models.ForeignKey(Assignment, on_delete = models.CASCADE)
    brief_description = models.CharField(max_length=100)
    mode = models.IntegerField(choices=EVAL_MODES)
    points = models.FloatField()
    test_input = models.FileField(upload_to='uploaded_files')
    grading_script = models.FileField(upload_to='uploaded_files')


class Submission(models.Model):
    STAT_RECEIVED = 0
    STAT_GRADING = 10
    STAT_REGRADING = 11
    STAT_GRADED = 20
    SUBMISSION_STATES = (
            (STAT_RECEIVED, "Received"),
            (STAT_GRADING, "Grading"),
            (STAT_REGRADING, "Rejudging"),
            (STAT_GRADED, "Result is ready"),
    )

    student_id = models.ForeignKey(User, on_delete = models.CASCADE)
    assignment_id = models.ForeignKey(Assignment, on_delete = models.CASCADE)
    submission_time = models.DateTimeField()
    grading_result = models.FloatField()
    status = models.IntegerField(choices = SUBMISSION_STATES, default = STAT_RECEIVED)
    #TODO: let's say the student is going to submit the binary only,
    #      we'll worry about the multiple submission files later
    file = models.FileField(upload_to='uploaded_files')


class TaskGradingStatus(models.Model):
    STAT_PENDING = 0
    STAT_EXECUTING = 10
    STAT_OUTPUT_TO_BE_CHECKED = 100
    STAT_FINISH = 110
    STAT_INTERNAL_ERROR = -1

    EXEC_UNKNOWN = -1
    EXEC_OK = 0
    EXEC_SEG_FAULT = 1

    GRADING_STATES = (
            (STAT_PENDING, 'Pending'),
            (STAT_EXECUTING, 'Executing'),
            (STAT_OUTPUT_TO_BE_CHECKED, 'Checking output'),
            (STAT_FINISH, 'Finished'),
            (STAT_INTERNAL_ERROR, 'Please contact PI'),
    )
    EXECUTION_STATUS = (
            (EXEC_UNKNOWN, 'Haven\'t executed yet'),
            (EXEC_OK, 'Successful execution'),
            (EXEC_SEG_FAULT, 'Segmentation fault'),
    )
    
    submission_id = models.ForeignKey(Submission, on_delete=models.CASCADE)
    assignment_task_id = models.ForeignKey(AssignmentTask, on_delete=models.CASCADE)
    grading_status = models.IntegerField(choices=GRADING_STATES, default=STAT_PENDING)
    execution_status = models.IntegerField(choices=EXECUTION_STATUS, default=EXECUTION_STATUS)
    output_file = models.FileField(upload_to='uploaded_files', null=True, blank=True)
    status_update_time = models.DateTimeField()
    points = models.FloatField(default=0.0)
    

class Testbed(models.Model):
    #STATUS_RESERVED = 0
    STATUS_AVAILABLE = 1
    STATUS_BUSY = 2
    STATUS_OFFLINE = -1
    STATUS_UNKNOWN = -2

    TESTBED_STATUS = (
        #(STATUS_RESERVED, 'Reserved'),
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_BUSY, 'Busy'),
        (STATUS_OFFLINE, 'Offline'),
    )
    REPORT_STATUS = (
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_BUSY, 'Busy'),
        (STATUS_UNKNOWN, 'Unknown'),
    )

    testbed_type = models.ForeignKey(TestbedType, on_delete=models.CASCADE)

    #IP Address. Only allowing IPv4 as the testers are internal
    ip_address = models.GenericIPAddressField(protocol='IPv4')
    unique_hardware_id = models.CharField(max_length=30, unique=True)
    task_being_graded = models.ForeignKey(TaskGradingStatus, null=True, on_delete=models.SET_NULL)
   
    # internal
    status = models.IntegerField(choices=TESTBED_STATUS)

    # report message
    report_time = models.DateTimeField()
    report_status = models.IntegerField(choices=REPORT_STATUS)


class HardwareDevice(models.Model):
    hardware_type = models.ForeignKey(
        HardwareType,
        on_delete = models.CASCADE,
    )

    testbed = models.ForeignKey(Testbed, on_delete=models.CASCADE)

   
#TODO: We're not going to use it for now
class SubmissionFile(models.Model):
    submission_id = models.ForeignKey(Submission, on_delete = models.CASCADE)
    file = models.FileField(upload_to='uploaded_files')


