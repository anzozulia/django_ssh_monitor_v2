import pytest
from django.urls import reverse

from apps.alerts.models import AlertRule
from apps.servers.models import MetricSnapshot, Server


@pytest.mark.django_db
def test_dashboard_view_builds_health_summary_counts(authenticated_client):
    server_ok = Server.objects.create(
        name="ok",
        host="10.0.0.51",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
        connection_status="online",
    )
    server_warn = Server.objects.create(
        name="warn",
        host="10.0.0.52",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
        connection_status="online",
    )
    server_critical = Server.objects.create(
        name="crit",
        host="10.0.0.53",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
        connection_status="unreachable",
    )
    MetricSnapshot.objects.create(server=server_ok, load_1min=0.2, ram_percent=30.0, swap_percent=0.0)
    MetricSnapshot.objects.create(server=server_warn, load_1min=0.5, ram_percent=60.0, swap_percent=1.0)
    MetricSnapshot.objects.create(server=server_critical, load_1min=2.5, ram_percent=90.0, swap_percent=9.0)
    AlertRule.objects.create(
        server=server_warn,
        name="Warn",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=50.0,
        enabled=True,
        current_state="triggered",
    )
    AlertRule.objects.create(
        server=server_critical,
        name="Critical",
        severity="critical",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=80.0,
        enabled=True,
        current_state="triggered",
    )

    response = authenticated_client.get(reverse("servers:dashboard"))
    assert response.status_code == 200
    assert response.context["total_servers"] == 3
    assert response.context["healthy_servers"] == 1
    assert response.context["warning_servers"] == 1
    assert response.context["critical_servers"] == 1
