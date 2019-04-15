# Mapround API 

La API de Mapground permite administrar capas y datos de forma programática de forma tal de poder automatizar completamente su operación con excepción de la edición de metadatos. La API utiliza autenticación JWT por lo que para utilizarla es necesario obtener previamente un token.

## Resumen de métodos

* `POST     /api/login      ` - Permite obtener un token
* `GET      /api/users      ` - Lista los usuarios
* `GET      /api/layers     ` - Lista las capas a las que se tiene acceso
* `GET      /api/layers/:id ` - Permite obtener los detalles de una capa
* `POST     /api/upload     ` - Permite subir un archivo
* `GET      /api/import     ` - Lista todas las capas importables
* `POST     /api/import     ` - Permite importar una capa
* `GET      /api/updates/:id` - Lista los updates aplicables a una capa
* `POST     /api/updates/:id/:filename` - Importa `filename` como actualizacion para los data sources de una capa
* `DELETE   /api/layers/:id` - Permite borrar una capa
* `POST     /api/layers/:id/update_datasource_date/:id_datasource` - Permite cambiar la fecha de un datasource en una capa
* `DELETE   /api/layers/:id/delete_datasource/:id_datasource` - Permite borrar un data source de una capa

## POST /api/login
Permite obtener un token para usar la API.

**Tipo de parámetros:** Body (form-data)

| Parámetro | Tipo    |
| --------- | --------|
| username  | String  |
| password  | String  |

**Ejemplo de respuesta**

    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidXNlcl9pZCI6MSwiZW1haWwiOiIiLCJleHAiOjE1NTUyNzY4MDR9.8XXkn7meyFR8wJpid8Mirf7PmWcDBq2MY4cZFLiyb1o"
    }

**cURL**

    curl -X POST \
        http://mapground/api/login/ \
        -H 'cache-control: no-cache' \
        -H 'content-type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW' \
        -F username=<username> \
        -F password=<password>

## GET /api/users
Lista los usuarios del sistema.

**Tipo de parámetros:** N/A

**Ejemplo de respuesta**

    [
        {
            "username": "mapground",
            "email": "",
            "is_staff": false
        },
        {
            "username": "admin",
            "email": "",
            "is_staff": true
        }
    ]

**cURL**

    curl -X GET \
        http://mapground/api/users/ \
        -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidXNlcl9pZCI6MSwiZW1haWwiOiIiLCJleHAiOjE1NTUyODE3Njd9.hC35B6Pgksj0un6OfRlvxKWBYM3QjsX4oqsl9pCY97Q' \
        -H 'cache-control: no-cache'

## GET /api/layers
Lista las capas a las que se tiene acceso

**Tipo de parámetros:** N/A

**Ejemplo de respuesta**

    [
        {
            "id": 1,
            "id_capa": "admin_provincias",
            "slug": "provincias",
            "owner": "admin",
            "nombre": "provincias",
            "tipo_de_capa": "vector",
            "srid": 4326,
            "proyeccion_proj4": "",
            "cantidad_de_registros": 48,
            "layer_srs_extent": "-73.5727040930923 -70.2613906860352 -44.9774017333984 -21.7784510000015",
            "wxs_publico": false,
            "timestamp_alta": "2019-03-24T14:17:40.755540Z",
            "timestamp_modificacion": "2019-03-25T02:45:59.380465Z",
            "rasterdatasources": [],
            "vectordatasources": [
                {
                    "id": 1,
                    "tabla": "admin_provincias_v1",
                    "cantidad_de_registros": 48,
                    "srid": 4326,
                    "proyeccion_proj4": "",
                    "data_datetime": "2019-03-24T14:17:00Z",
                    "timestamp_modificacion": "2019-03-24T14:17:40.924931Z"
                }
            ]
        },
        {
            "id": 11,
            "id_capa": "admin_wrfprs_d01",
            "slug": "wrfprs_d01",
            "owner": "admin",
            "nombre": "wrfprs_d01",
            "tipo_de_capa": "raster",
            "srid": 0,
            "proyeccion_proj4": "+proj=lcc +lat_1=-35 +lat_2=-35 +lat_0=-35 +lon_0=-65 +x_0=0 +y_0=0 +a=6371200 +b=6371200 +units=m +no_defs ",
            "cantidad_de_registros": null,
            "layer_srs_extent": "-1998383.7311 -2498492.28214 1997616.2689 2497507.71786",
            "wxs_publico": false,
            "timestamp_alta": "2019-03-25T02:35:34.731415Z",
            "timestamp_modificacion": "2019-03-25T02:53:31.112130Z",
            "rasterdatasources": [
                {
                    "id": 12,
                    "nombre_del_archivo": "admin_wrfprs_d01_v4.012",
                    "gdal_driver_longname": "GRIdded Binary (.grb)",
                    "cantidad_de_bandas": 9,
                    "srid": 0,
                    "proyeccion_proj4": "+proj=lcc +lat_1=-35 +lat_2=-35 +lat_0=-35 +lon_0=-65 +x_0=0 +y_0=0 +a=6371200 +b=6371200 +units=m +no_defs ",
                    "data_datetime": "2018-08-21T12:00:00Z",
                    "timestamp_modificacion": "2019-03-25T02:53:31.106566Z"
                },
                {
                    "id": 11,
                    "nombre_del_archivo": "admin_wrfprs_d01_v3.009",
                    "gdal_driver_longname": "GRIdded Binary (.grb)",
                    "cantidad_de_bandas": 9,
                    "srid": 0,
                    "proyeccion_proj4": "+proj=lcc +lat_1=-35 +lat_2=-35 +lat_0=-35 +lon_0=-65 +x_0=0 +y_0=0 +a=6371200 +b=6371200 +units=m +no_defs ",
                    "data_datetime": "2018-08-21T09:00:00Z",
                    "timestamp_modificacion": "2019-03-25T02:38:21.687972Z"
                },
                {
                    "id": 10,
                    "nombre_del_archivo": "admin_wrfprs_d01_v1.000",
                    "gdal_driver_longname": "GRIdded Binary (.grb)",
                    "cantidad_de_bandas": 9,
                    "srid": 0,
                    "proyeccion_proj4": "+proj=lcc +lat_1=-35 +lat_2=-35 +lat_0=-35 +lon_0=-65 +x_0=0 +y_0=0 +a=6371200 +b=6371200 +units=m +no_defs ",
                    "data_datetime": "2018-08-21T00:00:00Z",
                    "timestamp_modificacion": "2019-03-25T02:35:34.802212Z"
                }
            ],
            "vectordatasources": []
        }
    ]

**cURL**

    curl -X GET \
        http://mapground/api/layers/ \
        -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidXNlcl9pZCI6MSwiZW1haWwiOiIiLCJleHAiOjE1NTUyODE3Njd9.hC35B6Pgksj0un6OfRlvxKWBYM3QjsX4oqsl9pCY97Q' \
        -H 'cache-control: no-cache'