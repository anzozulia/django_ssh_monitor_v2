import pytest
from django.urls import reverse

from apps.alerts.models import AlertRule
from apps.core.encryption import encrypt_credential
from apps.servers.models import Server


@pytest.mark.django_db
def test_alert_crud_flow(authenticated_client):
    server = Server.objects.create(
        name="AlertSrv",
        host="10.3.0.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )

    # Create
    create_url = reverse("alerts:create", kwargs={"server_pk": server.id})
    resp = authenticated_client.post(
        create_url,
        data={
            "name": "RAM > 80",
            "severity": "warning",
            "metric_type": "ram_percent",
            "metric_param": "",
            "condition": "gt",
            "threshold_value": 80,
            "threshold_value_2": "",
            "use_dismissal_threshold": "on",
            "dismissal_threshold_value": 70,
            "dismissal_threshold_value_2": "",
            "reminder_interval_minutes": 0,
            "notify_on_dismissal": "on",
            "enabled": "on",
        },
    )
    assert resp.status_code == 302
    rule = AlertRule.objects.get(server=server, name="RAM > 80")

    # List (embedded in server detail page)
    list_url = reverse("servers:detail", kwargs={"pk": server.id})
    resp = authenticated_client.get(list_url)
    assert resp.status_code == 200
    assert b"RAM" in resp.content

    # Update
    update_url = reverse("alerts:update", kwargs={"pk": rule.id})
    resp = authenticated_client.post(
        update_url,
        data={
            "name": "RAM > 85",
            "severity": "critical",
            "metric_type": "ram_percent",
            "metric_param": "",
            "condition": "gt",
            "threshold_value": 85,
            "threshold_value_2": "",
            "use_dismissal_threshold": "on",
            "dismissal_threshold_value": 75,
            "dismissal_threshold_value_2": "",
            "reminder_interval_minutes": 15,
            "enabled": "on",
        },
    )
    assert resp.status_code == 302
    rule.refresh_from_db()
    assert rule.name == "RAM > 85"
    assert rule.severity == "critical"

    # Toggle
    toggle_url = reverse("alerts:toggle", kwargs={"pk": rule.id})
    resp = authenticated_client.post(toggle_url)
    assert resp.status_code == 302
    rule.refresh_from_db()
    assert rule.enabled is False

    # Delete
    delete_url = reverse("alerts:delete", kwargs={"pk": rule.id})
    resp = authenticated_client.post(delete_url)
    assert resp.status_code == 302
    assert AlertRule.objects.filter(id=rule.id).exists() is False
