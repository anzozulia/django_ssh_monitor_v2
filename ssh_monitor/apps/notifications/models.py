import json

from django.db import models
from django.utils import timezone

from apps.core.encryption import decrypt_credential, encrypt_credential


class ChannelType(models.TextChoices):
    TELEGRAM = "telegram", "Telegram"


class ValidationStatus(models.TextChoices):
    PENDING = "pending", "Pending Validation"
    VALID = "valid", "Valid"
    INVALID = "invalid", "Invalid"


class NotificationChannel(models.Model):
    channel_type = models.CharField(max_length=20, choices=ChannelType.choices, unique=True)
    config_encrypted = models.TextField(blank=True, default="")
    enabled = models.BooleanField(default=True)
    last_validated_at = models.DateTimeField(null=True, blank=True)
    validation_status = models.CharField(
        max_length=10,
        choices=ValidationStatus.choices,
        default=ValidationStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["channel_type"]

    def __str__(self) -> str:
        return f"{self.get_channel_type_display()} ({self.validation_status})"

    def set_config(self, config: dict[str, str]) -> None:
        payload = json.dumps(config)
        self.config_encrypted = encrypt_credential(payload)

    def get_config(self) -> dict[str, str]:
        if not self.config_encrypted:
            return {}
        try:
            payload = decrypt_credential(self.config_encrypted)
            data = json.loads(payload)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def mark_validation(self, ok: bool) -> None:
        self.last_validated_at = timezone.now()
        self.validation_status = ValidationStatus.VALID if ok else ValidationStatus.INVALID
