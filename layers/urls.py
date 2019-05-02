from django.conf.urls import url
from layers import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^public_wxs/(?P<id_capa>.+)/$', views.public_layer_wxs, name='public_layer_wxs'),
    url(r'^wxs/(?P<id_capa>.+)/$', views.wxs, name='wxs'),
    url(r'^wxs_raster_band/(?P<id_mapa>.+)/$', views.wxs_raster_band, name='wxs_raster_band'),
    url(r'^public_wxs/$', views.wxs_public, name='wxs_public'),
    url(r'^details/(?P<id_capa>.+)/$', views.detalle_capa, name='detalle_capa'),
    url(r'^delete/(?P<id_capa>.+)/$', views.borrar_capa, name='borrar_capa'),
    url(r'^update_data/(?P<id_capa>.+)/$', views.actualizar_capa, name='actualizar_capa'),
    url(r'^find/$', views.buscar, name='buscar'),

    url(r'^last$', views.ultimas, name='ultimas'),

    url(r'^metadata/(?P<id_capa>.+)/$', views.metadatos, name='metadatos'),
    url(r'^attr/(?P<id_capa>.+)/$', views.atributos, name='atributos'),
    url(r'^perm/(?P<id_capa>.+)/$', views.permisos, name='permisos'),
    url(r'^sld/(?P<id_capa>.+)/$', views.sld, name='sld'),
    url(r'^updates/(?P<id_capa>.+)/$', views.actualizaciones, name='actualizaciones'),
    url(r'^labels/$', views.categorias, name='categorias'),
    url(r'^scales/$', views.escalas, name='escalas'),
    url(r'^folders/$', views.areas_tematicas, name='areas_tematicas'),
    url(r'^label/(?P<categoriaid>[0-9]+)/$', views.detalle_categoria, name='detalle_categoria'),
    url(r'^scale/(?P<escalaid>[0-9]+)/$', views.detalle_escala, name='detalle_escala'),
    url(r'^folder/(?P<areatematicaid>[0-9]+)/$', views.detalle_area_tematica, name='detalle_area_tematica'),
    url(r'^symbology/(?P<id_capa>.+)/$', views.archivos_sld_de_capa, name='archivos_sld_de_capa'),
    url(r'^bands/(?P<id_capa>.+)/$', views.bandas_de_capa, name='bandas_de_capa'),

    url(r'^download/(?P<id_capa>\w+)/((?P<format>\w+)/)?$', views.download, name='download'),
]
