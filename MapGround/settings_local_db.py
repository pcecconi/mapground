# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'aKZXN0J4rihCCYzmqSJo9uSnOOsTydMvIOpKM8PVRI57uXHDBZbnmUuHlOY40U7qpxzmoLtAmojKxRjX24LgnFxVKHQZ88J9qt7a'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
         'ENGINE': 'django.contrib.gis.db.backends.postgis',
         'NAME': 'mapground',
         'USER': 'mapground',
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