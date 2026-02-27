import pytest

from apps.alerts.models import AlertEvent, AlertRule
from apps.alerts.services.evaluation_service import AlertEvaluationService
from apps.core.encryption import encrypt_credential
from apps.servers.models import MetricSnapshot, Server


@pytest.mark.django_db
def test_alert_event_tracks_notification_delivery(monkeypatch):
    server = Server.objects.create(
        name="SrvFlow",
        host="10.6.0.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    AlertRule.objects.create(
        server=server,
        name="RAM > 80",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=80,
    )
    MetricSnapshot.objects.create(server=server, collection_status="success", ram_percent=90)

    monkeypatch.setattr(
        "apps.alerts.services.notification_service.NotificationDispatcher.send_event",
        lambda self, event: (True, None),  # noqa: ARG005
    )

    AlertEvaluationService().evaluate_server_alerts(server)

    event = AlertEvent.objects.filter(server=server, event_type="triggered").first()
    assert event is not None
    assert event.notification_sent is True
    assert event.notification_error == ""
