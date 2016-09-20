# -*- coding: utf-8 -*-
# Generated by Django 1.11.dev20160819220457 on 2016-09-07 01:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serapis', '0021_taskgradingstatus_output_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskgradingstatus',
            name='grading_status',
            field=models.IntegerField(choices=[(0, 'Pending'), (10, 'Executing'), (100, 'Checking output'), (110, 'Finished'), (-1, 'Please contact PI')], default=0),
        ),
        migrations.AlterField(
            model_name='testbed',
            name='unique_hardware_id',
            field=models.CharField(max_length=30, unique=True),
        ),
    ]
