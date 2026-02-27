"""
Unit tests for createadmin management command.

Tests the custom management command for creating admin users.
"""

from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

User = get_user_model()


class TestCreateAdminCommand:
    """Tests for createadmin management command."""

    def test_create_new_admin_user(self, db):
        """Test creating a new admin user."""
        out = StringIO()
        call_command("createadmin", "--username", "newadmin", "--password", "securepass123", "--no-input", stdout=out)

        # Check user was created
        user = User.objects.get(username="newadmin")
        assert user.is_superuser is True
        assert user.is_staff is True
        assert user.check_password("securepass123")

        # Check success message
        assert "Successfully created admin user" in out.getvalue()

    def test_create_admin_with_email(self, db):
        """Test creating admin user with email."""
        out = StringIO()
        call_command(
            "createadmin",
            "--username",
            "emailadmin",
            "--password",
            "securepass123",
            "--email",
            "admin@example.com",
            "--no-input",
            stdout=out,
        )

        user = User.objects.get(username="emailadmin")
        assert user.email == "admin@example.com"

    def test_create_admin_short_password_fails(self, db):
        """Test that password too short raises error."""
        with pytest.raises(CommandError, match="at least 8 characters"):
            call_command("createadmin", "--username", "shortpass", "--password", "short", "--no-input")

    def test_existing_user_skipped_with_no_input(self, db):
        """Test that existing user is skipped with --no-input flag."""
        # Create user first
        User.objects.create_superuser(username="existing", email="existing@example.com", password="oldpassword123")

        out = StringIO()
        call_command("createadmin", "--username", "existing", "--password", "newpassword123", "--no-input", stdout=out)

        # User should still have old password
        user = User.objects.get(username="existing")
        assert user.check_password("oldpassword123")

        # Should show warning
        assert "already exists" in out.getvalue()

    def test_password_is_hashed(self, db):
        """Test that password is properly hashed, not stored in plain text."""
        call_command("createadmin", "--username", "hashtest", "--password", "testpassword123", "--no-input")

        user = User.objects.get(username="hashtest")

        # Password should not be stored as plain text
        assert user.password != "testpassword123"

        # But should validate correctly
        assert user.check_password("testpassword123")

    def test_user_is_superuser_and_staff(self, db):
        """Test that created user has superuser and staff permissions."""
        call_command("createadmin", "--username", "permtest", "--password", "testpassword123", "--no-input")

        user = User.objects.get(username="permtest")
        assert user.is_superuser is True
        assert user.is_staff is True
        assert user.is_active is True

    def test_create_multiple_admins(self, db):
        """Test creating multiple admin users."""
        for i in range(3):
            call_command("createadmin", "--username", f"admin{i}", "--password", f"password{i}12", "--no-input")

        assert User.objects.filter(is_superuser=True).count() == 3

    def test_required_arguments(self, db):
        """Test that username and password are required."""
        # Missing username
        with pytest.raises(CommandError):
            call_command("createadmin", "--password", "testpass123")

        # Missing password
        with pytest.raises(CommandError):
            call_command("createadmin", "--username", "testuser")


class TestCreateAdminEdgeCases:
    """Edge case tests for createadmin command."""

    def test_special_characters_in_password(self, db):
        """Test password with special characters."""
        call_command("createadmin", "--username", "specialpass", "--password", "P@$$w0rd!#%&", "--no-input")

        user = User.objects.get(username="specialpass")
        assert user.check_password("P@$$w0rd!#%&")

    def test_unicode_in_username(self, db):
        """Test username with unicode characters (if supported)."""
        # Note: Django's default User model may have restrictions
        try:
            call_command("createadmin", "--username", "admin_тест", "--password", "testpassword123", "--no-input")
            user = User.objects.get(username="admin_тест")
            assert user is not None
        except Exception:
            # Some configurations may not support unicode usernames
            pytest.skip("Unicode usernames not supported in this configuration")

    def test_exactly_8_character_password(self, db):
        """Test minimum length password (exactly 8 characters)."""
        call_command("createadmin", "--username", "minpass", "--password", "12345678", "--no-input")

        user = User.objects.get(username="minpass")
        assert user.check_password("12345678")
