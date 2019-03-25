# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import
# import traceback

from django.contrib.gis.geos import Point, Polygon, MultiPolygon
from django.shortcuts import HttpResponseRedirect, render, get_object_or_404
from django.utils import timezone
from fileupload.models import Archivo
from .models import TablaGeografica, ArchivoRaster
from utils.commons import normalizar_texto
from .utils import get_shapefile_files, determinar_id_capa, get_raster_metadata, get_raster_basic_metadata
from .import_utils import import_layer, import_shapefile, update_layer
from layers.models import Capa, TipoDeGeometria, RasterDataSource, VectorDataSource, CONST_VECTOR, CONST_RASTER
from MapGround.settings import IMPORT_SCHEMA, ENCODINGS, UPLOADED_RASTERS_PATH
from MapGround import MapGroundException, LayerAlreadyExists, LayerImportError, LayerNotFound
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
import os
import shutil
from datetime import datetime
import pytz
from sequences import get_next_value
from utils.db import drop_table, setup_inheritance, add_column, have_same_structure

def _get_posibles_rasters(request):
    l = []
    posibles_rasters = Archivo.objects.owned_by(request.user).exclude(extension__in=['.shp']).order_by('slug')

    for posible_raster in posibles_rasters:
        # analizamos el archivo para ver si es un raster, sin importar los metadatos en json
        raster = get_raster_basic_metadata(posible_raster.file.name)
        if raster:
            importable = Capa.objects.filter(id_capa=determinar_id_capa(request, posible_raster.nombre)).count() == 0
            l.append({
                'nombre': posible_raster.slug,
                'formato': raster['driver_short_name'],
                'tipo': CONST_RASTER,
                'detalle': '{}x{} px, {} {}'.format(raster['size_width'], raster['size_height'], raster['raster_count'], 'banda' if raster['raster_count'] == 1 else 'bandas'),
                'importable': importable})
    return l

def _get_shapefiles(request):
    l = []
    errores = []
    archivos_shapes = Archivo.objects.owned_by(request.user).filter(extension=".shp").order_by('slug')
    for archivo_shape in archivos_shapes:
        try:
            st = get_shapefile_files(unicode(archivo_shape.file))   # path absoluto para determinar si es un shape completo
            importable = Capa.objects.filter(id_capa=determinar_id_capa(request, archivo_shape.nombre)).count() == 0
            l.append({
                'nombre': archivo_shape.slug,
                'formato': 'Shapefile',
                'tipo': CONST_VECTOR,
                'detalle': '',
                'importable': importable})
        except MapGroundException as e:
            errores.append(unicode(e))
    return (l, errores)

def _get_capas_importables(request):
    rasters = _get_posibles_rasters(request)
    shapes, errores = _get_shapefiles(request)
    return (rasters+shapes, errores)

@login_required
def LayersListView(request):
    template_name = 'layers_list.html'
    l, errores = _get_capas_importables(request)

    return render(request, template_name, {"object_list": l, "errors_list": errores, "encodings": ENCODINGS})


def _get_actualizaciones_validas(archivos, capa):
    return map(lambda c: {
        'nombre': c['nombre'],
        'formato': c['formato'],
        'tipo': c['tipo'],
        'detalle': c['detalle'],
        'importable': c['tipo'] == capa.tipo_de_capa
    }, archivos)

def _haveSameStructure(t1, t2):
    return have_same_structure(t1, t2)

@login_required
def LayersUpdateListView(request, id_capa):
    template_name = 'layers_update.html'

    capa = get_object_or_404(Capa, id_capa=id_capa)
    archivos, errores = _get_capas_importables(request)

    l = _get_actualizaciones_validas(archivos, capa)

    return render(request, template_name, {"object_list": l, "errors_list": errores, "encodings": ENCODINGS, "id_capa": id_capa})

def _get_raster_date_time(raster_metadata):
    # Mapserver no soporta datetimes con microsegundos en WMS-T
    data_datetime = timezone.now().replace(microsecond=0).replace(tzinfo=pytz.utc)
    if raster_metadata['raster_count'] > 0:
        try:
            # Toda esta logica es MUY ad-hoc
            # Cuanto de esto funcionara en general para otros gribs y/o rasters es dudosisimo
            grib_ref_time = raster_metadata['metadata_json']['gdalinfo']['bands'][0]['metadata']['']['GRIB_VALID_TIME']
            data_datetime = datetime.utcfromtimestamp(int(grib_ref_time.split(' ')[0], 10)).replace(tzinfo=pytz.utc)
        except Exception as e:
            print unicode(e)
    return data_datetime


@login_required
def LayerImportView(request, filename):
    # filename tiene la forma "nombre.extension"
    template_name = 'layer_import.html'
    try:
        encoding = [item[0] for item in ENCODINGS if item[0] == request.GET['enc']][0]
    except Exception as e:
        print "ERROR intentando setear encoding: %s"%(unicode(e))
        encoding = 'LATIN1'

    try:
        capa = import_layer(request, filename, encoding)
    except LayerNotFound as e:
        return render(request, template_name, {
            "capa": filename, "ok": False,
            "error_msg": unicode(e)})

    except LayerAlreadyExists as e:
        return render(request, template_name, {
            "capa": filename, "ok": False,
            "error_msg": unicode(e)})
    
    except LayerImportError as e:
        return render(request, template_name, {
            "capa": filename, "ok": False,
            "error_msg": unicode(e)})

    return HttpResponseRedirect(reverse('layers:metadatos', args=(capa.id_capa,)))

@login_required
def LayerImportUpdateView(request, id_capa, filename):
    # filename tiene la forma "nombre.extension"
    capa = get_object_or_404(Capa, id_capa=id_capa)
    template_name = 'layer_import.html'
    try:
        encoding = [item[0] for item in ENCODINGS if item[0] == request.GET['enc']][0]
    except:
        encoding = 'LATIN1'
    try:
        capa = update_layer(request, capa, filename, encoding)
    except ValueError as e:
        return render(request, template_name, {
            "capa": filename, "ok": False,
            "error_msg": unicode(e)})
  
    except LayerImportError as e:
        return render(request, template_name, {
            "capa": filename, "ok": False,
            "error_msg": unicode(e)})

    return HttpResponseRedirect(reverse('layers:metadatos', args=(capa.id_capa,)))
