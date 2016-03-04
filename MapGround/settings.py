"""
Django settings for MapGround project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# El de arriva es el default de Django pero no sirve para algunos usos
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.gis',
    # 'migrations',
    'commons',
    'fileupload',
    'layerimport',
    'layers',
    'maps',
    'users',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django.contrib.auth.backends.RemoteUserBackend',
)

TEMPLATE_CONTEXT_PROCESSORS += ( 
    'django.core.context_processors.request',
)

ROOT_URLCONF = 'MapGround.urls'

WSGI_APPLICATION = 'MapGround.wsgi.application'

USE_I18N = True

USE_L10N = True

USE_TZ = True

TEMPLATE_DIRS = (
    os.path.join(BASE_PATH, "templates"),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_ROOT = os.path.abspath(os.path.dirname(__file__)) + '/static/'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.abspath(os.path.dirname(__file__)) + '/media/'

IMPORT_SCHEMA = 'data'

LOGIN_REDIRECT_URL = '/'

WMS_ONLINERESOURCE = 'http://localhost:8000/layers/wxs/'
WFS_ONLINERESOURCE = 'http://localhost:8000/layers/wxs/'
PROJ_LIB = '/usr/share/proj/'
MS_OPENLAYERS_JS_URL = 'http://openlayers.org/api/OpenLayers.js'
MAP_WEB_IMAGEPATH = '/dev/shm/'
MAP_WEB_IMAGEURL = '/ms_tmp/'

MAPAS_PATH = os.path.join(BASE_PATH, 'mapfiles')

ENCODINGS =(
    ('LATIN1', 'Latin-1'),
    ('UTF-8', 'UTF-8'),
    ('windows-1252', 'Windows 1252'),
    ('IBM850', 'IBM 850'),
)

from settings_local import *
