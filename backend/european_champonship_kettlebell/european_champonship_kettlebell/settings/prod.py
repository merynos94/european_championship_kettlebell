from .base import *
import os

DEBUG = True

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "fallback-secret-key")

ALLOWED_HOSTS = ["mehardstylekettlebell.pl","www.mehardstylekettlebell.pl", "localhost"]
CSRF_TRUSTED_ORIGINS = ["https://mehardstylekettlebell.pl", "https://www.mehardstylekettlebell.pl"]
# CSRF_TRUSTED_ORIGINS = ["https://mehardstylekettlebell.pl"]

LOG_PATH = BASE_DIR.parent / "logs"
DBBACKUP_PATH = BASE_DIR.parent / "dbbackup"
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

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
