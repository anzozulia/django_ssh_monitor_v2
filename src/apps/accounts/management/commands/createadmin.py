"""
Management command to create an admin user.

Usage:
    python manage.py createadmin --username admin --password mypassword
    python manage.py createadmin --username admin --password mypassword --email admin@example.com
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = "Create an admin user with specified username and password"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            required=True,
            help="Username for the admin account",
        )
        parser.add_argument(
            "--password",
            type=str,
            required=True,
            help="Password for the admin account",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="",
            help="Email for the admin account (optional)",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Skip confirmation prompts",
        )

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        email = options["email"]
        no_input = options["no_input"]

        # Validate password length
        if len(password) < 8:
            raise CommandError("Password must be at least 8 characters long")

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            if no_input:
                self.stdout.write(self.style.WARNING(f"User '{username}' already exists. Skipping."))
                return

            confirm = input(f"User '{username}' already exists. Update password? [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.WARNING("Operation cancelled."))
                return

            # Update existing user
            user = User.objects.get(username=username)
            user.set_password(password)
            if email:
                user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.save()

            self.stdout.write(self.style.SUCCESS(f"Updated admin user '{username}'"))
            return

        # Create new admin user
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully created admin user '{username}'"))
        except Exception as e:
            raise CommandError(f"Failed to create user: {e}") from e
