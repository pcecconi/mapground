# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-07-06 16:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0003_auto_20180620_1757'),
    ]

    operations = [
        migrations.AddField(
            model_name='capa',
            name='layer_srs_extent',
            field=models.CharField(default='', max_length=255, verbose_name='Original SRS Extent'),
        ),
    ]
