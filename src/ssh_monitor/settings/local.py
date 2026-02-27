"""
Local development settings for SSH Monitor project.

Extends base settings with development-specific configuration.
"""

import os

from .base import *  # noqa: F401, F403

DEBUG = True

# Database - SQLite for local development without Docker
# Override with DATABASE_URL for Docker development

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL.startswith("postgres"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "ssh_monitor",
            "USER": "ssh_monitor",
            "PASSWORD": "ssh_monitor",
            "HOST": DATABASE_URL.split("@")[1].split(":")[0] if "@" in DATABASE_URL else "localhost",
            "PORT": DATABASE_URL.split(":")[-1].split("/")[0] if DATABASE_URL else "5432",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }

# Development-specific apps
INSTALLED_APPS += [  # noqa: F405
    "django_extensions",
]

# Try to add debug toolbar if available
try:
    import debug_toolbar  # noqa: F401

    INSTALLED_APPS.insert(0, "debug_toolbar")  # noqa: F405
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
except ImportError:
    pass

# Show all SQL queries in console during development
if os.environ.get("SHOW_SQL", "").lower() in ("true", "1"):
    LOGGING["loggers"]["django.db.backends"] = {  # noqa: F405
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    }

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Tailwind - use browser reload
NPM_BIN_PATH = "/usr/bin/npm"
