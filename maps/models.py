# -*- coding: utf-8 -*-
# from __future__ import unicode_literals   # NO DESCOMENTAR! ROMPE TODO!

from django.db import models, connection, connections
from django.contrib.auth.models import User
from django.conf import settings
# import mapscript
from layerimport.models import TablaGeografica, ArchivoRaster
from layers.models import Capa, Categoria, Metadatos, Atributo, ArchivoSLD, Escala, CONST_VECTOR, CONST_RASTER
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
import urlparse
import urllib
import urllib2
import time
from lxml import etree
from subprocess import call
from utils import mapserver
from mapcache import mapcache
from .tasks import add_tileset, rm_tileset, add_or_replace_tileset

MAPA_DEFAULT_SRS = 3857
MAPA_DEFAULT_SIZE = (110, 150)
MAPA_DEFAULT_IMAGECOLOR = '#C6E2F2' # debe ser formato Hexa

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
    def delete_mapfile(cls, id_mapa):
        print "...ManejadorDeMapas.delete_mapfile %s"%(id_mapa)
        try:
             mapa=Mapa.objects.get(id_mapa=id_mapa)
        # if instance.tipo_de_mapa == 'layer':
        #     manage.remove([instance.id_mapa])
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
    def commit_mapfile(cls,id_mapa):
        print "ManejadorDeMapas.commit_mapfile: %s" %(id_mapa)
        mapfile_full_path=os.path.join(settings.MAPAS_PATH, id_mapa+'.map')
        if not os.path.isfile(mapfile_full_path):
            if id_mapa=='mapground_public_layers':
                cls.regenerar_mapa_publico()
            else:
                try:
                    mapa=Mapa.objects.get(id_mapa=id_mapa)
                except:
                    print "....ManejadorDeMapas.commit_mapfile: ERROR: mapa inexistente %s" %(mapfile_full_path) 
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
            msm=self.createMapfile(False)
            self.texto_output=msm.convertToString()[0:9999]
        except:
            self.texto_output=''
        if self.tipo_de_mapa=='general':
            self.actualizar_input_search_index()
        super(Mapa, self).save(*args, **kwargs)
        if escribir_imagen_y_mapfile:
            self.create_mapfile(True)
            self.generar_thumbnail_y_legend()
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

    @property
    def dame_wxs_url(self):
        if self.tipo_de_mapa=='public_layers':
            return urlparse.urljoin(settings.SITE_URL,'layers/public_wxs/')
        elif self.tipo_de_mapa=='user':
            return urlparse.urljoin(settings.SITE_URL, 'users/'+self.owner.username+'/wxs/')
        elif self.tipo_de_mapa=='layer_original_srs':
            return urlparse.urljoin(settings.WXS_ONLINERESOURCE,unicode(self.id_mapa.replace('_layer_srs',''))+'/')

        return urlparse.urljoin(settings.WXS_ONLINERESOURCE,unicode(self.id_mapa)+'/')

    def dame_mapserver_map_def(self):
        es_hexa, color = self.dame_imagecolor
        srid = self.dame_projection
        bbox = self.dame_extent(',', srid)
        mapExtent = self.dame_mapserver_extent(int(srid))
        wxs_url = self.dame_wxs_url
        layers = []
        if self.tipo_de_mapa in ('layer', 'layer_original_srs', 'user', 'general'):
            mapserverlayers = self.mapserverlayer_set.all().order_by('orden_de_capa','capa__metadatos__titulo')
        else:  # 'public_layers'
            mapserverlayers = self.mapserverlayer_set.filter(capa__wxs_publico=True).order_by('orden_de_capa')
        for msl in mapserverlayers:
            if self.tipo_de_mapa=='general':
                l=msl.dame_mapserver_layer_def('WMS')
            else:
                l=msl.dame_mapserver_layer_def(msl.dame_layer_connection_type())
                l['metadata']['ows_srs'] = 'epsg:%s epsg:4326'%(srid)
            layers.append(l)
        data = {
            "idMapa": self.id_mapa,
            "imageColor": {
                "type": "hex" if es_hexa else "rgb",
                "color": color
            },
            "srid": srid,
            "mapFullExtent": mapExtent,
            "mapBoundingBox": map(lambda x: float(x), bbox.split(',')) if bbox!="" else mapExtent,
            "mapSize": self.dame_mapserver_size,
            "fileName": self.dame_filename,
            "mapType": self.tipo_de_mapa,
            "metadata": {
                "ows_title": unicode(self.dame_titulo).encode('UTF-8'),
                "ows_abstract": unicode(self.dame_descripcion.replace('\r\n', ' ')).encode('UTF-8'),
                "ows_attribution_title": unicode(self.dame_fuente.replace('\r\n', ' ')).encode('UTF-8'),
                "ows_contactorganization": unicode(self.dame_contacto.replace('\r\n', ' ')).encode('UTF-8'),
                "wms_onlineresource": wxs_url,
                "wfs_onlineresource": wxs_url,
                "mg_onlineresource": unicode(self.dame_tilesurl).encode('UTF-8'),
                "mg_siteurl": unicode(settings.SITE_URL).encode('UTF-8'),
                "mg_baselayerurl": self.tms_base_layer.url if self.tms_base_layer else settings.MAPCACHE_URL+'tms/1.0.0/world_borders@GoogleMapsCompatible/{z}/{x}/{y}.png',
                "mg_tmsbaselayer": str(self.tms_base_layer.tms) if self.tms_base_layer else str(True),
                "mg_mapid": unicode(self.id_mapa),
                "ows_srs": 'epsg:%s epsg:4326'%(srid), # dejamos proyecciones del mapa y 4326 fijas. esta logica la repetimos en las capas 
                "wfs_getfeature_formatlist": 'geojson,shapezip,csv',
                "ows_encoding": 'UTF-8', # siempre
                "ows_enable_request": '*',
                "labelcache_map_edge_buffer": '-10'
            },
            "layers": layers
        }
        
        return data

    def create_mapfile(self, save=True):
        return mapserver.create_mapfile(self.dame_mapserver_map_def(), save)

    def generar_thumbnail_y_legend(self):
        print '...Grabando mapa e imagen de %s (tipo %s)'%(self.id_mapa, self.tipo_de_mapa)
        # mapa=self.dame_mapserver_mapObj()
        # mapa.save(os.path.join(settings.MAPAS_PATH, self.id_mapa+'.map'))
        # print "......mapa guardado %s"%(self.id_mapa+'.map')
        if self.tipo_de_mapa in ('layer_original_srs', 'general'):
            thumb = self.generar_thumbnail()
            print "......imagen creada: %s"%(thumb)
        if self.tipo_de_mapa in ('general', 'layer'):
            self.generar_legend()
        return True

    def agregar_a_mapcache(self):
        # rm_tileset(self.id_mapa)
        # Si estamos en una arquitectura distribuida los tiles son locales
        mapcache.remove_tileset(self.id_mapa)
        sld_url = ''
        srid = MAPA_DEFAULT_SRS
        if self.tipo_de_mapa == 'layer':
            capa = self.mapserverlayer_set.first().capa
            # params = ':%s:%d'%(capa.nombre, MAPA_DEFAULT_SRS)
            layers = capa.nombre
            srid = MAPA_DEFAULT_SRS
            for sld in capa.archivosld_set.all():
                # mapcache.remove_map(self.id_mapa, sld.id)
                # rm_tileset(self.id_mapa, sld.id)
                # Si estamos en una arquitectura distribuida los tiles son locales
                mapcache.remove_tileset(self.id_mapa, sld.id)
                sld_url = urlparse.urljoin(settings.SITE_URL, sld.filename.url)
                # mapcache.add_map(self.id_mapa, layers, srid, sld.id, sld_url)
                add_or_replace_tileset(self.id_mapa, layers, srid, sld.id, sld_url)
        elif self.tipo_de_mapa == 'general':
            layers = 'default'
                
        # mapcache.add_map(self.id_mapa, layers, srid, '', sld_url)
        add_or_replace_tileset(self.id_mapa, layers, srid, '', sld_url)

    def generar_thumbnail(self):
        mapfile=ManejadorDeMapas.commit_mapfile(self.id_mapa)
        if self.tipo_de_mapa == 'general':
            for c in self.capas.all():  # es necesario regenerar todo mapfile inexistente
                ManejadorDeMapas.commit_mapfile(c.id_capa)
            wms_url = mapserver.get_wms_request_url(self.id_mapa, 'default', self.srs, 110, 150, self.dame_extent(',','3857'))
        elif self.tipo_de_mapa=='layer_original_srs':
            c=self.capas.first()
            wms_url = mapserver.get_wms_request_url(self.id_mapa, c.nombre, str(c.srid), 110, 150, c.dame_extent(',', self.srs))
            try:
                sld=c.archivosld_set.filter(default=True)[0]
                sld_url = getSldUrl(sld.filename.url)
                wms_url = mapserver.get_wms_request_url(self.id_mapa, c.nombre, str(c.srid), 110, 150, c.dame_extent(',', self.srs), sld_url)
            except:
                pass 
        print wms_url
        thumb=os.path.join(settings.MEDIA_ROOT, self.id_mapa+'.png')
        return urlToFile(wms_url, thumb)

    def generar_legend(self):
        # capa = self.capas.first()
        mapfile=ManejadorDeMapas.commit_mapfile(self.id_mapa)
        filelist = []
        for mslayer in self.mapserverlayer_set.all():
            sld = urlparse.urljoin(settings.SITE_URL, mslayer.archivo_sld.filename.url) if mslayer.archivo_sld else mslayer.capa.dame_sld_default()
            url = mapserver.get_legend_graphic_url(self.id_mapa, mslayer.capa.nombre, sld)
            filename=os.path.join(settings.MEDIA_ROOT, self.id_mapa+('_legend_%i.png'%mslayer.orden_de_capa))
            filelist.append(filename)
            try:
                urlToFile(url, filename)
            except:
                print '\nFailed to create legend file %s\n'%filename
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

    def dame_layer_connection(self, connectiontype):
        if connectiontype == 'WMS':
            return mapserver.get_wms_url(self.capa.id_capa)
        else:
            return self.capa.dame_connection_string

    def dame_layer_connection_type(self):
        return self.capa.dame_connection_type

    def dame_data(self, srid=None):
        return self.capa.dame_data(srid)

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

    def dame_mapserver_layer_def(self, connectiontype='POSTGIS'):
        include_items, items_aliases = self.capa.metadatos.dame_gml_atributos()
        srid = 4326 if self.mapa.tipo_de_mapa in ('public_layers','user') and self.capa.srid!=4326 else int(self.capa.dame_projection)
        if self.capa.tipo_de_capa == CONST_VECTOR:
            data = {
                "connectionType": connectiontype,
                "layerName": self.capa.nombre,
                "layerTitle": self.capa.dame_titulo.encode('utf-8'),
                "layerConnection": self.dame_layer_connection(connectiontype),
                "layerData": self.dame_data(srid),
                "sldUrl": (urlparse.urljoin(settings.SITE_URL, self.archivo_sld.filename.url)) if self.archivo_sld is not None else "",
                "layerType": 'RASTER' if connectiontype == 'WMS' else self.capa.tipo_de_geometria.mapserver_type,
                "srid": srid,
                "metadataIncludeItems": include_items,
                "metadataAliases": items_aliases,
                "layerDefinitionOverride": self.texto_input,
                "metadata": {}
            }
        elif self.capa.tipo_de_capa == CONST_RASTER:
            data = {
                "connectionType": connectiontype,
                "layerName": self.capa.nombre,
                "layerTitle": self.capa.dame_titulo.encode('utf-8'),
                "layerConnection": self.dame_layer_connection(connectiontype),
                "layerData": self.dame_data(srid),
                "sldUrl": (urlparse.urljoin(settings.SITE_URL, self.archivo_sld.filename.url)) if self.archivo_sld is not None else "",
                "layerType": 'RASTER',
                "srid": srid,
                "metadataIncludeItems": include_items,
                "metadataAliases": items_aliases,
                "layerDefinitionOverride": self.texto_input,
                "metadata": {}
            }

        return data


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
        if instance.tipo_de_capa == CONST_RASTER:
            try:
                print "Intentando setear baselayer..."
                mapa.tms_base_layer=TMSBaseLayer.objects.get(pk=1)
            except:
                pass
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
    if instance.tipo_de_capa == CONST_VECTOR:
        try:
            TablaGeografica.objects.filter(tabla=instance.id_capa)[0].delete()
        except:
            pass
    elif instance.tipo_de_capa == CONST_RASTER:
        try:
            ArchivoRaster.objects.filter(nombre_del_archivo=instance.nombre_del_archivo, owner=instance.owner)[0].delete()
        except:
            pass

@receiver(post_delete, sender=Mapa)
def onMapaPostDelete(sender, instance, **kwargs):
    print 'onMapaPostDelete %s'%(str(instance))
    if instance.tipo_de_mapa == 'layer':
        # manage.remove([instance.id_mapa])
        mapcache.remove_map(instance.id_mapa)
    try:
        os.remove(os.path.join(settings.MAPAS_PATH, instance.id_mapa+'.map'))
    except:
        pass
    try:  # deberia borrar solo si tipo_de_mapa in ['layer_original_srs', 'general']
        os.remove(os.path.join(settings.MEDIA_ROOT, instance.id_mapa + '.png'))
    except:
        pass

def getSldUrl(sld_file_url):
    return urlparse.urljoin(settings.SITE_URL, sld_file_url)

def generarThumbnailSLD(capa, sld):
    e = map(float, capa.dame_extent(',', 3857).split(','))
    ex = e[2]-e[0]
    ey = e[3]-e[1]
    z = (ey - ex)/2 if ey > ex else (ex - ey)/2
    e2 = [e[0], e[1]+z, e[2], e[3]-z] if ey > ex else [e[0]+z, e[1], e[2]-z, e[3]]
    extent = ','.join(map(str, e2))
    sld_url = getSldUrl(sld.filename.url)
    mapfile = ManejadorDeMapas.commit_mapfile(capa.id_capa)
    wms_url = mapserver.get_wms_request_url(capa.id_capa, capa.nombre, '3857', 150, 150, extent, sld_url)
    print wms_url
    thumb = os.path.splitext(sld.filename.path)[0]+'.png'
    try:
        urllib.urlretrieve(wms_url, thumb)
    except:
        print "Error generando preview de capa con SLD!!!"

@receiver(post_save, sender=ArchivoSLD)
def onArchivoSLDPostSave(sender, instance, created, **kwargs):
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
            # sizes = root.findall('.//{http://www.opengis.net/se}Size')
            # for s in sizes:
            #     s.text = str(float(s.text)*3.5)
            # stroke_widths = root.findall(".//{http://www.opengis.net/se}SvgParameter[@name='stroke-width']")
            # for s in stroke_widths:
            #     s.text = str(float(s.text)*3.5)
            properties = root.findall('.//{http://www.opengis.net/ogc}PropertyName')
            for p in properties:
                p.text = p.text.lower()
            tree.write(instance.filename.path, encoding='utf-8')
        except:
            print "Error tratando de escribir SLD"
    else:
        print "No se modifico el SLD"
    generarThumbnailSLD(instance.capa, instance)  # siempre
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
