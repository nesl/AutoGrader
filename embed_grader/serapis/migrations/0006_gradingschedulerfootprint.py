# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2019-01-27 22:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serapis', '0005_assignment_max_num_submissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='GradingSchedulerFootprint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pid', models.IntegerField()),
                ('woke_time', models.DateTimeField()),
                ('watchdog_time', models.DateTimeField()),
            ],
        ),
    ]
