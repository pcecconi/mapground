from MapGround import MapGroundException, LayerNotFound, LayerAlreadyExists, LayerImportError
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers, viewsets, routers
from rest_framework.decorators import action
from django.shortcuts import HttpResponseRedirect
from django.core.urlresolvers import reverse
from .serializers import ArchivoSerializer, CapaSerializer, UserSerializer, RasterDataSourceSerializer, VectorDataSourceSerializer, DataSourceDateTimeSerializer, TokenSerializer
from layerimport.views import _get_capas_importables, _get_actualizaciones_validas
from layers.models import Capa, VectorDataSource, RasterDataSource, CONST_RASTER, CONST_VECTOR
import json
from MapGround.settings import IMPORT_SCHEMA, ENCODINGS, UPLOADED_RASTERS_PATH
from layerimport.import_utils import import_layer, update_layer

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from rest_framework_jwt.settings import api_settings
from rest_framework import permissions, generics

# Get the JWT settings, add these lines after the import/from lines
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

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

    def post(self, request, filename, *args, **kwargs):
        # filename tiene la forma "nombre.extension"
        try:
            encoding = [item[0] for item in ENCODINGS if item[0] == request.POST['encoding']][0]
        except:
            encoding = 'LATIN1'

        try:
            capa = import_layer(request, filename, encoding)
        except LayerNotFound as e:
            return Response(unicode(e), status=status.HTTP_404_NOT_FOUND)

        except LayerAlreadyExists as e:
            return Response(unicode(e), status=status.HTTP_409_CONFLICT)
        
        except LayerImportError as e:
            return Response(unicode(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(CapaSerializer(capa).data, status=status.HTTP_200_OK)

class LayerUpdateAPIView(APIView):
    def get(self, request, pk, *args, **kwargs):
        try:
            capa = Capa.objects.get(pk=pk)
        except:
            return Response("Capa con id %s no encontrada."%(pk), status=status.HTTP_404_NOT_FOUND)

        archivos, errores = _get_capas_importables(request)

        updateables = _get_actualizaciones_validas(archivos, capa)
        return Response(updateables, status=status.HTTP_200_OK)


    def post(self, request, pk, filename, *args, **kwargs):
        # filename tiene la forma "nombre.extension"
        try:
            capa = Capa.objects.get(pk=pk)
        except:
            return Response("Capa con id %s no encontrada."%(pk), status=status.HTTP_404_NOT_FOUND)

        try:
            encoding = [item[0] for item in ENCODINGS if item[0] == request.POST['encoding']][0]
        except:
            encoding = 'LATIN1'

        try:
            capa = update_layer(request, capa, filename, encoding)
        except ValueError as e:
            return Response(unicode(e), status=status.HTTP_400_BAD_REQUEST)
        
        except LayerImportError as e:
            return Response(unicode(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(CapaSerializer(capa).data, status=status.HTTP_200_OK)

class CapaViewSet(viewsets.ModelViewSet):
    queryset = Capa.objects.all()
    serializer_class = CapaSerializer

    @action(detail=True, methods=['post'], url_path='update_datasource_date/(?P<ds_pk>[^/.]+)')
    def update_datasource_date(self, request, pk=None, ds_pk=None):
        capa = self.get_object()
        ds = None
        try:
            if capa.tipo_de_capa == CONST_RASTER:
                ds = capa.rasterdatasources.get(id=ds_pk)
            else:
                ds = capa.vectordatasources.get(id=ds_pk)
        except:
            return Response("Capa con id %s no tiene un data source con id %s."%(pk, ds_pk), status=status.HTTP_404_NOT_FOUND)
        serializer = DataSourceDateTimeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(ds, serializer.validated_data)
            return Response('Se actualizo date del datasource %s'%(ds_pk), status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='delete_datasource/(?P<ds_pk>[^/.]+)')
    def delete_datasource(self, request, pk=None, ds_pk=None):
        capa = self.get_object()
        ds = None
        try:
            if capa.tipo_de_capa == CONST_RASTER:
                ds = capa.rasterdatasources.get(id=ds_pk)
            else:
                ds = capa.vectordatasources.get(id=ds_pk)
        except:
            return Response("Capa con id %s no tiene un data source con id %s."%(pk, ds_pk), status=status.HTTP_404_NOT_FOUND)
        if not ds.is_only_datasource:
            ds.delete()
            return Response('Se elimino el datasource %s'%(ds_pk), status=status.HTTP_200_OK)
        else:
            return Response("No se puede eliminar el unico datasource de una capa", status=status.HTTP_400_BAD_REQUEST)

class RDSViewSet(viewsets.ModelViewSet):
    queryset = RasterDataSource.objects.all()
    serializer_class = RasterDataSourceSerializer

class VDSViewSet(viewsets.ModelViewSet):
    queryset = VectorDataSource.objects.all()
    serializer_class = VectorDataSourceSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class LoginView(APIView):
    """
    POST auth/login/
    """
    # This permission class will overide the global permission
    # class setting
    permission_classes = (permissions.AllowAny,)

    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # login saves the users ID in the session,
            # using Djangos session framework.
            login(request, user)
            serializer = TokenSerializer(data={
                # using drf jwt utility functions to generate a token
                "token": jwt_encode_handler(
                    jwt_payload_handler(user)
                )})
            serializer.is_valid()
            return Response(serializer.data)
        return Response("Login failed for user '%s' with password '%s'"%(username, password), status=status.HTTP_401_UNAUTHORIZED)