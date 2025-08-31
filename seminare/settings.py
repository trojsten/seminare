from pathlib import Path

from environ import Env

env = Env()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-zrj)_o^55fk_le7=sdm@u%plgdf+9jz!1pb!#jpn$*zfxku(1$",
)
DEBUG = env("DEBUG", default=False)
ALLOWED_HOSTS = env("ALLOWED_HOSTS", default=["*"])

X_FRAME_OPTIONS = "SAMEORIGIN"

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    #
    "seminare.style",
    "seminare.users",
    "seminare.submits",
    "seminare.problems",
    "seminare.contests",
    "seminare.content",
    "seminare.organizer",
    "seminare.legacy",
    #
    "django_probes",
    "debug_toolbar",
    "mozilla_django_oidc",
    "widget_tweaks",
    "rest_framework",
    "rest_framework.authtoken",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "mozilla_django_oidc.middleware.SessionRefresh",
]

ROOT_URLCONF = "seminare.urls"

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
                "seminare.contests.context_processors.contest",
            ],
        },
    },
]

WSGI_APPLICATION = "seminare.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {"default": env.db()}

# Authentication

AUTH_USER_MODEL = "users.User"
AUTH_PASSWORD_VALIDATORS = []
AUTHENTICATION_BACKENDS = [
    "seminare.users.auth.TrojstenOIDCAB",
    "django.contrib.auth.backends.ModelBackend",
]

OIDC_OP_JWKS_ENDPOINT = env(
    "OIDC_OP_JWKS_ENDPOINT",
    default="https://id.trojsten.sk/oauth/.well-known/jwks.json",
)
OIDC_OP_AUTHORIZATION_ENDPOINT = env(
    "OIDC_OP_AUTHORIZATION_ENDPOINT", default="https://id.trojsten.sk/oauth/authorize/"
)
OIDC_OP_USER_ENDPOINT = env(
    "OIDC_OP_USER_ENDPOINT", default="https://id.trojsten.sk/oauth/userinfo/"
)
OIDC_OP_TOKEN_ENDPOINT = env(
    "OIDC_OP_TOKEN_ENDPOINT", default="https://id.trojsten.sk/oauth/token/"
)
OIDC_RP_SCOPES = "openid email profile school_info"
OIDC_RP_SIGN_ALGO = "RS256"
OIDC_RP_CLIENT_ID = env("OIDC_RP_CLIENT_ID", default="")
OIDC_RP_CLIENT_SECRET = env("OIDC_RP_CLIENT_SECRET", default="")
OIDC_OP_LOGOUT_URL_METHOD = "seminare.users.auth.logout_url"
OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS = 3600  # 1-hour

LOGIN_URL = "oidc_authentication_init"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

JUDGE_URL: str = env("JUDGE_URL", default="https://judge.ksp.sk")
JUDGE_TOKEN: str = env("JUDGE_TOKEN")

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "seminare.organizer.api.auth.IsContestAdmin",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "sk"

TIME_ZONE = "Europe/Bratislava"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "uploads/"
MEDIA_ROOT = BASE_DIR / "uploads"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "private": {
        "BACKEND": "seminare.problems.storages.OverwriteStorage",
        "OPTIONS": {
            "location": BASE_DIR / "private",
            "base_url": "/.private/",
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if DEBUG:
    import socket  # only if you haven't already imported this

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1"]
