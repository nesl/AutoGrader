# -*- coding: utf-8 -*-
# Generated by Django 1.11.dev20160819220457 on 2016-09-22 23:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serapis', '0023_auto_20160906_2034'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='user_role',
        ),
        migrations.AlterField(
            model_name='assignmenttask',
            name='grading_script',
            field=models.FileField(upload_to='AssignmentTask_grading_script'),
        ),
        migrations.AlterField(
            model_name='assignmenttask',
            name='test_input',
            field=models.FileField(upload_to='AssignmentTask_test_input'),
        ),
        migrations.AlterField(
            model_name='hardwaretype',
            name='pinout',
            field=models.FileField(upload_to='HardwareType_pinout'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='file',
            field=models.FileField(upload_to='Submission_file'),
        ),
        migrations.AlterField(
            model_name='submissionfile',
            name='file',
            field=models.FileField(upload_to='SubmissionFile_file'),
        ),
        migrations.AlterField(
            model_name='taskgradingstatus',
            name='output_file',
            field=models.FileField(blank=True, null=True, upload_to='TaskGradingStatus_output_file'),
        ),
        migrations.AlterField(
            model_name='testbedhardwarelist',
            name='firmware',
            field=models.FileField(blank=True, null=True, upload_to='TestbedHardwareList_firmware'),
        ),
    ]
