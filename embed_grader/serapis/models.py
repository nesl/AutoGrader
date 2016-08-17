from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User




class HardwareTestBench(models.Model):
    STATUS_TYPES = (
        ('reserved','Reserved'),
        ('avail', 'Available'),
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_TYPES,
        default='avail',
    )
   
    #IP Address. Only allowing IPv4 as the testers are internal
    ip_address = models.GenericIPAddressField(protocol='IPv4')


class HardwareTester(models.Model):
    TESTER_TYPES = (
        ('beagle', 'BeagleBone'),
        ('rpi3', 'RaspberryPi3')
    )
    tester_type = models.CharField(
        max_length = 10,
        choices = TESTER_TYPES,
        default = 'beagle'
    )

    #Tester firmware will be saved to 'media/documents/tester_code/date/'
    firmware = models.FileField(upload_to='documents/tester_code/%Y/%m/%d')

    testbench = models.ForeignKey(
        HardwareTestBench,
        on_delete=models.CASCADE,
    )  

   
#Device Under Test (DUT) Model
class DUT(models.Model):
    DUT_TYPES = (
        ('mbed', 'mbed'),
        ('ice40', 'Lattice iCE40'),
    )
    dut_type = models.CharField(
        max_length = 10,
        choices = DUT_TYPES,
        default = 'mbed',
    )

    #TODO Regex to check binary is correct

    testbench = models.ForeignKey(
        HardwareTestBench,
        on_delete=models.CASCADE,
    )

#Wiring between DUT and Tester
class TesterToDUTWiring(models.Model):
    tester = models.ForeignKey(
        HardwareTester,
        on_delete=models.CASCADE,
    )

    tester_pin = models.CharField(max_length = 5)

    dut = models.ForeignKey(
        DUT,
        on_delete=models.CASCADE,
    )

    dut_pin = models.CharField(max_length = 5)

#Wiring between two DUTs
class DUTToDUTWiring(models.Model):
    DUT_first = models.ForeignKey(
        DUT,
        on_delete=models.CASCADE,
        related_name='DUT_first'
    )
    DUT_first_pin = models.CharField(max_length=5)

    DUT_second = models.ForeignKey(
        DUT,
        on_delete=models.CASCADE,
        related_name='DUT_second'
    )
    DUT_second_pin = models.CharField(max_length=5)


   
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

class Course(models.Model):
    instructor_id = models.ForeignKey(UserProfile, on_delete = models.CASCADE)
    course_code = models.CharField(max_length = 10, default = '')
    name = models.CharField(max_length = 100, default = '')
    description = models.TextField()

class Assignment(models.Model):
    course_id = models.ForeignKey(Course, on_delete = models.CASCADE)
    # TODO: permission only for instructor
    description = models.TextField()  # brief
    # TODO: link to assignment page (do we need this?)
    release_time = models.DateTimeField()
    deadline = models.DateTimeField()
    # TODO: tester type
    # TODO: DUT type
    DUT_count = models.IntegerField()
    # TODO: Wiring information
    # Testbenches are reserved using AssignmentTestBenches table
    num_testbenches = models.IntegerField()
    
    # TODO: status (what is this?)
    # TODO: grading script

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
