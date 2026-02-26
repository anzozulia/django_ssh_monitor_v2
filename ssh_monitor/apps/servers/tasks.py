import errno
import json
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from apps.alerts.models import AlertEvent
from apps.alerts.services.notification_service import NotificationDispatcher
from apps.servers.models import CollectionStatus, DiskMetric, MetricSnapshot, Server
from apps.servers.services.metrics_service import MetricsService
from apps.servers.services.ping_service import PingService
from apps.servers.services.ssh_service import SSHService

logger = logging.getLogger(__name__)


def _log_schedule_accuracy(server: Server) -> None:
    """Emit interval-accuracy metrics for SC-007 tracking."""
    task_name = f"collect_server_metrics_{server.id}"
    task = PeriodicTask.objects.filter(name=task_name).only("last_run_at").first()
    if not task or not task.last_run_at or not server.last_check_at:
        return
    expected_gap = timedelta(minutes=server.check_interval_minutes)
    actual_gap = server.last_check_at - task.last_run_at
    drift_seconds = abs((actual_gap - expected_gap).total_seconds())
    logger.info(
        "schedule_accuracy server_id=%s expected_seconds=%s actual_seconds=%.2f drift_seconds=%.2f",
        server.id,
        expected_gap.total_seconds(),
        actual_gap.total_seconds(),
        drift_seconds,
    )


def _notify_disk_full(server: Server, error_message: str) -> None:
    """
    Try to notify admins if monitoring host runs out of disk.
    Falls back to critical logs when notification channels are unavailable.
    """
    dispatcher = NotificationDispatcher()
    fake_event = AlertEvent(
        event_type="triggered",
        metric_value=1.0,
        threshold_value=1.0,
    )
    fake_event.server = server  # type: ignore[assignment]
    fake_event.alert_rule = type(
        "DiskFullRule",
        (),
        {
            "severity": "critical",
            "name": "Monitoring node disk full",
            "metric_type": "custom",
            "condition": "eq",
        },
    )()
    try:
        dispatcher.send_event(fake_event)
    except Exception as notify_exc:  # noqa: BLE001
        logger.error("Failed to send disk-full admin notification: %s", notify_exc)
    logger.critical("Disk full while collecting metrics for server %s: %s", server.id, error_message)


def _save_failed_snapshot(server: Server, message: str) -> None:
    try:
        MetricSnapshot.objects.create(
            server=server,
            collection_status=CollectionStatus.FAILED,
            error_message=message,
        )
    except OSError as exc:
        if exc.errno == errno.ENOSPC:
            _notify_disk_full(server, str(exc))
            return
        raise


@shared_task
def cleanup_old_data() -> dict[str, int]:
    """Delete metrics and alert events older than 30 days."""
    cutoff = timezone.now() - timedelta(days=30)
    from apps.alerts.models import AlertEvent

    deleted_metrics, _ = MetricSnapshot.objects.filter(timestamp__lt=cutoff).delete()
    deleted_events, _ = AlertEvent.objects.filter(created_at__lt=cutoff).delete()
    logger.info(
        "cleanup_old_data cutoff=%s metrics_deleted=%s events_deleted=%s",
        cutoff.isoformat(),
        deleted_metrics,
        deleted_events,
    )
    return {"metrics_deleted": deleted_metrics, "events_deleted": deleted_events}


def schedule_server_collection(server: Server) -> None:
    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=server.check_interval_minutes,
        period=IntervalSchedule.MINUTES,
    )
    task_name = f"collect_server_metrics_{server.id}"
    PeriodicTask.objects.update_or_create(
        name=task_name,
        defaults={
            "interval": schedule,
            "task": "apps.servers.tasks.collect_server_metrics",
            "args": json.dumps([server.id]),
            "enabled": server.monitoring_enabled,
        },
    )


@shared_task
def collect_server_metrics(server_id: int) -> None:
    server = Server.objects.get(id=server_id)
    if not server.monitoring_enabled:
        return

    ssh = SSHService(server)
    metrics_service = MetricsService()
    error_message = ""

    for attempt in range(3):
        try:
            ssh.connect()
            metrics = metrics_service.collect_metrics(ssh)
            try:
                snapshot = MetricSnapshot.objects.create(
                    server=server,
                    collection_status=CollectionStatus.SUCCESS,
                    load_1min=metrics["load_1min"],
                    load_5min=metrics["load_5min"],
                    load_15min=metrics["load_15min"],
                    ram_total_bytes=metrics["ram_total_bytes"],
                    ram_used_bytes=metrics["ram_used_bytes"],
                    ram_free_bytes=metrics["ram_free_bytes"],
                    ram_available_bytes=metrics["ram_available_bytes"],
                    ram_cached_bytes=metrics["ram_cached_bytes"],
                    ram_buffers_bytes=metrics["ram_buffers_bytes"],
                    ram_shared_bytes=metrics["ram_shared_bytes"],
                    ram_percent=metrics["ram_percent"],
                    ram_free_percent=metrics["ram_free_percent"],
                    ram_available_percent=metrics["ram_available_percent"],
                    swap_total_bytes=metrics["swap_total_bytes"],
                    swap_used_bytes=metrics["swap_used_bytes"],
                    swap_free_bytes=metrics["swap_free_bytes"],
                    swap_cached_bytes=metrics["swap_cached_bytes"],
                    swap_percent=metrics["swap_percent"],
                    swap_free_percent=metrics["swap_free_percent"],
                    cpu_cores=metrics["cpu_cores"],
                    uptime_seconds=metrics["uptime_seconds"],
                )
                for disk in metrics["disk_metrics"]:
                    DiskMetric.objects.create(snapshot=snapshot, **disk)
            except OSError as exc:
                if exc.errno == errno.ENOSPC:
                    _notify_disk_full(server, str(exc))
                    return
                raise
            from apps.alerts.tasks import evaluate_server_alerts

            evaluate_server_alerts.delay(server.id)
            server.connection_status = "online"
            server.last_check_at = timezone.now()
            server.save(update_fields=["connection_status", "last_check_at", "updated_at"])
            _log_schedule_accuracy(server)
            return
        except Exception as exc:  # noqa: BLE001
            error_message = str(exc)
            logger.warning("Metric collection attempt %s failed for server %s: %s", attempt + 1, server_id, exc)
        finally:
            try:
                ssh.disconnect()
            except Exception:  # noqa: BLE001
                pass

    ping_ok = PingService.ping(server.host)
    message = f"SSH failed after 3 retries. Ping status: {'ok' if ping_ok else 'failed'}. Error: {error_message}"
    _save_failed_snapshot(server, message)
    from apps.alerts.tasks import evaluate_server_alerts

    evaluate_server_alerts.delay(server.id)
    server.connection_status = "unreachable"
    server.last_check_at = timezone.now()
    server.save(update_fields=["connection_status", "last_check_at", "updated_at"])
