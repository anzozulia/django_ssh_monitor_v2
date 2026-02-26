"""
Celery application configuration for SSH Monitor.

Configures Celery with Redis broker and django-celery-beat scheduler.
"""

import os

from celery import Celery

# Set the default Django settings module for the 'celery' program
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ssh_monitor.settings.local")

# Create Celery application
app = Celery("ssh_monitor")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery connection."""
    print(f"Request: {self.request!r}")
