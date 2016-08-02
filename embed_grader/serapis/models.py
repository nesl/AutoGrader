from __future__ import unicode_literals

from django.db import models

# Create your models here.

class HardwareTester(models.Model):
    STATUS_TYPES = (
        ('reserved','Reserved'),
        ('avail', 'Available'),
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_TYPES,
        default='avail',
    )

    TESTER_TYPES = (
        ('beagle', 'BeagleBone'),
        ('rpi3', 'RaspberryPi3')
    )
    type = models.CharField(
        max_length = 10,
        choices = TESTER_TYPES,
        default = 'beagle'
    )

class HardwareTestBench(models.Model):
    
