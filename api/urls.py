from django.conf.urls import url, include
from rest_framework import routers
from .views import ArchivoAPIView, CapaViewSet, UserViewSet, LayerImportAPIView, LayerUpdateAPIView, RDSViewSet, VDSViewSet, LoginView

router = routers.DefaultRouter()
router.register(r'layers', CapaViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),    
    url(r'^login/$', LoginView.as_view(), name="auth-login"),
    url(r'^upload/$', ArchivoAPIView.as_view(), name='api-file-upload'),
    url(r'^import/$', LayerImportAPIView.as_view(), name='api-layer-importables'),
    url(r'^import/(?P<filename>[A-Za-z0-9-_\.]+)$', LayerImportAPIView.as_view(), name='api-import-layer'),
    url(r'^updates/(?P<pk>[^/.]+)/$', LayerUpdateAPIView.as_view(), name='api-layer-updates'),
    url(r'^update/(?P<pk>[^/.]+)/(?P<filename>[A-Za-z0-9-_\.]+)$', LayerUpdateAPIView.as_view(), name='api-layer-update'),
]