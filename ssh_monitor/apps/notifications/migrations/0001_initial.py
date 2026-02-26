from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="NotificationChannel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("channel_type", models.CharField(choices=[("telegram", "Telegram")], max_length=20, unique=True)),
                ("config_encrypted", models.TextField(blank=True, default="")),
                ("enabled", models.BooleanField(default=True)),
                ("last_validated_at", models.DateTimeField(blank=True, null=True)),
                (
                    "validation_status",
                    models.CharField(
                        choices=[("pending", "Pending Validation"), ("valid", "Valid"), ("invalid", "Invalid")],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["channel_type"]},
        ),
    ]
