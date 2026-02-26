import errno
from datetime import timedelta

import pytest
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from apps.servers.models import CollectionStatus, MetricSnapshot, Server
from apps.servers.tasks import _log_schedule_accuracy, _save_failed_snapshot, cleanup_old_data, collect_server_metrics


@pytest.mark.django_db
def test_cleanup_old_data_deletes_entries_older_than_30_days():
    server = Server.objects.create(
        name="cleanup-target",
        host="10.9.0.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
    )
    old_snapshot = MetricSnapshot.objects.create(
        server=server,
        collection_status=CollectionStatus.SUCCESS,
        error_message="",
    )
    fresh_snapshot = MetricSnapshot.objects.create(
        server=server,
        collection_status=CollectionStatus.SUCCESS,
        error_message="",
    )
    cutoff_old = timezone.now() - timedelta(days=31)
    cutoff_fresh = timezone.now() - timedelta(days=5)
    MetricSnapshot.objects.filter(id=old_snapshot.id).update(timestamp=cutoff_old)
    MetricSnapshot.objects.filter(id=fresh_snapshot.id).update(timestamp=cutoff_fresh)

    result = cleanup_old_data()
    assert result["metrics_deleted"] >= 1
    assert MetricSnapshot.objects.filter(id=old_snapshot.id).exists() is False
    assert MetricSnapshot.objects.filter(id=fresh_snapshot.id).exists() is True


@pytest.mark.django_db
def test_log_schedule_accuracy_emits_metric_line(monkeypatch):
    server = Server.objects.create(
        name="sched",
        host="10.9.0.2",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
        check_interval_minutes=5,
    )
    schedule, _ = IntervalSchedule.objects.get_or_create(every=5, period=IntervalSchedule.MINUTES)
    last_run = timezone.now() - timedelta(minutes=5, seconds=7)
    PeriodicTask.objects.create(
        name=f"collect_server_metrics_{server.id}",
        task="apps.servers.tasks.collect_server_metrics",
        interval=schedule,
        args=f"[{server.id}]",
        enabled=True,
        last_run_at=last_run,
    )
    server.last_check_at = timezone.now()
    server.save(update_fields=["last_check_at", "updated_at"])

    messages: list[str] = []

    def fake_info(message: str, *args):
        messages.append(message % args)

    monkeypatch.setattr("apps.servers.tasks.logger.info", fake_info)
    _log_schedule_accuracy(server)
    assert any("schedule_accuracy" in message for message in messages)


@pytest.mark.django_db
def test_save_failed_snapshot_handles_enospc(monkeypatch):
    server = Server.objects.create(
        name="enospc",
        host="10.9.0.3",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
    )

    def raise_enospc(*args, **kwargs):
        raise OSError(errno.ENOSPC, "No space left on device")

    notified = {"called": False}

    def mark_notified(*args, **kwargs):
        notified["called"] = True

    monkeypatch.setattr("apps.servers.tasks.MetricSnapshot.objects.create", raise_enospc)
    monkeypatch.setattr("apps.servers.tasks._notify_disk_full", mark_notified)

    _save_failed_snapshot(server, "err")
    assert notified["called"] is True


@pytest.mark.django_db
def test_collect_server_metrics_success_path(monkeypatch):
    server = Server.objects.create(
        name="ok",
        host="10.9.0.4",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
        monitoring_enabled=True,
    )

    class DummySsh:
        def __init__(self, _server):
            self.server = _server

        def connect(self):
            return None

        def disconnect(self):
            return None

    class DummyMetrics:
        @staticmethod
        def collect_metrics(_ssh):
            return {
                "load_1min": 0.1,
                "load_5min": 0.2,
                "load_15min": 0.3,
                "ram_total_bytes": 10,
                "ram_used_bytes": 5,
                "ram_free_bytes": 5,
                "ram_available_bytes": 6,
                "ram_cached_bytes": 1,
                "ram_buffers_bytes": 1,
                "ram_shared_bytes": 1,
                "ram_percent": 50.0,
                "ram_free_percent": 50.0,
                "ram_available_percent": 60.0,
                "swap_total_bytes": 10,
                "swap_used_bytes": 1,
                "swap_free_bytes": 9,
                "swap_cached_bytes": 0,
                "swap_percent": 10.0,
                "swap_free_percent": 90.0,
                "cpu_cores": 2,
                "uptime_seconds": 1000,
                "disk_metrics": [
                    {
                        "filesystem": "/dev/sda1",
                        "mount_point": "/",
                        "total_bytes": 100,
                        "used_bytes": 50,
                        "available_bytes": 50,
                        "percent": 50.0,
                    }
                ],
            }

    monkeypatch.setattr("apps.servers.tasks.SSHService", DummySsh)
    monkeypatch.setattr("apps.servers.tasks.MetricsService", DummyMetrics)
    monkeypatch.setattr("apps.alerts.tasks.evaluate_server_alerts.delay", lambda *args, **kwargs: None)
    monkeypatch.setattr("apps.servers.tasks._log_schedule_accuracy", lambda *args, **kwargs: None)

    collect_server_metrics(server.id)
    snap = MetricSnapshot.objects.filter(server=server, collection_status=CollectionStatus.SUCCESS).first()
    assert snap is not None
    server.refresh_from_db()
    assert server.connection_status == "online"
    assert snap.disk_metrics.count() == 1


@pytest.mark.django_db
def test_collect_server_metrics_all_retries_fail(monkeypatch):
    server = Server.objects.create(
        name="fail",
        host="10.9.0.5",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
        monitoring_enabled=True,
    )

    class DummySsh:
        def __init__(self, _server):
            return None

        def connect(self):
            raise RuntimeError("ssh down")

        def disconnect(self):
            return None

    monkeypatch.setattr("apps.servers.tasks.SSHService", DummySsh)
    monkeypatch.setattr("apps.servers.tasks.PingService.ping", lambda host: False)
    monkeypatch.setattr("apps.alerts.tasks.evaluate_server_alerts.delay", lambda *args, **kwargs: None)

    collect_server_metrics(server.id)
    server.refresh_from_db()
    assert server.connection_status == "unreachable"
    snap = MetricSnapshot.objects.filter(server=server, collection_status=CollectionStatus.FAILED).first()
    assert snap is not None
    assert "SSH failed after 3 retries" in snap.error_message
