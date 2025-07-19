from pathlib import Path

from dotenv import load_dotenv
from uuid import uuid4

import dj_database_url
from datetime import timedelta

from corsheaders.defaults import default_headers

from env import (
    DEBUG,
    DATABASE_URL,
    SECRET_KEY,
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_USE_TLS,
    EMAIL_HOST_USER,
    EMAIL_HOST_PASSWORD,
    STRIPE_KEY,
    STRIPE_PUBLISHABLE_KEY,
    DOMAIN
)

import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


SECRET_KEY = SECRET_KEY
STRIPE_KEY = STRIPE_KEY
STRIPE_PUBLISHABLE_KEY = STRIPE_PUBLISHABLE_KEY
ID_PREFIX = uuid4()

DEBUG = DEBUG

DOMAIN = DOMAIN

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = DEBUG

if DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:4200",
        "http://127.0.0.1:8080",
    ]
else:
    CORS_ALLOWED_ORIGINS = [
        DOMAIN,
        "https://checkout.stripe.com/"
    ]

if not DEBUG:
    ALLOWED_HOSTS.append(DOMAIN)
    ALLOWED_HOSTS.extend(CORS_ALLOWED_ORIGINS)

APPEND_SLASH = True

CORS_ALLOW_HEADERS = list(default_headers) + [
    "idempotency-key",
]

API_TITLE = "TITLE-API"
API_DESCRIPTION = "DESCRIPTION-API"
API_VERSION = "0.0.24"

JWT_TOKEN_EXPIRES = timedelta(minutes=30)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(minutes=60)
JWT_HASH_ALGORITHM = "HS256"

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
    'django_extensions',
    'corsheaders'
]

INSTALLED_APPS: list = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
        'DIRS': [
            BASE_DIR / 'templates',
        ],
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
    'default': dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
        default=DATABASE_URL
    )
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
    BASE_DIR / 'assets_src',
]
STATIC_ROOT = BASE_DIR / "assets"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de correo desde variables de entorno
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = EMAIL_HOST
EMAIL_PORT = EMAIL_PORT
#DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@example.com")
EMAIL_HOST_USER = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD
EMAIL_USE_TLS = EMAIL_USE_TLS

# Configuración de Celery (Redis)
CELERY_BROKER_URL  = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# Configuración de pasarela de pago
PAYMENT_GATEWAY = os.getenv("PAYMENT_GATEWAY", "dummy")

# Configuración de idempotencia
IDEMPOTENCY_ENABLED = os.getenv('IDEMPOTENCY_ENABLED', 'True').lower() == 'true'

# Configuración para archivos media (imágenes, uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
