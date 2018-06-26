# -*- coding: utf-8 -*-
# from __future__ import unicode_literals   # NO DESCOMENTAR! ROMPE TODO!

from django.db import models, connection, connections
from django.contrib.auth.models import User
from django.conf import settings
import mapscript
from layerimport.models import TablaGeografica
from layers.models import Capa, Categoria, Metadatos, Atributo, ArchivoSLD, Escala
import os
# slugs
from django.utils.text import slugify
# signals
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.gis.geos import MultiPoint
# fts
from djorm_pgfulltext.models import SearchManager
from djorm_pgfulltext.fields import VectorField
# misc
from utils.commons import normalizar_texto, urlToFile, coordConvert
from mapcache import manage
import urlparse
import urllib
import urllib2
import time
from lxml import etree
from mapcache.settings import MAPSERVER_URL
from subprocess import call

#CAPA_DEFAULT_SRS = 4326
#MAPA_DEFAULT_SRS = 22173
MAPA_DEFAULT_SRS = 3857
#MAPA_DEFAULT_SIZE = (800,600)
MAPA_DEFAULT_SIZE = (110, 150)
#MAPA_DEFAULT_EXTENT = (92000,90500,113500,112000) 
#MAPA_DEFAULT_EXTENT = (-180.0,-90.0,180.0,90.0)
#MAPA_DEFAULT_EXTENT = (-99.730966, -81.833764, -12.144851, -13.093764)
#MAPA_DEFAULT_EXTENT = (2315520, 2543567, 5144120, 7827023) #22173
MAPA_DEFAULT_EXTENT = (-20037508.3427892480, -20037508.3427892480, 20037508.3427892480, 20037508.3427892480) #3857 whole world
#MAPA_DEFAULT_EXTENT = (-6520000, -4125000, -6490000, -4098000) #3857 CABA
# MAPA_DEFAULT_EXTENT = (-8500000, -7500000,-5950000,-2400000) #3857 ARGENTINA
MAPA_DEFAULT_IMAGECOLOR = '#C6E2F2' # debe ser formato Hexa

MAPA_FONTSET_FILENAME = os.path.join(settings.MAPAS_PATH, 'fonts.txt')
MAPA_SYMBOLSET_FILENAME = os.path.join(settings.MAPAS_PATH, 'symbols.txt')
MAPA_DATA_PATH = '../data'
MAPA_ERRORFILE = os.path.join(settings.MAPAS_PATH, 'map-error.log')


TIPO_DE_MAPA_ENUM = (
    ('', ''),
    ('layer', 'layer'), # mapa de capa
    ('layer_original_srs', 'layer_original_srs'), # mapa de capa con srs original
    ('user', 'user'), # mapa de usuario
    ('public_layers', 'public_layers'), # mapa de todas las capas publicas en el sistema
    ('general', 'general'), # mapa de cualquier otro mapa creado ad-hoc
)

class TMSBaseLayer(models.Model):
    nombre = models.CharField('Nombre', null=False, blank=False, unique=True, max_length=255)
    url = models.CharField('URL', null=False, blank=False, max_length=2000)
    min_zoom = models.IntegerField('Min zoom', null=True, blank=True)
    max_zoom = models.IntegerField('Max zoom', null=True, blank=True)
    tms = models.BooleanField(u'TMS?', null=False, default=True)
    fuente = models.CharField('Fuente', null=False, blank=True, max_length=255) # attribution
    descripcion = models.TextField(u'Descripción', null=False, blank=True, max_length=10000)
     
    class Meta:
        verbose_name = 'TMS Base Layer'
        verbose_name_plural = 'TMS Base Layers'
    def __unicode__(self):
        return unicode(self.nombre)


class ManejadorDeMapas:
    @classmethod
    def delete_mapfile(cls,id_mapa):
        print "...ManejadorDeMapas.delete_mapfile %s"%(id_mapa)
        try:
             mapa=Mapa.objects.get(id_mapa=id_mapa)
        #if instance.tipo_de_mapa == 'layer':
        #    manage.remove([instance.id_mapa])
        except:
            print "......error: mapa inexistente" 
            return
        try:
            os.remove(os.path.join(settings.MAPAS_PATH, id_mapa+'.map'))
        except:
            pass
#         #if mapa.tipo_de_mapa in ['layer_original_srs', 'general']:
#         try:
#             os.remove(os.path.join(settings.MEDIA_ROOT, id_mapa+'.png'))
#         except:
#             pass    
        

    @classmethod
    def get_mapfile(cls,id_mapa):
        print "ManejadorDeMapas.get_mapfile: %s" %(id_mapa)
        mapfile_full_path=os.path.join(settings.MAPAS_PATH, id_mapa+'.map')
        if not os.path.isfile(mapfile_full_path):
            if id_mapa=='mapground_public_layers':
                cls.regenerar_mapa_publico()
            else:
                try:
                    mapa=Mapa.objects.get(id_mapa=id_mapa)
                except:
                    print "....ManejadorDeMapas.get_mapfile: ERROR: mapa inexistente %s" %(mapfile_full_path) 
                    return ''
                if mapa.tipo_de_mapa=='user':
                    cls.regenerar_mapas_de_usuarios([mapa.owner])
                elif mapa.tipo_de_mapa=='public_layers':
                    cls.regenerar_mapa_publico()
                elif mapa.tipo_de_mapa in ['layer', 'layer_original_srs']:
                    mapa.save() 
                elif mapa.tipo_de_mapa in ['general']: # a evaluar...
                    mapa.save()
                else:
                    return ''
        return mapfile_full_path
    
    @classmethod
    def regenerar_mapas_de_usuarios(cls,lista_users_inicial=None):
        from users.models import ManejadorDePermisos
        print "...ManejadorDeMapas.regenerar_mapas_de_usuarios %s"%(str(lista_users_inicial))
        q = Mapa.objects.filter(tipo_de_mapa='user')
        if lista_users_inicial is not None:
            q = q.filter(owner__in=lista_users_inicial)
        for m in q:
            m.mapserverlayer_set.all().delete()
            lista_capas=ManejadorDePermisos.capas_de_usuario(m.owner, 'all').order_by('metadatos__titulo')
            for idx, c in enumerate(lista_capas):
                MapServerLayer(mapa=m,capa=c,orden_de_capa=idx).save()
            m.save()
    
    @classmethod
    def regenerar_mapa_publico(cls):
        print "...ManejadorDeMapas.regenerar_mapa_publico"
        m, created = Mapa.objects.get_or_create(owner=User.objects.get(username='mapground'),nombre='mapground_public_layers',id_mapa='mapground_public_layers', tipo_de_mapa='public_layers')
        m.mapserverlayer_set.all().delete()
        for idx, c in enumerate(Capa.objects.filter(wxs_publico=True)):
            MapServerLayer(mapa=m,capa=c,orden_de_capa=idx).save()
        m.save()

    @classmethod
    def generar_thumbnail(cls,id_mapa):
        print "...ManejadorDeMapas.generar_thumbnail"
        try:
            mapa=Mapa.objects.get(id_mapa=id_mapa)
            thumb = mapa.generar_thumbnail()
            return thumb
        except:
            return ''
        
    @classmethod
    def generar_legend(cls,id_mapa):
        print "...ManejadorDeMapas.generar_legend"
        try:
            mapa=Mapa.objects.get(id_mapa=id_mapa)
            return mapa.generar_legend()
        except:
            return False

# podria ser Mapa/MapServerMap por separado
class Mapa(models.Model):
    owner = models.ForeignKey(User, null=False,blank=False) 
    nombre = models.CharField('Nombre', null=False, blank=False, max_length=255)
    id_mapa = models.CharField('Id mapa', null=False, blank=False, unique=True, max_length=255)
    slug = models.SlugField('Slug', null=False, blank=True, max_length=255)
    
    # metadatos del mapa
    titulo = models.CharField(u'Título', null=False, blank=True, max_length=255) # title
    fuente = models.TextField(u'Fuente', null=False, blank=True, max_length=1000) # attribution
    contacto = models.TextField(u'Contacto', null=False, blank=True, max_length=1000) # contact organization
    descripcion = models.TextField(u'Descripción', null=False, blank=True, max_length=10000) # abstract
    #fechas?
    
    srs = models.CharField('SRS', null=False, blank=True, max_length=100)
    tipo_de_mapa = models.CharField('Tipo de Mapa', choices=TIPO_DE_MAPA_ENUM, max_length=30, null=False, blank=True, default='')   

    tms_base_layer = models.ForeignKey(TMSBaseLayer, verbose_name='Capa Base', null=True, blank=True, on_delete=models.SET_NULL)    
    capas = models.ManyToManyField(Capa, blank=True, through='MapServerLayer') 
    
    size = models.CharField('Size', null=False, blank=True, max_length=100)
    extent = models.CharField('Extent', null=False, blank=True, max_length=100)
    imagecolor = models.CharField('Imagecolor', null=False, blank=True, max_length=100)
    imagetype = models.CharField('Imagetype', null=False, blank=True, max_length=100) #TODO
    # seguir agregando tags de mapserver

    publico = models.BooleanField(u'Público?', null=False, default=False)
    categorias = models.ManyToManyField(Categoria, blank=True, verbose_name=u'Categorías')
    escala = models.ForeignKey(Escala, null=True, blank=True, on_delete=models.SET_NULL)
    palabras_claves = models.TextField(u'Palabras Claves', null=False, blank=True, max_length=10000,default='')
    
    texto_output = models.TextField(u'Texto Output', null=False, blank=True, max_length=10000)
    
    timestamp_alta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de alta')
    timestamp_modificacion = models.DateTimeField(auto_now=True, verbose_name='Fecha de última modificación')

    input_search_index = models.TextField(null=False, blank=True, default='')
    search_index = VectorField()

    class Meta:
        verbose_name = 'Mapa'
        verbose_name_plural = 'Mapas'
    def __unicode__(self):
        return unicode(self.nombre)

    def actualizar_input_search_index(self):
        if self.tipo_de_mapa=='general':
            textos = []
            #TODO: ver si indexamos los titulos de las capas que lo componen
            textos.append(normalizar_texto(self.titulo))
            textos.append(normalizar_texto(self.palabras_claves))
            textos.append(normalizar_texto(self.escala))
            textos.append(normalizar_texto(self.descripcion))
            self.input_search_index = ' '.join(textos)
    
    def save(self, *args, **kwargs):
        escribir_imagen_y_mapfile = kwargs.pop('escribir_imagen_y_mapfile', True)
        self.slug=slugify(unicode(self.nombre)).replace('-', '_')
        
        # esto es para los casos de mapas 'general' que se crean a partir del titulo del form
        # los otros casos se completan en los creates de los objetos
        if self.nombre == '':
            self.nombre=unicode(normalizar_texto(self.titulo))
        if self.id_mapa == '':
            self.id_mapa = '%s_%s'%(self.owner.username,self.nombre)

        try:
            msm=self.dame_mapserver_mapObj()
            self.texto_output=msm.convertToString()[0:9999]
        except:
            self.texto_output=''
        if self.tipo_de_mapa=='general':
            self.actualizar_input_search_index()
        super(Mapa, self).save(*args, **kwargs)
        if escribir_imagen_y_mapfile:
            mapa = self.escribir_imagen_y_mapfile()
            if self.tipo_de_mapa in ('layer', 'general'):
                self.agregar_a_mapcache()
        return True
    
        
    @property
    def dame_titulo(self):
        if self.titulo!='':
            return self.titulo
        if self.tipo_de_mapa in ('layer_original_srs', 'layer'):
            try:
                return self.capas.first().dame_titulo
            except:
                pass
        return ''
    @property
    def dame_descripcion(self):
        if self.descripcion!='':
            return self.descripcion
        if self.tipo_de_mapa in ('layer_original_srs', 'layer'):
            try:
                return self.capas.first().dame_descripcion
            except:
                pass
        return ''
    @property
    def dame_fuente(self):
        if self.fuente!='':
            return self.fuente
        if self.tipo_de_mapa in ('layer_original_srs', 'layer'):
            try:
                return self.capas.first().dame_fuente
            except:
                pass
        return ''
    @property
    def dame_contacto(self):
        if self.contacto!='':
            return self.contacto
        if self.tipo_de_mapa in ('layer_original_srs', 'layer'):
            try:
                return self.capas.first().dame_contacto
            except:
                pass
        return ''
    @property
    def dame_tilesurl(self):
        if self.tipo_de_mapa in ('layer_original_srs', 'layer'):
            try:
                c = self.capas.first()
                return settings.MAPCACHE_URL+'tms/1.0.0/%s@GoogleMapsCompatible/{z}/{x}/{y}.png?t=%s'%(c.id_capa, time.mktime(c.timestamp_modificacion.timetuple()))
            except:
                pass
        elif self.tipo_de_mapa == 'general':
            return settings.MAPCACHE_URL+'tms/1.0.0/%s@GoogleMapsCompatible/{z}/{x}/{y}.png?t=%s'%(self.id_mapa, time.mktime(self.timestamp_modificacion.timetuple()))
        return ''
    # devuelve un string parametrizable tipo '-71.55 -41.966667 -63.0 -37.9'
    def dame_extent(self, separator=' ', srid=4326):
        if self.tipo_de_mapa in ('layer_original_srs', 'layer'):
            try:
                c = self.capas.first()
                return c.dame_extent(separator, srid)
            except:
                pass
        elif self.tipo_de_mapa in ('general'):
            try:
                extents=[]
                for c in self.capas.all():
                    extents+=c.dame_extent([], srid)
                mp=MultiPoint(extents)
                return separator.join(map(str, mp.extent))
            except:
                pass
        return ''
    @property
    def dame_filename(self):
        if '_' in self.id_mapa:
            res = self.id_mapa.split('_',1)[1]
        else:
            res = self.id_mapa
        return res.encode('utf-8')
    def dame_mapserver_size(self):
        try:
            if self.size!='':
                if self.size.count(',')==1:
                    return map(lambda x: int(x),self.size.split(','))
                else:
                    return map(lambda x: int(x),self.size.split())
            return MAPA_DEFAULT_SIZE
        except:
            return MAPA_DEFAULT_SIZE
    # @property
    # devuelve una 4-upla de floats para aplicar al mapObj
    def dame_mapserver_extent(self, srid=4326):
        try:
            if self.extent!='':
                if self.extent.count(',')==3:
                    ext = map(lambda x: float(x), self.extent.split(','))
                else:
                    ext = map(lambda x: float(x), self.extent.split()) # feo, pero permite mas de un espacio entre valores
                minxy = coordConvert(ext[0], ext[1], 4326, srid)
                maxxy = coordConvert(ext[2], ext[3], 4326, srid)
                return [minxy.x, minxy.y, maxxy.x, maxxy.y]
        except:
            return None
    @property
    def dame_imagecolor(self):
        try:
            if self.imagecolor!='':
                if self.imagecolor[0]=='#':
                    return True, self.imagecolor
                else:
                    if self.imagecolor.count(',')==2:
                        return False, map(lambda x: int(x), self.imagecolor.split(','))
                    elif self.imagecolor.count(' ')==2:
                        return False, map(lambda x: int(x), self.imagecolor.split())
            return True, MAPA_DEFAULT_IMAGECOLOR
        except:
            return True, MAPA_DEFAULT_IMAGECOLOR
        
    @property
    def dame_projection(self):
        return unicode(self.srs) if self.srs!='' else str(MAPA_DEFAULT_SRS)
    
    def dame_mapserver_mapObj(self):
        mapa = mapscript.mapObj()
        mapa.name='mapa_'+unicode(self.id_mapa)

        es_hexa, color = self.dame_imagecolor
        try:
            if es_hexa:
                mapa.imagecolor.setHex(color)
            else:
                mapa.imagecolor.setRGB(*(color))
        except:
            mapa.imagecolor.setHex(MAPA_DEFAULT_IMAGECOLOR)
        
        mapa.setSymbolSet(MAPA_SYMBOLSET_FILENAME)
        mapa.setFontSet(MAPA_FONTSET_FILENAME)
        mapa.shapepath=MAPA_DATA_PATH

        mapa.outputformat.transparent=True
            
        proj=self.dame_projection
        mapa.setProjection('epsg:%s'%(proj))
        if proj=='4326':
            mapa.units=mapscript.MS_DD
        else:
            mapa.units=mapscript.MS_METERS

        mapa.legend.updateFromString('LEGEND\n  KEYSIZE 20 10\n  KEYSPACING 5 5\n  LABEL\n    SIZE 10\n    OFFSET 0 0\n    SHADOWSIZE 1 1\n    TYPE TRUETYPE\n  FONT "Swz721lc"\nEND # LABEL\n  STATUS OFF\nEND # LEGEND\n\n')
        # primero seteamos extent, luego size. sino hay un comportamiento extranio y el extent no se respeta, quizas para igualar relaciones de aspecto entre ambos
        try:
            mapa.setExtent(*(self.dame_mapserver_extent(int(proj)))) # si tiene un extent overrideado
        except:
            if self.tipo_de_mapa in ('user', 'public_layers'): # en estos casos no los calculamos
                mapa.setExtent(*(MAPA_DEFAULT_EXTENT))
            else:
                try:
                    ext = self.dame_extent(',', proj)
                    mapa.setExtent(*(map(lambda x: float(x), ext.split(','))))
                except:
                    mapa.setExtent(*(MAPA_DEFAULT_EXTENT))
        try:
            mapa.setSize(*(self.dame_mapserver_size))
        except:
            mapa.setSize(*(MAPA_DEFAULT_SIZE))
                    
        output_geojson=mapscript.outputFormatObj('OGR/GEOJSON', 'GeoJson')
        output_geojson.setMimetype('application/json; subtype=geojson')
        output_geojson.setOption('STORAGE', 'stream')
        output_geojson.setOption('FORM', 'SIMPLE')
        mapa.appendOutputFormat(output_geojson)

        output_shapefile=mapscript.outputFormatObj('OGR/ESRI Shapefile', 'ShapeZip')
        output_shapefile.setMimetype('application/shapefile')
        output_shapefile.setOption('STORAGE', 'filesystem')
        output_shapefile.setOption('FORM', 'zip')
        output_shapefile.setOption('FILENAME', self.dame_filename+'.zip')
        mapa.appendOutputFormat(output_shapefile)

        output_csv=mapscript.outputFormatObj('OGR/CSV', 'CSV')
        output_csv.setMimetype('text/csv')
        # output_csv.setOption('LCO:GEOMETRY', 'AS_WKT')
        output_csv.setOption('STORAGE', 'filesystem')
        output_csv.setOption('FORM', 'simple')
        output_csv.setOption('FILENAME', self.dame_filename+'.csv')
        mapa.appendOutputFormat(output_csv)

        mapa.setConfigOption('MS_ERRORFILE',MAPA_ERRORFILE) 
        mapa.setConfigOption('PROJ_LIB',settings.PROJ_LIB)
        mapa.setConfigOption('MS_OPENLAYERS_JS_URL',settings.MS_OPENLAYERS_JS_URL)

        mapa.legend.template = 'templates/legend.html' # TODO: general o solo WMS?
        # mapa.web.updateFromString('VALIDATION\n \'TEMPLATE\'  \'[a-z/.]+\' \n END') # TODO: general o solo WMS?
        mapa.web.template = 'templates/mapa-interactivo.html' # TODO: general o solo WMS?
        
        mapa.web.imagepath = settings.MAP_WEB_IMAGEPATH
        mapa.web.imageurl = settings.MAP_WEB_IMAGEURL
        # mapa.web.template = 'blank.html' # siempre?
        # NOTA: algunos mapas que hicimos para SSPTIP usan wms_* en lugar de ows_*, no se si estan mal o hay alguna diferencia
        mapa.setMetaData('ows_title', unicode(self.dame_titulo).encode('UTF-8'))
        mapa.setMetaData('ows_abstract', unicode(self.dame_descripcion.replace('\r\n', ' ')).encode('UTF-8'))
        mapa.setMetaData('ows_attribution_title', unicode(self.dame_fuente.replace('\r\n', ' ')).encode('UTF-8'))
        mapa.setMetaData('ows_contactorganization', unicode(self.dame_contacto.replace('\r\n', ' ')).encode('UTF-8'))

        if self.tipo_de_mapa=='public_layers':
            mapa.setMetaData('wms_onlineresource', urlparse.urljoin(settings.SITE_URL,'layers/public_wxs/'))
            mapa.setMetaData('wfs_onlineresource', urlparse.urljoin(settings.SITE_URL,'layers/public_wxs/'))
        elif self.tipo_de_mapa=='user':
            mapa.setMetaData('wms_onlineresource', urlparse.urljoin(settings.SITE_URL, 'users/'+self.owner.username+'/wxs/'))
            mapa.setMetaData('wfs_onlineresource', urlparse.urljoin(settings.SITE_URL, 'users/'+self.owner.username+'/wxs/'))
        elif self.tipo_de_mapa=='layer_original_srs':
            mapa.setMetaData('wms_onlineresource', urlparse.urljoin(settings.WXS_ONLINERESOURCE,unicode(self.id_mapa.replace('_layer_srs',''))+'/'))
            mapa.setMetaData('wfs_onlineresource', urlparse.urljoin(settings.WXS_ONLINERESOURCE,unicode(self.id_mapa.replace('_layer_srs',''))+'/'))
        else:
            mapa.setMetaData('wms_onlineresource', urlparse.urljoin(settings.WXS_ONLINERESOURCE,unicode(self.id_mapa)+'/'))
            mapa.setMetaData('wfs_onlineresource', urlparse.urljoin(settings.WXS_ONLINERESOURCE,unicode(self.id_mapa)+'/'))

        mapa.setMetaData('mg_onlineresource', unicode(self.dame_tilesurl).encode('UTF-8'))
        mapa.setMetaData('mg_siteurl', unicode(settings.SITE_URL).encode('UTF-8'))
        if self.tms_base_layer:
            mapa.setMetaData('mg_baselayerurl', self.tms_base_layer.url)
            mapa.setMetaData('mg_tmsbaselayer', str(self.tms_base_layer.tms))
        else:
            mapa.setMetaData('mg_baselayerurl', settings.MAPCACHE_URL+'tms/1.0.0/world_borders@GoogleMapsCompatible/{z}/{x}/{y}.png')
            mapa.setMetaData('mg_tmsbaselayer', str(True))
        mapa.setMetaData('mg_mapid', unicode(self.id_mapa))

        mapa.setMetaData('ows_srs', 'epsg:%s epsg:4326'%(proj)) # dejamos proyecciones del mapa y 4326 fijas. esta logica la repetimos en las capas 
        mapa.setMetaData('wfs_getfeature_formatlist', 'geojson,shapezip,csv')
        mapa.setMetaData('ows_encoding', 'UTF-8') # siempre
        mapa.setMetaData('ows_enable_request', '*')
        mapa.setMetaData('labelcache_map_edge_buffer', '-10')
        #mapa.setMetaData('wms_feature_info_mime_type', 'application/json; subtype=geojson')
        
        if self.tipo_de_mapa in ('layer', 'layer_original_srs', 'user', 'general'):
            mapserverlayers = self.mapserverlayer_set.all().order_by('orden_de_capa','capa__metadatos__titulo')
        else: #'public_layers'
            mapserverlayers = self.mapserverlayer_set.filter(capa__wxs_publico=True).order_by('orden_de_capa')
        for msl in mapserverlayers:
            if self.tipo_de_mapa=='general':
                l=msl.dame_mapserver_layerObj('WMS')
            else:
                l=msl.dame_mapserver_layerObj()
                l.setMetaData('ows_srs','epsg:%s epsg:4326'%(proj))
            pos=mapa.insertLayer(l)
            
        return mapa

    def escribir_imagen_y_mapfile(self):
        print '...Grabando mapa e imagen de %s (tipo %s)'%(self.id_mapa, self.tipo_de_mapa)
        mapa=self.dame_mapserver_mapObj()
        mapa.save(os.path.join(settings.MAPAS_PATH, self.id_mapa+'.map'))
        print "......mapa guardado %s"%(self.id_mapa+'.map')
        if self.tipo_de_mapa in ('layer_original_srs', 'general'):
            thumb = self.generar_thumbnail()
            print "......imagen creada: %s"%(thumb)
        if self.tipo_de_mapa in ('general', 'layer'):
            self.generar_legend()
#         if self.tipo_de_mapa == 'layer_original_srs':
#             if not os.path.isfile(os.path.join(settings.MEDIA_ROOT, self.id_mapa+'.png')):
#                 self.capas.first().generar_thumbnail()
#                 print "......imagen creada" 
# #                 mapa=mapscript.mapObj(os.path.join(settings.MAPAS_PATH, self.id_mapa+'.map')) #reload del mapa para fixear capas de puntos
# #                 try:
# #                     mapa.draw().save(os.path.join(settings.MEDIA_ROOT, self.id_mapa+'.png'))
# #                     print "......imagen creada"
# #                 except:
# #                     print "......Fallo la creacion de la imagen!"
# #                     pass
#             else:
#                 print ".....(imagen ya existente, no se regenera)"
#         elif self.tipo_de_mapa == 'general':
#             self.generar_thumbnail()
        return mapa

    def agregar_a_mapcache(self):
        manage.remove([self.id_mapa])
        params = ''
        if self.tipo_de_mapa == 'layer':
            capa = self.mapserverlayer_set.first().capa
            params = ':%s:%d'%(capa.nombre, MAPA_DEFAULT_SRS)
            for sld in capa.archivosld_set.all():
                manage.remove([self.id_mapa+('$%d'%sld.id)])
                sld_url = urlparse.urljoin(settings.SITE_URL, sld.filename.url)
                if sld.default:
                    params = ':%s:%d:%s'%(capa.nombre, MAPA_DEFAULT_SRS, sld_url)
                pars = ':%s:%d:%s$%d'%(capa.nombre, MAPA_DEFAULT_SRS, sld_url, sld.id)
                print 'Mapcache capa: %s sld %d params: %s'%(capa.nombre, sld.id, pars)
                manage.add([self.id_mapa+pars])
            # default_sld = capa.dame_sld_default()
            # if default_sld is not None:
            #     params = ':%s:%d:%s'%(capa.nombre, MAPA_DEFAULT_SRS, default_sld)
            # else:
            #     params = ':%s:%d'%(capa.nombre, MAPA_DEFAULT_SRS)
        elif self.tipo_de_mapa == 'general':
            params = ':%s:%d'%('default', MAPA_DEFAULT_SRS)
                
        manage.add([self.id_mapa+params])

    def generar_thumbnail(self):
        mapfile=ManejadorDeMapas.get_mapfile(self.id_mapa)
        wms_url = '%s?map=%s'%(MAPSERVER_URL, mapfile)
        if self.tipo_de_mapa == 'general':
            for c in self.capas.all():  # es necesario regenerar todo mapfile inexistente
                ManejadorDeMapas.get_mapfile(c.id_capa)
            wms_url += '&LAYERS=%s&SRS=epsg:%s&MAP_RESOLUTION=96&SERVICE=WMS&FORMAT=image/png&REQUEST=GetMap&HEIGHT=%d&FORMAT_OPTIONS=dpi:96&WIDTH=%d&VERSION=1.1.1&BBOX=%s&STYLES=&TRANSPARENT=TRUE&DPI=96'%('default', self.srs, 150, 110, self.dame_extent(',','3857'))
        elif self.tipo_de_mapa=='layer_original_srs':
            c=self.capas.first()
            wms_url += '&LAYERS=%s&SRS=epsg:%s&MAP_RESOLUTION=96&SERVICE=WMS&FORMAT=image/png&REQUEST=GetMap&HEIGHT=%d&FORMAT_OPTIONS=dpi:96&WIDTH=%d&VERSION=1.1.1&BBOX=%s&STYLES=&TRANSPARENT=TRUE&DPI=96'%(c.nombre, str(c.srid), 150, 110, c.dame_extent())
            try:
                sld=c.archivosld_set.filter(default=True)[0]
                wms_url+='&sld=%s'%(urlparse.urljoin(settings.SITE_URL, sld.filename.url))
            except:
                pass 
        #print wms_url
        thumb=os.path.join(settings.MEDIA_ROOT, self.id_mapa+'.png')
        return urlToFile(wms_url, thumb)
        # try:
        #     proxy = urllib2.ProxyHandler({})
        #     opener = urllib2.build_opener(proxy)
        #     urllib2.install_opener(opener)

        #     with open(thumb,'wb') as f:
        #         f.write(urllib2.urlopen(wms_url).read())
        #         f.close()
        #     return thumb
        # except:
        #     print "Error generando preview de mapa %s"%(self.id_mapa)
        #     return ''

    def generar_legend(self):
        # capa = self.capas.first()
        mapfile=ManejadorDeMapas.get_mapfile(self.id_mapa)
        filelist = []
        for mslayer in self.mapserverlayer_set.all():
            try:
                sld = urlparse.urljoin(settings.SITE_URL, mslayer.archivo_sld.filename.url) if mslayer.archivo_sld else mslayer.capa.dame_sld_default()
                url = MAPSERVER_URL+'?map='+mapfile +'&SERVICE=WMS&VERSION=1.3.0&SLD_VERSION=1.1.0&REQUEST=GetLegendGraphic&FORMAT=image/png&LAYER=%s&STYLE=&SLD=%s'%(mslayer.capa.nombre,sld)
                filename=os.path.join(settings.MEDIA_ROOT, self.id_mapa+('_legend_%i.png'%mslayer.orden_de_capa))
                filelist.append(filename)
                urlToFile(url, filename)
            except:
                return False
        try:
            call('convert %s -background "rgba(0,0,0,0)" -append %s'%(' '.join(filelist), os.path.join(settings.MEDIA_ROOT, self.id_mapa+'_legend.png')), shell=True)
        except:
            return False
        for filename in filelist:
            try:
                os.remove(filename)
            except:
                return False
        return True

    objects = SearchManager(
        fields = ('input_search_index',), # esa coma final debe ir si o si
        config = 'pg_catalog.spanish', # this is default
        search_field = 'search_index', # this is default
        auto_update_search_field = True
    )    
            
class MapServerLayer(models.Model):
    capa = models.ForeignKey(Capa,null=False,blank=False)
    mapa = models.ForeignKey(Mapa)
    orden_de_capa = models.IntegerField(null=False)
    feature_info = models.BooleanField(u'Feature Info', null=False, default=True)
    archivo_sld = models.ForeignKey(ArchivoSLD, null=True, blank=True, on_delete=models.SET_NULL) 
    
    texto_input = models.TextField(u'Texto Input', null=False, blank=True, max_length=10000)
    texto_output = models.TextField(u'Texto Output', null=False, blank=True, max_length=10000)
    class Meta:
        verbose_name = 'MapServer Layer'
        verbose_name_plural = 'MapServer Layers'
    def __unicode__(self):
        return '%s.%s (%s)'%(unicode(self.mapa),unicode(self.capa),unicode(self.orden_de_capa))

    @property
    def dame_layer_type(self):
        return eval('mapscript.MS_LAYER_'+self.capa.tipo_de_geometria.mapserver_type) #medio feo...

    def dame_data(self, srid=None):
        if srid!=None:
            return "geom_proj from (select *, st_transform(%s, %d) as geom_proj from %s.%s) aa using unique gid using srid=%d"%(self.capa.campo_geom,srid,self.capa.esquema,self.capa.tabla,srid)
        else:
            return "%s from %s.%s"%(self.capa.campo_geom,self.capa.esquema,self.capa.tabla)

    def save(self, srid=None, *args, **kwargs):
        if self.archivo_sld is not None and self.archivo_sld.capa != self.capa:
            self.archivo_sld = None
        # innecesario por el momento
#         try:
#             mslo=self.dame_mapserver_layerObj()
#             self.texto_output=mslo.convertToString()
#         except:
#             self.texto_output=''
        super(MapServerLayer, self).save(*args, **kwargs)
        ManejadorDeMapas.delete_mapfile(self.mapa.id_mapa)
        return True


    
    def dame_mapserver_layerObj(self, connectiontype='POSTGIS'):
        layer = mapscript.layerObj()
        layer.name=self.capa.nombre
        layer.status = mapscript.MS_ON
        layer.group = 'default' #siempre        
        layer.template = 'blank.html' 
                
        if connectiontype=='WMS':
            layer.type=mapscript.MS_LAYER_RASTER
            layer.connectiontype = mapscript.MS_WMS
            layer.connection = '%s?map=%s.map'%(MAPSERVER_URL, os.path.join(settings.MAPAS_PATH, self.capa.id_capa))
            
            layer.setMetaData('wms_srs', 'epsg:3857')
            layer.setMetaData('wms_name', self.capa.nombre)
            layer.setMetaData('wms_server_version', '1.1.1')
            layer.setMetaData('wms_format', 'image/png')
            if self.archivo_sld is not None:
                layer.setMetaData('wms_sld_url', (urlparse.urljoin(settings.SITE_URL, self.archivo_sld.filename.url)))
        
        elif connectiontype=='POSTGIS':
            layer.type=self.dame_layer_type
            
            # layer.sizeunits = mapscript.MS_INCHES
            layer.addProcessing('LABEL_NO_CLIP=ON') 
            layer.addProcessing('CLOSE_CONNECTION=DEFER')
            layer.connectiontype = mapscript.MS_POSTGIS
            layer.connection = self.capa.dame_connection_string
    
            srid = 4326 if self.mapa.tipo_de_mapa in ('public_layers','user') and self.capa.srid!=4326 else None
            layer.data = self.dame_data(srid)
            #proj='epsg:%s'%(unicode(srid)) if srid!=None else self.capa.dame_projection
            proj=unicode(srid) if srid!=None else self.capa.dame_projection
            if proj!='':
                layer.setProjection('epsg:%s'%(proj))
            
            layer.setMetaData('ows_title', self.capa.dame_titulo.encode('utf-8'))
            layer.setMetaData('gml_types', 'auto')
            #layer.setMetaData('ows_srs','%s epsg:4326'%(proj)) # este campo lo llena el mapa 
            layer.setMetaData('gml_include_items','all') # por ahora queda asi, y ademas se suman los campos especificos
            layer.setMetaData('gml_featureid','gid') 
            layer.setMetaData('wms_enable_request', '*')
            layer.setMetaData('wfs_enable_request', '*')
            include_items, items_aliases = self.capa.metadatos.dame_gml_atributos() #TODO: revisar condiciones sobre item aliases
            if len(include_items)>0:
                layer.setMetaData('gml_include_items',','.join(include_items))
            for alias in items_aliases:
                layer.setMetaData('gml_%s_alias'%(alias[0]),alias[1])
            
            if self.texto_input!='':
                try:
                    layer.updateFromString(self.texto_input)
                except:
                    pass
            else:
                self.agregar_simbologia_basica(layer)
        return layer

    def agregar_simbologia_basica(self, layer):
        class1 = mapscript.classObj(layer)
        class1.name = 'Default'
        style = mapscript.styleObj(class1)
        if layer.type==mapscript.MS_LAYER_POINT:
            style.symbolname='circle'
            style.size=8
            style.minsize=8
            style.maxsize=10
            style.maxwidth=2
            style.outlinecolor.setRGB(0, 0, 255)
            style.color.setRGB(150, 150, 150)
        elif layer.type==mapscript.MS_LAYER_POLYGON:
            style.outlinecolor.setRGB(250, 50, 50)
            style.color.setRGB(150, 150, 150)
        elif layer.type==mapscript.MS_LAYER_LINE:
            style.color.setRGB(80, 80, 80)
            style.width=4
            style.minwidth=4
            style.maxwidth=6
            style2 = mapscript.styleObj(class1)
            style2.color.setRGB(255, 255, 0)
            style2.width=2
            style2.minwidth=2
            style2.maxwidth=4

                


@receiver(post_save, sender=Capa)
def onCapaPostSave(sender, instance, created, **kwargs):
    print 'onCapaPostSave %s'%(str(instance))
    if created:
        print '...capa creada'
        # ------------ creamos y completamos metadatos y atributos
        metadatos = Metadatos.objects.create(capa=instance,titulo=instance.nombre)        
        # devuelve <att_num, campo, tipo, default_value, uniq, pk>
        cursor = connection.cursor()
        cursor.execute("SELECT * from utils.campos_de_tabla(%s,%s)", [instance.esquema, instance.tabla])
        rows = cursor.fetchall()
        for r in rows:
            Atributo.objects.create(nombre_del_campo=r[1], tipo=r[2], unico=r[4], metadatos=metadatos)

        # ------------ creamos/actualizamos mapas
        # creamos el mapa canónico
        mapa = Mapa(owner=instance.owner,nombre=instance.nombre,id_mapa=instance.id_capa, tipo_de_mapa='layer')
        mapa.save(escribir_imagen_y_mapfile=False)
        MapServerLayer(mapa=mapa,capa=instance,orden_de_capa=0).save()
        mapa.save()

        # creamos el mapa en la proyeccion original
        extent_capa = instance.dame_extent(',', instance.srid)
        mapa_layer_srs = Mapa(owner=instance.owner,nombre=instance.nombre+'_layer_srs',id_mapa=instance.id_capa+'_layer_srs', tipo_de_mapa='layer_original_srs', srs=instance.srid, extent=extent_capa)
        mapa_layer_srs.save(escribir_imagen_y_mapfile=False)
        MapServerLayer(mapa=mapa_layer_srs,capa=instance,orden_de_capa=0).save()
        mapa_layer_srs.save()

        # actualizamos el mapa de usuario
        ManejadorDeMapas.delete_mapfile(instance.owner.username)
        
#         #mapa_usuario, created = Mapa.objects.get_or_create(owner=instance.owner,nombre=instance.owner.username,id_mapa=instance.owner.username, tipo_de_mapa='user')
#         try:
#             mapa_usuario=Mapa.objects.get(owner=instance.owner,nombre=instance.owner.username,id_mapa=instance.owner.username, tipo_de_mapa='user')
#         except:
#             mapa_usuario=Mapa(owner=instance.owner,nombre=instance.owner.username,id_mapa=instance.owner.username, tipo_de_mapa='user')
#             mapa_usuario.save(escribir_imagen_y_mapfile=False)
#         MapServerLayer(mapa=mapa_usuario,capa=instance,orden_de_capa=len(mapa_usuario.capas.all())+1).save() 
#         mapa_usuario.save()


        # actualizamos el mapa de capas públicas
        ManejadorDeMapas.delete_mapfile('mapground_public_layers')
    else:
        print '...capa actualizada (ya existia)'
        # actualizamos los mapas relacionados con la capa
        ManejadorDeMapas.delete_mapfile('mapground_public_layers')
        for m in instance.mapa_set.filter(tipo_de_mapa__in=['layer','layer_original_srs','general']):
            ManejadorDeMapas.delete_mapfile(m.id_mapa)
        for m in Mapa.objects.all().filter(tipo_de_mapa='user'):
            ManejadorDeMapas.delete_mapfile(m.id_mapa)            

@receiver(post_delete, sender=MapServerLayer)
def onMapServerLayerPostDelete(sender, instance, **kwargs):
    print 'onMapServerLayerPostDelete %s'%(str(instance))
    ManejadorDeMapas.delete_mapfile(instance.mapa.id_mapa)

@receiver(post_delete, sender=Capa)
def onCapaPostDelete(sender, instance, **kwargs):
    print 'onCapaPostDelete %s'%(str(instance))
    try:
        Mapa.objects.get(id_mapa=instance.id_capa,tipo_de_mapa='layer').delete()
    except:
        pass
    try:
        Mapa.objects.get(id_mapa=instance.id_capa+'_layer_srs',tipo_de_mapa='layer_original_srs').delete()
    except:
        pass
    try:
        TablaGeografica.objects.filter(tabla=instance.id_capa)[0].delete()
    except:
        pass

@receiver(post_delete, sender=Mapa)
def onMapaPostDelete(sender, instance, **kwargs):
    print 'onMapaPostDelete %s'%(str(instance))
    if instance.tipo_de_mapa == 'layer':
        manage.remove([instance.id_mapa])
    try:
        os.remove(os.path.join(settings.MAPAS_PATH, instance.id_mapa+'.map'))
    except:
        pass
    try: # deberia borrar solo si tipo_de_mapa in ['layer_original_srs', 'general']
        os.remove(os.path.join(settings.MEDIA_ROOT, instance.id_mapa+'.png'))
    except:
        pass    


def generarThumbnailSLD(capa, sld):
    e = map(float, capa.dame_extent(',', 3857).split(','))
    ex = e[2]-e[0]
    ey = e[3]-e[1]
    z = (ey - ex)/2 if ey > ex else (ex - ey)/2
    e2 = [e[0], e[1]+z, e[2], e[3]-z] if ey > ex else [e[0]+z, e[1], e[2]-z, e[3]]
    extent = ','.join(map(str, e2))
    sld_url = urlparse.urljoin(settings.SITE_URL, sld.filename.url)
    mapfile = ManejadorDeMapas.get_mapfile(capa.id_capa)
    wms_url = '%s?map=%s&LAYERS=%s&SRS=epsg:3857&MAP_RESOLUTION=96&SERVICE=WMS&FORMAT=image/png&REQUEST=GetMap&HEIGHT=%d&FORMAT_OPTIONS=dpi:96&WIDTH=%d&VERSION=1.1.1&BBOX=%s&STYLES=&TRANSPARENT=TRUE&DPI=96&sld=%s'%(MAPSERVER_URL, mapfile, capa.nombre, 150, 150, extent, sld_url)
    print wms_url
    thumb = os.path.splitext(sld.filename.path)[0]+'.png'
    try:
        urllib.urlretrieve(wms_url, thumb)
    except:
        print "Error generando preview de capa con SLD!!!"
    

@receiver(post_save, sender=ArchivoSLD)
def onArchivoSLDPostSave(sender, instance, **kwargs):
    print 'onArchivoSLDPostSave %s'%(str(instance))
    if instance.default:
        q=ArchivoSLD.objects.filter(capa=instance.capa).exclude(pk=instance.pk)
        q.update(default=False)
    if time.time()-os.path.getctime(instance.filename.path) < 3:
        try:
            # Nos aseguramos que el nombre de la capa en el SLD sea el correcto.
            print "Actualizando nombre de capa en el SLD: %s"%instance.filename.path
            tree = etree.parse(instance.filename.path)
        except:
            print "Error tratando de abrir archivo SLD: %s"%instance.filename.path
        try:
            root = tree.getroot()
            root.findall('*/{http://www.opengis.net/se}Name')[0].text = instance.capa.nombre
            sizes = root.findall('.//{http://www.opengis.net/se}Size')
            for s in sizes:
                s.text = str(float(s.text)*3.5)
            stroke_widths = root.findall(".//{http://www.opengis.net/se}SvgParameter[@name='stroke-width']")
            for s in stroke_widths:
                s.text = str(float(s.text)*3.5)
            properties = root.findall('.//{http://www.opengis.net/ogc}PropertyName')
            for p in properties:
                p.text = p.text.lower()
            tree.write(instance.filename.path, encoding='utf-8')
        except:
            print "Error tratando de escribir SLD"
    else:
        print "No se modifico el SLD"
    generarThumbnailSLD(instance.capa, instance) # siempre
    instance.capa.save()
    ManejadorDeMapas.generar_thumbnail(instance.capa.id_capa+'_layer_srs')

@receiver(post_delete, sender=ArchivoSLD)
def onArchivoSLDPostDelete(sender, instance, **kwargs):
    print 'onArchivoSLDPostDelete %s'%(str(instance))
    instance.capa.save()
    if instance.default:
        ManejadorDeMapas.generar_thumbnail(instance.capa.id_capa+'_layer_srs')        
    try:
        os.remove(os.path.splitext(instance.filename.path)[0]+'.png')
        os.remove(os.path.join(settings.MEDIA_ROOT, instance.filename.name))
    except:
        pass
        