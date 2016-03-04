# -*- coding: utf-8 -*-
from django.contrib import admin

from users.models import PermisoDeCapa, PermisoDeMapa, PermisoDeCapaPorGrupo

class PermisoDeCapaAdmin(admin.ModelAdmin):
    readonly_fields=('id',)
    search_fields = ('user__username', 'capa__id_capa', 'permiso')
    list_display = ['id', 'user', 'capa', 'permiso',]
    list_display_links = ['id',]
    ordering = ["-id"]
    list_filter = ['permiso', 'user', 'capa',]

admin.site.register(PermisoDeCapa, PermisoDeCapaAdmin)

class PermisoDeCapaPorGrupoAdmin(admin.ModelAdmin):
    readonly_fields=('id',)
    search_fields = ('group__name', 'capa__id_capa', 'permiso')
    list_display = ['id', 'group', 'capa', 'permiso',]
    list_display_links = ['id',]
    ordering = ["-id"]
    list_filter = ['permiso', 'group', 'capa',]

admin.site.register(PermisoDeCapaPorGrupo, PermisoDeCapaPorGrupoAdmin)

admin.site.register(PermisoDeMapa)
