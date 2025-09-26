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
        "ENGINE": os.environ.get("ENGINE", ""), 
         # Add the docker environment DATABASE variable or use the local sqlite database soruce
        "NAME": os.environ.get("NAME",""),
         # Add the docker USER environment variable or on need password for sqlite3
        "USER": os.environ.get("USER", ""),
         # Add the docker PASSWORD environment variable or on need password for sqlite3
        "PASSWORD": os.environ.get("PASSWORD", ""),
         # Add the docker HOST environment variable or on need host for sqlite3
        "HOST": os.environ.get("HOST", ""),
         # Add the docker HOST environment variable or on need port for sqlite3
        "PORT": os.environ.get("PORT", ""),
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
