# encoding: utf-8
from django.conf.urls import patterns, url
from layerimport.views import LayersListView, LayerImportView

urlpatterns = patterns('',
    url(r'^layers/$', LayersListView, name='layers-view'),
    url(r'^layer/(?P<filename>[A-Za-z0-9-_\.]+)$', LayerImportView, name='layer-import-view'),
)
