# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-20 03:13
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TablaGeografica',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_normalizado', models.CharField(max_length=255, verbose_name=b'Nombre Normalizado')),
                ('nombre_del_archivo', models.CharField(max_length=255, verbose_name=b'Nombre del Archivo')),
                ('esquema', models.CharField(max_length=100, verbose_name=b'Esquema')),
                ('tabla', models.CharField(max_length=100, verbose_name=b'Tabla')),
                ('srid', models.IntegerField(verbose_name=b'SRID')),
                ('timestamp_alta', models.DateTimeField(auto_now_add=True, verbose_name=b'Fecha de alta')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='layerimport_tablageografica_owner', to=settings.AUTH_USER_MODEL, verbose_name='owner')),
            ],
            options={
                'verbose_name': 'Tabla geogr\xe1fica',
                'verbose_name_plural': 'Tablas geogr\xe1ficas',
            },
        ),
        migrations.AlterUniqueTogether(
            name='tablageografica',
            unique_together=set([('esquema', 'tabla', 'owner')]),
        ),
    ]
