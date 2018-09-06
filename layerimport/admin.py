# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from layerimport.models import TablaGeografica, ArchivoRaster


class TablaGeograficaAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(TablaGeografica, TablaGeograficaAdmin)


class ArchivoRasterAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(ArchivoRaster, ArchivoRasterAdmin)
