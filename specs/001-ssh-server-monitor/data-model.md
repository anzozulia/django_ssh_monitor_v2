# Data Model: SSH Server Monitor

**Feature**: 001-ssh-server-monitor  
**Date**: 2026-02-03

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────────┐
│      User       │       │  NotificationChannel │
├─────────────────┤       ├─────────────────────┤
│ id              │       │ id                  │
│ username        │       │ channel_type        │
│ password_hash   │       │ config (encrypted)  │
│ created_at      │       │ enabled             │
│ last_login      │       │ last_validated_at   │
└─────────────────┘       │ validation_status   │
                          └─────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                           Server                                 │
├─────────────────────────────────────────────────────────────────┤
│ id                    │ PK                                       │
│ name                  │ Display name                             │
│ host                  │ Hostname or IP                           │
│ port                  │ SSH port (default 22)                    │
│ ssh_username          │ SSH login username                       │
│ auth_type             │ ENUM: password, key_file, generated_key  │
│ credentials_encrypted │ Encrypted password or private key        │
│ check_interval_minutes│ 1 to 1440 (24 hours)                     │
│ monitoring_enabled    │ Boolean toggle                           │
│ connection_status     │ ENUM: online, unreachable, auth_failed   │
│ last_check_at         │ Timestamp of last metric collection      │
│ created_at            │ Timestamp                                │
│ updated_at            │ Timestamp                                │
├─────────────────────────────────────────────────────────────────┤
│ UNIQUE: (host, port)                                            │
└─────────────────────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                       MetricSnapshot                             │
├─────────────────────────────────────────────────────────────────┤
│ id                    │ PK                                       │
│ server_id             │ FK → Server                              │
│ timestamp             │ When metrics were collected              │
│ collection_status     │ ENUM: success, partial, failed           │
│ load_1min             │ Float (nullable)                         │
│ load_5min             │ Float (nullable)                         │
│ load_15min            │ Float (nullable)                         │
│ ram_total_bytes       │ BigInt (nullable)                        │
│ ram_used_bytes        │ BigInt (nullable)                        │
│ ram_percent           │ Float (nullable)                         │
│ swap_total_bytes      │ BigInt (nullable)                        │
│ swap_used_bytes       │ BigInt (nullable)                        │
│ swap_percent          │ Float (nullable)                         │
│ uptime_seconds        │ BigInt (nullable)                        │
│ error_message         │ Text (nullable, for failed collections)  │
├─────────────────────────────────────────────────────────────────┤
│ INDEX: (server_id, timestamp DESC)                              │
└─────────────────────────────────────────────────────────────────┘
         │
         │ 1:N (separate table for variable mount points)
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DiskMetric                                 │
├─────────────────────────────────────────────────────────────────┤
│ id                    │ PK                                       │
│ snapshot_id           │ FK → MetricSnapshot                      │
│ mount_point           │ e.g., "/", "/home", "/var"               │
│ total_bytes           │ BigInt                                   │
│ used_bytes            │ BigInt                                   │
│ percent               │ Float                                    │
├─────────────────────────────────────────────────────────────────┤
│ INDEX: (snapshot_id)                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    DefaultAlertTemplate                          │
├─────────────────────────────────────────────────────────────────┤
│ id                    │ PK                                       │
│ name                  │ Display name for template                │
│ severity              │ ENUM: warning, critical                  │
│ metric_type           │ ENUM: cpu_load, ram_percent, disk_percent│
│                       │       swap_percent, custom               │
│ metric_param          │ Additional param (e.g., mount point)     │
│ condition             │ ENUM: gt, lt, eq, gte, lte, in_range,    │
│                       │       out_of_range                       │
│ threshold_value       │ Float                                    │
│ threshold_value_2     │ Float (nullable, for range conditions)   │
│ reminder_interval_min │ 0 (off) or 15-1440                       │
│ notify_on_dismissal   │ Boolean                                  │
│ dismissal_threshold_min│ Minutes condition must clear before     │
│                       │ dismissal notification                   │
│ enabled               │ Boolean                                  │
│ created_at            │ Timestamp                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        AlertRule                                 │
├─────────────────────────────────────────────────────────────────┤
│ id                    │ PK                                       │
│ server_id             │ FK → Server                              │
│ name                  │ Display name                             │
│ severity              │ ENUM: warning, critical                  │
│ metric_type           │ ENUM: cpu_load, ram_percent, disk_percent│
│                       │       swap_percent, custom               │
│ metric_param          │ Additional param (e.g., mount point)     │
│ condition             │ ENUM: gt, lt, eq, gte, lte, in_range,    │
│                       │       out_of_range                       │
│ threshold_value       │ Float                                    │
│ threshold_value_2     │ Float (nullable, for range conditions)   │
│ reminder_interval_min │ 0 (off) or 15-1440                       │
│ notify_on_dismissal   │ Boolean                                  │
│ dismissal_threshold_min│ Minutes condition must clear before     │
│                       │ dismissal notification                   │
│ enabled               │ Boolean                                  │
│ current_state         │ ENUM: normal, triggered                  │
│ triggered_at          │ Timestamp (nullable)                     │
│ last_reminder_at      │ Timestamp (nullable)                     │
│ condition_cleared_at  │ Timestamp (nullable, for dismissal calc) │
│ cloned_from_template_id│ FK → DefaultAlertTemplate (nullable)    │
│ created_at            │ Timestamp                                │
│ updated_at            │ Timestamp                                │
├─────────────────────────────────────────────────────────────────┤
│ INDEX: (server_id, enabled)                                     │
└─────────────────────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AlertEvent                                │
├─────────────────────────────────────────────────────────────────┤
│ id                    │ PK                                       │
│ alert_rule_id         │ FK → AlertRule                           │
│ server_id             │ FK → Server (denormalized for filtering) │
│ event_type            │ ENUM: triggered, reminded, dismissed     │
│ metric_value          │ Float (value at event time)              │
│ threshold_value       │ Float (threshold at event time)          │
│ notification_sent     │ Boolean                                  │
│ notification_error    │ Text (nullable)                          │
│ created_at            │ Timestamp                                │
├─────────────────────────────────────────────────────────────────┤
│ INDEX: (server_id, created_at DESC)                             │
│ INDEX: (alert_rule_id, created_at DESC)                         │
│ INDEX: (event_type, created_at DESC)                            │
└─────────────────────────────────────────────────────────────────┘
```

## Django Models

### Server Model

```python
# apps/servers/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class AuthType(models.TextChoices):
    PASSWORD = 'password', 'Password'
    KEY_FILE = 'key_file', 'SSH Key File'
    GENERATED_KEY = 'generated_key', 'Generated Key'

class ConnectionStatus(models.TextChoices):
    ONLINE = 'online', 'Online'
    UNREACHABLE = 'unreachable', 'Unreachable'
    AUTH_FAILED = 'auth_failed', 'Authentication Failed'
    PENDING = 'pending', 'Pending First Check'

class Server(models.Model):
    name = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField(default=22)
    ssh_username = models.CharField(max_length=255)
    auth_type = models.CharField(
        max_length=20,
        choices=AuthType.choices,
        default=AuthType.PASSWORD
    )
    credentials_encrypted = models.TextField()
    check_interval_minutes = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(1440)]
    )
    monitoring_enabled = models.BooleanField(default=True)
    connection_status = models.CharField(
        max_length=20,
        choices=ConnectionStatus.choices,
        default=ConnectionStatus.PENDING
    )
    last_check_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['host', 'port'],
                name='unique_server_host_port'
            )
        ]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"
```

### MetricSnapshot Model

```python
# apps/servers/models.py (continued)

class CollectionStatus(models.TextChoices):
    SUCCESS = 'success', 'Success'
    PARTIAL = 'partial', 'Partial'
    FAILED = 'failed', 'Failed'

class MetricSnapshot(models.Model):
    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name='metrics'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    collection_status = models.CharField(
        max_length=10,
        choices=CollectionStatus.choices,
        default=CollectionStatus.SUCCESS
    )
    
    # CPU Load
    load_1min = models.FloatField(null=True, blank=True)
    load_5min = models.FloatField(null=True, blank=True)
    load_15min = models.FloatField(null=True, blank=True)
    
    # RAM
    ram_total_bytes = models.BigIntegerField(null=True, blank=True)
    ram_used_bytes = models.BigIntegerField(null=True, blank=True)
    ram_percent = models.FloatField(null=True, blank=True)
    
    # Swap
    swap_total_bytes = models.BigIntegerField(null=True, blank=True)
    swap_used_bytes = models.BigIntegerField(null=True, blank=True)
    swap_percent = models.FloatField(null=True, blank=True)
    
    # Uptime
    uptime_seconds = models.BigIntegerField(null=True, blank=True)
    
    # Error info
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['server', '-timestamp']),
        ]
        ordering = ['-timestamp']


class DiskMetric(models.Model):
    snapshot = models.ForeignKey(
        MetricSnapshot,
        on_delete=models.CASCADE,
        related_name='disk_metrics'
    )
    mount_point = models.CharField(max_length=255)
    total_bytes = models.BigIntegerField()
    used_bytes = models.BigIntegerField()
    percent = models.FloatField()

    class Meta:
        indexes = [
            models.Index(fields=['snapshot']),
        ]
```

### Alert Models

```python
# apps/alerts/models.py
from django.db import models
from apps.servers.models import Server

class Severity(models.TextChoices):
    WARNING = 'warning', 'Warning'
    CRITICAL = 'critical', 'Critical'

class MetricType(models.TextChoices):
    CPU_LOAD_1 = 'cpu_load_1', 'CPU Load (1 min)'
    CPU_LOAD_5 = 'cpu_load_5', 'CPU Load (5 min)'
    CPU_LOAD_15 = 'cpu_load_15', 'CPU Load (15 min)'
    RAM_PERCENT = 'ram_percent', 'RAM Usage %'
    RAM_USED = 'ram_used', 'RAM Used (bytes)'
    SWAP_PERCENT = 'swap_percent', 'Swap Usage %'
    DISK_PERCENT = 'disk_percent', 'Disk Usage %'
    DISK_USED = 'disk_used', 'Disk Used (bytes)'

class Condition(models.TextChoices):
    GT = 'gt', 'Greater than'
    LT = 'lt', 'Less than'
    EQ = 'eq', 'Equals'
    GTE = 'gte', 'Greater than or equals'
    LTE = 'lte', 'Less than or equals'
    IN_RANGE = 'in_range', 'Within range'
    OUT_OF_RANGE = 'out_of_range', 'Outside range'

class AlertState(models.TextChoices):
    NORMAL = 'normal', 'Normal'
    TRIGGERED = 'triggered', 'Triggered'


class DefaultAlertTemplate(models.Model):
    """Blueprint for alerts auto-applied to new servers."""
    name = models.CharField(max_length=255)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    metric_type = models.CharField(max_length=20, choices=MetricType.choices)
    metric_param = models.CharField(max_length=255, blank=True, default='')
    condition = models.CharField(max_length=20, choices=Condition.choices)
    threshold_value = models.FloatField()
    threshold_value_2 = models.FloatField(null=True, blank=True)
    reminder_interval_minutes = models.PositiveIntegerField(default=0)
    notify_on_dismissal = models.BooleanField(default=False)
    dismissal_threshold_minutes = models.PositiveIntegerField(default=5)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AlertRule(models.Model):
    """Alert rule for a specific server (may be cloned from template)."""
    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name='alert_rules'
    )
    name = models.CharField(max_length=255)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    metric_type = models.CharField(max_length=20, choices=MetricType.choices)
    metric_param = models.CharField(max_length=255, blank=True, default='')
    condition = models.CharField(max_length=20, choices=Condition.choices)
    threshold_value = models.FloatField()
    threshold_value_2 = models.FloatField(null=True, blank=True)
    reminder_interval_minutes = models.PositiveIntegerField(default=0)
    notify_on_dismissal = models.BooleanField(default=False)
    dismissal_threshold_minutes = models.PositiveIntegerField(default=5)
    enabled = models.BooleanField(default=True)
    
    # State tracking
    current_state = models.CharField(
        max_length=10,
        choices=AlertState.choices,
        default=AlertState.NORMAL
    )
    triggered_at = models.DateTimeField(null=True, blank=True)
    last_reminder_at = models.DateTimeField(null=True, blank=True)
    condition_cleared_at = models.DateTimeField(null=True, blank=True)
    
    # Template tracking
    cloned_from_template = models.ForeignKey(
        DefaultAlertTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cloned_rules'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['server', 'enabled']),
        ]

    def __str__(self):
        return f"{self.name} ({self.server.name})"


class EventType(models.TextChoices):
    TRIGGERED = 'triggered', 'Triggered'
    REMINDED = 'reminded', 'Reminded'
    DISMISSED = 'dismissed', 'Dismissed'


class AlertEvent(models.Model):
    """Record of alert state changes."""
    alert_rule = models.ForeignKey(
        AlertRule,
        on_delete=models.CASCADE,
        related_name='events'
    )
    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name='alert_events'
    )
    event_type = models.CharField(max_length=10, choices=EventType.choices)
    metric_value = models.FloatField()
    threshold_value = models.FloatField()
    notification_sent = models.BooleanField(default=False)
    notification_error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['server', '-created_at']),
            models.Index(fields=['alert_rule', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]
        ordering = ['-created_at']
```

### Notification Channel Model

```python
# apps/notifications/models.py
from django.db import models

class ChannelType(models.TextChoices):
    TELEGRAM = 'telegram', 'Telegram'
    # Future: EMAIL = 'email', 'Email'
    # Future: SLACK = 'slack', 'Slack'

class ValidationStatus(models.TextChoices):
    VALID = 'valid', 'Valid'
    INVALID = 'invalid', 'Invalid'
    PENDING = 'pending', 'Pending Validation'


class NotificationChannel(models.Model):
    channel_type = models.CharField(
        max_length=20,
        choices=ChannelType.choices,
        unique=True  # Only one config per channel type
    )
    config_encrypted = models.TextField()  # JSON with bot_token, chat_id, etc.
    enabled = models.BooleanField(default=True)
    last_validated_at = models.DateTimeField(null=True, blank=True)
    validation_status = models.CharField(
        max_length=10,
        choices=ValidationStatus.choices,
        default=ValidationStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_channel_type_display()} ({self.validation_status})"
```

## Data Retention

- **MetricSnapshot + DiskMetric**: 30 days retention
- **AlertEvent**: 30 days retention (matches metrics)
- Cleanup via scheduled Celery task running daily

```python
# Cleanup task
@shared_task
def cleanup_old_data():
    cutoff = timezone.now() - timedelta(days=30)
    MetricSnapshot.objects.filter(timestamp__lt=cutoff).delete()
    AlertEvent.objects.filter(created_at__lt=cutoff).delete()
```
