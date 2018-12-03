# encoding: utf-8
from django.conf.urls import url
from layerimport.views import LayersListView, LayerImportView, LayerImportUpdateView, LayersUpdateListView

urlpatterns = [
    url(r'^layers/$', LayersListView, name='layers-view'),
    url(r'^layers_update/(?P<id_capa>.+)/$', LayersUpdateListView, name='layers-update-view'),
    url(r'^layer_update/(?P<id_capa>.+)/(?P<filename>[A-Za-z0-9-_\.]+)$', LayerImportUpdateView, name='layer-import-update-view'),
    url(r'^layer/(?P<filename>[A-Za-z0-9-_\.]+)$', LayerImportView, name='layer-import-view'),
]
