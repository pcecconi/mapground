# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from os import path
from django.conf import settings
from django_extras.contrib.auth.models import SingleOwnerMixin
from utils.commons import normalizar_texto


# Función mejorada: además de determinar el path absoluto final del archivo, lo normaliza y acorta a 100 chars
# Esto corrige: nombres largos que no entran en el varchar de la base, caracteres especiales y soporte a extensiones en mayúsculas
def getUploadPath(inst, filename):
    partes = filename.split('.')
    filename_final = '.'.join(map(lambda x: normalizar_texto(x[:100]), partes))
    return settings.UPLOADED_FILES_PATH + str(inst.owner) + '/' + filename_final


class Archivo(SingleOwnerMixin, models.Model):
    """This is a small demo using just two fields. The slug field is really not
    necessary, but makes the code simpler. ImageField depends on PIL or
    pillow (where Pillow is easily installable in a virtualenv. If you have
    problems installing pillow, use a more generic FileField instead.

    """

    # Por lo que veo, el campo slug venía en el ejemplo original:
    # en realidad no es un slug pero sirve porque guarda el nombre completo del archivo (sin path) y es util para los Archivo.get()
    # No es clave pues distintos usuarios pueden subir el mismo archivo, pero sí debería ser clave la tupla <owner, slug>
    file = models.FileField(max_length=255, upload_to=getUploadPath)  # ej: /datos/admin/world_border.shp
    slug = models.SlugField(max_length=255, blank=True)                 # ej: world_border.shp
    nombre = models.CharField(max_length=255, blank=True)               # ej: world_border
    extension = models.CharField(max_length=15, blank=True)             # ej: .shp

    def __unicode__(self):
        return self.file.name

    @models.permalink
    def get_absolute_url(self):
        return ('fileupload:upload-new', )

    def save(self, *args, **kwargs):
        super(Archivo, self).save(*args, **kwargs)
        self.slug = path.basename(self.file.name)
        self.nombre, self.extension = path.splitext(self.slug)
        super(Archivo, self).save(update_fields=['slug', 'nombre', 'extension'])

    def delete(self, *args, **kwargs):
        """Delete -- Remove to leave file."""
        self.file.delete(False)
        super(Archivo, self).delete(*args, **kwargs)
