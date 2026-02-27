from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class AuthType(models.TextChoices):
    PASSWORD = "password", "Password"
    KEY_FILE = "key_file", "SSH Key File"
    GENERATED_KEY = "generated_key", "Generate and Install Key"


class ConnectionStatus(models.TextChoices):
    ONLINE = "online", "Online"
    UNREACHABLE = "unreachable", "Unreachable"
    AUTH_FAILED = "auth_failed", "Authentication Failed"
    PENDING = "pending", "Pending First Check"


class CollectionStatus(models.TextChoices):
    SUCCESS = "success", "Success"
    PARTIAL = "partial", "Partial"
    FAILED = "failed", "Failed"


class Server(models.Model):
    name = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField(default=22)
    ssh_username = models.CharField(max_length=255)
    auth_type = models.CharField(
        max_length=20,
        choices=AuthType.choices,
        default=AuthType.PASSWORD,
    )
    credentials_encrypted = models.TextField()
    check_interval_minutes = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
    )
    monitoring_enabled = models.BooleanField(default=True)
    connection_status = models.CharField(
        max_length=20,
        choices=ConnectionStatus.choices,
        default=ConnectionStatus.PENDING,
    )
    last_check_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["host", "port"],
                name="unique_server_host_port",
            )
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.host}:{self.port})"


class MetricSnapshot(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="metrics")
    timestamp = models.DateTimeField(auto_now_add=True)
    collection_status = models.CharField(
        max_length=10,
        choices=CollectionStatus.choices,
        default=CollectionStatus.SUCCESS,
    )

    load_1min = models.FloatField(null=True, blank=True)
    load_5min = models.FloatField(null=True, blank=True)
    load_15min = models.FloatField(null=True, blank=True)

    ram_total_bytes = models.BigIntegerField(null=True, blank=True)
    ram_used_bytes = models.BigIntegerField(null=True, blank=True)
    ram_free_bytes = models.BigIntegerField(null=True, blank=True)
    ram_available_bytes = models.BigIntegerField(null=True, blank=True)
    ram_cached_bytes = models.BigIntegerField(null=True, blank=True)
    ram_buffers_bytes = models.BigIntegerField(null=True, blank=True)
    ram_shared_bytes = models.BigIntegerField(null=True, blank=True)
    ram_percent = models.FloatField(null=True, blank=True)
    ram_free_percent = models.FloatField(null=True, blank=True)
    ram_available_percent = models.FloatField(null=True, blank=True)

    swap_total_bytes = models.BigIntegerField(null=True, blank=True)
    swap_used_bytes = models.BigIntegerField(null=True, blank=True)
    swap_free_bytes = models.BigIntegerField(null=True, blank=True)
    swap_cached_bytes = models.BigIntegerField(null=True, blank=True)
    swap_percent = models.FloatField(null=True, blank=True)
    swap_free_percent = models.FloatField(null=True, blank=True)

    cpu_cores = models.PositiveIntegerField(null=True, blank=True)

    uptime_seconds = models.BigIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["server", "-timestamp"])]
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.server.name} @ {self.timestamp.isoformat()}"


class DiskMetric(models.Model):
    snapshot = models.ForeignKey(
        MetricSnapshot,
        on_delete=models.CASCADE,
        related_name="disk_metrics",
    )
    mount_point = models.CharField(max_length=255)
    filesystem = models.CharField(max_length=255, blank=True, default="", db_default="")
    total_bytes = models.BigIntegerField()
    used_bytes = models.BigIntegerField()
    available_bytes = models.BigIntegerField(null=True, blank=True)
    percent = models.FloatField()

    class Meta:
        indexes = [models.Index(fields=["snapshot"])]

    def __str__(self) -> str:
        return f"{self.mount_point} ({self.percent:.2f}%)"
