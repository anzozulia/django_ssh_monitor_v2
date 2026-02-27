from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.alerts.models import AlertEvent, AlertRule
from apps.servers.models import Server


@pytest.mark.django_db
def test_global_alert_history_filters_by_server(authenticated_client):
    server_a = Server.objects.create(
        name="srv-a",
        host="10.0.2.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
    )
    server_b = Server.objects.create(
        name="srv-b",
        host="10.0.2.2",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
    )
    rule_a = AlertRule.objects.create(
        server=server_a,
        name="A-Rule",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=80.0,
        enabled=True,
        current_state="normal",
    )
    rule_b = AlertRule.objects.create(
        server=server_b,
        name="B-Rule",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=80.0,
        enabled=True,
        current_state="normal",
    )
    AlertEvent.objects.create(
        alert_rule=rule_a,
        server=server_a,
        event_type="triggered",
        metric_value=90.0,
        threshold_value=80.0,
    )
    AlertEvent.objects.create(
        alert_rule=rule_b,
        server=server_b,
        event_type="triggered",
        metric_value=91.0,
        threshold_value=80.0,
    )

    response = authenticated_client.get(reverse("alerts:history"), data={"server": server_a.id})
    assert response.status_code == 200
    events = list(response.context["events"])
    assert len(events) == 1
    assert events[0].server_id == server_a.id


@pytest.mark.django_db
def test_server_alert_history_filters_by_date_range(authenticated_client):
    server = Server.objects.create(
        name="srv-date",
        host="10.0.2.3",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
    )
    rule = AlertRule.objects.create(
        server=server,
        name="Date Rule",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=80.0,
        enabled=True,
        current_state="normal",
    )
    old_event = AlertEvent.objects.create(
        alert_rule=rule,
        server=server,
        event_type="triggered",
        metric_value=81.0,
        threshold_value=80.0,
    )
    recent_event = AlertEvent.objects.create(
        alert_rule=rule,
        server=server,
        event_type="dismissed",
        metric_value=60.0,
        threshold_value=80.0,
    )
    now = timezone.now()
    AlertEvent.objects.filter(id=old_event.id).update(created_at=now - timedelta(days=4))
    AlertEvent.objects.filter(id=recent_event.id).update(created_at=now - timedelta(hours=2))

    response = authenticated_client.get(
        reverse("alerts:server-history", kwargs={"server_pk": server.id}),
        data={"date_from": (now - timedelta(days=1)).date().isoformat()},
    )
    assert response.status_code == 200
    events = list(response.context["events"])
    assert len(events) == 1
    assert events[0].event_type == "dismissed"
