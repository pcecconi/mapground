from django.conf.urls import url
from layers import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^wxs/(?P<id_capa>.+)/$', views.wxs, name='wxs'),
    url(r'^wxs_raster_band/(?P<id_mapa>.+)/$', views.wxs_raster_band, name='wxs_raster_band'),
    url(r'^public_wxs/$', views.wxs_public, name='wxs_public'),
    url(r'^detalle_capa/(?P<id_capa>.+)/$', views.detalle_capa, name='detalle_capa'),
    url(r'^borrar_capa/(?P<id_capa>.+)/$', views.borrar_capa, name='borrar_capa'),
    url(r'^buscar/$', views.buscar, name='buscar'),

    url(r'^ultimas$', views.ultimas, name='ultimas'),

    url(r'^metadatos/(?P<id_capa>.+)/$', views.metadatos, name='metadatos'),
    url(r'^atributos/(?P<id_capa>.+)/$', views.atributos, name='atributos'),
    url(r'^permisos/(?P<id_capa>.+)/$', views.permisos, name='permisos'),
    url(r'^sld/(?P<id_capa>.+)/$', views.sld, name='sld'),
    url(r'^categorias/$', views.categorias, name='categorias'),
    url(r'^escalas/$', views.escalas, name='escalas'),
    url(r'^areas_tematicas/$', views.areas_tematicas, name='areas_tematicas'),
    url(r'^detalle_categoria/(?P<categoriaid>[0-9]+)/$', views.detalle_categoria, name='detalle_categoria'),
    url(r'^detalle_escala/(?P<escalaid>[0-9]+)/$', views.detalle_escala, name='detalle_escala'),
    url(r'^detalle_area_tematica/(?P<areatematicaid>[0-9]+)/$', views.detalle_area_tematica, name='detalle_area_tematica'),
    url(r'^archivos_sld_de_capa/(?P<id_capa>.+)/$', views.archivos_sld_de_capa, name='archivos_sld_de_capa'),

    url(r'^download/(?P<id_capa>\w+)/((?P<format>\w+)/)?$', views.download, name='download'),
]
