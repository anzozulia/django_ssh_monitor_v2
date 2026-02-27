from django.utils import timezone

from apps.alerts.models import AlertEvent, AlertRule, AlertState, Condition, EventType, MetricType
from apps.alerts.services.notification_service import NotificationDispatcher
from apps.servers.models import MetricSnapshot, Server


class AlertEvaluationService:
    @staticmethod
    def _emit_event(
        *,
        rule: AlertRule,
        server: Server,
        event_type: str,
        metric_value: float,
    ) -> None:
        event = AlertEvent.objects.create(
            alert_rule=rule,
            server=server,
            event_type=event_type,
            metric_value=metric_value,
            threshold_value=rule.threshold_value,
        )
        sent, error = NotificationDispatcher().send_event(event)
        event.notification_sent = sent
        event.notification_error = error or ""
        event.save(update_fields=["notification_sent", "notification_error"])

    @staticmethod
    def _resolve_metric(rule: AlertRule, snapshot: MetricSnapshot) -> float | None:
        if rule.metric_type == MetricType.CPU_LOAD_1:
            return snapshot.load_1min
        if rule.metric_type == MetricType.CPU_LOAD_5:
            return snapshot.load_5min
        if rule.metric_type == MetricType.CPU_LOAD_15:
            return snapshot.load_15min
        if rule.metric_type == MetricType.RAM_PERCENT:
            return snapshot.ram_percent
        if rule.metric_type == MetricType.RAM_USED:
            return float(snapshot.ram_used_bytes) if snapshot.ram_used_bytes is not None else None
        if rule.metric_type == MetricType.RAM_FREE:
            return float(snapshot.ram_free_bytes) if snapshot.ram_free_bytes is not None else None
        if rule.metric_type == MetricType.RAM_AVAILABLE:
            return float(snapshot.ram_available_bytes) if snapshot.ram_available_bytes is not None else None
        if rule.metric_type == MetricType.RAM_CACHED:
            return float(snapshot.ram_cached_bytes) if snapshot.ram_cached_bytes is not None else None
        if rule.metric_type == MetricType.RAM_FREE_PCT:
            return snapshot.ram_free_percent
        if rule.metric_type == MetricType.RAM_AVAILABLE_PCT:
            return snapshot.ram_available_percent
        if rule.metric_type == MetricType.SWAP_PERCENT:
            return snapshot.swap_percent
        if rule.metric_type == MetricType.SWAP_USED:
            return float(snapshot.swap_used_bytes) if snapshot.swap_used_bytes is not None else None
        if rule.metric_type == MetricType.SWAP_FREE:
            return float(snapshot.swap_free_bytes) if snapshot.swap_free_bytes is not None else None
        if rule.metric_type == MetricType.SWAP_FREE_PCT:
            return snapshot.swap_free_percent
        if rule.metric_type == MetricType.DISK_PERCENT:
            if not rule.metric_param:
                disk = snapshot.disk_metrics.order_by("-percent").first()
                return disk.percent if disk else None
            disk = snapshot.disk_metrics.filter(mount_point=rule.metric_param).first()
            return disk.percent if disk else None
        if rule.metric_type == MetricType.DISK_USED:
            if not rule.metric_param:
                disk = snapshot.disk_metrics.order_by("-used_bytes").first()
                return float(disk.used_bytes) if disk else None
            disk = snapshot.disk_metrics.filter(mount_point=rule.metric_param).first()
            return float(disk.used_bytes) if disk else None
        if rule.metric_type == MetricType.DISK_FREE:
            if not rule.metric_param:
                disk = snapshot.disk_metrics.filter(available_bytes__isnull=False).order_by("available_bytes").first()
                return float(disk.available_bytes) if disk and disk.available_bytes is not None else None
            disk = snapshot.disk_metrics.filter(mount_point=rule.metric_param).first()
            return float(disk.available_bytes) if disk and disk.available_bytes is not None else None
        if rule.metric_type == MetricType.DISK_FREE_PCT:
            if not rule.metric_param:
                disk = snapshot.disk_metrics.order_by("percent").first()
                return float(100 - disk.percent) if disk else None
            disk = snapshot.disk_metrics.filter(mount_point=rule.metric_param).first()
            return float(100 - disk.percent) if disk else None
        if rule.metric_type == MetricType.UPTIME:
            return float(snapshot.uptime_seconds) if snapshot.uptime_seconds is not None else None
        if rule.metric_type == MetricType.CUSTOM and rule.metric_param == "ssh_connectivity":
            return 0.0 if snapshot.collection_status == "success" else 1.0
        return None

    @staticmethod
    def _condition_matches(rule: AlertRule, value: float) -> bool:
        v1 = rule.threshold_value
        v2 = rule.threshold_value_2
        if rule.condition == Condition.GT:
            return value > v1
        if rule.condition == Condition.LT:
            return value < v1
        if rule.condition == Condition.EQ:
            return value == v1
        if rule.condition == Condition.GTE:
            return value >= v1
        if rule.condition == Condition.LTE:
            return value <= v1
        if rule.condition == Condition.IN_RANGE and v2 is not None:
            return v1 <= value <= v2
        if rule.condition == Condition.OUT_OF_RANGE and v2 is not None:
            return value < v1 or value > v2
        return False

    @staticmethod
    def _dismissal_matches(rule: AlertRule, value: float) -> bool:
        d1 = rule.dismissal_threshold_value
        d2 = rule.dismissal_threshold_value_2
        v1 = rule.threshold_value
        v2 = rule.threshold_value_2

        if rule.metric_type == MetricType.CUSTOM:
            return not AlertEvaluationService._condition_matches(rule, value)

        if rule.condition == Condition.GT:
            return value <= (d1 if d1 is not None else v1)
        if rule.condition == Condition.GTE:
            return value < (d1 if d1 is not None else v1)
        if rule.condition == Condition.LT:
            return value >= (d1 if d1 is not None else v1)
        if rule.condition == Condition.LTE:
            return value > (d1 if d1 is not None else v1)
        if rule.condition == Condition.EQ:
            tolerance = d1 if d1 is not None else 0
            if tolerance <= 0:
                return value != v1
            return abs(value - v1) >= tolerance
        if rule.condition == Condition.IN_RANGE and v2 is not None:
            if d1 is None or d2 is None:
                return value < v1 or value > v2
            return value <= d1 or value >= d2
        if rule.condition == Condition.OUT_OF_RANGE and v2 is not None:
            if d1 is None or d2 is None:
                return v1 <= value <= v2
            return d1 <= value <= d2
        return not AlertEvaluationService._condition_matches(rule, value)

    def evaluate_server_alerts(self, server: Server) -> None:
        snapshot = server.metrics.first()
        if not snapshot:
            return
        now = timezone.now()
        rules = server.alert_rules.filter(enabled=True)
        for rule in rules:
            metric_value = self._resolve_metric(rule, snapshot)
            if metric_value is None:
                continue
            matches = self._condition_matches(rule, metric_value)

            if matches and rule.current_state == AlertState.NORMAL:
                rule.current_state = AlertState.TRIGGERED
                rule.triggered_at = now
                rule.last_reminder_at = now
                rule.condition_cleared_at = None
                rule.save(
                    update_fields=[
                        "current_state",
                        "triggered_at",
                        "last_reminder_at",
                        "condition_cleared_at",
                        "updated_at",
                    ]
                )
                self._emit_event(
                    rule=rule,
                    server=server,
                    event_type=EventType.TRIGGERED,
                    metric_value=metric_value,
                )
                continue

            if matches and rule.current_state == AlertState.TRIGGERED:
                if rule.reminder_interval_minutes > 0:
                    last = rule.last_reminder_at or rule.triggered_at or now
                    if (now - last).total_seconds() >= rule.reminder_interval_minutes * 60:
                        rule.last_reminder_at = now
                        rule.save(update_fields=["last_reminder_at", "updated_at"])
                        self._emit_event(
                            rule=rule,
                            server=server,
                            event_type=EventType.REMINDED,
                            metric_value=metric_value,
                        )
                continue

            if not matches and rule.current_state == AlertState.TRIGGERED:
                if not self._dismissal_matches(rule, metric_value):
                    continue
                rule.current_state = AlertState.NORMAL
                rule.triggered_at = None
                rule.last_reminder_at = None
                rule.condition_cleared_at = None
                rule.save(
                    update_fields=[
                        "current_state",
                        "triggered_at",
                        "last_reminder_at",
                        "condition_cleared_at",
                        "updated_at",
                    ]
                )
                if rule.notify_on_dismissal:
                    self._emit_event(
                        rule=rule,
                        server=server,
                        event_type=EventType.DISMISSED,
                        metric_value=metric_value,
                    )
