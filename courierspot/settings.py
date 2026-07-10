import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Environment detection (filesystem-based — no env variables needed).
# The cPanel home directory only exists on the live server, so:
#   on the server  -> production mode (DEBUG off, full security on)
#   on your laptop -> development mode (DEBUG on, runs with plain runserver)
# ---------------------------------------------------------------------------
CPANEL_HOME = Path('/home/bishalda')
IS_PRODUCTION = CPANEL_HOME.exists()

DEBUG = not IS_PRODUCTION

# SECRET_KEY comes from cPanel "Setup Python App" -> Environment Variables.
# In production the app REFUSES to start without it (never fall back to a
# known key on the live site — that would let anyone forge session cookies).
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise ImproperlyConfigured(
            'SECRET_KEY environment variable is not set. '
            'Add it in cPanel -> Setup Python App -> Environment Variables.')
    SECRET_KEY = 'dev-only-insecure-key'

ALLOWED_HOSTS = ["courierspot.com.np", "www.courierspot.com.np"]
if DEBUG:
    ALLOWED_HOSTS += ["127.0.0.1", "localhost"]

# Used for QR code tracking links — must be the real live domain, not localhost
SITE_URL = 'https://courierspot.com.np'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'accounts',
    'core',
    'tracking',
    'operations',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'courierspot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'courierspot.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/redirect/'
LOGOUT_REDIRECT_URL = '/'

# Stronger password rules — applies to NEW passwords only;
# existing accounts keep working and are not affected.
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

if IS_PRODUCTION:
    STATIC_ROOT = "/home/bishalda/courierspot.com.np/staticfiles"
    MEDIA_ROOT = "/home/bishalda/courierspot.com.np/media"
else:
    STATIC_ROOT = BASE_DIR / "staticfiles"
    MEDIA_ROOT = BASE_DIR / "media"

MEDIA_URL = "/media/"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        # Local: plain storage so runserver works without collectstatic.
        # Production: WhiteNoise compressed + hashed files (cache-safe).
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if IS_PRODUCTION
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # swap for SMTP later

# CSRF: required for login/forms to work over HTTPS in production
CSRF_TRUSTED_ORIGINS = ["https://courierspot.com.np", "https://www.courierspot.com.np"]

# ---------------------------------------------------------------------------
# Production security hardening — only active on the live server
# ---------------------------------------------------------------------------
if IS_PRODUCTION:
    # Cookies only ever travel over HTTPS and are invisible to JavaScript
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'

    # Staff sessions expire after 24 hours instead of Django's 2-week default
    SESSION_COOKIE_AGE = 60 * 60 * 24

    # Browser-level protections
    SECURE_CONTENT_TYPE_NOSNIFF = True      # stop MIME-type sniffing attacks
    SECURE_REFERRER_POLICY = 'same-origin'  # don't leak URLs to other sites
    X_FRAME_OPTIONS = 'DENY'                # nobody can embed the site in an iframe

    # Tell browsers to always use HTTPS for this domain (starts at 1 hour;
    # once you're confident everything works, raise to 31536000 = 1 year)
    SECURE_HSTS_SECONDS = 3600

    # NOTE: HTTP -> HTTPS redirect is normally handled by cPanel/Apache itself.
    # Only uncomment this if plain http:// pages are still reachable:
    # SECURE_SSL_REDIRECT = True