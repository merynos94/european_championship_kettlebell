from .base import *
import os

DEBUG = False

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "fallback-secret-key")

ALLOWED_HOSTS = ["mehardstylekettlebell.pl", "localhost"]
CSRF_TRUSTED_ORIGINS = ["https://mehardstylekettlebell.pl"]

LOG_PATH = BASE_DIR.parent / "logs"
DBBACKUP_PATH = BASE_DIR.parent / "dbbackup"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "default_db"),
        "USER": os.getenv("POSTGRES_USER", "default_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "default_password"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# STATIC_ROOT = BASE_DIR.joinpath("public")