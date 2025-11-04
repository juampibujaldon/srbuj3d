"""
Django settings for srbuj3d project (Deploy en Railway)
"""

from pathlib import Path
from datetime import timedelta
import os
from urllib.parse import urlparse, parse_qsl

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# 🔐 CONFIGURACIÓN GENERAL
# ==============================
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-placeholder")

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

def _env_list(key: str, *, default=None):
    value = os.getenv(key)
    if not value:
        return list(default) if default else []
    items = [item.strip() for item in value.split(",")]
    return [item for item in items if item]


ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".railway.app"]

DEFAULT_CSRF_TRUSTED = [
    "https://*.railway.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://srbuj3d.netlify.app",
]
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(DEFAULT_CSRF_TRUSTED + _env_list("CSRF_TRUSTED_ORIGINS")))

# ==============================
# 🧩 APPS INSTALADAS
# ==============================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "rest_framework.authtoken",
    # tus apps locales:
    "ventas",
    "ventas_user_admin",
]

# ==============================
# ⚙️ MIDDLEWARE
# ==============================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "srbuj_3d.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "srbuj_3d.wsgi.application"

# ==============================
# 💾 BASE DE DATOS (MYSQL)
# ==============================
def _parse_database_url(url: str) -> dict:
    parsed = urlparse(url)
    engine_map = {
        "mysql": "django.db.backends.mysql",
        "mysql2": "django.db.backends.mysql",
        "postgres": "django.db.backends.postgresql",
    }
    scheme = (parsed.scheme or "").split("+")[0]
    engine = engine_map.get(scheme)
    if not engine:
        raise ValueError(f"Unsupported database engine in DATABASE_URL: {parsed.scheme!r}")

    options = {}
    if parsed.query:
        options = {key: value for key, value in parse_qsl(parsed.query, keep_blank_values=True)}

    return {
        "ENGINE": engine,
        "NAME": parsed.path.lstrip("/") or os.getenv("NAME", ""),
        "USER": parsed.username or os.getenv("USER", ""),
        "PASSWORD": parsed.password or os.getenv("PASSWORD", ""),
        "HOST": parsed.hostname or os.getenv("HOST", ""),
        "PORT": str(parsed.port) if parsed.port else "3306",
        "OPTIONS": options,
    }


def _sqlite_config():
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }


def _mysql_config():
    return {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("NAME", "railway"),
        "USER": os.getenv("USER", "root"),
        "PASSWORD": os.getenv("PASSWORD", ""),
        "HOST": os.getenv("HOST") or os.getenv("DB_HOST") or "mysql.railway.internal",
        "PORT": os.getenv("PORT") or os.getenv("DB_PORT") or "3306",
        "OPTIONS": {},
    }


def _database_from_env() -> dict:
    if os.getenv("USE_SQLITE", "").lower() in {"1", "true", "yes", "on"}:
        return _sqlite_config()

    url = os.getenv("MYSQL_URL") or os.getenv("DATABASE_URL")
    if url:
        try:
            return _parse_database_url(url) | {"CONN_MAX_AGE": 600}
        except ValueError:
            pass

    explicit_engine = os.getenv("DB_ENGINE") or ""
    explicit_engine = explicit_engine.strip()
    if explicit_engine == "django.db.backends.sqlite3":
        return _sqlite_config()
    if explicit_engine in {"django.db.backends.mysql", "django.db.backends.postgresql"}:
        return _mysql_config()

    if os.getenv("MYSQL_URL") or os.getenv("DATABASE_URL"):
        return _mysql_config()

    host_envs = [os.getenv("HOST"), os.getenv("DB_HOST")]
    if any(host_envs):
        return _mysql_config()

    return _sqlite_config()


DATABASES = {"default": _database_from_env()}

# ==============================
# 🔑 AUTH / VALIDADORES
# ==============================
AUTH_USER_MODEL = "ventas_user_admin.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==============================
# 🌍 INTERNACIONALIZACIÓN
# ==============================
LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

# ==============================
# 🗂️ ARCHIVOS ESTÁTICOS / MEDIA
# ==============================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# ==============================
# ⚙️ DJANGO REST FRAMEWORK
# ==============================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ==============================
# 🌐 CORS CONFIG
# ==============================
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "https://srbuj3d-production.up.railway.app",
    "https://srbuj3d.netlify.app",
]
CORS_ALLOWED_ORIGINS = list(dict.fromkeys(DEFAULT_CORS_ORIGINS + _env_list("CORS_ALLOWED_ORIGINS")))
CORS_ALLOW_CREDENTIALS = True

# ==============================
# 🔒 SEGURIDAD EXTRA (RAILWAY HTTPS)
# ==============================
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ==============================
# 🧱 AUTO FIELD
# ==============================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
