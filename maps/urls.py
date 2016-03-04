from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from maps import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'), 
    url(r'^ultimos$', views.ultimos, name='ultimos'),
    url(r'^embeddable/(?P<id_mapa>.+)/$', views.embeddable, name='embeddable'),
    url(r'^detalle_mapa/(?P<id_mapa>.+)/$', views.detalle_mapa, name='detalle_mapa'),
    url(r'^crear_mapa/$', views.crear_mapa, name='crear_mapa'),
    url(r'^actualizar_mapa/(?P<id_mapa>.+)/$', views.actualizar_mapa, name='actualizar_mapa'),
    url(r'^metadatos/(?P<id_mapa>.+)/$', views.metadatos, name='metadatos'),
    url(r'^borrar_mapa/(?P<id_mapa>.+)/$', views.borrar_mapa, name='borrar_mapa'),
    url(r'^buscar/$', views.buscar, name='buscar'),
    url(r'^getfeatureinfo/(?P<id_mapa>.+)/$', views.getfeatureinfo, name='getfeatureinfo'),
    url(r'^getlayersinfo/$', views.getlayersinfo, name='getlayersinfo'),
    url(r'^legend/(?P<id_mapa>.+)/$', views.legend, name='legend'),
    url(r'^detalle_categoria/(?P<categoriaid>[0-9]+)/$', views.detalle_categoria, name='detalle_categoria'),
    url(r'^detalle_escala/(?P<escalaid>[0-9]+)/$', views.detalle_escala, name='detalle_escala'),
    url(r'^visor/(?P<id_mapa>.+)/$', views.visor, name='visor'),
    url(r'^visor/$', views.visor, name='visor'),
)