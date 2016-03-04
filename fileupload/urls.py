# encoding: utf-8
from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from fileupload.views import (
        ArchivoCreateView, ArchivoDeleteView, ArchivoListView
        )

urlpatterns = patterns('',
    url(r'^new/$', login_required(ArchivoCreateView.as_view()), name='upload-new'),
    url(r'^delete/(?P<pk>\d+)$', login_required(ArchivoDeleteView.as_view()), name='upload-delete'),
    url(r'^view/$', login_required(ArchivoListView.as_view()), name='upload-view'),
)
