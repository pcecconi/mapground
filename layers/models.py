# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# core
from django.conf import settings
from django.db import connection
# slugs
from django.utils.text import slugify
# signals
from django.db.models.signals import post_save, pre_save  # , post_delete
from django.dispatch import receiver
# fts
from djorm_pgfulltext.models import SearchManager
from djorm_pgfulltext.fields import VectorField
# mapscript
# misc
import os
from utils.commons import normalizar_texto
# from mapcache.settings import MAPSERVER_URL
import urlparse
# from lxml import etree

# geodjango
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.contrib.gis.gdal import GDALRaster
from django_extras.contrib.auth.models import SingleOwnerMixin

CONST_VECTOR = 'vector'
CONST_RASTER = 'raster'

TIPO_DE_CAPA_ENUM = (
    (CONST_VECTOR, CONST_VECTOR),
    (CONST_RASTER, CONST_RASTER),
)


class TipoDeGeometria(models.Model):
    nombre = models.CharField('Nombre', null=False, blank=False, unique=True, max_length=50)  # Punto/Linea/Poligono/Raster
    postgres_type = models.CharField('Postgres Type', null=False, blank=False, max_length=100)  # Point/LineString/Polygon/"Raster"
    mapserver_type = models.CharField('Mapserver Type', null=False, blank=False, max_length=50)  # POINT/LINE/POLYGON/RASTER

    class Meta:
        verbose_name = u'Tipo de Geometría'
        verbose_name_plural = u'Tipos de Geometría'

    def __unicode__(self):
        return unicode(self.nombre)


# TODO: el save de esta clase debe garantizar datos minimos necesarios de raster o bin de vector
class Capa(SingleOwnerMixin, models.Model):
    nombre = models.CharField('Nombre', null=False, blank=False, max_length=255)  # puede repetirse para distintos usuarios
    id_capa = models.CharField('Id capa', null=False, blank=False, unique=True, max_length=255)
    slug = models.SlugField('Slug', null=False, blank=True, max_length=255)

    # vector/raster?
    tipo_de_capa = models.CharField('Tipo de capa', choices=TIPO_DE_CAPA_ENUM, default=CONST_VECTOR, max_length=10, null=False, blank=False)
    tipo_de_geometria = models.ForeignKey('TipoDeGeometria', null=False, blank=False)  # read_only  #TODO: esto cambio

    # si es raster...
    nombre_del_archivo = models.CharField('Nombre del archivo', null=True, default=True, max_length=255)

    # si es vector...
    conexion_postgres = models.ForeignKey('ConexionPostgres', null=True, blank=True)
    esquema = models.CharField('Esquema', null=True, blank=True, max_length=100)  # TODO: esto cambio
    tabla = models.CharField('Tabla', null=True, blank=True, max_length=100)  # TODO: esto cambio
    campo_geom = models.CharField(u'Campo de Geometría', null=True, blank=True, max_length=30, default='geom')  # read_only  # TODO: esto cambio
    cantidad_de_registros = models.IntegerField('Cantidad de registros', null=True, blank=True)  # read_only, 0 a n para vector, None para raster
    srid = models.IntegerField('SRID', null=False, blank=False)
    extent_minx_miny = models.PointField('(Minx, Miny)', null=True, blank=True)  # extent en 4326 calculado por postgres en el signal de creacion
    extent_maxx_maxy = models.PointField('(Maxx, Maxy)', null=True, blank=True)  # extent en 4326 calculado por postgres en el signal de creacion
    layer_srs_extent = models.CharField('Original SRS Extent', null=False, blank=False, max_length=255, default='')  # extent en el srid original calculado por postgres en el signal de creacion

    # publico? TODO: me parece mejor modelarlo aparte ya que es el unico atributo variable
    wxs_publico = models.BooleanField(u'WMS/WFS Público?', null=False, default=False)

    # automaticos...
    timestamp_alta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de alta')
    timestamp_modificacion = models.DateTimeField(auto_now=True, verbose_name='Fecha de última modificación')
    objects = models.GeoManager()

    class Meta:
        # unique_together = (('esquema', 'tabla'),)  # ya no puede serlo por permitir nulos
        verbose_name = 'Capa'
        verbose_name_plural = 'Capas'

    def __unicode__(self):
        return unicode(self.nombre)

    @property
    def dame_titulo(self):
        return self.metadatos.titulo if self.metadatos.titulo != '' else self.nombre

    @property
    def dame_projection(self):
        return unicode(self.srid)

    @property
    def dame_descripcion(self):
        if self.metadatos.descripcion == '':
            return u'Sin descripción'
        else:
            return self.metadatos.descripcion
        # TODO: sacar de epok/commons.py funcion que trunca sin cortar palabras

    @property
    def dame_fuente(self):
        return self.metadatos.fuente

    @property
    def dame_contacto(self):
        return self.metadatos.contacto

    @property
    def dame_connection_string(self):
        if self.conexion_postgres is None:
            return settings.DEFAULT_DB_CONNECTION_STRING
        else:
            return self.conexion_postgres.dame_connection_string

    def dame_data(self, srid=None):
        if self.tipo_de_capa == CONST_VECTOR:
            if srid is not None:
                return "geom_proj from (select *, st_transform(%s, %d) as geom_proj from %s.%s) aa using unique gid using srid=%d" % (self.campo_geom, srid, self.esquema, self.tabla, srid)
            else:
                return "%s from %s.%s" % (self.campo_geom, self.esquema, self.tabla)
        elif self.tipo_de_capa == CONST_RASTER:
            print 'DATA ES:', settings.UPLOADED_RASTERS_PATH + unicode(self.owner) + '/' + self.nombre_del_archivo
            return settings.UPLOADED_RASTERS_PATH + unicode(self.owner) + '/' + self.nombre_del_archivo


    def dame_extent(self, separador=',', srid=4326):
        # heuristica para arreglar thumbnails: corta por la mitad a la antartida (lo maximo es -90)
        # print 'layer.dame_extent(srid=%i), original srid: %i'%(srid, self.srid)
        if srid == self.srid:
            return self.layer_srs_extent.replace(' ', separador)
        if srid == 3857:
            if self.extent_minx_miny.y < -70:
                self.extent_minx_miny.y = -70
        min = self.extent_minx_miny.transform(srid, clone=True)
        max = self.extent_maxx_maxy.transform(srid, clone=True)
        if separador == []:
            return [min, max]
        else:
            return separador.join([str(min.x), str(min.y)]) + separador + separador.join([str(max.x), str(max.y)])

    @property
    def dame_datos(self):
        if self.tipo_de_capa == CONST_RASTER:
            return None
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT %s from %s.%s limit 100" % (','.join(map(lambda x: '\"%s\"' % x, self.metadatos.dame_nombres_atributos())), self.esquema, self.tabla))
        except:
            cursor.execute("SELECT * from %s.%s limit 100" % (self.esquema, self.tabla))
        rows = cursor.fetchall()
        return rows

    def dame_sld_default(self):
        slds = self.archivosld_set.filter(default=True)
        if len(slds) > 0:
            default_sld = slds[0].filename.url
            return urlparse.urljoin(settings.SITE_URL, default_sld)
        return None

    def actualizar_atributos(self):
        cursor = connection.cursor()
        cursor.execute("SELECT * from utils.campos_de_tabla(%s,%s)", [self.esquema, self.tabla])
        rows = cursor.fetchall()
        for r in rows:
            try:
                attr = self.metadatos.atributo_set.get(nombre_del_campo=r[1])
                attr.tipo = r[2]
                attr.save()
            except:
                pass

    def save(self, *args, **kwargs):
        # TODO: pensar: vamos a permitir que una capa pueda cambiar su nombre? esto cambaria el id con el tiempo, hay que actualizar las referencias en los mapfiles....si no queremos, hay que hacer algun truco:dirtyfields,compararcontra la base,etc
        # if self.slug == '':
        #     self.slug=slugify(unicode(self.nombre)).replace("-", "_")
        self.slug = slugify(unicode(self.nombre)).replace('-', '_')
        # el id_capa lo setea la aplicacion que hace el upload
        # self.id_capa=self.owner.username+'_'+self.slug

        super(Capa, self).save(*args, **kwargs)
        return True


class Categoria(models.Model):
    nombre = models.CharField('Nombre', null=False, blank=False, unique=True, max_length=50)
    descripcion = models.TextField(u'Descripción', null=False, blank=True, max_length=255)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __unicode__(self):
        return unicode(self.nombre)


class AreaTematica(models.Model):
    nombre = models.CharField('Nombre', null=False, blank=False, unique=True, max_length=50)
    descripcion = models.TextField(u'Descripción', null=False, blank=True, max_length=255)

    class Meta:
        verbose_name = 'Área Temática'
        verbose_name_plural = 'Áreas Temáticas'
        ordering = ['nombre']

    def __unicode__(self):
        return unicode(self.nombre)


class Escala(models.Model):
    nombre = models.CharField('Nombre', null=False, blank=False, unique=True, max_length=100)

    class Meta:
        verbose_name = 'Escala'
        verbose_name_plural = 'Escalas'
        ordering = ['nombre']

    def __unicode__(self):
        return unicode(self.nombre)


class Atributo(models.Model):
    nombre_del_campo = models.CharField('Nombre del Campo', null=False, blank=False, max_length=50)  # debe ser r/o
    tipo = models.CharField('Tipo', null=False, blank=True, max_length=50)  # lo que diga postgres!, debe ser r/o
    alias = models.CharField('Alias', null=False, blank=True, max_length=50)
    descripcion = models.TextField(u'Descripción', null=False, blank=True, max_length=1000)
    publicable = models.BooleanField(null=False, default=True)
    unico = models.BooleanField(null=False, default=False)
    metadatos = models.ForeignKey('Metadatos', null=False)

    class Meta:
        unique_together = (('nombre_del_campo', 'metadatos'),)
        verbose_name = 'Atributo'
        verbose_name_plural = 'Atributos'

    def __unicode__(self):
        return unicode(self.nombre_del_campo) + ('(%s)' % (unicode(self.alias)) if self.alias != '' else '')

    @property
    def dame_descripcion(self):
        descr = self.descripcion[:50]
        if descr == '':
            return 'Sin descripción'
        else:
            return descr + '...'  # TODO: sacar de epok/commons.py funcion que trunca sin cortar palabras

    def save(self, *args, **kwargs):
        self.alias = normalizar_texto(self.alias, False)  # sacamos espacios y caracteres especiales que traen problemas en WXS pero mantenemos mayusculas y minusculas
        if self.alias != '':  # si empieza con numero le agregamos un _ al inicio
            if self.alias[0].isdigit():
                self.alias = '_' + self.alias
        super(Atributo, self).save(*args, **kwargs)


class ConexionPostgres(models.Model):
    nombre = models.CharField('Nombre', null=False, blank=True, max_length=50)
    host = models.CharField('Host', null=False, blank=False, max_length=50)
    port = models.CharField('Port', null=False, blank=True, max_length=50)
    dbname = models.CharField('Database', null=False, blank=False, max_length=50)
    user = models.CharField('User', null=False, blank=False, max_length=50)
    password = models.CharField('Password', null=False, blank=False, max_length=50)

    class Meta:
        verbose_name = u'Conexión Postgres'
        verbose_name_plural = 'Conexiones Postgres'
        ordering = ['nombre']

    def __unicode__(self):
        if self.nombre != '':
            return unicode(self.nombre)
        """ Devuelve algo de la forma 'Nombre (user@host:port.dbname)' """
        conexion = '%s@%s' % (self.user, self.host)
        if self.port != '':
            conexion += ':%s' % (self.port)
        conexion += '.%s' % (self.dbname)
#        if self.nombre!='':
#            conexion='%s (%s)'%(unicode(self.nombre),conexion)
        return conexion
    # TODO: encriptamos conexiones? que implica?

    @property
    def dame_connection_string(self):
        return 'host=%s dbname=%s user=%s password=%s port=%s'\
            % (self.host, self.dbname, self.user, self.password, self.port)


class Metadatos(models.Model):
    capa = models.OneToOneField(Capa, null=False)
    nombre_capa = models.CharField('Nombre Capa', null=False, blank=True, max_length=255)  # TODO: ver si al final usamos solo slug
    slug_capa = models.CharField('Slug Capa', null=False, blank=True, max_length=255)

    titulo = models.CharField(u'Título', null=False, blank=False, max_length=255)  # title
    fuente = models.TextField(u'Fuente', null=False, blank=True, max_length=1000)  # attribution
    contacto = models.TextField(u'Contacto', null=False, blank=True, max_length=1000)  # contact organization
    descripcion = models.TextField(u'Descripción', null=False, blank=True, max_length=10000)  # abstract
    escala = models.ForeignKey(Escala, null=True, blank=True, on_delete=models.SET_NULL)
    palabras_claves = models.TextField(u'Palabras Claves', null=False, blank=True, max_length=10000)
    categorias = models.ManyToManyField('Categoria', blank=True, verbose_name=u'Categorías')
    area_tematica = models.ForeignKey('AreaTematica', null=True, blank=True, on_delete=models.SET_NULL, verbose_name=u'Área Temática')

    fecha_de_relevamiento = models.CharField('Fecha de Relevamiento', null=False, blank=True, max_length=50)
    fecha_de_actualizacion = models.CharField(u'Fecha de Actualización', null=False, blank=True, max_length=50)
    frecuencia_de_actualizacion = models.CharField(u'Frecuencia de Actualización', null=False, blank=True, max_length=100)
    timestamp_alta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de alta')
    timestamp_modificacion = models.DateTimeField(auto_now=True, verbose_name='Fecha de última modificación')

    input_search_index = models.TextField(null=False, blank=True, default='')
    search_index = VectorField()

    class Meta:
        verbose_name = 'Metadatos de Capa'
        verbose_name_plural = 'Metadatos de Capas'

    def __unicode__(self):
        try:
            return unicode(self.capa)
        except:
            return 'sin capa!'  # no deberia pasar por disenio

    # TODO: def save(self): obligar a mantener la capa original!
    def dame_gml_atributos(self):
        include_items = []
        items_aliases = []
        for a in self.atributo_set.all():
            if a.publicable and a.nombre_del_campo not in ('gid', 'geom'):
                include_items.append(a.nombre_del_campo.encode('UTF-8'))
                if a.alias != '':
                    items_aliases.append((a.nombre_del_campo.encode('UTF-8'), a.alias.encode('UTF-8')))
        return include_items, items_aliases

    def dame_nombres_atributos(self):
        include_items = []
        for a in self.atributo_set.all():
            if a.nombre_del_campo not in ('gid', 'geom'):
                include_items.append(a.nombre_del_campo)
        return include_items

    @property
    def dame_categorias(self):
        res = []
        for cat in self.categorias.all():
            res.append(cat.nombre)
        return res

    def actualizar_input_search_index(self):
        textos = []
        textos.append(self.capa.nombre)
        textos.append(self.capa.id_capa)
        textos.append(normalizar_texto(self.titulo))
        textos.append(normalizar_texto(self.palabras_claves))
        textos.append(normalizar_texto(self.descripcion))
        self.input_search_index = ' '.join(textos)

    def save(self, *args, **kwargs):
        self.actualizar_input_search_index()
        super(Metadatos, self).save(*args, **kwargs)

    objects = SearchManager(
        # fields = ('nombre_capa', 'slug_capa', 'titulo', 'palabras_claves'),
        fields=('input_search_index',),
        config='pg_catalog.spanish',  # this is default
        search_field='search_index',  # this is default
        auto_update_search_field=True
    )


@receiver(pre_save, sender=Capa)
def onCapaPreSave(sender, instance, **kwargs):
    print 'onCapaPreSave %s' % (str(instance))
    # carga inicial de campos read only de la capa
    if instance.id is None:
        print '...carga inicial de datos read only'
        if instance.tipo_de_capa == CONST_VECTOR:
            cursor = connection.cursor()
            # esta escritura (segura y recomendada) no funciona porque internamente escapea strings con ' y no sirve para el FROM
            # cursor.execute("SELECT count(*) from %s.%s", [instance.esquema, instance.tabla])
            cursor.execute("SELECT count(*) from %s.%s" % (instance.esquema, instance.tabla))
            rows = cursor.fetchone()
            instance.cantidad_de_registros = int(rows[0])
            cursor.execute("SELECT GeometryType(%s) FROM %s.%s LIMIT 1" % (instance.campo_geom, instance.esquema, instance.tabla))
            rows = cursor.fetchone()
            instance.tipo_de_geometria = TipoDeGeometria.objects.get(postgres_type=rows[0])
            cursor.execute("SELECT st_extent(%s) from %s.%s;" % (instance.campo_geom, instance.esquema, instance.tabla))
            rows = cursor.fetchone()
            instance.layer_srs_extent = rows[0].replace('BOX(', '').replace(')', '').replace(',', ' ')
            cursor.execute("SELECT st_extent(st_transform(%s,4326)) from %s.%s;" % (instance.campo_geom, instance.esquema, instance.tabla))
            rows = cursor.fetchone()
            extent_capa = rows[0].replace('BOX(', '').replace(')', '').replace(',', ' ').split(' ')
            instance.extent_minx_miny = Point(float(extent_capa[0]), float(extent_capa[1]), srid=4326)
            instance.extent_maxx_maxy = Point(float(extent_capa[2]), float(extent_capa[3]), srid=4326)


@receiver(post_save, sender=Metadatos)
def onMetadatosPostSave(sender, instance, created, **kwargs):
    print 'onMetadatosPostSave'
    instance.capa.save()  # forzamos la actualizacion de la fecha de ultima modificacion de la capa y posterior borrado de mapfile


def get_sld_filename(instance, filename):
    return os.path.join('sld', instance.id_archivo_sld)


class ArchivoSLD(models.Model):
    id_archivo_sld = models.CharField('Id Archivo SLD', null=False, blank=False, unique=True, max_length=500)
    capa = models.ForeignKey('Capa', null=False)
    filename = models.FileField('Nombre de Archivo', upload_to=get_sld_filename, max_length=500)
    descripcion = models.TextField(u'Descripción', null=False, blank=True, max_length=10000)
    default = models.BooleanField(u'Activa', null=False, default=False)
    user_alta = models.CharField(u'Subido por', null=False, blank=True, max_length=50, default='')
    user_modificacion = models.CharField(u'Modificado por', null=False, blank=True, max_length=50, default='')
    timestamp_alta = models.DateTimeField('Fecha de alta', null=True, blank=True)
    timestamp_modificacion = models.DateTimeField('Fecha de última modificación', null=True, blank=True)

    class Meta:
        verbose_name = 'Archivo SLD'
        verbose_name_plural = 'Archivos SLD'

    def __unicode__(self):
        return unicode(self.id_archivo_sld)


@receiver(pre_save, sender=ArchivoSLD)
def onArchivoSLDPreSave(sender, instance, **kwargs):
    print 'onArchivoSLDPreSave %s' % (str(instance))
    # instance.id_archivo_sld = instance.capa.id_capa+'_'+instance.filename.name
    if instance.pk is None:  # si voy a crear un nuevo SLD:
        # 1 - defino el id, unico, garantizado por validacion previa en el form
        uploaded_filename = normalizar_texto(os.path.splitext(instance.filename.name)[0])
        instance.id_archivo_sld = (instance.capa.id_capa + '_' if not uploaded_filename.startswith(instance.capa.id_capa) else '') + uploaded_filename + '.sld'
        # 2 - lo marco como default si no hay otro
        if not instance.default and len(ArchivoSLD.objects.filter(capa=instance.capa).filter(default=True)) == 0:
            instance.default = True
    else:  # si voy a actualizar un SLD:
        try:
            # borro el SLD anterior
            old_filename = ArchivoSLD.objects.get(pk=instance.pk).filename
            if old_filename != instance.filename:
                os.remove(os.path.join(settings.MEDIA_ROOT, old_filename.name))
        except:
            pass
