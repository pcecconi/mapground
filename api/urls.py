from django.conf.urls import url, include
from rest_framework import routers
from .views import ArchivoAPIView, CapaViewSet, UserViewSet, LayerImportAPIView

layers_list = CapaViewSet.as_view({
    'get': 'list',
})

layers_detail = CapaViewSet.as_view({
    'get': 'retrieve',
})

users_list = UserViewSet.as_view({
    'get': 'list',
})

# user_detail = UserViewSet.as_view({
#     'get': 'retrieve',
# })
router = routers.DefaultRouter()
router.register(r'layers', CapaViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),    
    # url(r'^layers/$', layers_list, name='layers-list'),
    # url(r'^layers/(?P<id_capa>.+)/$', layers_detail, name='layers-detail'),
    # url(r'^users/', users_list, name='users-list'),
    # url(r'^users/<int:pk>/', user_detail, name='user-detail'),
    url(r'^upload/$', ArchivoAPIView.as_view(), name='file-upload'),
    url(r'^import/$', LayerImportAPIView.as_view(), name='layer-importables'),
]