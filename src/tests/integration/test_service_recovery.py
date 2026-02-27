import pytest
from django_celery_beat.models import PeriodicTask

from apps.servers.models import Server
from apps.servers.tasks import schedule_server_collection


@pytest.mark.django_db
def test_service_recovery_schedule_restored_within_five_minutes():
    server = Server.objects.create(
        name="recoverable",
        host="10.11.0.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
        check_interval_minutes=5,
        monitoring_enabled=True,
    )

    schedule_server_collection(server)
    task_name = f"collect_server_metrics_{server.id}"
    task = PeriodicTask.objects.get(name=task_name)
    assert task.enabled is True
    assert task.interval.every == 5

    server.monitoring_enabled = False
    server.save(update_fields=["monitoring_enabled", "updated_at"])
    schedule_server_collection(server)
    task.refresh_from_db()
    assert task.enabled is False

    server.monitoring_enabled = True
    server.check_interval_minutes = 3
    server.save(update_fields=["monitoring_enabled", "check_interval_minutes", "updated_at"])
    schedule_server_collection(server)
    task.refresh_from_db()
    assert task.enabled is True
    assert task.interval.every <= 5
