from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers, viewsets, routers
from django.contrib.auth.models import User
from .serializers import ArchivoSerializer, CapaSerializer, UserSerializer, RasterDataSourceSerializer
from layerimport.views import _get_capas_importables
from layers.models import Capa, RasterDataSource
import json

class ArchivoAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request, *args, **kwargs):
        file_serializer = ArchivoSerializer(data=request.data)
        if file_serializer.is_valid():
            file_serializer.save(owner=self.request.user)
            importables, errores = _get_capas_importables(self.request)
            return Response(importables, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LayerImportAPIView(APIView):
    def get(self, request, *args, **kwargs):
        importables, errores = _get_capas_importables(self.request)
        return Response(importables, status=status.HTTP_200_OK)

class CapaViewSet(viewsets.ModelViewSet):
    queryset = Capa.objects.all()
    serializer_class = CapaSerializer

class RDSViewSet(viewsets.ModelViewSet):
    queryset = RasterDataSource.objects.all()
    serializer_class = RasterDataSourceSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

