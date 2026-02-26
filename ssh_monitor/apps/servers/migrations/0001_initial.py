# Generated manually for initial servers models.
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Server",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("host", models.CharField(max_length=255)),
                ("port", models.PositiveIntegerField(default=22)),
                ("ssh_username", models.CharField(max_length=255)),
                (
                    "auth_type",
                    models.CharField(
                        choices=[
                            ("password", "Password"),
                            ("key_file", "SSH Key File"),
                            ("generated_key", "Generate and Install Key"),
                        ],
                        default="password",
                        max_length=20,
                    ),
                ),
                ("credentials_encrypted", models.TextField()),
                (
                    "check_interval_minutes",
                    models.PositiveIntegerField(
                        default=5,
                        validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(1440)],
                    ),
                ),
                ("monitoring_enabled", models.BooleanField(default=True)),
                (
                    "connection_status",
                    models.CharField(
                        choices=[
                            ("online", "Online"),
                            ("unreachable", "Unreachable"),
                            ("auth_failed", "Authentication Failed"),
                            ("pending", "Pending First Check"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("last_check_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="MetricSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "collection_status",
                    models.CharField(
                        choices=[("success", "Success"), ("partial", "Partial"), ("failed", "Failed")],
                        default="success",
                        max_length=10,
                    ),
                ),
                ("load_1min", models.FloatField(blank=True, null=True)),
                ("load_5min", models.FloatField(blank=True, null=True)),
                ("load_15min", models.FloatField(blank=True, null=True)),
                ("ram_total_bytes", models.BigIntegerField(blank=True, null=True)),
                ("ram_used_bytes", models.BigIntegerField(blank=True, null=True)),
                ("ram_percent", models.FloatField(blank=True, null=True)),
                ("swap_total_bytes", models.BigIntegerField(blank=True, null=True)),
                ("swap_used_bytes", models.BigIntegerField(blank=True, null=True)),
                ("swap_percent", models.FloatField(blank=True, null=True)),
                ("uptime_seconds", models.BigIntegerField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True, null=True)),
                (
                    "server",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="metrics", to="servers.server"),
                ),
            ],
            options={"ordering": ["-timestamp"]},
        ),
        migrations.CreateModel(
            name="DiskMetric",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("mount_point", models.CharField(max_length=255)),
                ("total_bytes", models.BigIntegerField()),
                ("used_bytes", models.BigIntegerField()),
                ("percent", models.FloatField()),
                (
                    "snapshot",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="disk_metrics", to="servers.metricsnapshot"),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="server",
            constraint=models.UniqueConstraint(fields=("host", "port"), name="unique_server_host_port"),
        ),
        migrations.AddIndex(
            model_name="metricsnapshot",
            index=models.Index(fields=["server", "-timestamp"], name="servers_met_server__e9b54d_idx"),
        ),
        migrations.AddIndex(
            model_name="diskmetric",
            index=models.Index(fields=["snapshot"], name="servers_dis_snapsho_7143be_idx"),
        ),
    ]
