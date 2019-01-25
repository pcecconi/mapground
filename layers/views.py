# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# core
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template import loader
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.conf import settings

from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

import json, os
from proxy import views
from django.forms.models import inlineformset_factory, modelformset_factory
import urlparse
# models
from layers.models import Capa, Metadatos, Atributo, Categoria, ArchivoSLD, Escala, AreaTematica, CONST_RASTER, CONST_VECTOR, RasterDataSource, VectorDataSource, get_newest_datasource_for_layer
from maps.models import Mapa, ManejadorDeMapas, MapServerLayer
from layerimport.models import TablaGeografica
from layers.forms import MetadatosForm, AtributoForm, make_permisodecapa_form, CapaForm, CategoriaForm, PermisoDeCapaPorGrupoForm, ArchivoSLDForm, make_band_sld_form, EscalaForm, AreaTematicaForm, RasterDataSourceForm
# from mapcache.settings import MAPSERVER_URL
from users.models import ManejadorDePermisos, PermisoDeCapa, PermisoDeCapaPorGrupo
# utils
from utils.commons import normalizar_texto, aplicar_callback, paginar_y_elegir_pagina
from datetime import datetime


import base64
from django.contrib.auth import authenticate, login
from utils import mapserver


#############################################################################
#
def view_or_basicauth(view, request, test_func, realm = "", *args, **kwargs):
    """
    This is a helper function used by both 'logged_in_or_basicauth' and
    'has_perm_or_basicauth' that does the nitty of determining if they
    are already logged in or if they have provided proper http-authorization
    and returning the view if all goes well, otherwise responding with a 401.
    """
    if test_func(request.user):
        # Already logged in, just return the view.
        #
        return view(request, *args, **kwargs)

    # They are not logged in. See if they provided login credentials
    #
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            # NOTE: We are only support basic authentication for now.
            #
            if auth[0].lower() == "basic":
                # uname, passwd = base64.b64decode(auth[1]).split(':')
                uname, passwd = base64.b64decode(auth[1]).decode("ascii").split(':')
                user = authenticate(username=uname, password=passwd)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        request.user = user
                        return view(request, *args, **kwargs)

    # Either they did not provide an authorization header or
    # something in the authorization attempt failed. Send a 401
    # back to them to ask them to authenticate.
    #
    response = HttpResponse()
    response.status_code = 401
    response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
    return response
    
#############################################################################
#
def logged_in_or_basicauth(realm = ""):
    """
    A simple decorator that requires a user to be logged in. If they are not
    logged in the request is examined for a 'authorization' header.

    If the header is present it is tested for basic authentication and
    the user is logged in with the provided credentials.

    If the header is not present a http 401 is sent back to the
    requestor to provide credentials.

    The purpose of this is that in several django projects I have needed
    several specific views that need to support basic authentication, yet the
    web site as a whole used django's provided authentication.

    The uses for this are for urls that are access programmatically such as
    by rss feed readers, yet the view requires a user to be logged in. Many rss
    readers support supplying the authentication credentials via http basic
    auth (and they do NOT support a redirect to a form where they post a
    username/password.)

    Use is simple:

    @logged_in_or_basicauth
    def your_view:
        ...

    You can provide the name of the realm to ask for authentication within.
    """
    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return view_or_basicauth(func, request,
                                     lambda u: u.is_authenticated(),
                                     realm, *args, **kwargs)
        return wrapper
    return view_decorator

#############################################################################
#
def has_perm_or_basicauth(perm, realm = ""):
    """
    This is similar to the above decorator 'logged_in_or_basicauth'
    except that it requires the logged in user to have a specific
    permission.

    Use:

    @logged_in_or_basicauth('asforums.view_forumcollection')
    def your_view:
        ...

    """
    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return view_or_basicauth(func, request,
                                     lambda u: u.has_perm(perm),
                                     realm, *args, **kwargs)
        return wrapper
    return view_decorator

# @login_required    
def ultimas(request):
    lista_capas = ManejadorDePermisos.capas_de_usuario(request.user, 'all')
    lista_capas=lista_capas.order_by('-timestamp_alta')[:settings.CANTIDAD_DE_ULTIMAS_CAPAS]
    ManejadorDePermisos.anotar_permiso_a_queryset_de_capas(request.user, lista_capas)
    lista_categorias=ManejadorDePermisos.capas_agrupadas_por_categoria()
    lista_areas_tematicas=ManejadorDePermisos.capas_agrupadas_por_area_tematica()
    lista_escalas=ManejadorDePermisos.capas_agrupadas_por_escala()
    
    return render(request, 'layers/index.html', {'lista_capas': lista_capas, 'cantidad_total': lista_capas.count(), 'page_title': 'Capas más recientes', 'lista_categorias': lista_categorias, 'lista_areas_tematicas': lista_areas_tematicas, 'lista_escalas': lista_escalas})    

# @login_required
def index(request):
    vista=request.GET.get('view')
    order_by=request.GET.get('order_by')
    if not vista or not order_by:
        return HttpResponseRedirect(reverse('layers:index')+'?view=own&order_by=mr')
    pagina = request.GET.get('p')
    
    if vista in ('all','list'):
        lista_capas = ManejadorDePermisos.capas_de_usuario(request.user, 'all') # casos 'own' y 'all', y si no devuelve qset vacio
    else:
        lista_capas = ManejadorDePermisos.capas_de_usuario(request.user, 'own') # casos 'own' y 'all', y si no devuelve qset vacio
    
    if order_by=='mr':
        lista_capas=lista_capas.order_by('-timestamp_alta')
    elif order_by=='lr':
        lista_capas=lista_capas.order_by('timestamp_alta')
    elif order_by=='mrm':
        lista_capas=lista_capas.order_by('-timestamp_modificacion')
    elif order_by=='lrm':
        lista_capas=lista_capas.order_by('timestamp_modificacion')
    elif order_by=='az':
        lista_capas=lista_capas.order_by('metadatos__titulo')
    elif order_by=='za':
        lista_capas=lista_capas.order_by('-metadatos__titulo')

    cantidad_total = lista_capas.count()
    if vista=='list':
        lista_capas=paginar_y_elegir_pagina(lista_capas, pagina, settings.CANTIDAD_DE_CAPAS_EN_LISTA_POR_PAGINA)
    else:
        lista_capas=paginar_y_elegir_pagina(lista_capas, pagina, settings.CANTIDAD_DE_CAPAS_POR_PAGINA)
    ManejadorDePermisos.anotar_permiso_a_queryset_de_capas(request.user, lista_capas)
    lista_categorias=ManejadorDePermisos.capas_agrupadas_por_categoria()
    lista_areas_tematicas=ManejadorDePermisos.capas_agrupadas_por_area_tematica()
    lista_escalas=ManejadorDePermisos.capas_agrupadas_por_escala()

    return render(request, 'layers/index.html', {'lista_capas': lista_capas, 'cantidad_total': cantidad_total, 'order_by': order_by, 'lista_categorias': lista_categorias, 'lista_areas_tematicas': lista_areas_tematicas, 'lista_escalas': lista_escalas})    


# @login_required
def detalle_capa(request, id_capa):
    capa = get_object_or_404(Capa, id_capa=id_capa)
    ManejadorDePermisos.anotar_permiso_a_capa(request.user, capa)
    if capa.permiso is None:
        return HttpResponseRedirect(reverse('layers:index'))
    ManejadorDeMapas.commit_mapfile(id_capa)
    permisos=ManejadorDePermisos.usuarios_con_permiso_a_capa(capa)

    if request.user==capa.owner or request.user.is_superuser:
        mapas=capa.mapa_set.filter(tipo_de_mapa='general').distinct()
    else:
        mapas=capa.mapa_set.filter(tipo_de_mapa='general', publico=True).distinct()
    return render(request, 'layers/detalle_capa.html', {'capa': capa, 'permisos': permisos, 'mapas': mapas, 'MAPCACHE_URL': settings.MAPCACHE_URL })


# @login_required
def detalle_categoria(request, categoriaid):
    if (categoriaid!='0'):
        categoria = get_object_or_404(Categoria, pk=categoriaid)
        lista_capas = Capa.objects.filter(metadatos__categorias=categoria)
    else:
        lista_capas = Capa.objects.filter(metadatos__categorias=None)
        categoria = {'nombre': 'Sin categoría', 'descripcion': 'Las siguientes capas no tienen una categoría asignada'}

    lista_capas = ManejadorDePermisos.capas_de_usuario(request.user, 'all', lista_capas).order_by('metadatos__titulo')    
    cantidad_total = lista_capas.count()

    pagina = request.GET.get('p')
    lista_capas=paginar_y_elegir_pagina(lista_capas, pagina, settings.CANTIDAD_DE_CAPAS_POR_PAGINA)
    ManejadorDePermisos.anotar_permiso_a_queryset_de_capas(request.user, lista_capas)
    lista_categorias=ManejadorDePermisos.capas_agrupadas_por_categoria()

    return render(request, 'layers/detalle_categoria.html', {'lista_capas': lista_capas, 'cantidad_total': cantidad_total, 'categoria': categoria, 'lista_categorias': lista_categorias})    

def detalle_escala(request, escalaid):
    if (escalaid!='0'):
        escala = get_object_or_404(Escala, pk=escalaid)
        lista_capas = Capa.objects.filter(metadatos__escala=escala)
    else:
        lista_capas = Capa.objects.filter(metadatos__escala=None)
        escala = {'nombre': 'Sin escala', 'descripcion': 'Las siguientes capas no tienen una escala asignada'}

    lista_capas = ManejadorDePermisos.capas_de_usuario(request.user, 'all', lista_capas).order_by('metadatos__titulo')    
    cantidad_total = lista_capas.count()

    pagina = request.GET.get('p')
    lista_capas=paginar_y_elegir_pagina(lista_capas, pagina, settings.CANTIDAD_DE_CAPAS_POR_PAGINA)
    ManejadorDePermisos.anotar_permiso_a_queryset_de_capas(request.user, lista_capas)
    lista_escalas=ManejadorDePermisos.capas_agrupadas_por_escala()

    return render(request, 'layers/detalle_escala.html', {'lista_capas': lista_capas, 'cantidad_total': cantidad_total, 'escala': escala, 'lista_escalas': lista_escalas})    

def detalle_area_tematica(request, areatematicaid):
    if (areatematicaid!='0'):
        area_tematica = get_object_or_404(AreaTematica, pk=areatematicaid)
        lista_capas = Capa.objects.filter(metadatos__area_tematica=area_tematica)
    else:
        lista_capas = Capa.objects.filter(metadatos__area_tematica=None)
        area_tematica = {'nombre': 'Sin área temática', 'descripcion': 'Las siguientes capas no tienen un área temática asignada'}

    lista_capas = ManejadorDePermisos.capas_de_usuario(request.user, 'all', lista_capas).order_by('metadatos__titulo')    
    cantidad_total = lista_capas.count()

    pagina = request.GET.get('p')
    lista_capas=paginar_y_elegir_pagina(lista_capas, pagina, settings.CANTIDAD_DE_CAPAS_POR_PAGINA)
    ManejadorDePermisos.anotar_permiso_a_queryset_de_capas(request.user, lista_capas)
    lista_areas_tematicas=ManejadorDePermisos.capas_agrupadas_por_area_tematica()

    return render(request, 'layers/detalle_area_tematica.html', {'lista_capas': lista_capas, 'cantidad_total': cantidad_total, 'area_tematica': area_tematica, 'lista_areas_tematicas': lista_areas_tematicas})    

# @login_required
def buscar(request):
    texto = normalizar_texto(request.GET.get('texto',''))
    #texto = unicode(request.GET.get('texto',''))
    pagina = request.GET.get('p')
    
    lista_capas=[]
    cantidad_total = 0
    if texto!='':
        # busco metadatos con matchings
        resMetadatos=Metadatos.objects.search(texto)
        # busco capas asociados a esos metadatos
        lista_capas=Capa.objects.filter(metadatos__in=resMetadatos)
        # filtro por permiso y ordeno
        lista_capas = ManejadorDePermisos.capas_de_usuario(request.user, 'all', lista_capas).order_by('-timestamp_alta')
        # anoto permisos
        ManejadorDePermisos.anotar_permiso_a_queryset_de_capas(request.user, lista_capas)
        cantidad_total = lista_capas.count()

        lista_capas=paginar_y_elegir_pagina(lista_capas, pagina, settings.CANTIDAD_DE_CAPAS_POR_PAGINA)
    lista_categorias=ManejadorDePermisos.capas_agrupadas_por_categoria()
    lista_areas_tematicas=ManejadorDePermisos.capas_agrupadas_por_area_tematica()
    lista_escalas=ManejadorDePermisos.capas_agrupadas_por_escala()
        
    return render(request, 'layers/index.html', {'lista_capas': lista_capas, 'cantidad_total': cantidad_total, 'lista_categorias': lista_categorias, 'lista_areas_tematicas': lista_areas_tematicas, 'lista_escalas': lista_escalas})

@login_required
def metadatos(request, id_capa):
    c=get_object_or_404(Capa, id_capa=id_capa)
    if ManejadorDePermisos.permiso_de_capa(request.user, id_capa) not in ('owner','write','superuser'):
        return HttpResponseRedirect(reverse('layers:index'))

    m=c.metadatos
    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('layers:detalle_capa', kwargs={'id_capa':id_capa}))
        form = MetadatosForm(request.POST, instance=m)
        if form.is_valid():
            form.save()
            #c.save() # no es necesario llamar al save de la capa para actualizar timestamp y regenerarmapa, usamos una senial
            if '_save_and_continue' in request.POST:
                return HttpResponseRedirect(reverse('layers:metadatos', kwargs={'id_capa':id_capa}))
            if '_save_and_next' in request.POST:
                return HttpResponseRedirect(reverse('layers:atributos', kwargs={'id_capa':id_capa}))
            return HttpResponseRedirect(reverse('layers:detalle_capa', kwargs={'id_capa':id_capa}))
    else:
        form = MetadatosForm(instance=m)

    return render(request, 'layers/metadatos.html', {'form': form, 'capa': c })

@login_required
def actualizar_capa(request, id_capa):
    c=get_object_or_404(Capa, id_capa=id_capa)
    if ManejadorDePermisos.permiso_de_capa(request.user, id_capa) not in ('owner','write','superuser'):
        return HttpResponseRedirect(reverse('layers:index'))

    m=c.metadatos
    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('layers:detalle_capa', kwargs={'id_capa':id_capa}))
        form = MetadatosForm(request.POST, instance=m)
        if form.is_valid():
            form.save()
            #c.save() # no es necesario llamar al save de la capa para actualizar timestamp y regenerarmapa, usamos una senial
            if '_save_and_continue' in request.POST:
                return HttpResponseRedirect(reverse('layers:metadatos', kwargs={'id_capa':id_capa}))
            if '_save_and_next' in request.POST:
                return HttpResponseRedirect(reverse('layers:atributos', kwargs={'id_capa':id_capa}))
            return HttpResponseRedirect(reverse('layers:detalle_capa', kwargs={'id_capa':id_capa}))
    else:
        form = MetadatosForm(instance=m)

    return render(request, 'layers/metadatos.html', {'form': form, 'capa': c })


@login_required
def atributos(request, id_capa):
    c=get_object_or_404(Capa, id_capa=id_capa)
    if ManejadorDePermisos.permiso_de_capa(request.user, id_capa) not in ('owner','write','superuser'):
        return HttpResponseRedirect(reverse('layers:index'))        

    m=c.metadatos
    # definimos un queryset para instanciar el inlineformset vacio o por post
    queryset=Atributo.objects.filter(metadatos=m).exclude(nombre_del_campo='geom').exclude(nombre_del_campo='gid')
    AtributoInlineFormSet = inlineformset_factory(Metadatos, Atributo, form=AtributoForm, can_delete=False, extra=0)
    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('layers:detalle_capa', kwargs={'id_capa':id_capa}))
        formset = AtributoInlineFormSet(request.POST, request.FILES, instance=m, queryset=queryset) 
        if formset.is_valid():
            formset.save()
            c.save() # a diferencia de metadatos, actualizamos timestamp de la capa aca para evitar un save por cada atributo en el formsave si usaramos seniales
            if '_save_and_continue' in request.POST:
                return HttpResponseRedirect(reverse('layers:atributos', kwargs={'id_capa':id_capa}))
            if '_save_and_next' in request.POST:
                return HttpResponseRedirect(reverse('layers:permisos', kwargs={'id_capa':id_capa}))
            return HttpResponseRedirect(reverse('layers:detalle_capa', kwargs={'id_capa':id_capa}))
    else:
        formset = AtributoInlineFormSet(instance=m, queryset=queryset)

    return render(request, 'layers/atributos.html', {'formset': formset, 'capa': c })


@login_required
def permisos(request, id_capa):
    c=get_object_or_404(Capa, id_capa=id_capa)
    if ManejadorDePermisos.permiso_de_capa(request.user, id_capa) not in ('owner','write','superuser'):
        return HttpResponseRedirect(reverse('layers:index'))
    if ManejadorDePermisos.permiso_de_capa(request.user, id_capa) == 'write':
        return render(request, 'layers/permisos.html', {'formset': None, 'capa': c })        

    #PermisoDeCapaInlineFormSet = inlineformset_factory(Capa, PermisoDeCapa, form=PermisoDeCapaForm, can_delete=True, extra=2)
    queryset=PermisoDeCapa.objects.filter(capa=c).exclude(user__username__in=['admin','mapground'])
    DynamicPermisoDeCapaForm = make_permisodecapa_form(request.user)
    PermisoDeCapaInlineFormSet = inlineformset_factory(Capa, PermisoDeCapa, form=DynamicPermisoDeCapaForm, can_delete=True, extra=2)

    PermisoDeCapaPorGrupoInlineFormSet = inlineformset_factory(Capa, PermisoDeCapaPorGrupo, form=PermisoDeCapaPorGrupoForm, can_delete=True, extra=2)
    
    
    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('layers:detalle_capa', kwargs={'id_capa':id_capa}))
        formset = PermisoDeCapaInlineFormSet(request.POST, request.FILES, instance=c, queryset=queryset)
        formset_grupo = PermisoDeCapaPorGrupoInlineFormSet(request.POST, request.FILES, instance=c)
        capa_form = CapaForm(request.POST, request.FILES, instance=c)
        if capa_form.is_valid(): # siempre da True, pero internamente cambia algunas cosas
            if 'wxs_publico' in capa_form.changed_data: # con esto evitamos una actualizacion del repo de usuarios si en la pantalla solo se modifican permisos de usuarios y/o grupos            
                capa_form.save() # TODO: esta logica creo que no escala cuando agreguemos cambio de owner, habra que invertir y llamar al manejadordemapas
        if formset.is_valid() and formset_grupo.is_valid():
            formset.save()
            formset_grupo.save()
            # las actualizaciones de los mapas las actualizamos con seniales, no aca, pero podrian hacerse aca detectando changed_datas
            if '_save_and_continue' in request.POST:
                return HttpResponseRedirect(reverse('layers:permisos', kwargs={'id_capa':id_capa}))
            return HttpResponseRedirect(reverse('layers:detalle_capa', kwargs={'id_capa':id_capa}))
    else:
        formset = PermisoDeCapaInlineFormSet(instance=c, queryset=queryset)
        formset_grupo = PermisoDeCapaPorGrupoInlineFormSet(instance=c)
        
        capa_form = CapaForm(instance=c)

    return render(request, 'layers/permisos.html', {'formset_grupo': formset_grupo, 'formset': formset, 'capa_form': capa_form, 'capa': c })


@login_required
def categorias(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('layers:index'))

    CategoriaFormSet = modelformset_factory(Categoria, form=CategoriaForm, can_delete=True, extra=2)

    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('layers:index'))
        formset = CategoriaFormSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            if '_save_and_continue' in request.POST:
                return HttpResponseRedirect(reverse('layers:categorias'))
            return HttpResponseRedirect(reverse('layers:index'))
    else:
        formset = CategoriaFormSet()

    return render(request, 'layers/categorias.html', {'formset': formset})

@login_required
def escalas(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('layers:index'))

    EscalaFormSet = modelformset_factory(Escala, form=EscalaForm, can_delete=True, extra=2)

    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('layers:index'))
        formset = EscalaFormSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            if '_save_and_continue' in request.POST:
                return HttpResponseRedirect(reverse('layers:escalas'))
            return HttpResponseRedirect(reverse('layers:index'))
    else:
        formset = EscalaFormSet()

    return render(request, 'layers/escalas.html', {'formset': formset})

@login_required
def areas_tematicas(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('layers:index'))

    AreaTematicaFormSet = modelformset_factory(AreaTematica, form=AreaTematicaForm, can_delete=True, extra=2)

    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('layers:index'))
        formset = AreaTematicaFormSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            if '_save_and_continue' in request.POST:
                return HttpResponseRedirect(reverse('layers:areas_tematicas'))
            return HttpResponseRedirect(reverse('layers:index'))
    else:
        formset = AreaTematicaFormSet()

    return render(request, 'layers/areas_tematicas.html', {'formset': formset})

@login_required
def borrar_capa(request, id_capa):
    capa = get_object_or_404(Capa, id_capa=id_capa)
    if ManejadorDePermisos.permiso_de_capa(request.user, id_capa) in ('owner','superuser'):
        if len(capa.mapa_set.filter(tipo_de_mapa='general'))==0: # si la capa no esta en ningun mapa...
            capa.delete()
    return HttpResponseRedirect(reverse('layers:index'))

@logged_in_or_basicauth()
def wxs(request, id_capa):
    capa = get_object_or_404(Capa, id_capa=id_capa)
    if ManejadorDePermisos.permiso_de_capa(request.user, id_capa) is None:
        return HttpResponseForbidden()

    extra_requests_args = {}
    mapfile=ManejadorDeMapas.commit_mapfile(id_capa+'_layer_srs')
    # remote_url = MAPSERVER_URL+'?map='+mapfile # +'&mode=browse&layers=all&template=openlayers'
    remote_url = mapserver.get_wms_url(id_capa+'_layer_srs')
    sld = capa.dame_sld_default()
    if sld is not None:
        remote_url = remote_url + '&SLD='+sld
        # print remote_url
    return views.proxy_view(request, remote_url, extra_requests_args)

def wxs_public(request):
    extra_requests_args = {}
    mapfile=ManejadorDeMapas.commit_mapfile('mapground_public_layers')
    # remote_url = MAPSERVER_URL+'?map='+mapfile
    remote_url = mapserver.get_wms_url('mapground_public_layers')
    return views.proxy_view(request, remote_url, extra_requests_args)


@logged_in_or_basicauth()
def wxs_raster_band(request, id_mapa):
    mapa = get_object_or_404(Mapa, id_mapa=id_mapa, tipo_de_mapa='layer_raster_band')
    ManejadorDePermisos.anotar_permiso_a_mapa(request.user, mapa)
    if mapa.permiso is None:
        return HttpResponseForbidden()
    extra_requests_args = {}
    mapfile = ManejadorDeMapas.commit_mapfile(mapa.id_mapa)
    remote_url = mapserver.get_wms_url(mapa.id_mapa)
    sld = mapa.mapserverlayer_set.first().archivo_sld
    if sld:
        remote_url = remote_url + '&SLD=' + urlparse.urljoin(settings.SITE_URL, sld.filename.url)
    return views.proxy_view(request, remote_url, extra_requests_args)


# @login_required
def download(request, id_capa, format='shapezip'):
    capa = get_object_or_404(Capa, id_capa=id_capa)
    if ManejadorDePermisos.permiso_de_capa(request.user, id_capa) is None:
        return HttpResponseForbidden()
    # Ahora el download de capas solo se invoca para shapes, en el caso rasters lo sirve directamente nginx
    if capa.tipo_de_capa == CONST_RASTER:
        return views.proxy_view(request, settings.UPLOADED_RASTERS_URL + unicode(capa.owner) + '/' + capa.nombre_del_archivo)
    elif capa.tipo_de_capa == CONST_VECTOR:
        extra_requests_args = {}
        if format not in ['shapezip', 'geojson', 'csv']:
            format = 'shapezip'
        mapfile=ManejadorDeMapas.commit_mapfile(id_capa+'_layer_srs')
        # remote_url = MAPSERVER_URL+'?map='+mapfile+'&SERVICE=WFS&VERSION=1.0.0&REQUEST=getfeature&TYPENAME='+capa.nombre+'&outputformat='+format
        remote_url = mapserver.get_feature_url(id_capa+'_layer_srs', capa.nombre, format)
        print remote_url
        return views.proxy_view(request, remote_url, extra_requests_args)

# primera implementacion de wxs usando mapscript
# def wxs():
#     path_map = 'ogc_ori.map'
#     if not request.vars:
#         return ''
#     req = mapscript.OWSRequest()
#     for v in request.vars:
#         req.setParameter(v, request.vars[v])

#     map = mapscript.mapObj(path_map)
#     mapscript.msIO_installStdoutToBuffer()
#     map.OWSDispatch(req)

#     content_type = mapscript.msIO_stripStdoutBufferContentType()
#     content = mapscript.msIO_getStdoutBufferBytes()
#     response.header = "Content-Type","%s; charset=utf-8"%content_type
#     return content


@login_required
def sld(request, id_capa):
    capa = get_object_or_404(Capa, id_capa=id_capa)
    if ManejadorDePermisos.permiso_de_capa(request.user, id_capa) not in ('owner', 'write', 'superuser'):
        return HttpResponseForbidden()

    # form1: ArchivoSLD, o sea, todos los SLDs de la capa
    ArchivoSLDInlineFormSet = inlineformset_factory(Capa, ArchivoSLD, form=ArchivoSLDForm, can_delete=True, extra=1)

    # form2: SLD por banda
    DynamicBandSLDForm = make_band_sld_form(capa)
    BandSLDFormInlineFormSet = inlineformset_factory(Capa, MapServerLayer, form=DynamicBandSLDForm, can_delete=False, extra=0)

    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('layers:detalle_capa', kwargs={'id_capa': id_capa}))

        formset_archivos_sld = ArchivoSLDInlineFormSet(request.POST, request.FILES, instance=capa)
        formset_bandas_sld = BandSLDFormInlineFormSet(request.POST, request.FILES, instance=capa)

        if formset_archivos_sld.is_valid() and formset_bandas_sld.is_valid():
            # grabamos primero las bandas por si el usuario decide borrar un SLD activo:
            # de esta manera se garantiza un save correcto de SLDs activos (luego el delete se hace en cascada por Django),
            # si lo hacemos al reves se genera una excepcion porque el SLD ya no existira en este punto

            # formset_bandas_sld.save()
            # reemplazamos el clasico formset.save() por las siguientes lineas que solo graban los objetos que han sido modificados
            for form in formset_bandas_sld:
                if 'archivo_sld' in form.changed_data:
                    form.save()

            # formset_archivos_sld.save()
            # reemplazamos el clasico formset.save() por las siguientes lineas que cargan el username y el timestamp en cada objeto
            modificadas = []
            for form in formset_archivos_sld:    # detecto los objetos que tienen nuevos slds y me guardo los ids
                if 'filename' in form.changed_data:
                    modificadas.append(form.instance.id_archivo_sld)
            instances = formset_archivos_sld.save(commit=False)  # grabo los forms obteniendo las instancias
            for obj in instances:
                if obj.pk is None:
                    obj.user_alta = obj.user_modificacion = request.user.username
                    obj.timestamp_alta = obj.timestamp_modificacion = datetime.now()
                elif obj.id_archivo_sld in modificadas:
                    obj.user_modificacion = request.user.username
                    obj.timestamp_modificacion = datetime.now()
                obj.save()

            for obj in formset_archivos_sld.deleted_objects:
                obj.delete()

            if '_save_and_continue' in request.POST:
                return HttpResponseRedirect(reverse('layers:sld', kwargs={'id_capa': id_capa}))
            return HttpResponseRedirect(reverse('layers:detalle_capa', kwargs={'id_capa': id_capa}))
    else:
        formset_archivos_sld = ArchivoSLDInlineFormSet(instance=capa)
        formset_bandas_sld = BandSLDFormInlineFormSet(instance=capa, queryset=MapServerLayer.objects.filter(capa=capa, mapa__tipo_de_mapa='layer_raster_band').order_by('mapa__nombre'))

    return render(request, 'layers/sld.html', {'formset_archivos_sld': formset_archivos_sld, 'formset_bandas_sld': formset_bandas_sld, 'capa': capa})


def archivos_sld_de_capa(request, id_capa):
    capa = get_object_or_404(Capa, id_capa=id_capa)
    ManejadorDePermisos.anotar_permiso_a_capa(request.user, capa)
    res=[]
    if capa.permiso is None:
        return HttpResponse(json.dumps(res), content_type="application/json")
    
    for sld in capa.archivosld_set.all().order_by('-timestamp_modificacion'):
        res.append({'id':sld.id, 'id_archivo_sld': sld.id_archivo_sld, 'url':sld.filename.url.replace('.sld','.png'), 'descripcion':sld.descripcion, 'default':sld.default})    

    return HttpResponse(json.dumps(res), content_type="application/json")

@login_required
def actualizaciones(request, id_capa):
    capa = get_object_or_404(Capa, id_capa=id_capa)
    if ManejadorDePermisos.permiso_de_capa(request.user, id_capa) not in ('owner', 'write', 'superuser'):
        return HttpResponseForbidden()

    # form1: RasterDataSource o VectorDataSouce, o sea, todos los datasets de la capa
    ActualizacionesInlineFormSet = inlineformset_factory(Capa, RasterDataSource, form=RasterDataSourceForm, can_delete=True, extra=0)

    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('layers:detalle_capa', kwargs={'id_capa': id_capa}))

        formset_actualizaciones = ActualizacionesInlineFormSet(request.POST, request.FILES, instance=capa)

        if formset_actualizaciones.is_valid():
            instances = formset_actualizaciones.save(commit=False)  # grabo los forms obteniendo las instancias

            layer_changed = False
            for form in formset_actualizaciones:
                if 'data_datetime' in form.changed_data:
                    layer_changed = True
                    form.save()

            for obj in formset_actualizaciones.deleted_objects:
                if not obj.is_only_datasource:
                    layer_changed = True
                    obj.delete()
                else:
                    print "Can't delete only datasource on layer %s"%(capa.id_capa)

            # Usamos un flag para hacer un unico save independientemente de la 
            # cantidad de cambios que haya
            if layer_changed:
                nds = get_newest_datasource_for_layer(capa)
                capa.actualizar_datasource(nds)

            if '_save_and_continue' in request.POST:
                return HttpResponseRedirect(reverse('layers:actualizaciones', kwargs={'id_capa': id_capa}))
            return HttpResponseRedirect(reverse('layers:detalle_capa', kwargs={'id_capa': id_capa}))
    else:
        formset_actualizaciones = ActualizacionesInlineFormSet(instance=capa)

    return render(request, 'layers/actualizaciones.html', {'formset_actualizaciones': formset_actualizaciones, 'capa': capa})
