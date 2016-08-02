from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

# Create your models here.

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

   
class UserProfile(models.Model):
    ROLE_SUPER_USER = 0
    ROLE_INSTRUCTOR = 10
    ROLE_TA = 11
    ROLE_GRADER = 12
    ROLE_STUDENT = 20
    choices = (
            (ROLE_SUPER_USER, 'Super user'),
            (ROLE_INSTRUCTOR, 'Instructor'),
            (ROLE_TA, 'TA'),
            (ROLE_GRADER, 'Grader'),
            (ROLE_STUDENT, 'Student'),
    )
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    first_name = models.CharField(max_length = 30)
    last_name = models.CharField(max_length = 30)
    email = models.EmailField()

class Course(models.Model):
    instructor_id = models.ForeignKey(UserProfile, on_delete = models.CASCADE)
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
    # TODO: DUT count
    # TODO: Wiring information
    # TODO: number of testbenches - reservation of IDs
    # TODO: status (what is this?)
    # TODO: grading script

class AssignmentTask(models.Model):
    assignment_id = models.ForeignKey(Assignment, on_delete = models.CASCADE)
    task_order = models.IntegerField()
    description = models.TextField()
    # TODO: test input
    # TODO: test output

class Submission(models.Model):
    student_id = models.ForeignKey(UserProfile, on_delete = models.CASCADE)
    assignment_id = models.ForeignKey(Assignment, on_delete = models.CASCADE)
    submission_time = models.DateTimeField()
    grading_result = models.FloatField()
    #submission_status  TODO

class SubmissionFile(models.Model):
    submission_id = models.ForeignKey(Submission, on_delete = models.CASCADE)
    file = models.FileField()
