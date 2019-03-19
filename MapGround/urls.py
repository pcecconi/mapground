# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""MapGround URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import include, url
from django.http import HttpResponseRedirect
from django.contrib import admin
from django.contrib.auth import views
from django.views.static import serve
from django.conf import settings
admin.autodiscover()

admin.site.site_header = 'Administración de la IDE'
admin.site.site_title = 'Administración de la IDE'
admin.site.index_title = 'Módulos de Administración'

urlpatterns = [
    # Examples:
    # url(r'^$', 'MapGround.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', lambda x: HttpResponseRedirect('/layers/last')),
    url(r'^layers/', include('layers.urls', namespace='layers')),
    url(r'^maps/', include('maps.urls', namespace='maps')),
    url(r'^upload/', include('fileupload.urls', namespace="fileupload")),
    url(r'^import/', include('layerimport.urls', namespace='layerimport')),
    url(r'^users/', include('users.urls', namespace='users')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', views.login, name='login'),
    url(r'^accounts/logout/$', views.logout_then_login, name='logout'),

    url(r'^media/(.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^api/', include('api.urls', namespace='api')),
]

# urlpatterns += [
#     (r'^media/(.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
# ]
