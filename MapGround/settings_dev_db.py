# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'xp23UNUVbYb6Y7RhWn4Xa3IWSwzSZ8N2z7cLSiyrGGQSTBEpIIyHVy02bA4VF2VfY4sf1E2Y2OBEUVQsOM94QoSUDkPArbMGIi2g'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
         'ENGINE': 'django.contrib.gis.db.backends.postgis',
         'NAME': 'mapground_dev',
         'USER': 'mapground_dev',
         'PASSWORD': 'asdfp',
         'HOST': 'localhost', 
     }
}

DEFAULT_DB_CONNECTION_STRING = "host='%s' dbname='%s' user='%s' password='%s'"%(DATABASES['default']['HOST'],DATABASES['default']['NAME'], DATABASES['default']['USER'], DATABASES['default']['PASSWORD'])

POSTGIS_VERSION = ( 2, 3 )

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }