# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from os import path
from django.conf import settings
from django_extras.contrib.auth.models import SingleOwnerMixin


def getUploadPath(inst, filename):
    return settings.MEDIA_ROOT + 'uploaded/' + str(inst.owner) + '/' + filename
    # return settings.MEDIA_ROOT+filename


class Archivo(SingleOwnerMixin, models.Model):
    """This is a small demo using just two fields. The slug field is really not
    necessary, but makes the code simpler. ImageField depends on PIL or
    pillow (where Pillow is easily installable in a virtualenv. If you have
    problems installing pillow, use a more generic FileField instead.

    """
    file = models.FileField(max_length=255, upload_to=getUploadPath)
    slug = models.SlugField(max_length=255, blank=True)
    nombre = models.CharField(max_length=128, blank=True)
    extension = models.CharField(max_length=15, blank=True)

    def __unicode__(self):
        return self.file.name

    @models.permalink
    def get_absolute_url(self):
        return ('fileupload:upload-new', )

    def save(self, *args, **kwargs):
        super(Archivo, self).save(*args, **kwargs)
        self.slug = path.basename(self.file.name)
        self.nombre, self.extension = path.splitext(self.slug)
        # self.owner = self.request.user
        super(Archivo, self).save(update_fields=['slug', 'nombre', 'extension'])

    def delete(self, *args, **kwargs):
        """delete -- Remove to leave file."""
        self.file.delete(False)
        super(Archivo, self).delete(*args, **kwargs)
