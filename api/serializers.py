from rest_framework import serializers

from django.contrib.auth.models import User
from fileupload.models import Archivo
from layers.models import Capa, VectorDataSource, RasterDataSource

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'email', 'is_staff')

class ArchivoSerializer(serializers.ModelSerializer):
  class Meta():
    model = Archivo
    fields = ('file', 'slug', 'nombre', 'extension')

class RasterDataSourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = RasterDataSource
        fields = ('nombre_del_archivo', 'gdal_driver_longname', 'cantidad_de_bandas',
            'srid', 'proyeccion_proj4', 'data_datetime', 'timestamp_modificacion')

class VectorDataSourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = VectorDataSource
        fields = ('tabla', 'cantidad_de_registros',
            'srid', 'proyeccion_proj4', 'data_datetime', 'timestamp_modificacion')

class CapaSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    rasterdatasources = RasterDataSourceSerializer(many=True, read_only=True)
    vectordatasources = VectorDataSourceSerializer(many=True, read_only=True)

    class Meta:
        model = Capa
        fields = ('id_capa', 'slug', 'owner', 'nombre', 'tipo_de_capa', 'srid', 'proyeccion_proj4',
                    'cantidad_de_registros', 'layer_srs_extent', 'wxs_publico', 
                    'timestamp_alta', 'timestamp_modificacion','rasterdatasources','vectordatasources')