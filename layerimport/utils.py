# -*- coding: utf-8 -*-
from MapGround import MapGroundException
from django.db import connection
from osgeo import gdal, osr
from MapGround.settings import DEFAULT_SRID, DATABASES

from subprocess import Popen, PIPE
from threading import Thread
from StringIO import StringIO
import os
import subprocess
import re
import glob
import json
import hashlib
import random
import string

epsg_hashes = dict()


GRIB_VARIABLES_DE_INTERES = [
    'TMP',      # temperatura
    'UGRD',     # viento - componente u
    'VGRD',     # viento - componente v
    'APCP',     # precipitacion
    'PRMSL',    # presion atmosferica
    'RH'        # humedad relativa
]


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


def drop_table(schema, table):
    query = ('SELECT DropGeometryColumn(\'%s\',\'%s\',\'geom\'); '
                'DROP TABLE "%s"."%s"') % (schema, table, schema, table)
    cur = connection.cursor()
    cur.execute(query)


def load_shape(shapefile, schema, table, srid=0, encoding='LATIN1'):
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


def import_layer(filename, schema, table, encoding='LATIN1'):
    try:
        st = get_shapefile_files(filename)
    except MapGroundException:
        raise

    srid = DEFAULT_SRID
    try:
        srid = get_epsg_from_prj(st['prj'])
    except KeyError:
        pass

    try:
        load_shape(st['shp'], schema, table, srid, encoding)
    except MapGroundException:
        raise
    print 'import srid %d' % srid

    return srid


def determinar_id_capa(request, nombre):
    return unicode(request.user) + '_' + ((nombre.replace('-', '_')).replace(' ', '_').replace('.', '_').lower())


def get_raster_metadata(file, con_stats=True):
    """Devuelve un json con metadatos detallados de un raster interfaseando con gdal y gdalinfo.

    Pensado para capturar toda la info posible del archivo y almacenarla en la IDE, en el campo Capa.gdal_metadata.
    El parametro optativo con_stats obliga a gdal_info a calcular los valores minimos, maximos y promedios de cada banda.
    """
    raster = gdal.Open(file, gdal.GA_ReadOnly)
    if raster is None:
        return None

    stats_param = '-stats' if con_stats else ''

    # https://gis.stackexchange.com/questions/267321/extracting-epsg-from-a-raster-using-gdal-bindings-in-python
    proj = osr.SpatialReference(wkt=raster.GetProjectionRef())
    proj.AutoIdentifyEPSG()
    srid = proj.GetAttrValue(str('AUTHORITY'), 1)   # el str() debe ir porque el literal no puede ser un unicode, explota

    geotransform = raster.GetGeoTransform()
    minx = geotransform[0]
    maxy = geotransform[3]
    maxx = minx + geotransform[1] * raster.RasterXSize
    miny = maxy + geotransform[5] * raster.RasterYSize
    extent_capa = (minx, miny, maxx, maxy)

    metadata_gdalinfo_json = json.loads(subprocess.check_output('gdalinfo -json {} {}'.format(stats_param, file), shell=True))
    if con_stats:
        # Eliminamos el archivo .aux.xml (PAM, Permanent Auxiliar Metadata) que se crea al aplicar gdalinfo -stats
        try:
            os.remove('{}.aux.xml'.format(file))
        except:
            pass

    variables_detectadas = {}

    # Segun el formato del raster, determinamos las bandas para armar los mapas 'layer_raster_band' (mapas de variables)
    if raster.GetDriver().ShortName == 'GRIB':
        try:
            for banda in metadata_gdalinfo_json['bands']:
                grib_element = banda['metadata']['']['GRIB_ELEMENT']
                if grib_element in GRIB_VARIABLES_DE_INTERES and grib_element not in variables_detectadas:
                    variables_detectadas[grib_element] = str(banda['band'])

            # Invento la componente de viento en base a UGRD y VGRD, y borro las originales
            if 'UGRD' in variables_detectadas and 'VGRD' in variables_detectadas:
                variables_detectadas['WIND'] = '{},{}'.format(variables_detectadas['UGRD'], variables_detectadas['VGRD'])
            if 'UGRD' in variables_detectadas:
                del(variables_detectadas['UGRD'])
            if 'VGRD' in variables_detectadas:
                del(variables_detectadas['VGRD'])
        except:
            print "Error al detectar bandas de interes en raster GRIB!"

    # construimos
    return {
        'driver_short_name': raster.GetDriver().ShortName,
        'driver_long_name': raster.GetDriver().LongName,
        'raster_count': raster.RasterCount,
        'srid': srid,   # puede ser None
        'extent_capa': extent_capa,
        'metadata_json': {
            'gdalinfo': metadata_gdalinfo_json,
            'variables_detectadas': variables_detectadas,
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

    return {
        'driver_short_name': raster.GetDriver().ShortName,
        'driver_long_name': raster.GetDriver().LongName,
        'raster_count': raster.RasterCount,
        'size_height': raster.RasterYSize,
        'size_width': raster.RasterXSize,
    }
