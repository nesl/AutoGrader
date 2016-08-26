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
    uid = models.CharField(max_length=20, unique=True, default = '123456789', verbose_name = "University ID")


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


#Model that encapsulates the entire Testbed, including the Hardware Engines and DUTs
class TestbedType(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)


#Model that links the TestbedType to it's list of hardware types
class TestbedHardwareList(models.Model):
    hardware_type = models.ForeignKey(HardwareType, on_delete=models.CASCADE) 
    hardware_index = models.IntegerField()
    firmware = models.FileField(null=True, blank=True)


#Wiring for the TestbedType
class TestbedTypeWiring(models.Model):
    testbed_type = models.ForeignKey(
        TestbedType,
        on_delete = models.CASCADE,
    )
    #The device index should match the index in TestbedHardwareList model
    dev_1_index = models.IntegerField()
    dev_1_pin = models.ForeignKey(HardwareTypePin, related_name = 'dev_1_pin', on_delete = models.CASCADE)
    #The device index should match the index in TestbedHardwareList model
    dev_2_index = models.IntegerField()
    dev_2_pin = models.ForeignKey(HardwareTypePin, related_name = 'dev_2_pin', on_delete = models.CASCADE)


class Testbed(models.Model):
    STATUS_TYPES = (
        ('reserved','Reserved'),
        ('avail', 'Available'),
    )
    #IP Address. Only allowing IPv4 as the testers are internal
    ip_address = models.GenericIPAddressField(protocol='IPv4')
   
    testbed_type = models.ForeignKey(TestbedType, on_delete=models.CASCADE)
    
    # internal
    status = models.CharField(
        max_length=10,
        choices=STATUS_TYPES,
        default='avail',
    )


class HardwareDevice(models.Model):
    hardware_type = models.ForeignKey(
        HardwareType,
        on_delete = models.CASCADE,
    )

    testbed = models.ForeignKey(Testbed, on_delete=models.CASCADE)

   
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

    #Django does not support years field by default. So this is a hack to get a list of valid years.
    YEAR_CHOICES = []
    for r in range(1980, (datetime.datetime.now().year+1)):
        YEAR_CHOICES.append((r,r))

    instructor_id = models.ForeignKey(UserProfile, on_delete = models.CASCADE)
    course_code = models.CharField(max_length = 10, default = '')
    name = models.CharField(max_length = 100, default = '')
    description = models.TextField()
    quarter = models.IntegerField(choices=QUARTER_TYPES)
    year = models.IntegerField(_('year'), max_length=4, choices=YEAR_CHOICES, default=datetime.datetime.now().year)


class Assignment(models.Model):
    # basic information
    course_id = models.ForeignKey(Course, on_delete = models.CASCADE)
    # TODO: permission only for instructor
    description = models.TextField()  # brief
    release_time = models.DateTimeField()
    deadline = models.DateTimeField()
    problem_statement = models.TextField()
    input_statement = models.TextField()
    output_statement = models.TextField()

    # testbench related
    testbed_type_id = models.ForeignKey(TestbedType, on_delete = models.CASCADE, default = None, null = True)
    # Testbenches are reserved using AssignmentTestBenches table
    num_testbeds = models.IntegerField(default = None, null = True)
    
    # grading related
    # TODO: grading script

    # internal
    # TODO: status (completition of problem statement, is it ready to submit)


class AssignmentTestbed(models.Model):
    assignment_id = models.ForeignKey(Assignment, on_delete = models.CASCADE)
    testbed_id = models.ForeignKey(Testbed, on_delete = models.CASCADE)


class AssignmentTask(models.Model):
    assignment_id = models.ForeignKey(Assignment, on_delete = models.CASCADE)
    task_order = models.IntegerField()
    description = models.TextField()
    # TODO: test input
    # TODO: test output
    # TODO: points as integer
    # TODO: mode (public, feedback, hidden)


class Submission(models.Model):
    STAT_RECEIVED = 0
    STAT_GRADING = 10
    STAT_REGRADING = 11
    STAT_GRADED = 20
    SUBMISSION_STATES = (
            (STAT_RECEIVED, "Received"),
            (STAT_GRADING, "Grading"),
            (STAT_REGRADING, "Rejudging"),
            (STAT_GRADED, "Final result"),
    )

    student_id = models.ForeignKey(UserProfile, on_delete = models.CASCADE)
    assignment_id = models.ForeignKey(Assignment, on_delete = models.CASCADE)
    submission_time = models.DateTimeField()
    grading_result = models.FloatField()
    status = models.IntegerField(choices = SUBMISSION_STATES, default = STAT_RECEIVED)


class SubmissionFile(models.Model):
    submission_id = models.ForeignKey(Submission, on_delete = models.CASCADE)
    file = models.FileField()


