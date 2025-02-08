import os
from .base import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

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


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'