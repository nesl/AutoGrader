from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

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
    pinout = models.FileField()
    link_to_manual = models.URLField()
    hardware_role = models.IntegerField(choices=HARDWARE_ROLES)

class HardwareTypePin(models.Model):
    hardware_type = models.ForeignKey(
        HardwareType,
        on_delete = models.CASCADE,
    )
    
    pin_name = models.CharField(max_length=10)
    
#Model that encapsulates the entire Testbed, including the Hardware Engines and DUTs
class TestbedType(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)

#Model that links the TestbedType to it's list of hardware types
class TestbedHardwareList(models.Model):
    hardware_type = models.ForeignKey(
        HardwareType,
        on_delete=models.CASCADE,
    ) 
    hardware_index = models.IntegerField()
    firmware = models.FileField(null=True,blank=True)

#Wiring for the TestbedType
class TestbedTypeWiring(models.Model):
    testbed_type = models.ForeignKey(
        TestbedType,
        on_delete = model.CASCADE,
    )
    #The device index should match the index in TestbedHardwareList model
    dev_1_index = models.IntegerField()
    dev_1_pin = models.ForeignKey(
        HardwareTypePin,
        on_delete = models.CASCADE,
    )
    #The device index should match the index in TestbedHardwareList model
    dev_2_index = models.IntegerField()
    dev_2_pin = models.ForeignKey(
        HardwareTypePin,
        on_delete = models.CASCADE,
    )

class HardwareDevice(models.Model):
    hardware_type = models.ForeignKey(
        HardwareType,
        on_delete = models.CASCADE,
    )

    #Tester firmware will be saved to 'media/documents/tester_code/date/'
    firmware = models.FileField(upload_to='documents/tester_code/%Y/%m/%d')

    #TODO: remove testbench attribute (BHARATH, can you confirm this deletion?)
    #testbench = models.ForeignKey(
    #    HardwareTestBench,
    #    on_delete=models.CASCADE,
    #)  

   
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

class Course(models.Model):
    instructor_id = models.ForeignKey(UserProfile, on_delete = models.CASCADE)
    course_code = models.CharField(max_length = 10, default = '')
    name = models.CharField(max_length = 100, default = '')
    description = models.TextField()


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
    testbench_id = models.ForeignKey(HardwareTestBench, on_delete = models.CASCADE, default = None, null = True)
    # Testbenches are reserved using AssignmentTestBenches table
    num_testbenches = models.IntegerField(default = None, null = True)
    
    # grading related
    # TODO: grading script

    # internal
    # TODO: status (completition of problem statement, is it ready to submit)


class AssignmentTestBenches(models.Model):
    assignment_id = models.ForeignKey(Assignment, on_delete = models.CASCADE)
    testbench_id = models.ForeignKey(HardwareTestBench, on_delete=models.CASCADE)


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


