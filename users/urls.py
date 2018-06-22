from django.conf.urls import url
from users import views

urlpatterns = [
    url(r'^(?P<username>.+)/wxs/$', views.wxs, name='wxs'),
    url(r'^usuarios/$', views.usuarios, name='usuarios'),
    url(r'^grupos/$', views.grupos, name='grupos'),
]
