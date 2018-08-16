# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

from django.contrib.gis.geos import Point
from django.contrib.gis.gdal import GDALRaster
from django.shortcuts import render
from django.shortcuts import HttpResponseRedirect
from fileupload.models import Archivo
from layerimport.models import TablaGeografica, ArchivoRaster
from utils.commons import normalizar_texto
from .utils import get_shapefile_files, import_layer, determinar_id_capa
from layers.models import Capa, TipoDeGeometria, CONST_VECTOR, CONST_RASTER
from MapGround.settings import IMPORT_SCHEMA, ENCODINGS, UPLOADED_RASTERS_PATH
from MapGround import MapGroundException
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
import os
import shutil


@login_required
def LayersListView(request):
    template_name = 'layers_list.html'
    l = []
    errores = []

    posibles_rasters = Archivo.objects.owned_by(request.user).exclude(extension__in=['.shp']).order_by('slug')

    for posible_raster in posibles_rasters:
        try:
            raster = GDALRaster(posible_raster.file.name)
            l.append({
                'nombre': posible_raster.slug,
                'formato': raster.driver.name,
                'tipo': CONST_RASTER})
        except:
            pass

    archivos_shapes = Archivo.objects.owned_by(request.user).filter(extension=".shp").order_by('slug')
    for archivo_shape in archivos_shapes:
        try:
            st = get_shapefile_files(unicode(archivo_shape.file))   # path absoluto para determinar si es un shape completo
            l.append({
                'nombre': archivo_shape.slug,
                'formato': 'Shapefile',
                'tipo': CONST_VECTOR})
        except MapGroundException as e:
            errores.append(unicode(e))

    return render(request, template_name, {"object_list": l, "errors_list": errores, "encodings": ENCODINGS})


@login_required
def LayerImportView(request, filename):
    template_name = 'layer_import.html'
    try:
        encoding = [item[0] for item in ENCODINGS if item[0] == request.GET['enc']][0]
    except:
        encoding = 'LATIN1'

    # Chequeo basico de consistencia entre filename de la vista y algun Archivo existente
    try:
        archivo = Archivo.objects.get(owner=request.user, slug=filename)  # filename tiene la forma "nombre.extension"
    except (Archivo.DoesNotExist, MapGroundException) as e:  # no deberia pasar...
        return render(request, template_name, {
            "capa": filename, "ok": False,
            "error_msg": 'No se pudo encontrar la capa "{0}" para importar.'.format(filename)})

    # determinamos el id unico que le corresponde a esta capa, sin importar si es vector o raster, y verificamos que no exista en la IDE
    id_capa = determinar_id_capa(request, archivo.nombre)

    try:
        existe = Capa.objects.get(id_capa=id_capa)     # este chequeo podría ser reemplazado a futuro por la funcionalidad de "upload nueva versión de la capa"
        return render(request, template_name, {
            "capa": filename, "ok": False,
            "error_msg": 'Ya existe una capa suya con el nombre "{0}" en la base de datos.'.format(filename)})
    except:
        if archivo.extension == '.shp':     # Esto podría mejorarse guardando el tipo de archivo en el modelo Archivo
            try:
                srid = import_layer(unicode(archivo.file), IMPORT_SCHEMA, id_capa, encoding)
                tabla_geografica = TablaGeografica.objects.create(
                    nombre_normalizado=normalizar_texto(filename),
                    nombre_del_archivo=os.path.basename(unicode(archivo.file)),
                    esquema=IMPORT_SCHEMA,
                    srid=srid,
                    tabla=id_capa,  # antes esta variable era nombre_tabla, cambio variable pero es el mismo valor
                    owner=request.user)

                c = Capa.objects.create(
                    owner=tabla_geografica.owner,
                    nombre=tabla_geografica.nombre_normalizado,
                    id_capa=id_capa,    # equivalente a tabla_geografica.tabla,
                    tipo_de_capa=CONST_VECTOR,
                    nombre_del_archivo=None,
                    conexion_postgres=None,
                    esquema=tabla_geografica.esquema,
                    tabla=tabla_geografica.tabla,
                    tipo_de_geometria=TipoDeGeometria.objects.all()[0],  # uno cualquiera, pues el capa_pre_save lo calcula y lo overridea
                    srid=tabla_geografica.srid)

                for a in Archivo.objects.filter(owner=request.user, nombre=os.path.splitext(filename)[0]):
                    a.delete()

            except Exception as e:
                return render(request, template_name, {
                    "capa": filename, "ok": False,
                    "error_msg": 'Se produjo un error al intentar importar la capa vectorial "{0}": {1}'.format(filename, unicode(e))})

        else:   # caso rasters

            # Validamos primero la consistencia entre el filename y un raster valido, por ejemplo, para evitar vulnerabilidad por url
            try:
                raster = GDALRaster(archivo.file.name)
                extent_capa = raster.extent
            except:
                return render(request, template_name, {
                    "capa": filename, "ok": False,
                    "error_msg": 'Se produjo un error al intentar importar la capa "{0}" '.format(filename)})

            # El 'import' del raster consiste en moverlo al repo definitivo
            directorio_destino = UPLOADED_RASTERS_PATH + unicode(request.user) + '/'
            filename_destino = directorio_destino + id_capa + archivo.extension
            try:
                # movemos el archivo al path destino...
                if not os.path.exists(directorio_destino):
                    os.makedirs(directorio_destino)
                shutil.move(archivo.file.name, filename_destino)

                # ...y luego creamos los objetos
                archivo_raster = ArchivoRaster.objects.create(
                    owner=request.user,
                    nombre_del_archivo=id_capa,
                    path_del_archivo=filename_destino,
                    formato=raster.driver.name,
                    cantidad_de_bandas=len(raster.bands),
                    srid=raster.srs.srid if raster.srs is not None else 4326,
                    extent=' '.join(map(str, extent_capa)),
                    heigth=raster.height,
                    width=raster.width)

                c = Capa.objects.create(
                    owner=request.user,
                    nombre=normalizar_texto(archivo.nombre),
                    id_capa=id_capa,
                    tipo_de_capa=CONST_RASTER,
                    nombre_del_archivo=archivo_raster.path_del_archivo,  # path final, unico, normalizado
                    conexion_postgres=None,
                    esquema=None,
                    tabla=None,
                    tipo_de_geometria=TipoDeGeometria.objects.get(nombre='Raster'),
                    srid=archivo_raster.srid,
                    extent_minx_miny=Point(float(extent_capa[0]), float(extent_capa[1]), srid=4326),  # TODO:no hay que reproyectar? pensar
                    extent_maxx_maxy=Point(float(extent_capa[2]), float(extent_capa[3]), srid=4326),  # TODO:no hay que reproyectar? pensar
                    layer_srs_extent=archivo_raster.extent,
                    cantidad_de_registros=None)

                archivo.delete()

            except Exception as e:
                return render(request, template_name, {
                    "capa": filename, "ok": False,
                    "error_msg": 'Se produjo un error al intentar importar la capa raster {0}: {1}'.format(filename, unicode(e))})

    return HttpResponseRedirect(reverse('layers:metadatos', args=(c.id_capa,)))
