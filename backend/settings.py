"""
Django settings for backend project.
"""

from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────
# Security  (move these to a .env file!)
# ──────────────────────────────────────────────
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me-in-production")

DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")


# ──────────────────────────────────────────────
# Installed Apps
# ──────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',          

    # Third-party
    'rest_framework',
    'rest_framework.authtoken',      # required by dj-rest-auth
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'dj_rest_auth',
    'dj_rest_auth.registration',

    # Local
    'authentication',
]

SITE_ID = 1


# ──────────────────────────────────────────────
# Middleware
# ──────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',          # must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',   # required by allauth
]


# ──────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")


# ──────────────────────────────────────────────
# Templates
# ──────────────────────────────────────────────
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

ROOT_URLCONF    = 'backend.urls'
WSGI_APPLICATION = 'backend.wsgi.application'


# ──────────────────────────────────────────────
# Database
# ──────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.getenv('DB_NAME'),
        'USER':     os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST':     os.getenv('DB_HOST', 'localhost'),
        'PORT':     os.getenv('DB_PORT', '5432'),
    }
}


# ──────────────────────────────────────────────
# Authentication backends  (needed for allauth)
# ──────────────────────────────────────────────
AUTH_USER_MODEL = "authentication.User"

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',         # default username/password
    'allauth.account.auth_backends.AuthenticationBackend', # allauth (social + email)
]


# ──────────────────────────────────────────────
# Django REST Framework
# ──────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'authentication.authentication.CookieJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Throttle defaults (your auth views override these per-view)
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
}


# ──────────────────────────────────────────────
# SimpleJWT
# ──────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':  True,     
    'BLACKLIST_AFTER_ROTATION': True,    
}


# ──────────────────────────────────────────────
# dj-rest-auth  →  use JWT, not DRF token
# ──────────────────────────────────────────────
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE':         os.getenv("JWT_AUTH_COOKIE", "jwt-auth"),
    'JWT_AUTH_REFRESH_COOKIE': os.getenv("JWT_AUTH_REFRESH_COOKIE", "jwt-refresh"),
    'TOKEN_MODEL': None,   
}

JWT_AUTH_COOKIE = REST_AUTH['JWT_AUTH_COOKIE']
JWT_AUTH_REFRESH_COOKIE = REST_AUTH['JWT_AUTH_REFRESH_COOKIE']
JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "False" if DEBUG else "True") == "True"
JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax" if DEBUG else "None")
JWT_COOKIE_DOMAIN = os.getenv("JWT_COOKIE_DOMAIN") or None

CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "False" if DEBUG else "True") == "True"
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", JWT_COOKIE_SAMESITE)


# ──────────────────────────────────────────────
# django-allauth
# ──────────────────────────────────────────────
# Using Django's default User model (which has username), so we keep
# USERNAME_FIELD at its default. Email is still required and unique.
ACCOUNT_EMAIL_VERIFICATION       = 'none'        # we handle email verify ourselves
ACCOUNT_LOGIN_METHODS            = {'email'}
ACCOUNT_SIGNUP_FIELDS            = ['email*', 'username*', 'password1*', 'password2*']  

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': os.getenv("GOOGLE_CLIENT_ID"),
            'secret':    os.getenv("GOOGLE_CLIENT_SECRET"),
            'key':       '',
        },
        'VERIFIED_EMAIL': True,   # trust Google-verified emails → skip extra verification
    }
}

# Auto-connect social account if the email already exists in the DB
SOCIALACCOUNT_EMAIL_AUTHENTICATION         = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True


# ──────────────────────────────────────────────
# Password validation
# ──────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

PASSWORD_RESET_TIMEOUT = 10800   # 3 hours


# ──────────────────────────────────────────────
# Email
# ──────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")


# ──────────────────────────────────────────────
# Frontend URL  (used in password-reset / verify-email links)
# ──────────────────────────────────────────────
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


# ──────────────────────────────────────────────
# Internationalisation
# ──────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
