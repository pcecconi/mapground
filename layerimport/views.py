# encoding: utf-8
from django.shortcuts import render_to_response, HttpResponseRedirect
from django.template import RequestContext
from fileupload.models import Archivo
from layerimport.models import TablaGeografica
from utils import get_shapefile_files, import_layer, nombre_tabla, normalizar_texto
from MapGround.settings import MEDIA_ROOT, IMPORT_SCHEMA, ENCODINGS
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
			l.append({"nombre":shp.nombre, "tipo": "Shapefile"})
		except MapGroundException as e:
			errores.append(unicode(e))

	return render_to_response(template_name, { "object_list": l, "errors_list": errores, "encodings": ENCODINGS }, context_instance=RequestContext(request))

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
		error_msg = ('Ya existe una tabla suya con el nombre %s en la base de datos.') % filename
	except:
		try:
			archivo = Archivo.objects.get(nombre=filename, extension=".shp")
			nombreTabla = nombre_tabla(request, filename)
			srid = import_layer(unicode(archivo.file), IMPORT_SCHEMA, nombreTabla, encoding)
			TablaGeografica.objects.create(
				nombre_normalizado=normalizar_texto(filename), 
				nombre_del_archivo=os.path.basename(unicode(archivo.file)), 
				esquema=IMPORT_SCHEMA, 
				srid=srid,
				tabla=nombreTabla,
				owner=request.user)
		except (Archivo.DoesNotExist, MapGroundException) as e:
			ok = False
			if isinstance(e, Archivo.DoesNotExist):
				error_msg = ('No se pudo encontrar la capa "%s" para importar.') % filename
			else:
				error_msg = ('Se produjo un error al intentar importar la capa %s: %s') % (filename, unicode(e))
	if not ok:
		return render_to_response(template_name, { "capa": filename, "ok": ok, "error_msg": error_msg }, context_instance=RequestContext(request))
	else:
		return HttpResponseRedirect(reverse('layers:metadatos',args=(nombreTabla,)))