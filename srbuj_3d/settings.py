from pathlib import Path
import dj_database_url
import os

from urllib.parse import urlparse, parse_qsl
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Environment helpers
def _env_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _env_list(value, default=None):
    if value is None:
        return list(default) if default else []
    items = [item.strip() for item in value.split(",")]
    return [item for item in items if item]


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')

# Railway genera dominios *.railway.app
ALLOWED_HOSTS = [os.environ.get('ALLOWED_HOSTS')]

# Para CSRF (si usás formularios/cookies)
CSRF_TRUSTED_ORIGINS = [
    "https://*.railway.app",
]
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'corsheaders',
    'rest_framework',
    'django.contrib.staticfiles',
    'ventas',
    'drf_spectacular',
    'ventas_user_admin',
    'rest_framework.authtoken',
    rest_framework_simplejwt.token_blacklist
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'srbuj_3d.urls'

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

AUTH_USER_MODEL = 'ventas_user_admin.User'


WSGI_APPLICATION = 'srbuj_3d.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

default_db_engine = os.getenv('DB_ENGINE', 'django.db.backends.mysql')


def _parse_database_url(url: str) -> dict:
    parsed = urlparse(url)
    engine_map = {
        'postgres': 'django.db.backends.postgresql',
        'postgresql': 'django.db.backends.postgresql',
        'pgsql': 'django.db.backends.postgresql',
        'postgresql_psycopg2': 'django.db.backends.postgresql',
        'mysql': 'django.db.backends.mysql',
        'mysql2': 'django.db.backends.mysql',
    }
    scheme = (parsed.scheme or '').split('+')[0]
    engine = engine_map.get(scheme)
    if not engine:
        raise ValueError(f"Unsupported database engine in DATABASE_URL: {parsed.scheme!r}")

    options = {}
    if parsed.query:
        options = {key: value for key, value in parse_qsl(parsed.query, keep_blank_values=True)}

    return {
        'ENGINE': engine,
        'NAME': parsed.path.lstrip('/') or os.getenv('DB_NAME', ''),
        'USER': parsed.username or '',
        'PASSWORD': parsed.password or '',
        'HOST': parsed.hostname or '',
        'PORT': str(parsed.port) if parsed.port else '',
        'OPTIONS': options,
    }


def _database_from_env() -> dict:
    url = os.getenv('DATABASE_URL')
    if url:
        try:
            return _parse_database_url(url)
        except ValueError:
            pass
    return {
        'ENGINE': os.getenv('DB_ENGINE', default_db_engine),
        'NAME': os.getenv('DB_NAME', 'srbuj_db'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', '070524JN'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {},
    }


DATABASES = {
    'default': _database_from_env()
}

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_RATES': {
        'order_file_upload': '5/min',
        'shipping_quote': '20/min',
        'shipping_quote_anon': '10/min',
    },
}

_default_frontend_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOWED_ORIGINS = _env_list(
    os.getenv('CORS_ALLOWED_ORIGINS'),
    default=[
        * _default_frontend_origins,
        "https://srbuj3d.netlify.app",
    ]
)
)
if not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = list(_default_frontend_origins)

CORS_ALLOW_ALL_ORIGINS = _env_bool(os.getenv('CORS_ALLOW_ALL'), default=False)
CORS_ALLOW_CREDENTIALS = _env_bool(os.getenv('CORS_ALLOW_CREDENTIALS'), default=True)  # esto es para las cookies

if CORS_ALLOW_ALL_ORIGINS:
    # When true, the rest framework will accept requests from any origin.
    CORS_ALLOWED_ORIGINS = []

CSRF_TRUSTED_ORIGINS = _env_list(
    os.getenv('CSRF_TRUSTED_ORIGINS'),
    default=_default_frontend_origins,
)
if not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = list(_default_frontend_origins)

RS_ALLOW_CREDENTIALS = True