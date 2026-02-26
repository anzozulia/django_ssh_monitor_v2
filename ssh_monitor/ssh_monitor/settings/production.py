"""
Production settings for SSH Monitor project.

Extends base settings with production-specific configuration.
"""

import os

from .base import *  # noqa: F401, F403

DEBUG = False

# Database - PostgreSQL for production
DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    # Parse DATABASE_URL: postgres://user:password@host:port/dbname
    import re

    match = re.match(r"postgres://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", DATABASE_URL)
    if match:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": match.group(5),
                "USER": match.group(1),
                "PASSWORD": match.group(2),
                "HOST": match.group(3),
                "PORT": match.group(4),
                "CONN_MAX_AGE": 60,
                "OPTIONS": {
                    "connect_timeout": 10,
                },
            }
        }
else:
    raise ValueError("DATABASE_URL environment variable is required in production")

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# HTTPS settings (enable when behind SSL-terminating proxy)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SECURE_SSL_REDIRECT = True  # Enable if not behind a proxy that handles redirects

# HSTS settings (enable after confirming HTTPS works)
# SECURE_HSTS_SECONDS = 31536000  # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# Static files
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Logging - more restrictive in production
LOGGING["handlers"]["console"]["level"] = "WARNING"  # noqa: F405

# Sentry integration (optional)
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
