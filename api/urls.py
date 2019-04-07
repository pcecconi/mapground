from django.conf.urls import url, include
from rest_framework import routers
from .views import ArchivoAPIView, CapaViewSet, UserViewSet, LayerImportAPIView, LayerUpdateAPIView, RDSViewSet, VDSViewSet

# layers_list = CapaViewSet.as_view({
#     'get': 'list',
# })

# layers_detail = CapaViewSet.as_view({
#     'get': 'retrieve',
# })

# users_list = UserViewSet.as_view({
#     'get': 'list',
# })

# user_detail = UserViewSet.as_view({
#     'get': 'retrieve',
# })
router = routers.DefaultRouter()
router.register(r'layers', CapaViewSet)
# router.register(r'rasters', RDSViewSet)
# router.register(r'vectors', VDSViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),    
    # url(r'^layers/$', layers_list, name='layers-list'),
    # url(r'^layers/(?P<id_capa>.+)/$', layers_detail, name='layers-detail'),
    # url(r'^layers/<int:pk>/', layers_detail, name='api-layers-detail'),
    # url(r'^users/', users_list, name='users-list'),
    # url(r'^users/<int:pk>/', user_detail, name='user-detail'),
    url(r'^upload/$', ArchivoAPIView.as_view(), name='api-file-upload'),
    url(r'^import/$', LayerImportAPIView.as_view(), name='api-layer-importables'),
    url(r'^import/(?P<filename>[A-Za-z0-9-_\.]+)$', LayerImportAPIView.as_view(), name='api-import-layer'),
    url(r'^updates/(?P<pk>[^/.]+)/$', LayerUpdateAPIView.as_view(), name='api-layer-updates'),
    url(r'^update/(?P<pk>[^/.]+)/(?P<filename>[A-Za-z0-9-_\.]+)$', LayerUpdateAPIView.as_view(), name='api-layer-update'),
]