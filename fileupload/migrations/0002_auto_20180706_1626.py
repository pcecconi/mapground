# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-07-06 16:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fileupload', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='archivo',
            name='slug',
            field=models.SlugField(blank=True, max_length=255),
        ),
    ]