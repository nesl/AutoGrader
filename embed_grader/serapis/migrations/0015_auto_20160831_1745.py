# -*- coding: utf-8 -*-
# Generated by Django 1.11.dev20160819220457 on 2016-09-01 00:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serapis', '0014_auto_20160829_2347'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submissionfile',
            name='submission_id',
        ),
        migrations.AddField(
            model_name='submission',
            name='file',
            field=models.FileField(default='', upload_to='uploaded_files'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='assignment',
            name='description',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='assignmenttask',
            name='grading_script',
            field=models.FileField(upload_to='uploaded_files'),
        ),
        migrations.AlterField(
            model_name='assignmenttask',
            name='test_input',
            field=models.FileField(upload_to='uploaded_files'),
        ),
        migrations.AlterField(
            model_name='testbed',
            name='status',
            field=models.IntegerField(choices=[(0, 'Reserved'), (1, 'Available')]),
        ),
        migrations.AlterField(
            model_name='testbedhardwarelist',
            name='firmware',
            field=models.FileField(blank=True, null=True, upload_to='uploaded_files'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='uid',
            field=models.CharField(max_length=20, unique=True, verbose_name='University ID'),
        ),
        migrations.DeleteModel(
            name='SubmissionFile',
        ),
    ]
