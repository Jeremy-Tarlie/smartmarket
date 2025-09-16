"""
Paramètres de développement pour SmartMarket.
"""

from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

INSTALLED_APPS += [
    "debug_toolbar",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TEMPLATE_CONTEXT": True,
}

LOGGING["handlers"]["console"]["level"] = "DEBUG"
LOGGING["root"]["level"] = "DEBUG"
