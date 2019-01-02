# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django_extras.contrib.auth.models import SingleOwnerMixin
from utils import drop_table
import os


class TablaGeografica(SingleOwnerMixin, models.Model):
    nombre_normalizado = models.CharField('Nombre Normalizado', null=False, blank=False, unique=False, max_length=255)
    nombre_del_archivo = models.CharField('Nombre del Archivo', null=False, blank=False, unique=False, max_length=255)
    esquema = models.CharField('Esquema', null=False, blank=False, max_length=100)
    tabla = models.CharField('Tabla', null=False, blank=False, max_length=100)
    # tipo_de_geometria = models.CharField(u'Tipo de Geometría', null=False, blank=False, max_length=50)    # originalmente iba a ir, luego lo agregamos directamente en Capa y se completa en el signal via postgres
    srid = models.IntegerField('SRID', null=False, blank=False)
    timestamp_alta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de alta')

    class Meta:
        unique_together = (('esquema', 'tabla', 'owner'),)
        verbose_name = 'Tabla Geográfica'
        verbose_name_plural = 'Tablas Geográficas'

    def __unicode__(self):
        return unicode(self.nombre_normalizado)


@receiver(post_delete, sender=TablaGeografica)
def onTablaGeograficaPostDelete(sender, instance, **kwargs):
    pass
    # print 'onTablaGeograficaPostDelete'
    # try:
    #    drop_table(instance.esquema, instance.tabla)
    # except:
    #    pass


# Clase equivalente a TablaGeografica pero a nivel raster, o sea, todo raster en la IDE subido via GDAL con metadatos determinados por esta libreria
class ArchivoRaster(SingleOwnerMixin, models.Model):
    nombre_del_archivo = models.CharField('Nombre del Archivo', null=False, blank=False, unique=False, max_length=255)
    path_del_archivo = models.CharField('Path absoluto del Archivo', null=False, blank=False, unique=True, max_length=255)
    formato_driver_shortname = models.CharField(null=False, blank=True, unique=False, max_length=255)   # según GDAL
    formato_driver_longname = models.CharField(null=False, blank=True, unique=False, max_length=255)   # según GDAL
    srid = models.IntegerField(null=True, blank=True)                                   # según GDAL, puede ser None
    timestamp_alta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de alta')

    class Meta:
        unique_together = (('owner', 'nombre_del_archivo'),)
        verbose_name = 'Archivo Raster'
        verbose_name_plural = 'Archivos Rasters'

    def __unicode__(self):
        return unicode(self.nombre_del_archivo)


@receiver(post_delete, sender=ArchivoRaster)
def onArchivoRasterPostDelete(sender, instance, **kwargs):
    # print 'onArchivoRasterPostDelete'
    try:
        os.remove(instance.path_del_archivo)
    except:
        pass
