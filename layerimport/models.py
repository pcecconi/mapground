# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from fileupload.models import Archivo
from utils import drop_table
from django_extras.contrib.auth.models import SingleOwnerMixin
import os
# import os, subprocess, re, glob

class TablaGeografica(SingleOwnerMixin, models.Model):
#    owner = models.ForeignKey(User,null=False,blank=False) #TODO
    nombre_normalizado = models.CharField('Nombre Normalizado', null=False, blank=False, unique=False, max_length=255)
    nombre_del_archivo = models.CharField('Nombre del Archivo', null=False, blank=False, unique=False, max_length=255)
    esquema = models.CharField('Esquema', null=False, blank=False, max_length=100)
    tabla = models.CharField('Tabla', null=False, blank=False, max_length=100)
#    tipo_de_geometria = models.CharField(u'Tipo de Geometría', null=False, blank=False, max_length=50) #TODO: va? es char?
    srid = models.IntegerField('SRID', null=False, blank=False)
    timestamp_alta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de alta')
    class Meta:
        unique_together=(('esquema', 'tabla', 'owner'),)
        verbose_name = 'Tabla geográfica'
        verbose_name_plural = 'Tablas geográficas'
    def __unicode__(self):
        return unicode(self.nombre_normalizado)
	
capasPendientes = []

@receiver(post_save, sender=TablaGeografica)
def onLayerImport(sender, **kwargs):
#    print 'onLayerImport'
    archivos = Archivo.objects.filter(owner=kwargs['instance'].owner, nombre=os.path.splitext(kwargs['instance'].nombre_del_archivo)[0])
    for a in archivos:
#        print "Borrando archivo %s..." % a.file
        a.delete()

@receiver(post_delete, sender=TablaGeografica)
def onLayerDelete(sender, instance, **kwargs):
#    print 'onLayerDelete'
    try:
        drop_table(instance.esquema, instance.tabla)
    except:
        pass

# @receiver(post_save, sender=Archivo)
# def onFileUpload(sender, **kwargs):
# 	global capasPendientes
# 	print 'onFileUpload'
# 	capasPendientes.append(kwargs['instance'].file)
# 	print 'Capas Pendientes:'
# 	for c in capasPendientes:
# 		print c
# 	for name, value in kwargs.items():
# 		print '{0} = {1}'.format(name, value)
# 	 	if name == 'instance':
# 	 		print 'slug: ', value.slug
# 	 		print 'file: ', value.file
# 	 		# print 'nombre: ', value.dameNombre

