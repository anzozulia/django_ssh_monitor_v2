from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.alerts.models import AlertEvent, AlertRule
from apps.servers.models import DiskMetric, MetricSnapshot, Server


@pytest.mark.django_db
def test_metrics_endpoint_returns_range_scoped_history_and_alert_periods(authenticated_client):
    server = Server.objects.create(
        name="chart-server",
        host="10.0.0.41",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
    )
    snapshot = MetricSnapshot.objects.create(
        server=server,
        load_1min=1.2,
        ram_percent=67.5,
        swap_percent=8.1,
    )
    DiskMetric.objects.create(
        snapshot=snapshot,
        mount_point="/",
        filesystem="ext4",
        total_bytes=1000,
        used_bytes=900,
        available_bytes=100,
        percent=90.0,
    )
    MetricSnapshot.objects.filter(id=snapshot.id).update(timestamp=timezone.now() - timedelta(hours=2))

    rule = AlertRule.objects.create(
        server=server,
        name="High RAM",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=60.0,
        enabled=True,
        current_state="normal",
    )
    triggered = AlertEvent.objects.create(
        alert_rule=rule,
        server=server,
        event_type="triggered",
        metric_value=70.0,
        threshold_value=60.0,
    )
    dismissed = AlertEvent.objects.create(
        alert_rule=rule,
        server=server,
        event_type="dismissed",
        metric_value=50.0,
        threshold_value=60.0,
    )
    now = timezone.now()
    AlertEvent.objects.filter(id=triggered.id).update(created_at=now - timedelta(minutes=90))
    AlertEvent.objects.filter(id=dismissed.id).update(created_at=now - timedelta(minutes=30))

    response = authenticated_client.get(reverse("servers:metrics", kwargs={"pk": server.id}), data={"range": "6h"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["range"] == "6h"
    assert payload["latest"]["load_1min"] == 1.2
    assert payload["history"]["disk_percent"] == [90.0]
    assert payload["alert_periods"]
