"""
Pytest configuration and fixtures for SSH Monitor tests.

This file is automatically loaded by pytest and provides shared fixtures
for all tests in the project.
"""

import os

import pytest
from celery import current_app
from django.contrib.auth import get_user_model

# Set default Django settings module for tests
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ssh_monitor.settings.local")

User = get_user_model()


@pytest.fixture(autouse=True)
def eager_celery(settings):
    """Prevent tests from requiring a live Redis/Celery backend."""
    settings.CELERY_BROKER_URL = "memory://"
    settings.CELERY_RESULT_BACKEND = "cache+memory://"
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

    current_app.conf.update(
        broker_url="memory://",
        result_backend="cache+memory://",
        task_always_eager=True,
        task_eager_propagates=True,
    )


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username="testuser", email="testuser@example.com", password="testpass123")


@pytest.fixture
def admin_user(db):
    """Create a test admin user."""
    return User.objects.create_superuser(username="admin", email="admin@example.com", password="adminpass123")


@pytest.fixture
def authenticated_client(client, user):
    """Return a client logged in as a regular user."""
    client.login(username="testuser", password="testpass123")
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Return a client logged in as an admin user."""
    client.login(username="admin", password="adminpass123")
    return client


@pytest.fixture
def encryption_key():
    """Generate a test encryption key."""
    from cryptography.fernet import Fernet

    return Fernet.generate_key().decode("utf-8")


@pytest.fixture
def encryption_service(encryption_key, settings):
    """Create an EncryptionService with a test key."""
    settings.CREDENTIAL_ENCRYPTION_KEY = encryption_key
    from apps.core.encryption import EncryptionService

    return EncryptionService()


@pytest.fixture
def disable_initial_metrics_collection(monkeypatch):
    """Skip immediate metric collection for CRUD tests that don't assert metrics."""
    from apps.servers import views as server_views

    monkeypatch.setattr(server_views.collect_server_metrics, "delay", lambda *_args, **_kwargs: None)


# Add more fixtures as needed for servers, alerts, etc.
# These will be added in later phases when the models are created.
