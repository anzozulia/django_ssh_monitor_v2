from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.alerts.models import AlertEvent, AlertRule
from apps.servers.models import Server


def _create_rule(server: Server, name: str, metric_type: str = "ram_percent") -> AlertRule:
    return AlertRule.objects.create(
        server=server,
        name=name,
        severity="warning",
        metric_type=metric_type,
        condition="gt",
        threshold_value=80.0,
        enabled=True,
        current_state="normal",
    )


@pytest.mark.django_db
def test_alert_history_filters_by_event_and_metric(authenticated_client):
    server = Server.objects.create(
        name="history-server",
        host="10.0.1.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
    )
    rule_ram = _create_rule(server, "High RAM", metric_type="ram_percent")
    rule_swap = _create_rule(server, "High Swap", metric_type="swap_percent")
    AlertEvent.objects.create(
        alert_rule=rule_ram,
        server=server,
        event_type="triggered",
        metric_value=85.0,
        threshold_value=80.0,
    )
    AlertEvent.objects.create(
        alert_rule=rule_swap,
        server=server,
        event_type="dismissed",
        metric_value=60.0,
        threshold_value=70.0,
    )

    response = authenticated_client.get(
        reverse("alerts:history"),
        data={"event_type": "triggered", "metric_type": "ram_percent"},
    )
    assert response.status_code == 200
    events = list(response.context["events"])
    assert len(events) == 1
    assert events[0].event_type == "triggered"
    assert events[0].alert_rule.metric_type == "ram_percent"


@pytest.mark.django_db
def test_alert_history_paginates_results(authenticated_client):
    server = Server.objects.create(
        name="pager-server",
        host="10.0.1.2",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
    )
    rule = _create_rule(server, "High CPU", metric_type="cpu_load_1")
    for i in range(30):
        event = AlertEvent.objects.create(
            alert_rule=rule,
            server=server,
            event_type="triggered",
            metric_value=1.0 + i,
            threshold_value=1.0,
        )
        AlertEvent.objects.filter(id=event.id).update(created_at=timezone.now() - timedelta(minutes=i))

    response = authenticated_client.get(reverse("alerts:history"))
    assert response.status_code == 200
    page_obj = response.context["page_obj"]
    assert page_obj.paginator.per_page == 25
    assert page_obj.paginator.count == 30
    assert page_obj.has_next() is True
