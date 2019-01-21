# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from users.models import UserProfile, PermisoDeCapa, PermisoDeMapa, PermisoDeCapaPorGrupo

# Esta es la definicion estandar del admin para UserProfile.
# La cambie por la siguiente a continuacion para que se renderice directamente como columnas del User default
# class UserProfileAdmin(admin.ModelAdmin):
#     readonly_fields = ('id',)
#     list_display = ['id', 'user', 'puede_subir_capas']
#     list_display_links = ['id', ]
#     ordering = ["-id"]
#     list_filter = ['puede_subir_capas']

# admin.site.register(UserProfile, UserProfileAdmin)


# Override del admin de User segun la documentacion oficial:
# https://docs.djangoproject.com/en/1.11/topics/auth/customizing/#custom-permissions
# Define an inline admin descriptor for UserProfile model
# which acts a bit like a singleton
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'perfiles'
    verbose_name = 'perfil'


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'userprofile__puede_subir_capas')

    def userprofile__puede_subir_capas(self, x):
        return x.userprofile.puede_subir_capas
    userprofile__puede_subir_capas.short_description = 'puede subir capas?'
    userprofile__puede_subir_capas.boolean = True

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class PermisoDeCapaAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    search_fields = ('user__username', 'capa__id_capa', 'permiso')
    list_display = ['id', 'user', 'capa', 'permiso']
    list_display_links = ['id', ]
    ordering = ["-id"]
    list_filter = ['permiso', 'user', 'capa']

admin.site.register(PermisoDeCapa, PermisoDeCapaAdmin)


class PermisoDeCapaPorGrupoAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    search_fields = ('group__name', 'capa__id_capa', 'permiso')
    list_display = ['id', 'group', 'capa', 'permiso']
    list_display_links = ['id', ]
    ordering = ["-id"]
    list_filter = ['permiso', 'group', 'capa']

admin.site.register(PermisoDeCapaPorGrupo, PermisoDeCapaPorGrupoAdmin)

admin.site.register(PermisoDeMapa)
