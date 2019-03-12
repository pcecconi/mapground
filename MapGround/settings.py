"""
Django settings for MapGround project.

Generated by 'django-admin startproject' using Django 1.11.13.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# OJO: En Django 1.11 es como el BASE_PATH nuestro:
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# El de arriba es el default de Django pero no sirve para algunos usos (comentario de la 1.6)
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/


# Application definition

INSTALLED_APPS = (
    # --- ini defaults 1.11
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # --- fin defaults 1.11
    'django.contrib.humanize',
    'django.contrib.gis',
    'background_task',
    'sequences.apps.SequencesConfig',
    'commons',
    'fileupload',
    'layerimport',
    'layers',
    'maps',
    'users',
    'rest_framework',
)
# original del proyecto, en django 1.6
# MIDDLEWARE_CLASSES = (
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.auth.middleware.RemoteUserMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
#     'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
# )

# nuevo en django 1.11, cambian keyword y valores
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
]

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

# nuevo en django 1.11
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# lo heredamos de 1.6
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django.contrib.auth.backends.RemoteUserBackend',
)

# de django 1.6, no va mas en 1.11
# TEMPLATE_CONTEXT_PROCESSORS = (
#     'django.core.context_processors.request',
#     'commons.context_processors.front_end_settings',
# )

ROOT_URLCONF = 'MapGround.urls'

WSGI_APPLICATION = 'MapGround.wsgi.application'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Django 1.6 deprecated
# TEMPLATE_DIRS = (
#     os.path.join(BASE_PATH, "templates"),
# )

# nueva estructura de Django 1.11
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'commons.context_processors.front_end_settings',
            ],
            'debug': True,
        },
    },
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_ROOT = os.path.abspath(os.path.dirname(__file__)) + '/static/'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.abspath(os.path.dirname(__file__)) + '/media/'
MAPAS_PATH = os.path.join(BASE_PATH, 'mapfiles')

UPLOADED_FILES_PATH = os.path.join(MEDIA_ROOT, 'uploaded/')
UPLOADED_RASTERS_PATH = os.path.join(MEDIA_ROOT, 'uploaded-rasters/')

CANTIDAD_MAXIMA_DE_BANDAS_POR_RASTER = 200

IMPORT_SCHEMA = 'data'

LOGIN_REDIRECT_URL = '/'

WMS_ONLINERESOURCE = 'http://localhost:8000/layers/wxs/'
WFS_ONLINERESOURCE = 'http://localhost:8000/layers/wxs/'
PROJ_LIB = '/usr/share/proj/'
MS_OPENLAYERS_JS_URL = 'http://openlayers.org/api/OpenLayers.js'
MAP_WEB_IMAGEPATH = '/dev/shm/'
MAP_WEB_IMAGEURL = '/ms_tmp/'

ENCODINGS = (
    ('LATIN1', 'Latin-1'),
    ('UTF-8', 'UTF-8'),
    ('windows-1252', 'Windows 1252'),
    ('IBM850', 'IBM 850'),
)

# https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-FILE_UPLOAD_PERMISSIONS
FILE_UPLOAD_PERMISSIONS = 0664

from settings_local import *
