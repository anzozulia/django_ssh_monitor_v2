"""
Pytest configuration and fixtures for SSH Monitor tests.

This file is automatically loaded by pytest and provides shared fixtures
for all tests in the project.
"""

import os

import pytest
from django.contrib.auth import get_user_model

# Set default Django settings module for tests
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ssh_monitor.settings.local")

User = get_user_model()


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


# Add more fixtures as needed for servers, alerts, etc.
# These will be added in later phases when the models are created.
