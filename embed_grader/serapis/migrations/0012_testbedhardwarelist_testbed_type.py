# -*- coding: utf-8 -*-
# Generated by Django 1.11.dev20160801201541 on 2016-08-28 07:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('serapis', '0011_auto_20160826_1820'),
    ]

    operations = [
        migrations.AddField(
            model_name='testbedhardwarelist',
            name='testbed_type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='serapis.TestbedType'),
            preserve_default=False,
        ),
    ]
