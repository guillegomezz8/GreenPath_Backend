from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Cargar el archivo .env
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

# Variables de entorno cargadas
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
# DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1']

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

BASE_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'apps.base',
    'apps.user',
    'apps.company',
    'apps.route',
    'apps.collection'
]

THIRD_APPS = [
    'corsheaders',
    'automatic_crud',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',  
    'simple_history',
    'drf_spectacular',
    'django_extensions',
    'django_filters',
]

INSTALLED_APPS = BASE_APPS + LOCAL_APPS + THIRD_APPS

SWAGGER_SETTINGS = {
    'DOC_EXPANSION': 'none'
}

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication', 
    ],
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

MIDDLEWARE = [    
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'global.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'global.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

AUTH_USER_MODEL = 'user.User'

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://example.com',
]

SPECTACULAR_SETTINGS = {
    'TITLE': 'GreenPath API',
    'DESCRIPTION': 'Welcome to the GreenPath API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,  # Set to True if you want to serve the schema at /schema/
    'SCHEMA_PATH_PREFIX': '/api/v1',  # Adjust as needed
    'COMPONENT_SPLIT_REQUEST': True, # Important to manage files
    'AUTHENTICATION': [
        {
            'name': 'Bearer',
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',  # Optional, depending on your token format
        }
    ],
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True
}
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
