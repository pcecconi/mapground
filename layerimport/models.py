# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from fileupload.models import Archivo
from utils import drop_table
from django_extras.contrib.auth.models import SingleOwnerMixin
import os
# import os, subprocess, re, glob


class TablaGeografica(SingleOwnerMixin, models.Model):
    nombre_normalizado = models.CharField('Nombre Normalizado', null=False, blank=False, unique=False, max_length=255)  # TODO: esto guarda el archivo original? para que?
    nombre_del_archivo = models.CharField('Nombre del Archivo', null=False, blank=False, unique=False, max_length=255)  # TODO: esto guarda el archivo original? para que?
    esquema = models.CharField('Esquema', null=False, blank=False, max_length=100)
    tabla = models.CharField('Tabla', null=False, blank=False, max_length=100)
    # tipo_de_geometria = models.CharField(u'Tipo de Geometría', null=False, blank=False, max_length=50)    # originalmente iba a ir, luego lo agregamos directamente en Capa y se completa en el signal via postgres
    srid = models.IntegerField('SRID', null=False, blank=False)
    timestamp_alta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de alta')

    class Meta:
        unique_together = (('esquema', 'tabla', 'owner'),)
        verbose_name = 'Tabla geográfica'
        verbose_name_plural = 'Tablas geográficas'

    def __unicode__(self):
        return unicode(self.nombre_normalizado)


# @receiver(post_save, sender=TablaGeografica)
# def onTablaGeograficaPostSave(sender, instance, created, **kwargs):
#     # print 'onTablaGeograficaPostSave...a.k.a. onLayerImport'
#     archivos = Archivo.objects.filter(owner=instance.owner, nombre=os.path.splitext(instance.nombre_del_archivo)[0])
#     for a in archivos:
#         a.delete()


@receiver(post_delete, sender=TablaGeografica)
def onTablaGeograficaPostDelete(sender, instance, **kwargs):
    # print 'onTablaGeograficaPostDelete...a.k.a. onLayerDelete'
    try:
        drop_table(instance.esquema, instance.tabla)
    except:
        pass


# Clase equivalente a TablaGeografica pero a nivel raster, o sea, todo raster en la IDE subido via GDAL con metadatos determinados por esta libreria
class ArchivoRaster(SingleOwnerMixin, models.Model):
    nombre_del_archivo = models.CharField('Nombre del Archivo', null=False, blank=False, unique=False, max_length=255)
    path_del_archivo = models.CharField('Path absoluto del Archivo', null=False, blank=False, unique=True, max_length=255)
    formato = models.CharField(null=False, blank=False, unique=False, max_length=255)   # según GDALRaster
    cantidad_de_bandas = models.IntegerField(null=True, blank=True)                     # según GDALRaster  # TODO: podrá ser null?
    srid = models.IntegerField(null=False, blank=False, default=4326)                   # según GDALRaster, hay rasters que tienen srid=None
    extent = models.CharField(null=False, blank=False, max_length=255, default='')      # según GDALRaster
    heigth = models.IntegerField(null=False, blank=False)                               # según GDALRaster
    width = models.IntegerField(null=False, blank=False)                                # según GDALRaster
    timestamp_alta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de alta')

    class Meta:
        unique_together = (('owner', 'nombre_del_archivo'),)
        verbose_name = 'Archivo Raster'
        verbose_name_plural = 'Archivos Rasters'

    def __unicode__(self):
        return unicode(self.nombre_del_archivo)  # TODO: por ahora no es unique

# @receiver(post_save, sender=ArchivoRaster)
# def OnArchivoRasterPostSave(sender, instance, created, **kwargs):
#     print 'OnArchivoRasterPostSave'
#     # print kwargs['instance'].owner, kwargs['instance'].nombre_del_archivo
#     print instance.owner, instance.nombre_del_archivo[len(unicode(instance.owner) + '_'):]
#     #archivos = Archivo.objects.filter(owner=instance.owner, nombre=instance.nombre_del_archivo)
#     archivos = Archivo.objects.filter(owner=instance.owner, nombre=instance.nombre_del_archivo[len(unicode(instance.owner) + '_'):])
#     for a in archivos:
#         print 'Borrando:', a
#         a.delete()


@receiver(post_delete, sender=ArchivoRaster)
def onArchivoRasterPostDelete(sender, instance, **kwargs):
    # print 'onArchivoRasterPostDelete'
    try:
        os.remove(instance.path_del_archivo)
    except:
        pass
