"""Django settings for the StudySpot API.

One settings module serves every environment, driven by the environment itself:

======================  ==========================================
Docker Compose          ``DATABASE_URL`` points at the postgres service
Native development      ``DATABASE_URL`` points at localhost
AWS Lambda              ``DATABASE_URL`` points at RDS in the VPC
======================  ==========================================

Nothing here reads a secret from a file, because two of those three
environments have no filesystem to read one from.
"""

from __future__ import annotations

import os
from pathlib import Path

import dj_database_url

#: ``src/backend/studyspot/settings.py`` -> ``src/backend/``
BASE_DIR = Path(__file__).resolve().parent.parent


def _flag(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


DEBUG = _flag("DJANGO_DEBUG", default=False)

# A generated key for local work only. Deployments must supply their own, and a
# deployment that forgets is better stopped here than left serving signed
# cookies anyone can forge.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or ""
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError(
            "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is off. "
            "Terraform generates one and passes it to the Lambda functions."
        )
    SECRET_KEY = "django-insecure-local-development-key-not-for-deployment"

# CloudFront is the only route to the API: the Lambda function URL rejects any
# request that is not SigV4-signed by the distribution, and CloudFront does not
# forward the Host header to it. The host Django sees is therefore the function
# URL's own, which is not knowable ahead of an apply. Host-header validation
# would add nothing that the signature does not already guarantee, so the
# default is permissive and DJANGO_ALLOWED_HOSTS can narrow it.
ALLOWED_HOSTS = [
    host.strip() for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",") if host.strip()
]

# Set to the CloudFront domain once it exists, so that the admin and any future
# session-authenticated write can pass CSRF checks.
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "spots",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Directly after SecurityMiddleware, as WhiteNoise requires.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Last, so that it sees exceptions from every view below it.
    "studyspot.middleware.DatabaseUnavailableMiddleware",
]

ROOT_URLCONF = "studyspot.urls"
WSGI_APPLICATION = "studyspot.wsgi.application"
ASGI_APPLICATION = "studyspot.asgi.application"

# The public contract is /spots and /spots/{id} without trailing slashes, and
# APPEND_SLASH would answer those with a 301 to /spots/ instead of the page the
# frontend asked for.
APPEND_SLASH = False

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# -- Database ------------------------------------------------------------------

#: Matches the Compose service, so `just dev-backend` and `docker compose up`
#: reach the same database without anyone exporting anything.
DEFAULT_DATABASE_URL = "postgresql://studyspot:studyspot@localhost:5432/studyspot"

DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        # A connection per request, deliberately. Lambda freezes an execution
        # environment between invocations, and a persistent connection is
        # usually a dead socket by the time the next request thaws it.
        conn_max_age=0,
        ssl_require=_flag("DATABASE_SSL_REQUIRE", default=False),
    )
}

# Set after parsing rather than passed in: dj_database_url.parse() takes a fixed
# set of keyword arguments and would reject this one. Shorter than the API
# function's own timeout, so a database that is gone produces an error response
# rather than a request that dies when Lambda stops it.
DATABASES["default"].setdefault("OPTIONS", {})["connect_timeout"] = 5

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -- Internationalization ------------------------------------------------------

LANGUAGE_CODE = "en-us"

# Every record in the dataset is in New York City, and opening hours are on the
# backlog, so local time is the useful default rather than UTC.
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True

# -- Static files --------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        # Compressed but unhashed: the manifest variant raises on any file
        # collectstatic has not seen, which would turn a forgotten build step
        # into a 500 on the admin rather than a missing stylesheet.
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

if DEBUG:
    # Serve static files from the apps themselves rather than from STATIC_ROOT.
    # A checkout that has not run collectstatic has no STATIC_ROOT, and without
    # this WhiteNoise warns about the missing directory on every single request.
    # Deployments run collectstatic at build time; see infra/scripts/build-lambda.sh.
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_AUTOREFRESH = True

# -- Django REST Framework -----------------------------------------------------

REST_FRAMEWORK = {
    # JSON only in deployments. The browsable API is a development convenience
    # and pulls in template rendering the API has no other use for.
    "DEFAULT_RENDERER_CLASSES": (
        [
            "rest_framework.renderers.JSONRenderer",
            "rest_framework.renderers.BrowsableAPIRenderer",
        ]
        if DEBUG
        else ["rest_framework.renderers.JSONRenderer"]
    ),
    # Every error response shares one envelope; see studyspot/errors.py.
    "EXCEPTION_HANDLER": "studyspot.errors.exception_handler",
    "UNAUTHENTICATED_USER": None,
}

# -- Admin ---------------------------------------------------------------------

#: The admin is off unless asked for. It is reachable from the internet through
#: CloudFront, and the backlog has not reached accounts yet, so there is nothing
#: to protect it but a password nobody has set.
ENABLE_ADMIN = _flag("DJANGO_ENABLE_ADMIN", default=DEBUG)

# -- Security ------------------------------------------------------------------

# CloudFront terminates TLS and redirects HTTP, so Django sees a plain HTTP
# request and must be told what the viewer used.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # The redirect itself is CloudFront's job; doing it here as well would cost
    # a Lambda invocation to answer with a 301.
    SECURE_SSL_REDIRECT = False

# -- Logging -------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        # CloudWatch captures stdout from the Lambda runtime, so structured log
        # shipping is something this does not need to arrange.
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
}
