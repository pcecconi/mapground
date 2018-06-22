# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib import messages
from django import forms
from maps.models import Mapa, MapServerLayer, TMSBaseLayer, ArchivoSLD
from utils.commons import normalizar_texto
from users.models import ManejadorDePermisos
from django.forms import ValidationError


class TMSBaseLayerAdmin(admin.ModelAdmin):
    readonly_fields=('id', )
    list_display = ['id', 'nombre', 'tms', 'min_zoom','max_zoom', 'fuente', 'url',]
    list_display_links = ['id', 'nombre']
    ordering = ["-id"]

admin.site.register(TMSBaseLayer, TMSBaseLayerAdmin)

# esta clase permite filtrar el combo de archivos slds que coinciden con la capa del mapserverlayer actual
class MapServerLayerAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MapServerLayerAdminForm, self).__init__(*args, **kwargs)
        if self.instance.id is not None:
            self.fields['archivo_sld'].queryset = self.fields['archivo_sld'].queryset.filter(capa=self.instance.capa).order_by('id_archivo_sld')


class MapServerLayerAdmin(admin.ModelAdmin):
    readonly_fields=('id', 'capa', 'mapa')
    list_display = ['id', '__unicode__', 'capa', 'mapa', 'orden_de_capa','feature_info', 'archivo_sld']
    list_display_links = ['id', '__unicode__']
    ordering = ["-id"]
    list_filter = ['capa', 'mapa', 'feature_info', 'archivo_sld']
    form = MapServerLayerAdminForm
#    def has_add_permission(self, request):
#        return False
#    def has_delete_permission(self, request, obj=None):
#        return False

admin.site.register(MapServerLayer, MapServerLayerAdmin)


# esta clase permite filtrar inline el combo de archivos slds que coinciden con la capa del mapserverlayer actual
class MapServerLayerInlineAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MapServerLayerInlineAdminForm, self).__init__(*args, **kwargs)
        if self.instance.id is not None:
            self.fields['archivo_sld'].queryset = self.fields['archivo_sld'].queryset.filter(capa=self.instance.capa).order_by('id_archivo_sld')
            # self.fields['capa'].queryset = self.fields['capa'].queryset.exclude(id__in=self.instance.mapa.capas.all()).order_by('nombre')
        else:
            self.fields['capa'].queryset = self.fields['capa'].queryset.order_by('id_capa')
        
        # esta linea magica permite redefinir el __unicode__() de cada capa sin tener que heredar de ModelChoiceField porque esto ultimo requiere un queryset obligatorio de parametro que pisa el filtro complicado de "capas de usuario"
        # sacado del anteultimo comentario de aca: http://stackoverflow.com/questions/3167824/change-django-modelchoicefield-to-show-users-full-names-rather-than-usernames
        self.fields['capa'].label_from_instance = lambda obj: "%s" % obj.id_capa
            
class MapServerLayerInline(admin.TabularInline):
    model = MapServerLayer
    extra = 2 
    fields = ['capa', 'orden_de_capa', 'feature_info','capa_cantidad_de_archivos_sld', 'archivo_sld', 'capa_tipo_de_geometria',]    
    readonly_fields=('capa_tipo_de_geometria','capa_cantidad_de_archivos_sld',)
    ordering = ('orden_de_capa',)
    form = MapServerLayerInlineAdminForm
    # esto permite filtrar por "capas de usuario", para eso necesito el request y en este contexto está disponible
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(MapServerLayerInline, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'capa':
            field.queryset = ManejadorDePermisos.capas_de_usuario(kwargs['request'].user, 'all').order_by('id_capa')
        return field    
    def capa_tipo_de_geometria(self, obj):
        return unicode(obj.capa.tipo_de_geometria)
    capa_tipo_de_geometria.short_description='Tipo'
    def capa_cantidad_de_archivos_sld(self, obj):
        return unicode(obj.capa.archivosld_set.count())
    capa_cantidad_de_archivos_sld.short_description='# SLDs'
    #archivo_sld.short_description='SLD elegido'
    #feature_info.short_description='¿Tooltip?' # si queremos overridear estos textos tenemos que agregar verbose names en la definicion en models.py


class MapaAdminForm(forms.ModelForm):
    def clean(self):
        if self.instance.id is None:
            cleaned_data = super(MapaAdminForm, self).clean()
            nombre = unicode(normalizar_texto(cleaned_data.get('titulo')))
            if nombre == '':
                raise ValidationError(u'Error: el mapa debe tener un nombre válido')
            id_mapa = '%s_%s'%(self.request.user.username,nombre)
            if len(Mapa.objects.filter(id_mapa=id_mapa)) > 0: # si ya existe un mapa con este nombre
                raise ValidationError(u'Error: ya existe un mapa con ese nombre')
        else:
            if self.instance.tipo_de_mapa != 'general':
                raise ValidationError('Error: no puede editarse este mapa')
            
        
    
class MapaAdmin(admin.ModelAdmin):
    inlines = (MapServerLayerInline,)

    readonly_fields=('id', 'owner', 'nombre', 'id_mapa', 'slug', 'tipo_de_mapa', 'srs')
    search_fields = ('nombre', 'titulo', 'fuente', 'contacto', 'descripcion','palabras_claves' )
    list_display = ['id', 'id_mapa', 'nombre', 'owner', 'tipo_de_mapa', 'publico', 'escala', 'tms_base_layer', 'timestamp_alta', 'timestamp_modificacion']
    list_display_links = ['id', 'id_mapa']
    ordering = ["-id"]
    list_filter = ['tipo_de_mapa', 'publico', 'tms_base_layer', 'owner', 'escala', 'categorias']
    date_hierarchy = 'timestamp_alta'
    
    # overrideamos el form para poder aplicar un clean y determinar la validez del input; esta es la forma para evitar grabar un objeto inválido desde el admin
    form = MapaAdminForm
    # además, pasamos el request al form overrideado para poder chequear condición de "mapa ya existente" que requiere el request.user 
    def get_form(self, request, *args, **kwargs):
        form = super(MapaAdmin, self).get_form(request, *args, **kwargs)
        form.request = request
        return form    
    
    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            obj.owner = request.user
            obj.tipo_de_mapa = 'general'
            obj.srs = '3857' 
            obj.nombre = unicode(normalizar_texto(obj.titulo))
            obj.id_mapa = obj.slug = '%s_%s'%(obj.owner.username,obj.nombre)
        obj.save()                
        #super(MapaAdmin, self).save_model(request, obj, form, change)

admin.site.register(Mapa, MapaAdmin)
