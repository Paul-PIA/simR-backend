"""
Django settings for simR project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""
import os
from pathlib import Path

from datetime import timedelta # import this library top of the settings.py file

import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-m121fuicgj5gd-4a1g@6jkitxbc%inpycqi8*8n*s#%^s6s$!2'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'simr-yo8m.onrender.com']



# Application definition

INSTALLED_APPS = [
    'data.apps.DataConfig', # apps
    # default
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "django.contrib.sites",  # new
    
    'django_filters',#filter API
    'rest_framework',# bridge to API
    'rest_framework.authtoken',# bridge to API
    'drf_spectacular',# docs of API
    'drf_yasg',# docs of API

    "corsheaders",# CORS protector
    
    'dj_rest_auth',# combine DRF and allauth
    'dj_rest_auth.registration',# combine DRF and allauth
    'allauth',
    'allauth.account',
    # Optional -- requires install using `django-allauth[socialaccount]`.
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.github',
    # celery 
    'celery',
    'django_celery_beat',
    'django_celery_results',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #CORS protector
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    #allauth regisration
    "allauth.account.middleware.AccountMiddleware",
    # whitenoise
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = 'simR.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'templates')],
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

REST_FRAMEWORK = {# API framework
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
SIMPLE_JWT = { #Json Web tokens settings
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
    'SLIDING_TOKEN_LIFETIME': timedelta(days=30),
    'SLIDING_TOKEN_REFRESH_LIFETIME_LATE_USER': timedelta(days=1),
    'SLIDING_TOKEN_LIFETIME_LATE_USER': timedelta(days=30),
}
CORS_ALLOWED_ORIGINS = [ #CROS protector
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "https://simr.vercel.app",
    'https://simr-frontend-9t2m.onrender.com',
    'https://simr-frontend-service.onrender.com'
]

CORS_ALLOW_CREDENTIALS = True 
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_AGE = 31449600  # Durée de vie du cookie en secondes (par exemple 1 an)
SESSION_COOKIE_AGE = 1209600  # Durée de vie de la session (2 semaines)

SOCIALACCOUNT_PROVIDERS = {
    # For each OAuth based provider, either add a ``SocialApp``
    # (``socialaccount`` app) containing the required client
    # credentials, or list them here:
    'google': {
        'APP': {
            'client_id': '123',
            'secret': '456',
            'key': '',
        },
    },
    'facebook': {
        'APP': {
            'client_id': '123',
            'secret': '456',
            'key': '',
        },
    },
}

WSGI_APPLICATION = 'simR.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         "NAME": "dj_test",
#         "USER": "postgres",
#         "PASSWORD": "1234",
#         "HOST": "localhost",
#         "PORT": "5432",
#     }
# }
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://user:rrAOPJqB2H2nrjUIgXuuYG2ZNWnBzsac@dpg-ctcl0sbtq21c73frvan0-a.frankfurt-postgres.render.com/simr_database_638b',
        conn_max_age=600
    )  
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'CET'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR,'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')



# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Redirect to home URL after login (Default redirects to /accounts/profile/)
LOGIN_REDIRECT_URL = '/'

# Change the default class of user 
AUTH_USER_MODEL = 'data.CustomUser'

# Email Settings
#See hidden files

#django-allauth registraion settings 
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS =1
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_RATE_LIMITS = {
    "change_password": "5/m/user", # Changing the password (for already authenticated users).
    "manage_email": "10/m/user", # Email management related actions, such as add, remove, change primary.
    "reset_password":"20/m/ip,5/m/key", # Requesting a password reset. The email for which the password is to be reset is passed as the key.
    "reauthenticate":"10/m/user", # Reauthentication (for users already logged in).
    "reset_password_from_key":"20/m/ip", # Password reset (the view the password reset email links to).
    "signup":"20/m/ip", # Signups.
    "login":"30/m/ip", # Logins.
    "login_failed":"10/m/ip,5/5m/key",
    # Restricts the allowed number of failed login attempts. When exceeded, the user is prohibited from logging in for the remainder of the rate limit. Important: while this protects the allauth login view, it does not protect Django’s admin login from being brute forced. Note that a successful login will clear this rate limit.
    "confirm_email":"1/3m/key",
    # Users can request email confirmation mails via the email management view, and, implicitly, when logging in with an unverified account. This rate limit prevents users from sending too many of these mails.
}

REST_USE_JWT = True #optional, instead of Bearer tokens
SITE_ID = 1 
ACCOUNT_EMAIL_VERIFICATION = "mandatory"  # new
#or any other page 
ACCOUNT_LOGOUT_REDIRECT_URL ='/accounts/login/'

SPECTACULAR_SETTINGS = { #API documentation 
    'TITLE': 'SimR API',
    'DESCRIPTION': 'Still in test',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # OTHER SETTINGS
}

MEDIA_ROOT = os.path.join(BASE_DIR,'media')
MEDIA_URL = '/media/'

# DEBUG = True
# DEBUG = config("DEBUG", cast=bool, default=False)

# save Celery task results in Django's database
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672'
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERELIZER = 'json'
CELERY_RESULT_SERELIZER = 'json'
# CELERY_TIMEZONE = 'CET'
# CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'

FRONT_END_URL = 'https://simr-frontend-9t2m.onrender.com/'
ACCOUNT_EMAIL_CONFIRMATION_URL = FRONT_END_URL + 'activate/{key}/'