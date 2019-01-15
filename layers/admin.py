# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.gis.admin import GeoModelAdmin

from models import Capa, RasterDataSource, VectorDataSource,Categoria, TipoDeGeometria, Metadatos, Escala, ConexionPostgres, Atributo, ArchivoSLD, AreaTematica


class AtributoAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'nombre_del_campo', 'tipo')
    search_fields = ('nombre_del_campo', 'alias', 'descripcion')
    list_display = ['id', 'nombre_del_campo', 'alias', 'tipo', 'descripcion', 'publicable', 'unico']
    list_display_links = ['id', 'nombre_del_campo']
    ordering = ["-id"]
    list_filter = ['tipo', 'publicable', 'unico', 'metadatos']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Atributo, AtributoAdmin)


class AtributoInline(admin.TabularInline):
    model = Atributo
    extra = 2
    fields = ['nombre_del_campo', 'alias', 'tipo', 'descripcion', 'publicable', 'unico']
    readonly_fields = ('id', 'nombre_del_campo', 'tipo')
    ordering = ('nombre_del_campo',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class MetadatosAdmin(admin.ModelAdmin):
    inlines = (AtributoInline,)

    readonly_fields = ('id', 'capa')
    search_fields = ('nombre_capa', 'titulo', 'fuente', 'contacto', 'descripcion', 'palabras_claves',)
    list_display = ['id', 'capa', 'titulo', 'escala', 'area_tematica', 'timestamp_alta', 'timestamp_modificacion']
    list_display_links = ['id', 'capa']
    ordering = ["-id"]
    list_filter = ['escala', 'area_tematica', 'categorias']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Metadatos, MetadatosAdmin)


class CapaAdmin(GeoModelAdmin):
    modifiable = False
    map_srid = 4326
    readonly_fields = ('id', 'owner', 'nombre', 'tipo_de_capa', 'id_capa', 'slug', 'conexion_postgres', 'campo_geom', 'esquema', 'tabla', 'srid', 'proyeccion_proj4',
                       'tipo_de_geometria', 'cantidad_de_registros', 'nombre_del_archivo', 'cantidad_de_bandas', 'size_height', 'size_width',
                       'gdal_driver_shortname', 'gdal_driver_longname', 'gdal_metadata', 'layer_srs_extent')  # si agrego 'extent_minx_miny','extent_maxx_maxy')  se muestran como texto
    search_fields = ('nombre', )
    list_display = ['id', 'id_capa', 'nombre', 'tipo_de_capa', 'owner', 'wxs_publico', 'tipo_de_geometria', 'gdal_driver_shortname', 'cantidad_de_registros', 'timestamp_alta', 'timestamp_modificacion']
    list_display_links = ['id', 'id_capa']
    ordering = ["-id"]
    list_filter = ['owner', 'tipo_de_capa', 'gdal_driver_shortname', 'tipo_de_geometria', 'wxs_publico', 'conexion_postgres', 'srid']
    date_hierarchy = 'timestamp_alta'

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

admin.site.register(Capa, CapaAdmin)


class TipoDeGeometriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'postgres_type', 'mapserver_type']

admin.site.register(TipoDeGeometria, TipoDeGeometriaAdmin)


class CategoriaAdmin(admin.ModelAdmin):
    search_fields = ('nombre', 'descripcion')
    list_display = ['id', 'nombre', 'descripcion']
    list_display_links = ['id', 'nombre']
    ordering = ["-id"]

admin.site.register(Categoria, CategoriaAdmin)


class AreaTematicaAdmin(admin.ModelAdmin):
    search_fields = ('nombre', 'descripcion')
    list_display = ['id', 'nombre', 'descripcion']
    list_display_links = ['id', 'nombre']
    ordering = ["nombre"]

admin.site.register(AreaTematica, AreaTematicaAdmin)


class ArchivoSLDAdmin(admin.ModelAdmin):
    readonly_fields = ('id_archivo_sld', 'capa', 'filename')
    search_fields = ('filename', 'descripcion', )
    list_display = ['id', 'capa', 'filename', 'descripcion', 'default', 'user_alta', 'timestamp_alta', 'user_modificacion', 'timestamp_modificacion']
    list_display_links = ['id', 'filename']
    ordering = ["-id"]
    list_filter = ['user_alta', 'user_modificacion', 'default', 'capa']
    date_hierarchy = 'timestamp_modificacion'

    def has_add_permission(self, request):
        return False
#     def has_delete_permission(self, request, obj=None):
#         return False

admin.site.register(ArchivoSLD, ArchivoSLDAdmin)

# modelos con admins genericos
admin.site.register(ConexionPostgres)
admin.site.register(Escala)

class RasterDataSourceAdmin(admin.ModelAdmin):
    search_fields = ('nombre_del_archivo', 'capa')
    list_display = ['id', 'nombre_del_archivo', 'capa', 'owner']
    list_display_links = ['id', 'nombre_del_archivo', 'capa', 'owner']
    ordering = ["nombre_del_archivo"]
    date_hierarchy = 'data_datetime'

admin.site.register(RasterDataSource, RasterDataSourceAdmin)
admin.site.register(VectorDataSource)
