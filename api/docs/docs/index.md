# Mapround API 

La API de Mapground permite administrar capas y datos de forma programática de forma tal de poder automatizar completamente su operación con excepción de la edición de metadatos. La API utiliza autenticación JWT por lo que para utilizarla es necesario obtener previamente un token.

## Resumen de métodos

* `POST     /api/login      ` - Permite obtener un token
* `GET      /api/users      ` - Lista los usuarios
* `GET      /api/layers     ` - Lista las capas a las que se tiene acceso
* `GET      /api/layers/:id ` - Permite obtener los detalles de una capa
* `POST     /api/upload     ` - Permite subir un archivo
* `GET      /api/import     ` - Lista todas las capas importables
* `POST     /api/import/:layername` - Permite importar una capa
* `GET      /api/updates/:id` - Lista los updates aplicables a una capa
* `POST     /api/update/:id/:filename` - Importa `filename` como actualizacion para los data sources de una capa
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
        -H 'content-type: multipart/form-data;' \
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

## GET /api/layers/:id
Permite obtener el detalle de una capa

**Tipo de parámetros:** Query string

| Parámetro | Tipo    |
| --------- | --------|
| id  | Integer  |

**Ejemplo de respuesta**

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
    }

**cURL**

    curl -X GET \
        http://mapground/api/layers/1 \
        -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidXNlcl9pZCI6MSwiZW1haWwiOiIiLCJleHAiOjE1NTUyODE3Njd9.hC35B6Pgksj0un6OfRlvxKWBYM3QjsX4oqsl9pCY97Q' \
        -H 'cache-control: no-cache'

## POST /api/upload
Permite subir un archivo tanto para la creación de una nueva capa como para la actualización de datos de una capa existente. 

*Nota*: En el caso de un Shapefile se deberá utilizar esta operación varias veces hasta haber subido todos los archivos que lo componen antes de que la respuesta incluya la capa como importable.

**Tipo de parámetros:**  Body (form-data)

| Parámetro | Tipo    |
| --------- | --------|
| file  | File  |

**Ejemplo de respuesta**

    [
        {
            "nombre": "epecuen_oli_2013156_geo.tif",
            "formato": "GTiff",
            "detalle": "2500x2500 px, 3 bandas",
            "tipo": "raster",
            "importable": true
        }
    ]

**cURL**

    curl -X POST \
        http://mapground/api/upload/ \
        -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidXNlcl9pZCI6MSwiZW1haWwiOiIiLCJleHAiOjE1NTU4ODczMjB9.7sCb7DsyFH7PUhXiy22tD3ALw1PwmMvdgNpmHrkjzRw' \
        -H 'cache-control: no-cache' \
        -H 'content-type: multipart/form-data;' \
        -F file=@/tmp/epecuen_oli_2013156_geo.tif

## GET /api/import
Devuelve un listado de todas las capas importables en función de los archivos previamente subidos usando el método upload.

**Tipo de parámetros:** N/A

**Ejemplo de respuesta**

    [
        {
            "nombre": "b4_20082018_1028_n15_1km_tiff.tif",
            "formato": "GTiff",
            "detalle": "1827x3706 px, 1 banda",
            "tipo": "raster",
            "importable": true
        },
        {
            "nombre": "epecuen_oli_2013156_geo.tif",
            "formato": "GTiff",
            "detalle": "2500x2500 px, 3 bandas",
            "tipo": "raster",
            "importable": true
        }
    ]

**cURL**

    curl -X GET \
        http://mapground/api/import \
        -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidXNlcl9pZCI6MSwiZW1haWwiOiIiLCJleHAiOjE1NTU4ODczMjB9.7sCb7DsyFH7PUhXiy22tD3ALw1PwmMvdgNpmHrkjzRw' \
        -H 'cache-control: no-cache'

## POST /api/import/:layername
Permite importar una capa a partir del nombre devuelto por el método anterior.

**Tipo de parámetros:** Query string

| Parámetro | Tipo    |
| --------- | --------|
| layername  | String  |

**Ejemplo de respuesta**

    {
        "id": 12,
        "id_capa": "admin_epecuen_oli_2013156_geo",
        "slug": "epecuen_oli_2013156_geo",
        "owner": "admin",
        "nombre": "epecuen_oli_2013156_geo",
        "tipo_de_capa": "raster",
        "srid": 32620,
        "proyeccion_proj4": "+proj=utm +zone=20 +datum=WGS84 +units=m +no_defs ",
        "cantidad_de_registros": null,
        "layer_srs_extent": "411585.0 -4111185.0 486585.0 -4036185.0",
        "wxs_publico": false,
        "timestamp_alta": "2019-04-21T22:39:15.499281Z",
        "timestamp_modificacion": "2019-04-21T22:39:15.645350Z",
        "rasterdatasources": [
            {
                "id": 13,
                "nombre_del_archivo": "admin_epecuen_oli_2013156_geo_v1.tif",
                "gdal_driver_longname": "GeoTIFF",
                "cantidad_de_bandas": 3,
                "srid": 32620,
                "proyeccion_proj4": "+proj=utm +zone=20 +datum=WGS84 +units=m +no_defs ",
                "data_datetime": "2019-04-21T22:39:15Z",
                "timestamp_modificacion": "2019-04-21T22:39:15.759138Z"
            }
        ],
        "vectordatasources": []
    }

**cURL**

    curl -X POST \
        http://mapground/api/import/epecuen_oli_2013156_geo.tif \
        -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidXNlcl9pZCI6MSwiZW1haWwiOiIiLCJleHAiOjE1NTU4ODczMjB9.7sCb7DsyFH7PUhXiy22tD3ALw1PwmMvdgNpmHrkjzRw' \
        -H 'cache-control: no-cache'

## GET /api/updates/:id/
Permite obtener un listado de los archivos subidos que podrían ser actualizaciones válidas para una capa.

**Tipo de parámetros:** Query string

| Parámetro | Tipo    |
| --------- | --------|
| id  | Integer  |

**Ejemplo de respuesta**

    [
        {
            "nombre": "b4_20082018_1028_n15_1km_tiff_7DJpiSF.tif",
            "formato": "GTiff",
            "detalle": "1827x3706 px, 1 banda",
            "tipo": "raster",
            "importable": true
        },
        {
            "nombre": "b4_20082018_1028_n15_1km_tiff.tif",
            "formato": "GTiff",
            "detalle": "1827x3706 px, 1 banda",
            "tipo": "raster",
            "importable": true
        },
        {
            "nombre": "wrfprs_d01.029",
            "formato": "GRIB",
            "detalle": "999x1249 px, 9 bandas",
            "tipo": "raster",
            "importable": true
        }
    ]


**cURL**

    curl -X GET http://mapground/api/updates/11/ 
        -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidXNlcl9pZCI6MSwiZW1haWwiOiIiLCJleHAiOjE1NTU4OTk2MDh9.s3ZvCyr7gN6iF5RwCNcZxJ4596RtFeJ_pkqtABI_X_8'

## POST /api/update/:id/:filename
Importa filename como actualización para la capa identificada por :id.

**Tipo de parámetros:** Query string

| Parámetro | Tipo    | Descripción |
| --------- | --------| ------------|
| :id  | Integer  | Id de la capa que se desea actualizar | 
| :filename  | String  | Nombre del archivo a usar como actualización tal como lo devuelve el método /api/updates/:id | 

**Ejemplo de respuesta**

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
        "timestamp_modificacion": "2019-04-22T02:11:34.810508Z",
        "rasterdatasources": [
            {
            "id": 14,
            "nombre_del_archivo": "admin_wrfprs_d01_v5.029",
            "gdal_driver_longname": "GRIdded Binary (.grb)",
            "cantidad_de_bandas": 9,
            "srid": 0,
            "proyeccion_proj4": "+proj=lcc +lat_1=-35 +lat_2=-35 +lat_0=-35 +lon_0=-65 +x_0=0 +y_0=0 +a=6371200 +b=6371200 +units=m +no_defs ",
            "data_datetime": "2018-08-22T05:00:00Z",
            "timestamp_modificacion": "2019-04-22T02:11:34.805474Z"
            },
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

**cURL**

    curl -X POST http://mapground/api/update/11/wrfprs_d01.029 
        -H 'content-type: multipart/form-data;' -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidXNlcl9pZCI6MSwiZW1haWwiOiIiLCJleHAiOjE1NTU4OTk2MDh9.s3ZvCyr7gN6iF5RwCNcZxJ4596RtFeJ_pkqtABI_X_8'

## POST /api/layers/:id/update_datasource_date/:id_datasource
Permite actualizar la fecha de un datasource particular para una capa.

**Parámetros Query string:**

| Parámetro | Tipo    | Descripción |
| --------- | --------| ------------|
| :id  | Integer  | Id de la capa que se desea actualizar | 
| :id_datasource  | Integer  | Identificador del datasource a actualizar | 

**Parámetros Body (form-data):**

| Parámetro | Tipo    | Descripción |
| --------- | --------| ------------|
| :data_datetime  | String  | Fecha en formato ISO-8601 YYYY-MM-DDTHH:MM. Ejemplo: 2019-04-07T18:00 | 

**Ejemplo de respuesta**

    "Se actualizo date del datasource 13"

**cURL**

    curl -X POST http://mapground/api/layers/12/update_datasource_date/13/ 
        -H 'content-type: multipart/form-data;' -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidXNlcl9pZCI6MSwiZW1haWwiOiIiLCJleHAiOjE1NTU5MDE0ODN9.T27IAqhjdVqC2gHPeULj_pwk8eKavtbNDIsXzzagi80' 
        -F data_datetime=2019-04-07T18:00

## DELETE /api/layers/:id/delete_datasource/:id_datasource
Permite borrar un datasource de una capa.

**Tipo de parámetros:** Query string

| Parámetro | Tipo    | Descripción |
| --------- | --------| ------------|
| :id  | Integer  | Id de la capa que se desea actualizar | 
| :id_datasource  | Integer  | Id del datasource que se desea eliminar de la capa | 

**Ejemplo de respuesta**

    "Se elimino el datasource 12"

**cURL**

    curl -X DELETE http://localhost:8000/api/layers/11/delete_datasource/12/ 
        -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidXNlcl9pZCI6MSwiZW1haWwiOiIiLCJleHAiOjE1NTU5MDE0ODN9.T27IAqhjdVqC2gHPeULj_pwk8eKavtbNDIsXzzagi80'

## DELETE /api/layers/:id/
Permite borrar una capa.

**Tipo de parámetros:** Query string

| Parámetro | Tipo    | Descripción |
| --------- | --------| ------------|
| :id  | Integer  | Id de la capa que se desea eliminar | 

**Ejemplo de respuesta**

    "Se elimino la capa 11"

**cURL**

    curl -X DELETE http://localhost:8000/api/layers/11/ 
        -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidXNlcl9pZCI6MSwiZW1haWwiOiIiLCJleHAiOjE1NTU5MDE0ODN9.T27IAqhjdVqC2gHPeULj_pwk8eKavtbNDIsXzzagi80'        