import os
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '.vercel.app', '.railway.app']
CSRF_TRUSTED_ORIGINS = ['https://localhost:8000', 'https://green-path-frontend.vercel.app/']

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": {
         # Add the docker environment ENGINE variable or for local development use sqlite3 engine
        "DB_ENGINE": os.environ.get("DB_ENGINE", ""), 
         # Add the docker environment DATABASE variable or use the local sqlite database soruce
        "DB_NAME": os.environ.get("DB_NAME",""),
         # Add the docker USER environment variable or on need password for sqlite3
        "DB_USER": os.environ.get("DB_USER", ""),
         # Add the docker PASSWORD environment variable or on need password for sqlite3
        "DB_PASSWORD": os.environ.get("DB_PASSWORD", ""),
         # Add the docker HOST environment variable or on need host for sqlite3
        "DB_HOST": os.environ.get("DB_HOST", ""),
         # Add the docker HOST environment variable or on need port for sqlite3
        "DB_PORT": os.environ.get("DB_PORT", ""),
    }
}

GDAL_LIBRARY_PATH = os.environ.get('GDAL_LIBRARY_PATH', '/usr/lib/x86_64-linux-gnu/libgdal.so')
GEOS_LIBRARY_PATH = os.environ.get('GEOS_LIBRARY_PATH', '/usr/lib/x86_64-linux-gnu/libgeos_c.so')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = (BASE_DIR, 'static')
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
