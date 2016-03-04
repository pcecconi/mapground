from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from users import views

urlpatterns = patterns('',
    url(r'^(?P<username>.+)/wxs/$', views.wxs, name='wxs'),
    url(r'^usuarios/$', views.usuarios, name='usuarios'),
    url(r'^grupos/$', views.grupos, name='grupos'),
)