# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import
# import traceback

from MapGround import MapGroundException, LayerNotFound, LayerAlreadyExists, LayerImportError
from django.db import connection
from django.contrib.gis.geos import Point, Polygon, MultiPolygon
from osgeo import gdal, osr
from MapGround.settings import DEFAULT_SRID, DATABASES
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from MapGround.settings import IMPORT_SCHEMA, ENCODINGS, UPLOADED_RASTERS_PATH
from sequences import get_next_value
from utils.db import drop_table, setup_inheritance, add_column, have_same_structure
from utils.commons import normalizar_texto
import pytz
from django.utils import timezone
from datetime import datetime
from fileupload.models import Archivo
from .models import TablaGeografica, ArchivoRaster

from subprocess import Popen, PIPE
from threading import Thread
from StringIO import StringIO
import os
import shutil
import subprocess
import re
import glob
import json
import hashlib
import random
import string

epsg_hashes = dict()

# Por el momento no las estamos usando: finalmente decidimos tener en cuenta todas las variables
# GRIB_VARIABLES_DE_INTERES = [
#     'TMP',      # temperatura
#     'UGRD',     # viento - componente u
#     'VGRD',     # viento - componente v
#     'APCP',     # precipitacion
#     'PRMSL',    # presion atmosferica
#     'RH'        # humedad relativa
# ]

def coordConvert(x, y, sridFrom, sridTo):
    fromCoord = SpatialReference(sridFrom)
    toCoord = SpatialReference(sridTo)
    trans = CoordTransform(fromCoord, toCoord)

    pnt = Point(x, y, srid=sridFrom)
    pnt.transform(trans)
    return pnt

def extentConvert(extent, sridFrom, sridTo):
    minx_miny = coordConvert(extent[0], extent[1], sridFrom, sridTo)
    maxx_maxy = coordConvert(extent[2], extent[3], sridFrom, sridTo)
    return (minx_miny.x, minx_miny.y, maxx_maxy.x, maxx_maxy.y)

def tee(infile, *files):
    """Print `infile` to `files` in a separate thread."""
    def fanout(infile, *files):
        for line in iter(infile.readline, ''):
            for f in files:
                f.write(line)
        infile.close()
    t = Thread(target=fanout, args=(infile,) + files)
    t.daemon = True
    t.start()
    return t


def teed_call(cmd_args, **kwargs):
    stdout, stderr = [kwargs.pop(s, None) for s in 'stdout', 'stderr']
    p = Popen(cmd_args,
              stdout=PIPE if stdout is not None else None,
              stderr=PIPE if stderr is not None else None,
              **kwargs)
    threads = []
    if stdout is not None:
        threads.append(tee(p.stdout, stdout))
    if stderr is not None:
        threads.append(tee(p.stderr, stderr))
    for t in threads:
        t.join()  # wait for IO completion
    return p.wait()


def get_shapefile_files(filename):
    """Verifica las dependencias para un shapefile y devuelve un diccionario
    con todas las dependencias
    """
    # print 'get_shapefile_files: '+filename
    files = {'base': filename}

    base_name, extension = os.path.splitext(filename)
    # Replace special characters in filenames - []{}()
    glob_name = re.sub(r'([\[\]\(\)\{\}])', r'[\g<1>]', base_name)

    if extension.lower() == '.shp':
        required_extensions = dict(
            shp='.[sS][hH][pP]', dbf='.[dD][bB][fF]', shx='.[sS][hH][xX]')
        for ext, pattern in required_extensions.iteritems():
            matches = glob.glob(glob_name + pattern)
            if len(matches) == 0:
                msg = ('Se esperaba un archivo "%s" que no existe; un Shapefile '
                       'requiere archivos con las siguientes extensiones: '
                       '%s') % (os.path.basename(base_name) + "." + ext,
                                required_extensions.keys())
                # print msg
                raise MapGroundException(msg)
            elif len(matches) > 1:
                msg = ('Existen múltiples archivos %s; tienen que llamarse distinto '
                       'y no solo diferenciarse en mayúsculas y minúsculas.') % filename
                raise MapGroundException(msg)
                # print msg
            else:
                files[ext] = matches[0]

        matches = glob.glob(glob_name + ".[pP][rR][jJ]")
        if len(matches) == 1:
            files['prj'] = matches[0]
        elif len(matches) > 1:
            msg = ('Existen múltiples archivos %s; tienen que llamarse distinto '
                   'y no solo diferenciarse en mayúsculas y minúsculas.') % filename
            raise MapGroundException(msg)
            # print msg

        matches = glob.glob(glob_name + ".[sS][lL][dD]")
        if len(matches) == 1:
            files['sld'] = matches[0]
        elif len(matches) > 1:
            msg = ('Existen múltiples archivos de estilo para %s; tienen que llamarse '
                   'distinto y no solo diferenciarse en mayúsculas y minúsculas.') % filename
            raise MapGroundException(msg)
            # print msg

        matches = glob.glob(base_name + ".[xX][mM][lL]")

        # shapefile XML metadata is sometimes named base_name.shp.xml
        # try looking for filename.xml if base_name.xml does not exist
        if len(matches) == 0:
            matches = glob.glob(filename + ".[xX][mM][lL]")

        if len(matches) == 1:
            files['xml'] = matches[0]
        elif len(matches) > 1:
            msg = ('Existen múltiples archivos XML para %s; tienen que llamarse '
                   'distinto y no solo diferenciarse en mayúsculas y minúsculas.') % filename
            raise MapGroundException(msg)
            # print msg

    return files


def get_random_string(len=20):
    return "".join([random.SystemRandom().choice(string.digits + string.letters) for i in range(len)])


# def drop_table(schema, table, cascade=False):
#     query = ('SELECT DropGeometryColumn(\'%s\',\'%s\',\'geom\'); '
#                 'DROP TABLE "%s"."%s"') % (schema, table, schema, table)
#     if cascade:
#         query += ' CASCADE'
#     cur = connection.cursor()
#     cur.execute(query)

def load_shape(shapefile, schema, table, srid=0, encoding='LATIN1', create_table_only=False):
    print 'loading shape with encoding %s ' % encoding
    shp2pgsql_call = ('shp2pgsql -s %s -W %s -p -I -D -N skip "%s" %s.%s') % (srid, encoding,
            shapefile, schema, table)

    try:
        fout, ferr = StringIO(), StringIO()
        exitcode = teed_call(shp2pgsql_call, stdout=fout, stderr=ferr, shell=True)
        create_query = fout.getvalue()
        err = ferr.getvalue()
        if exitcode != 0:
            raise MapGroundException(err)
    except Exception, e:
        raise MapGroundException(e)

    tmp_filename = '/tmp/data' + get_random_string()
    tmp_copy_filename = tmp_filename + '_copy'
    shp2pgsql_call = ('shp2pgsql -s %s -W %s -a -D -N skip "%s" %s.%s 2>/dev/null | awk \'NR<5 {print >> "/dev/stdout"; next } {print > "%s"} END{print}\' - | sed "s:stdin:\'%s\':g"') % (srid, encoding,
            shapefile, schema, table, tmp_filename, tmp_filename)

    try:
        fout, ferr = StringIO(), StringIO()
        exitcode = teed_call(shp2pgsql_call, stdout=fout, stderr=ferr, shell=True)
        copy_query = fout.getvalue()
        err = ferr.getvalue()
        if exitcode != 0:
            raise MapGroundException(err)
    except Exception, e:
        raise MapGroundException(e)

    try:
        drop_table(schema, table)
    except:
        pass

    try:
        cur = connection.cursor()
        cur.execute(create_query)
    except Exception, e:
        os.remove(tmp_filename)
        raise MapGroundException(e)

    if not create_table_only:
        try:
            copy_query += 'COMMIT;'
            with open(tmp_copy_filename, 'w') as text_file:
                text_file.write(copy_query.replace('COPY', '\\copy'))
            copy_call = 'PGPASSWORD="%s" psql -d %s -U %s -w -h %s -f %s' % (DATABASES['default']['PASSWORD'],
            DATABASES['default']['NAME'], DATABASES['default']['USER'], DATABASES['default']['HOST'], tmp_copy_filename)
            fout, ferr = StringIO(), StringIO()
            exitcode = teed_call(copy_call, stdout=fout, stderr=ferr, shell=True)
            # print copy_call
            err = ferr.getvalue()
            if exitcode != 0:
                raise MapGroundException(err)
            # cur = connection.cursor()
            # cur.execute(copy_query)
        except Exception, e:
            os.remove(tmp_filename)
            os.remove(tmp_copy_filename)
            raise MapGroundException(e)

        try:
            os.remove(tmp_filename)
            os.remove(tmp_copy_filename)
        except:
            pass


def get_epsg_from_prj(prjfile):
    srid = DEFAULT_SRID
    print 'default srid %d' % srid
    try:
        prj_file = open(prjfile, 'r')
        prj_txt = prj_file.read()
        srs = osr.SpatialReference()
        srs.ImportFromESRI([prj_txt])
        srs.MorphToESRI()
        wkt = srs.ExportToWkt()
        l = re.findall('\[.*?\]', wkt)
        h = hashlib.sha256(unicode(frozenset(l))).hexdigest()
        srid = get_srid_from_hash(h)
    except Exception:
        # print 'Exception', e
        pass
    print 'srid %d' % srid
    return srid


def fill_epsg_hashes():
    cur = connection.cursor()
    cur.execute("select srid from spatial_ref_sys;")

    rows = cur.fetchall()
    srs = osr.SpatialReference()
    print "Generating hashes for %d EPSG codes..." % len(rows)
    for r in rows:
        try:
            srs.ImportFromEPSG(r[0])
            srs.MorphToESRI()
            wkt = srs.ExportToWkt()
            l = re.findall('\[.*?\]', wkt)
            h = hashlib.sha256(unicode(frozenset(l))).hexdigest()
            epsg_hashes[h] = r[0]
        except Exception, e:
            print e
            pass


def get_srid_from_hash(h):
    if len(epsg_hashes) == 0:
        fill_epsg_hashes()
    return epsg_hashes[h]


# def import_layer(filename, schema, table, encoding='LATIN1', create_table_only=False):
#     try:
#         st = get_shapefile_files(filename)
#     except MapGroundException:
#         raise

#     srid = DEFAULT_SRID
#     try:
#         srid = get_epsg_from_prj(st['prj'])
#     except KeyError:
#         pass

#     try:
#         load_shape(st['shp'], schema, table, srid, encoding, create_table_only)
#     except MapGroundException:
#         raise
#     print 'import srid %d' % srid

#     return srid


def determinar_id_capa(request, nombre):
    return unicode(request.user) + '_' + ((nombre.replace('-', '_')).replace(' ', '_').replace('.', '_').lower())

def _get_polygon_extent(poly):
    (minx, miny, maxx, maxy) = poly[0][0], poly[0][1], poly[0][0], poly[0][1]
    for c in poly:
        if c[0] < minx:
            minx = c[0]
        if c[1] < miny:
            miny = c[1]
        if c[0] > maxx:
            maxx = c[0]
        if c[1] > maxy:
            maxy = c[1]
    return (minx, miny, maxx, maxy)

def get_raster_metadata(file, con_stats=True):
    """Devuelve un json con metadatos detallados de un raster interfaseando con gdal y gdalinfo.

    Pensado para capturar toda la info posible del archivo y almacenarla en la IDE, en el campo Capa.gdal_metadata.
    El parametro optativo con_stats obliga a gdal_info a calcular los valores minimos, maximos y promedios de cada banda.
    """
    raster = gdal.Open(file, gdal.GA_ReadOnly)
    if raster is None:
        return None

    # extraemos toda info de proyeccion del raster usando gdal
    srid, proj, extent_capa = _get_raster_proj_info(raster)

    # extraemos todos los metadatos del raster usando gdalinfo
    metadata_gdalinfo_json = _run_gdalinfo(file, con_stats)

    # esto no es correcto pero va a evitar que explote si faltan metadatos
    extent_capa_4326 = extent_capa
    try:
        extent_capa_4326 = extentConvert(extent_capa, metadata_gdalinfo_json['coordinateSystem']['wkt'], 'EPSG:4326')
    except:
        pass

    # print "Calculated extent: %s"%(str(extent_capa))
    # extent_capa_4326 = _get_polygon_extent(metadata_gdalinfo_json['wgs84Extent']['coordinates'][0])
    # print "GDAL Info: proj: %s, srid: %s, extent 4326: %s"%(
    #     metadata_gdalinfo_json['coordinateSystem']['wkt'],
    #     str(srid),
    #     extentConvert(extent_capa, metadata_gdalinfo_json['coordinateSystem']['wkt'], 'EPSG:4326')
    # )
    # if 'wgs84Extent' in metadata_gdalinfo_json:
    #     try:
    #         extent_capa_4326 = _get_polygon_extent(metadata_gdalinfo_json['wgs84Extent']['coordinates'][0])
    #     except:
    #         pass


    variables_detectadas = {}
    subdatasets = []
    # Segun el formato del raster, determinamos las bandas para armar los mapas 'layer_raster_band' (mapas de variables)
    if raster.GetDriver().ShortName == 'GRIB':
        # en el caso de GRIB nos interesan los elementos en 'bands'
        if 'bands' in metadata_gdalinfo_json:
            wind_u_band = wind_v_band = None
            for banda in metadata_gdalinfo_json['bands']:
                try:    # si por algun motivo la banda no tiene la info necesaria la ignoramos
                    nro_banda = banda['band']
                    grib_element = banda['metadata']['']['GRIB_ELEMENT']
                    grib_comment = banda['metadata']['']['GRIB_COMMENT']
                    minimo = banda.get('minimum')
                    maximo = banda.get('maximum')

                    if grib_element in ('UGRD', 'UOGRD'):
                        wind_u_band = nro_banda
                    elif grib_element in ('VGRD', 'VOGRD'):
                        wind_v_band = nro_banda
                    else:
                        variables_detectadas[nro_banda] = {
                            'elemento': grib_element,
                            'descripcion': grib_comment,
                            'rango': (minimo, maximo),  # almacenamos el rango de la banda por si lo necesitamos en el DATARANGE
                        }
                except:
                    pass

                if wind_u_band and wind_v_band:
                    nro_banda = '{},{}'.format(wind_u_band, wind_v_band)
                    variables_detectadas[nro_banda] = {
                        'elemento': 'WIND',
                        'descripcion': 'Wind',
                        'rango': (None, None),  # Por el momento no necesitamos rangos para WIND, ya que la simbologia usa uv_length y uv_angle
                    }
                    wind_u_band = wind_v_band = None

    # Ahora analizamos subdatasets
    for subdataset in raster.GetSubDatasets():
        # Ejemplo de un subdataset: ('NETCDF:"/vagrant/data/SABANCAYA_2018062806_fcst_VAG_18.res.nc":TOPOGRAPHY', '[41x65] TOPOGRAPHY (32-bit floating-point)')
        # Ejemplo de un subdataset: ('HDF5:"data/RMA1_0201_01_TH_20180713T164924Z.H5"://dataset1/data1/data', '[360x526] //dataset1/data1/data (64-bit floating-point)')
        raster_subdataset = gdal.Open(subdataset[0], gdal.GA_ReadOnly)
        srid, proj, extent = _get_raster_proj_info(raster_subdataset)
        subdataset_gdalinfo_json = _run_gdalinfo(subdataset[0], con_stats)
        formato, path, identificador = subdataset[0].split(':')
        # Creamos la siguiente estructura para guardar todala info en la IDE, independientemente del formato
        subdatasets.append({
            'definicion': subdataset,               # Ej: ('HDF5:/path/al/archivo:identificador', [alguna descripcion])
            'identificador': identificador,         # Ej: TOPOGRAPHY
            'gdalinfo': subdataset_gdalinfo_json,   # toda la matadata provista por gdalinfo para el subdataset actual
        })

        # Y en el caso de netCDF y HDF5, detectamos variables para crear los mapas layer_raster_band, como hacemos con GRIBs
        # Tomamos la primer banda por convencion, ya que mapserver no permite trabajar especificamente una banda dentro de un subdataset (la unidad es el dataset),
        # y en todos los casos que vimos las bandas tienen la misma variable, solo cambia el timestamp
        if 'bands' in subdataset_gdalinfo_json:
            banda0 = subdataset_gdalinfo_json['bands'][0]
            if raster.GetDriver().ShortName == 'netCDF':
                variables_detectadas[identificador] = {
                    'elemento': banda0['metadata'][''].get('NETCDF_VARNAME', ''),   # aparentemente todo netCDF tiene este campo y es igual para toda banda del subdataset
                    'descripcion': banda0['metadata'][''].get('description', ''),   # algunos netCDF no tienen este campo
                    'rango': (banda0.get('minimum'), banda0.get('maximum')),        # en principio este rango no nos interesa porque este formato se renderiza directamente, va por compatibilidad
                    'extent': extent                                                # extent, necesario para cada mapa layer_raster_band
                }
            elif raster.GetDriver().ShortName == 'HDF5':
                variables_detectadas[identificador] = {
                    'elemento': subdataset_gdalinfo_json['metadata'][''].get('what_object', ''),    # aparentemente los HDF5 de SMN tienen toooodo duplicado en todas bandas y son todas iguales
                    'descripcion': '',                                                              # no encontre nada para cargar...
                    'rango': (None, None),                                                          # no nos interesa este campo, solo por compatibilidad
                    'extent': extent                                                                # extent, necesario para cada mapa layer_raster_band
                }
            else:
                # Necesitamos info estructural especifica si es otro formato...
                pass

    # Lamentablemente hay inconsistencias en algunos archivos analizados con respecto al extent:
    # a veces el de la capa no coincide con el de los subdatasets. Tomamos el primero, que se utilizara para renderizar
    if len(subdatasets) > 0:
        extent_capa = variables_detectadas[subdatasets[0]['identificador']]['extent']
        try:
            # los casos analizados NO incluyen informacion de la proyeccion en bandas, solo coordenadas que parecen ser 4326, como no hay garantia intento reproyectarlo
            extent_capa_4326 = extentConvert(extent_capa, 'EPSG:4326', 'EPSG:4326')
        except:
            pass

    # construimos la respuesta
    return {
        'driver_short_name': raster.GetDriver().ShortName,
        'driver_long_name': raster.GetDriver().LongName,
        'raster_count': raster.RasterCount,
        'subdataset_count': len(raster.GetSubDatasets()),
        'srid': srid,   # puede ser None
        'extent_capa': extent_capa,
        'extent_capa_4326': extent_capa_4326,
        'metadata_json': {
            'gdalinfo': metadata_gdalinfo_json,
            'variables_detectadas': variables_detectadas,
            'subdatasets': subdatasets,
        },
        'proyeccion_proj4': proj.ExportToProj4(),
        'size_height': raster.RasterYSize,
        'size_width': raster.RasterXSize,
    }


def get_raster_basic_metadata(file):
    """
    Devuelve un json con metadatos basicos de un raster interfaseando con gdal.

    Pensado para mostrar en la vista de importacion de capas, antes de ser incorporado a la IDE.
    """
    raster = gdal.Open(file, gdal.GA_ReadOnly)
    if raster is None:
        return None

    # BUG FIX: tenemos que agregar además el siguiente chequeo para evitar que suban archivos 'rotos' como el caso de z_cams_c_ecmf_20190125000000_prod_fc_sfc_002_uvbedcs.grib
    # que al abrirlo con la línea anterior tira este error pero no lo ataja:
    # Warning: Inside GRIB2Inventory, Message # 2
    # ERROR: Ran out of file reading SECT0
    # There were 518 trailing bytes in the file.

    json = _run_gdalinfo(file, con_stats=False)
    if len(json) == 0:
        return None

    return {
        'driver_short_name': raster.GetDriver().ShortName,
        'driver_long_name': raster.GetDriver().LongName,
        'raster_count': raster.RasterCount,
        'subdataset_count': len(raster.GetSubDatasets()),
        'size_height': raster.RasterYSize,
        'size_width': raster.RasterXSize,
    }


def _run_gdalinfo(file, con_stats=True):
    """Ejecuta el gdalinfo en disco, con o sin stats."""
    stats_param = '-stats' if con_stats else ''
    res = subprocess.check_output('gdalinfo -json {} {}'.format(stats_param, file), shell=True)
    # BUG FIX para casos donde gdalinfo devuelve un json invalido con campostipo: "stdDev":inf,
    res = res.replace(':inf,', ': "inf",').replace(':-inf,', ': "-inf",').replace(':nan,', ': "nan",')
    try:
        gdalinfo_json = json.loads(res)
    except:
        return {}
    if con_stats:
        # Eliminamos el archivo .aux.xml (PAM, Permanent Auxiliar Metadata) que se crea al aplicar gdalinfo -stats
        try:
            os.remove('{}.aux.xml'.format(file))
        except:
            pass

    return gdalinfo_json


def _get_raster_proj_info(raster):
    """
    Devuelve info de proyeccion y extent de un raster o de un dataset dentro del raster.

    En el caso de que haya subdatasets, no hay otra que abrirlos de a uno, no se puede obtener toda esta info con un solo acceso
    """
    # https://gis.stackexchange.com/questions/267321/extracting-epsg-from-a-raster-using-gdal-bindings-in-python
    proj = osr.SpatialReference(wkt=raster.GetProjectionRef())
    proj.AutoIdentifyEPSG()
    srid = proj.GetAttrValue(str('AUTHORITY'), 1)   # el str() debe ir porque el literal no puede ser un unicode, explota

    geotransform = raster.GetGeoTransform()
    minx = geotransform[0]
    maxy = geotransform[3]
    maxx = minx + geotransform[1] * raster.RasterXSize
    miny = maxy + geotransform[5] * raster.RasterYSize
    extent = (minx, miny, maxx, maxy)

    return srid, proj, extent
