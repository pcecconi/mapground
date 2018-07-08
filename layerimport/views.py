# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

from django.shortcuts import render
from django.shortcuts import HttpResponseRedirect
from fileupload.models import Archivo
from layerimport.models import TablaGeografica
from utils.commons import normalizar_texto
from .utils import get_shapefile_files, import_layer, nombre_tabla
from layers.models import Capa, TipoDeGeometria
from MapGround.settings import IMPORT_SCHEMA, ENCODINGS
from MapGround import MapGroundException
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
import os


@login_required
def LayersListView(request):
    template_name = 'layers_list.html'
    shapes = Archivo.objects.filter(extension=".shp")
    l = []
    errores = []
    for shp in shapes:
        try:
            st = get_shapefile_files(unicode(shp.file))
            l.append({"nombre": shp.nombre, "tipo": "Shapefile"})
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
        existe = TablaGeografica.objects.get(tabla=nombre_tabla(request, filename))
        ok = False
        error_msg = 'Ya existe una tabla suya con el nombre {0} en la base de datos.'.format(filename)
    except:
        try:
            archivo = Archivo.objects.get(nombre=filename, extension=".shp")
        except (Archivo.DoesNotExist, MapGroundException) as e:
            ok = False
            error_msg = 'No se pudo encontrar la capa {0} para importar.'.format(filename)
        else:
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
                    conexion_postgres=None,
                    esquema=tabla_geografica.esquema,
                    tabla=tabla_geografica.tabla,
                    tipo_de_geometria=TipoDeGeometria.objects.all()[0],
                    srid=tabla_geografica.srid)

            except:
                ok = False
                error_msg = 'Se produjo un error al intentar importar la capa {0}: {1}'.format(filename, unicode(e))

    if not ok:
        return render(request, template_name, {"capa": filename, "ok": ok, "error_msg": error_msg})
    else:
        return HttpResponseRedirect(reverse('layers:metadatos', args=(c.id_capa,)))
