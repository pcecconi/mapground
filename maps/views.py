# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# core
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from proxy import views
from maps.models import Mapa, ManejadorDeMapas, TMSBaseLayer, MapServerLayer
from maps.forms import MapaForm
# from mapcache.settings import MAPSERVER_URL
from django.shortcuts import get_object_or_404

from layers.models import Categoria, Escala, Capa

from users.models import ManejadorDePermisos

from utils.commons import normalizar_texto, aplicar_callback, paginar_y_elegir_pagina
from django.conf import settings
import urllib2
# from utils.xml_to_json import xml_to_json
import xml.etree.cElementTree as etree
import json
import urlparse
from utils import mapserver

# @login_required
def index(request):
    vista=request.GET.get('view')
    order_by=request.GET.get('order_by')
    if not vista or not order_by:
        return HttpResponseRedirect(reverse('maps:index')+'?view=own&order_by=mr')
    pagina = request.GET.get('p')
    
    if vista in ('all','list'):
        lista_mapas = ManejadorDePermisos.mapas_de_usuario(request.user, 'all') # casos 'own' y 'all', y si no devuelve qset vacio
    else:
        lista_mapas = ManejadorDePermisos.mapas_de_usuario(request.user, 'own') # casos 'own' y 'all', y si no devuelve qset vacio
        
    if order_by=='mr':
        lista_mapas=lista_mapas.order_by('-timestamp_alta')
    elif order_by=='lr':
        lista_mapas=lista_mapas.order_by('timestamp_alta')
    elif order_by=='mrm':
        lista_mapas=lista_mapas.order_by('-timestamp_modificacion')
    elif order_by=='lrm':
        lista_mapas=lista_mapas.order_by('timestamp_modificacion')
    elif order_by=='az':
        lista_mapas=lista_mapas.order_by('titulo')
    elif order_by=='za':
        lista_mapas=lista_mapas.order_by('-titulo')

    cantidad_total = lista_mapas.count()
    if vista=='list':
        lista_mapas=paginar_y_elegir_pagina(lista_mapas, pagina, settings.CANTIDAD_DE_MAPAS_EN_LISTA_POR_PAGINA)
    else:
        lista_mapas=paginar_y_elegir_pagina(lista_mapas, pagina, settings.CANTIDAD_DE_MAPAS_POR_PAGINA)
    ManejadorDePermisos.anotar_permiso_a_queryset_de_mapas(request.user, lista_mapas)
    lista_categorias=ManejadorDePermisos.mapas_agrupados_por_categoria()
    lista_escalas=ManejadorDePermisos.mapas_agrupados_por_escala()

    return render(request, 'maps/index.html', {'lista_mapas': lista_mapas, 'cantidad_total': cantidad_total, 'order_by': order_by, 'lista_categorias': lista_categorias, 'lista_escalas': lista_escalas})    

def ultimos(request):
    lista_mapas = ManejadorDePermisos.mapas_de_usuario(request.user, 'all')
    lista_mapas=lista_mapas.order_by('-timestamp_alta')[:settings.CANTIDAD_DE_ULTIMOS_MAPAS]
    ManejadorDePermisos.anotar_permiso_a_queryset_de_mapas(request.user, lista_mapas)
    lista_categorias=ManejadorDePermisos.mapas_agrupados_por_categoria()
    lista_escalas=ManejadorDePermisos.mapas_agrupados_por_escala()

    return render(request, 'maps/index.html', {'lista_mapas': lista_mapas, 'cantidad_total': lista_mapas.count(), 'page_title': 'Mapas más recientes', 'lista_categorias': lista_categorias, 'lista_escalas': lista_escalas})    

def detalle_categoria(request, categoriaid):
    if (categoriaid!='0'):
        categoria = get_object_or_404(Categoria, pk=categoriaid)
        lista_mapas = Mapa.objects.filter(tipo_de_mapa='general').filter(categorias=categoria)
    else:
        lista_mapas = Mapa.objects.filter(tipo_de_mapa='general').filter(categorias=None)
        categoria = {'nombre': 'Sin categoría', 'descripcion': 'Los siguientes mapas no tienen una categoría asignada'}
    
    lista_mapas = ManejadorDePermisos.mapas_de_usuario(request.user, 'all', lista_mapas).order_by('titulo')    
    cantidad_total = lista_mapas.count()

    pagina = request.GET.get('p')
    lista_mapas=paginar_y_elegir_pagina(lista_mapas, pagina, settings.CANTIDAD_DE_MAPAS_POR_PAGINA)
    ManejadorDePermisos.anotar_permiso_a_queryset_de_mapas(request.user, lista_mapas)
    lista_categorias=ManejadorDePermisos.mapas_agrupados_por_categoria()

    return render(request, 'maps/detalle_categoria.html', {'lista_mapas': lista_mapas, 'cantidad_total': cantidad_total, 'categoria': categoria, 'lista_categorias': lista_categorias}) 

def detalle_escala(request, escalaid):
    if (escalaid!='0'):
        escala = get_object_or_404(Escala, pk=escalaid)
        lista_mapas = Mapa.objects.filter(tipo_de_mapa='general').filter(escala=escala)
    else:
        lista_mapas = Mapa.objects.filter(tipo_de_mapa='general').filter(escala=None)
        escala = {'nombre': 'Sin escala', 'descripcion': 'Los siguientes mapas no tienen una escala asignada'}

    lista_mapas = ManejadorDePermisos.mapas_de_usuario(request.user, 'all', lista_mapas).order_by('titulo')    
    cantidad_total = lista_mapas.count()

    pagina = request.GET.get('p')
    lista_mapas=paginar_y_elegir_pagina(lista_mapas, pagina, settings.CANTIDAD_DE_MAPAS_POR_PAGINA)
    ManejadorDePermisos.anotar_permiso_a_queryset_de_mapas(request.user, lista_mapas)
    lista_escalas=ManejadorDePermisos.mapas_agrupados_por_escala()

    return render(request, 'maps/detalle_escala.html', {'lista_mapas': lista_mapas, 'cantidad_total': cantidad_total, 'escala': escala, 'lista_escalas': lista_escalas})    


def detalle_mapa(request, id_mapa):
    mapa = get_object_or_404(Mapa, id_mapa=id_mapa)
    ManejadorDePermisos.anotar_permiso_a_mapa(request.user, mapa)
    if mapa.permiso is None:
        return HttpResponseRedirect(reverse('maps:index'))
    ManejadorDeMapas.commit_mapfile(id_mapa) 
    return render(request, 'maps/detalle_mapa.html', {'mapa': mapa, 'MAPCACHE_URL': settings.MAPCACHE_URL })

@login_required
def crear_mapa(request):
    if request.method == 'POST':
        if 'layers' in request.POST:
            posted_layers = json.loads(request.POST.get('layers'))
            mapa=Mapa(owner=request.user, tipo_de_mapa='general',srs = '3857')
            mapa.titulo=request.POST.get('title')
            nombre=normalizar_texto(mapa.titulo)
            
            #calculamos nombre y id de mapa
            if len(Mapa.objects.filter(id_mapa='%s_%s'%(request.user.username,nombre)))>0:
                sufijo=2
                while len(Mapa.objects.filter(id_mapa='%s_%s_%s'%(request.user.username,nombre,str(sufijo))))>0:
                    sufijo+=1
                nombre=nombre+'_%s'%(str(sufijo))
            mapa.nombre=nombre
            mapa.id_mapa='%s_%s'%(request.user.username,nombre)
            # armamos los objetos y grabamos
            try:
                mapa.tms_base_layer=TMSBaseLayer.objects.get(pk=posted_layers['baseLayer'])
            except:
                pass
            if 'extent' in posted_layers:
                mapa.extent=posted_layers['extent']
            mapa.save(escribir_imagen_y_mapfile=False)      
            if 'layers' in posted_layers:
                for idx, l in enumerate(posted_layers['layers']):
                    try:
                        capa=Capa.objects.get(id_capa=l['layerId'])
                        if ManejadorDePermisos.permiso_de_capa(request.user,capa) is not None:
                            if l['sldId'] == 0:
                                try:
                                    sld = capa.archivosld_set.filter(default=True)[0]
                                except:
                                    sld = None
                            else:
                                try:
                                    sld = capa.archivosld_set.filter(id=l['sldId'])[0]
                                    # sld = capa.archivosld_set.filter(default=True)[0]
                                except:
                                    sld = None
                            try:
                                feature_info=l['tooltip']
                            except:
                                feature_info=True
                            if 'bandId' in l and l['bandId']:
                                MapServerLayer(mapa=mapa,capa=capa,bandas=l['bandId'],orden_de_capa=idx,feature_info=feature_info,archivo_sld=sld).save()
                            else:
                                MapServerLayer(mapa=mapa,capa=capa,orden_de_capa=idx,feature_info=feature_info,archivo_sld=sld).save()
                    except:
                        pass
            #ManejadorDeMapas.generar_thumbnail(mapa.id_mapa)
            mapa.save()
            return HttpResponseRedirect(reverse('maps:metadatos', kwargs={'id_mapa':mapa.id_mapa}))
    
    return HttpResponseRedirect(reverse('maps:visor'))

@login_required
def actualizar_mapa(request,id_mapa):
    mapa = get_object_or_404(Mapa, id_mapa=id_mapa)
    if mapa.tipo_de_mapa!='general':
        return HttpResponseRedirect(reverse('maps:index'))
    if ManejadorDePermisos.permiso_de_mapa(request.user, mapa) not in ('owner','superuser'):
        return HttpResponseRedirect(reverse('maps:index'))
    
    if request.method == 'POST':
        if 'layers' in request.POST:
            posted_layers = json.loads(request.POST.get('layers'))
            try:
                mapa.tms_base_layer=TMSBaseLayer.objects.get(pk=posted_layers['baseLayer'])
            except:
                pass
            if 'extent' in posted_layers:
                mapa.extent=posted_layers['extent']
            mapa.save()
            for msl in mapa.mapserverlayer_set.all():
                msl.delete()
            if 'layers' in posted_layers:
                for idx, l in enumerate(posted_layers['layers']):
                    try:
                        capa=Capa.objects.get(id_capa=l['layerId'])
                        if ManejadorDePermisos.permiso_de_capa(request.user,capa) is not None:
                            if l['sldId'] == 0:
                                try:
                                    sld = capa.archivosld_set.filter(default=True)[0]
                                except:
                                    sld = None
                            else:
                                try:
                                    sld = capa.archivosld_set.filter(id=l['sldId'])[0]
                                    # sld = capa.archivosld_set.filter(default=True)[0]
                                except:
                                    sld = None
                            try:
                                feature_info=l['tooltip']
                            except:
                                feature_info=True
                            if 'bandId' in l and l['bandId']:
                                MapServerLayer(mapa=mapa,capa=capa,bandas=l['bandId'],orden_de_capa=idx,feature_info=feature_info,archivo_sld=sld).save()
                            else:
                                MapServerLayer(mapa=mapa,capa=capa,orden_de_capa=idx,feature_info=feature_info,archivo_sld=sld).save()
                    except:
                        pass
            #ManejadorDeMapas.generar_thumbnail(id_mapa)
            mapa.save()
            return HttpResponseRedirect(reverse('maps:detalle_mapa', kwargs={'id_mapa':mapa.id_mapa}))
    
    return HttpResponseRedirect(reverse('maps:visor'))

    
@login_required
def metadatos(request, id_mapa):
    mapa = get_object_or_404(Mapa, id_mapa=id_mapa)
    if mapa.tipo_de_mapa!='general':
        return HttpResponseRedirect(reverse('maps:index'))
    if ManejadorDePermisos.permiso_de_mapa(request.user, mapa) not in ('owner','superuser'):
        return HttpResponseRedirect(reverse('maps:index'))
    
    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('maps:detalle_mapa', kwargs={'id_mapa':id_mapa}))
        form = MapaForm(request.POST, instance=mapa)
        if form.is_valid():
            form.save()
            if '_save_and_continue' in request.POST:
                return HttpResponseRedirect(reverse('maps:metadatos', kwargs={'id_mapa':id_mapa}))
            if '_save_and_next' in request.POST:
                return HttpResponseRedirect(reverse('maps:visor', kwargs={'id_mapa':id_mapa}))
            return HttpResponseRedirect(reverse('maps:detalle_mapa', kwargs={'id_mapa':id_mapa}))
    else:
        form = MapaForm(instance=mapa)
 
    return render(request, 'maps/metadatos.html', {'form': form, 'mapa': mapa, 'MAPCACHE_URL': settings.MAPCACHE_URL })


# @login_required
def buscar(request):
    texto = normalizar_texto(request.GET.get('texto',''))
    pagina = request.GET.get('p')
    
    lista_mapas=[]
    cantidad_total = 0
    if texto!='':
        # busco mapas con matchings
        lista_mapas=Mapa.objects.search(texto).filter(tipo_de_mapa='general') #no filtramos por publico=True para que un user pueda buscar sus propios mapas
        # filtro por permiso y ordeno
        lista_mapas=ManejadorDePermisos.mapas_de_usuario(request.user, 'all', lista_mapas).order_by('-timestamp_alta')
        # anoto permisos
        ManejadorDePermisos.anotar_permiso_a_queryset_de_mapas(request.user, lista_mapas)
        cantidad_total = lista_mapas.count()
        lista_mapas=paginar_y_elegir_pagina(lista_mapas, pagina, settings.CANTIDAD_DE_MAPAS_POR_PAGINA)
    lista_categorias=ManejadorDePermisos.mapas_agrupados_por_categoria()
    lista_escalas=ManejadorDePermisos.mapas_agrupados_por_escala()

    return render(request, 'maps/index.html', {'lista_mapas': lista_mapas, 'cantidad_total': cantidad_total, 'lista_categorias': lista_categorias, 'lista_escalas': lista_escalas})

@login_required
def borrar_mapa(request, id_mapa):
    mapa = get_object_or_404(Mapa, id_mapa=id_mapa)
    if ManejadorDePermisos.permiso_de_mapa(request.user, id_mapa) in ('owner','superuser'):
        mapa.delete()
    return HttpResponseRedirect(reverse('maps:index'))

# @login_required
def embeddable(request, id_mapa):
    m = get_object_or_404(Mapa, id_mapa=id_mapa)
    if ManejadorDePermisos.permiso_de_mapa(request.user, m) is None:
        return HttpResponseForbidden()
    	
    extra_requests_args = {}
    mapfile=ManejadorDeMapas.commit_mapfile(id_mapa)
    if m.tipo_de_mapa == 'general':
    	for c in m.capas.all():
    		ManejadorDeMapas.commit_mapfile(c.id_capa)
    
    # remote_url = MAPSERVER_URL+'?map='+mapfile +'&mode=browse&layers=all'
    remote_url = mapserver.get_map_browser_url(id_mapa)
    # print remote_url
    return views.proxy_view(request, remote_url, extra_requests_args)

def getlayersinfo(request):
    res = {'count': 0, 'layers': [], 'result': 'ok'}
    layers=request.GET.get('layers')
    if layers:
        for layer in layers.split(','):
            info = getfeatureinfo(request, layer) # info es un HttpResponse
            if json.loads(info.content)['count']>0:
                return info
    return HttpResponse(json.dumps(res), content_type="application/json")

def getfeatureinfo(request, id_mapa):
    m = get_object_or_404(Mapa, id_mapa=id_mapa)
    if ManejadorDePermisos.permiso_de_mapa(request.user, m) is None:
        return HttpResponseForbidden()
        
    extra_requests_args = {}
    mapfile=ManejadorDeMapas.commit_mapfile(id_mapa)
    if m.tipo_de_mapa == 'general':
        for c in m.capas.all():
            ManejadorDeMapas.commit_mapfile(c.id_capa)
    
    bbox=request.GET.get('BBOX')
    w=request.GET.get('WIDTH')
    h=request.GET.get('HEIGHT')
    i=request.GET.get('I')
    j=request.GET.get('J')

    res = {'count': 0, 'layers': [], 'result': 'ok'}
    count = 0
    for msl in m.mapserverlayer_set.filter(feature_info=True).order_by('-orden_de_capa'):
        c=msl.capa
        id_layer=c.nombre
        # remote_url = settings.MAPSERVER_URL+'?map='+mapfile +'&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetFeatureInfo&BBOX=%s&CRS=epsg:3857&WIDTH=%s&HEIGHT=%s&LAYERS=default&STYLES=&FORMAT=image/png&QUERY_LAYERS=%s&INFO_FORMAT=application/vnd.ogc.gml&I=%s&J=%s'%(bbox, w, h, id_layer, i, j)
        remote_url = mapserver.get_featureinfo_url(id_mapa, bbox, w, h, id_layer, i, j)
        response = urllib2.urlopen(remote_url)
        parser = etree.XMLParser(encoding="utf-8")
        tree = etree.parse(response, parser=parser)
        root = tree.getroot()
        if len(root) > 0 and root[0].tag.endswith('ServiceException'):
            return HttpResponse(json.dumps({ 'result': 'error', 'msg': root[0].text }), content_type="application/json")
        if len(root) > 0:
            layerObj = {'id': id_layer,'name': root.findall('*/{http://www.opengis.net/gml}name')[0].text, 'items': []};
            for e in root[0].getchildren():
                if (e.tag.endswith('feature')):
                    feat = {}
                    for it in e.getchildren():
                        if (not it.tag.endswith('boundedBy')):
                            feat[it.tag]=it.text
                    layerObj['items'].append(feat)
            res['layers'].append(layerObj)
            count = count + len(root)
            break; # Por lo pronto corta cuando encuentra el primer resultado

    res['count'] = count
    return HttpResponse(json.dumps(res), content_type="application/json")
    # return HttpResponse(etree.tostring(root, 'utf-8', method="xml"), content_type="application/xml")

def legend(request, id_mapa):
    mapa = get_object_or_404(Mapa, id_mapa=id_mapa)
    if ManejadorDePermisos.permiso_de_mapa(request.user, mapa) is None:
        return HttpResponseForbidden()

    capa = mapa.capas.first()
    extra_requests_args = {}
    mapfile = ManejadorDeMapas.commit_mapfile(id_mapa)

    if mapa.tipo_de_mapa == 'layer_raster_band':
        sld = mapa.mapserverlayer_set.first().archivo_sld
    else:
        sld = capa.dame_sld_default()
    remote_url = mapserver.get_legend_graphic_url(id_mapa, capa.nombre, sld)
    # remote_url = MAPSERVER_URL+'?map='+mapfile +'&SERVICE=WMS&VERSION=1.3.0&SLD_VERSION=1.1.0&REQUEST=GetLegendGraphic&FORMAT=image/png&LAYER=%s&STYLE=&SLD=%s'%(capa.nombre,capa.dame_sld_default())
    return views.proxy_view(request, remote_url, extra_requests_args)

def visor(request, id_mapa=None):
    capas=ManejadorDePermisos.capas_de_usuario_para_el_visor_por_area_tematica(request.user)
    base_layer = 'world_borders'
    initialLayers = []
    titulo = ''
    extent = settings.VISOR_INITIAL_EXTENT
    if id_mapa:
        m = get_object_or_404(Mapa, id_mapa=id_mapa)
        if m.tms_base_layer:
            base_layer = m.tms_base_layer.id            
        titulo = m.dame_titulo
        if m.extent != '':
            extent = m.extent
        # "initialLayers": [{layerId: 'daniela_paises_suramerica', sldId: 0, tooltip: true}, {layerId: 'pc_infraestructura_basica_x_dpto', sldId: 0, tooltip: true}],
        for msl in m.mapserverlayer_set.all().order_by('orden_de_capa'):
            initialLayers.append({
                'layerId': msl.capa.id_capa,
                'bandId': msl.bandas,
                'sldId': msl.archivo_sld.id if msl.archivo_sld else 0,
                'tooltip': msl.feature_info,
                'layerType': msl.capa.dame_tipo_de_capa
            })

    # por el momento el world borders lo manejamos como un caso especial
    base_layers= {'world_borders': {
                      'url': settings.MAPCACHE_URL+'tms/1.0.0/world_borders@GoogleMapsCompatible/{z}/{x}/{y}.png',
                      'nombre': u'Mapa básico',
                      'tms': True,
                      },
                  }
    for t in TMSBaseLayer.objects.all().order_by('id'):
        base_layers[t.id]= {'url': t.url, 'nombre': unicode(t.nombre), 'tms': t.tms}

    visor_config = {}
    visor_config['layerWMSUrlTemplate'] = urlparse.urljoin(settings.SITE_URL,reverse("layers:wxs", kwargs={'id_capa': '$layerId'}))
    visor_config['layerBandWMSUrlTemplate'] = urlparse.urljoin(settings.SITE_URL,reverse("layers:wxs_raster_band", kwargs={'id_mapa': '$bandId'}))
    visor_config['layerUrlTemplate'] = settings.MAPCACHE_URL+'tms/1.0.0/$layer@GoogleMapsCompatible/{z}/{x}/{y}.png'
    visor_config['baseLayer'] = base_layer
    visor_config['baseLayers'] = base_layers
    visor_config['initialLayers'] = initialLayers
    visor_config['extent'] = extent
    visor_config['layers'] = capas
    
    return render(request, 'maps/visor.html', {'visor_config': json.dumps(visor_config), 'titulo': titulo, 'id_mapa': id_mapa })
