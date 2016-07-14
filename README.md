# AutoGrader

grader/models.py (only three classes finished)

from __future__ import unicode_literals

from django.db import models

class Person(models.Model):
    ROLE_CHOICES = ('teacher', 'student')
    role = models.CharField(max_length=7, choices= ROLE_CHOICES)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    account = models.CharField(max_length=20)
    UID = models.CharField(max_length=9)

class Problem(models.Model):
    PLATFORM_CHOICES = (('1','Mbead'),('2','FPGA'))
    platform = models.PositiveSmallIntegerField(choices = PLATFORM_CHOICES)
    problem_statement = models.CharField(max_length=100)
    input_statement = models.CharField(max_length=500)
    output_statement = models.CharField(max_length=500)

class Submission_table(models.Model):
    problem = models.ForeignKey('grader.Problem', on_delete = models.CASCADE,)
    file = models.FileField(upload_to = 'sum/mysite/uploads')
    submission_date = models.DateField('date submitted')
    score = models.IntegerField(default = 0)

Web frontend of Embedded Systems Auto Grader project
