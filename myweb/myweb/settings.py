from pathlib import Path
import os
from dotenv import load_dotenv

import dj_database_url
from datetime import timedelta

from django.conf.global_settings import AUTH_USER_MODEL
from env import DEBUG, SECRET_KEY

import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


SECRET_KEY = SECRET_KEY

DEBUG = DEBUG

ALLOWED_HOSTS = ["*"]

API_TITLE = "TITLE-API"
API_DESCRIPTION = "DESCRIPTION-API"
API_VERSION = "0.0.24"

JWT_TOKEN_EXPIRES = timedelta(minutes=15)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(minutes=30)

LOCAL_APPS = [
    'api.users',
    'api.clients',
    'api.employees',
    'api.products',
    'api.store',
    'api.core'
]

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

INSTALLED_APPS: list = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myweb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ASGI_APPLICATION = 'myweb.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = "users.Users"

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



LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/assets/'
STATICFILES_DIRS = [
    BASE_DIR / 'assets',
]
STATIC_ROOT = BASE_DIR / "assets_production"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de correo desde variables de entorno
EMAIL_BACKEND      = os.getenv("EMAIL_BACKEND")
EMAIL_HOST         = os.getenv("SMTP_HOST")
EMAIL_PORT         = int(os.getenv("SMTP_PORT", 25))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@example.com")
EMAIL_HOST_USER    = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD= os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS      = os.getenv("EMAIL_USE_TLS", "False") == "True"

# Configuración de Celery (Redis)
CELERY_BROKER_URL  = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# Configuración de pasarela de pago
PAYMENT_GATEWAY = os.getenv("PAYMENT_GATEWAY", "dummy")
