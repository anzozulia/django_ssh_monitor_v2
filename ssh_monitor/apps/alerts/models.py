from django.db import models

from apps.servers.models import Server


class Severity(models.TextChoices):
    WARNING = "warning", "Warning"
    CRITICAL = "critical", "Critical"


class MetricType(models.TextChoices):
    CPU_LOAD_1 = "cpu_load_1", "CPU Load (1 min)"
    CPU_LOAD_5 = "cpu_load_5", "CPU Load (5 min)"
    CPU_LOAD_15 = "cpu_load_15", "CPU Load (15 min)"
    RAM_PERCENT = "ram_percent", "RAM Usage %"
    RAM_USED = "ram_used", "RAM Used (bytes)"
    RAM_FREE = "ram_free", "RAM Free (bytes)"
    RAM_AVAILABLE = "ram_available", "RAM Available (bytes)"
    RAM_CACHED = "ram_cached", "RAM Cached (bytes)"
    RAM_FREE_PCT = "ram_free_pct", "RAM Free %"
    RAM_AVAILABLE_PCT = "ram_available_pct", "RAM Available %"
    SWAP_PERCENT = "swap_percent", "Swap Usage %"
    SWAP_USED = "swap_used", "Swap Used (bytes)"
    SWAP_FREE = "swap_free", "Swap Free (bytes)"
    SWAP_FREE_PCT = "swap_free_pct", "Swap Free %"
    DISK_PERCENT = "disk_percent", "Disk Usage %"
    DISK_USED = "disk_used", "Disk Used (bytes)"
    DISK_FREE = "disk_free", "Disk Free (bytes)"
    DISK_FREE_PCT = "disk_free_pct", "Disk Free %"
    UPTIME = "uptime", "Uptime (seconds)"
    CUSTOM = "custom", "Custom"


class Condition(models.TextChoices):
    GT = "gt", "Greater than"
    LT = "lt", "Less than"
    EQ = "eq", "Equals"
    GTE = "gte", "Greater than or equals"
    LTE = "lte", "Less than or equals"
    IN_RANGE = "in_range", "Within range"
    OUT_OF_RANGE = "out_of_range", "Outside range"


class AlertState(models.TextChoices):
    NORMAL = "normal", "Normal"
    TRIGGERED = "triggered", "Triggered"


class EventType(models.TextChoices):
    TRIGGERED = "triggered", "Triggered"
    REMINDED = "reminded", "Reminded"
    DISMISSED = "dismissed", "Dismissed"


class AlertRule(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="alert_rules", null=True, blank=True)
    is_default_template = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    metric_type = models.CharField(max_length=20, choices=MetricType.choices)
    metric_param = models.CharField(max_length=255, blank=True, default="")
    condition = models.CharField(max_length=20, choices=Condition.choices)
    threshold_value = models.FloatField()
    threshold_value_2 = models.FloatField(null=True, blank=True)
    reminder_interval_minutes = models.PositiveIntegerField(default=0)
    notify_on_dismissal = models.BooleanField(default=False)
    dismissal_threshold_value = models.FloatField(null=True, blank=True)
    dismissal_threshold_value_2 = models.FloatField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    current_state = models.CharField(
        max_length=10,
        choices=AlertState.choices,
        default=AlertState.NORMAL,
    )
    triggered_at = models.DateTimeField(null=True, blank=True)
    last_reminder_at = models.DateTimeField(null=True, blank=True)
    condition_cleared_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["server", "enabled"])]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        if self.is_default_template or self.server_id is None:
            return self.name
        return f"{self.name} ({self.server.name})"


class AlertEvent(models.Model):
    alert_rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name="events")
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="alert_events")
    event_type = models.CharField(max_length=10, choices=EventType.choices)
    metric_value = models.FloatField()
    threshold_value = models.FloatField()
    notification_sent = models.BooleanField(default=False)
    notification_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["server", "-created_at"]),
            models.Index(fields=["alert_rule", "-created_at"]),
            models.Index(fields=["event_type", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.server.name} {self.event_type} ({self.alert_rule.name})"
