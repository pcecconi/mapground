# encoding: utf-8
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from fileupload.views import ArchivoCreateView, ArchivoActualizacionCreateView, ArchivoDeleteView, ArchivoListView

urlpatterns = [
    url(r'^new/$', login_required(ArchivoCreateView.as_view()), name='upload-new'),
    url(r'^new_update/(?P<id_capa>.+)/$', login_required(ArchivoActualizacionCreateView.as_view()), name='upload-update'),
    url(r'^delete/(?P<pk>\d+)$', login_required(ArchivoDeleteView.as_view()), name='upload-delete'),
    url(r'^view/$', login_required(ArchivoListView.as_view()), name='upload-view'),
]
