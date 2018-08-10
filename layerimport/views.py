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
from .utils import get_shapefile_files, import_layer, nombre_tabla
from layers.models import Capa, TipoDeGeometria, CONST_VECTOR, CONST_RASTER
from MapGround.settings import IMPORT_SCHEMA, ENCODINGS, MEDIA_ROOT
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

    posibles_rasters = Archivo.objects.owned_by(request.user).exclude(extension__in=['.shp'])

    for posible_raster in posibles_rasters:
        try:
            raster = GDALRaster(posible_raster.file.name)
            l.append({
                'nombre': posible_raster.slug,
                'formato': 'Raster {}'.format(raster.driver.name),
                'tipo': CONST_RASTER})
        except:
            pass

    archivos_shapes = Archivo.objects.owned_by(request.user).filter(extension=".shp")
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
    ok = True
    error_msg = ""
    try:
        encoding = [item[0] for item in ENCODINGS if item[0] == request.GET['enc']][0]
    except:
        encoding = 'LATIN1'

    try:
        archivo = Archivo.objects.get(owner=request.user, slug=filename)  # ahora filename tiene "nombre.extension"
    except (Archivo.DoesNotExist, MapGroundException) as e:  # no deberia pasar...
        ok = False
        error_msg = 'No se pudo encontrar la capa {0} para importar.'.format(filename)
    else:
        if archivo.extension == '.shp':
            try:
                existe = TablaGeografica.objects.get(tabla=nombre_tabla(request, filename))
                ok = False
                error_msg = 'Se produjo un error al intentar importar la capa {0}: {1}'.format(filename, unicode(e))
                error_msg = 'Ya existe una tabla suya con el nombre {0} en la base de datos.'.format(filename)
            except:
                try:
                    nombreTabla = nombre_tabla(request, filename)
                    srid = import_layer(unicode(archivo.file), IMPORT_SCHEMA, nombreTabla, encoding)
                    tabla_geografica = TablaGeografica.objects.create(
                        nombre_normalizado=normalizar_texto(filename),
                        nombre_del_archivo=os.path.basename(unicode(archivo.file)),
                        esquema=IMPORT_SCHEMA,
                        srid=srid,
                        tabla=nombreTabla,
                        owner=request.user)

                    c = Capa.objects.create(
                        owner=tabla_geografica.owner,
                        nombre=tabla_geografica.nombre_normalizado,
                        id_capa=tabla_geografica.tabla,
                        tipo_de_capa=CONST_VECTOR,
                        nombre_del_archivo=None,
                        conexion_postgres=None,
                        esquema=tabla_geografica.esquema,
                        tabla=tabla_geografica.tabla,
                        tipo_de_geometria=TipoDeGeometria.objects.all()[0],  # uno cualquiera, pues el capa_pre_save lo calcula y lo overridea
                        srid=tabla_geografica.srid)

                except Exception as e:
                    ok = False
                    error_msg = 'Se produjo un error al intentar importar la capa {0}: {1}'.format(filename, unicode(e))
        else:   # es un raster...
            # TODO: revisar primero que no exista el archivo

            # El 'import' del raster consiste en moverlo al repo definitivo
            directorio_destino = MEDIA_ROOT + 'uploaded-rasters/' + unicode(request.user) + '/'     # TODO: idea temporal, pensar la ubicacion final de los rasters y pasarlo al settings
            filename_destino = directorio_destino + nombre_tabla(request, filename) + archivo.extension    # TODO: MEJORAR ESTO

            print 'copiando {} a {}...'.format(archivo.file.name, filename_destino)
            if not os.path.exists(directorio_destino):
                os.makedirs(directorio_destino)
            shutil.move(archivo.file.name, filename_destino)    # movemos el archivo al path destino

            # Y luego creamos los objetos...

            raster = GDALRaster(filename_destino)   # Esto no deberia pasar TODO: poner try
            extent_capa = raster.extent

            archivo_raster = ArchivoRaster.objects.create(
                owner=request.user,
                nombre_del_archivo=nombre_tabla(request, filename),
                path_del_archivo=filename_destino,
                formato=raster.driver.name,
                cantidad_de_bandas=len(raster.bands),
                srid=raster.srs.srid if raster.srs is not None else 4326,   # TODO: pensar si esta bien
                heigth=raster.height,
                width=raster.width)
            # ################### extent=raster.extent)   # TODO: agregar

            c = Capa.objects.create(
                owner=request.user,
                nombre=normalizar_texto(filename),     # ??? ??? por ahora,misma logica que tabla
                id_capa=nombre_tabla(request, filename),     # ??? por ahora,misma logica que tabla
                tipo_de_capa=CONST_RASTER,
                nombre_del_archivo=archivo_raster.path_del_archivo,  # path final, unico, normalizado
                conexion_postgres=None,
                esquema=None,
                tabla=None,
                tipo_de_geometria=TipoDeGeometria.objects.get(nombre='Raster'),
                srid=archivo_raster.srid,
                extent_minx_miny=Point(float(extent_capa[0]), float(extent_capa[1]), srid=4326),  # TODO:no hay que reproyectar? pensar
                extent_maxx_maxy=Point(float(extent_capa[2]), float(extent_capa[3]), srid=4326),  # TODO:no hay que reproyectar? pensar
                layer_srs_extent=' '.join(map(str, extent_capa)),
                cantidad_de_registros=None)

    if not ok:
        return render(request, template_name, {"capa": filename, "ok": ok, "error_msg": error_msg})
    else:
        return HttpResponseRedirect(reverse('layers:metadatos', args=(c.id_capa,)))
