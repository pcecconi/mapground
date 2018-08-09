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
    # tipo_de_geometria = models.CharField(u'Tipo de Geometría', null=False, blank=False, max_length=50) #TODO: va? es char?
    srid = models.IntegerField('SRID', null=False, blank=False)
    timestamp_alta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de alta')

    class Meta:
        unique_together = (('esquema', 'tabla', 'owner'),)
        verbose_name = 'Tabla geográfica'
        verbose_name_plural = 'Tablas geográficas'

    def __unicode__(self):
        return unicode(self.nombre_normalizado)


@receiver(post_save, sender=TablaGeografica)
def onTablaGeograficaPostSave(sender, **kwargs):
    # print 'onTablaGeograficaPostSave...a.k.a. onLayerImport'
    archivos = Archivo.objects.filter(owner=kwargs['instance'].owner, nombre=os.path.splitext(kwargs['instance'].nombre_del_archivo)[0])
    for a in archivos:
        # print "Borrando archivo %s..." % a.file
        a.delete()


@receiver(post_delete, sender=TablaGeografica)
def onTablaGeograficaPostDelete(sender, instance, **kwargs):
    # print 'onTablaGeograficaPostDelete...a.k.a. onLayerDelete'
    try:
        drop_table(instance.esquema, instance.tabla)
    except:
        pass


# Clase equivalente a TablaGeografica pero a nivel raster, o sea, todo raster en la IDE subido via GDAL con metadatos accesibles por esta libreria
class ArchivoRaster(SingleOwnerMixin, models.Model):
    nombre_del_archivo = models.CharField('Nombre del Archivo', null=False, blank=False, unique=False, max_length=255)
    path_del_archivo = models.CharField('Path absoluto del Archivo', null=False, blank=False, unique=True, max_length=255)
    formato = models.CharField('Formato segun GDAL', null=False, blank=False, unique=False, max_length=255)
    cantidad_de_bandas = models.IntegerField(null=True, blank=True)     # TODO: podra ser null?
    srid = models.IntegerField('SRID', null=False, blank=False)     # TODO: algunos rasters pueden ser null, pensar que hacer
    heigth = models.IntegerField(null=False, blank=False)
    width = models.IntegerField(null=False, blank=False)
    timestamp_alta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de alta')

    class Meta:
        unique_together = (('owner', 'nombre_del_archivo'),)
        verbose_name = 'Archivo Raster'
        verbose_name_plural = 'Archivos Rasters'

    def __unicode__(self):
        return unicode(self.nombre_del_archivo)  # TODO: por ahora no es unique


@receiver(post_delete, sender=ArchivoRaster)
def onArchivoRasterPostDelete(sender, instance, **kwargs):
    # print 'onArchivoRasterPostDelete'
    pass
    # TODO: borrar archivo
