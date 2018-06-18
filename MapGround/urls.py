from django.conf.urls import patterns, include, url
from django.http import HttpResponseRedirect
from django.contrib import admin
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'MapGround.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', lambda x: HttpResponseRedirect('/layers/ultimas')),
    url(r'^layers/', include('layers.urls', namespace='layers')),
    url(r'^maps/', include('maps.urls', namespace='maps')),
    url(r'^upload/', include('fileupload.urls', namespace="fileupload")),
    url(r'^import/', include('layerimport.urls', namespace='layerimport')),
    url(r'^users/', include('users.urls', namespace='users')),
    
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login'),
)

import os
urlpatterns += patterns('',
    (r'^media/(.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT }),
)
