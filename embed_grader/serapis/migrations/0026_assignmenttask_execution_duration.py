# -*- coding: utf-8 -*-
# Generated by Django 1.11.dev20160801201541 on 2016-10-05 15:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serapis', '0025_courseuserlist_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignmenttask',
            name='execution_duration',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
