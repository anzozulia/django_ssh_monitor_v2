import pytest
from django.urls import reverse

from apps.alerts.models import AlertRule
from apps.core.encryption import encrypt_credential
from apps.servers.models import Server


@pytest.mark.django_db
def test_default_alerts_page_ensures_connectivity_template(authenticated_client):
    response = authenticated_client.get(reverse("alerts:defaults"))
    assert response.status_code == 200
    assert AlertRule.objects.filter(
        is_default_template=True,
        server__isnull=True,
        metric_type="custom",
        metric_param="ssh_connectivity",
    ).exists()


@pytest.mark.django_db
def test_default_connectivity_template_is_not_deletable_and_settings_are_editable(authenticated_client):
    authenticated_client.get(reverse("alerts:defaults"))
    template = AlertRule.objects.get(
        is_default_template=True,
        server__isnull=True,
        metric_type="custom",
        metric_param="ssh_connectivity",
    )

    update_response = authenticated_client.post(
        reverse("alerts:defaults-update", kwargs={"pk": template.id}),
        data={
            "name": "Renamed by user",
            "severity": "warning",
            "metric_type": "custom",
            "metric_param": "custom_value",
            "condition": "gt",
            "threshold_value": 5,
            "threshold_value_2": "",
            "use_dismissal_threshold": "",
            "dismissal_threshold_value": "",
            "dismissal_threshold_value_2": "",
            "threshold_unit": "B",
            "reminder_interval_minutes": 30,
            "notify_on_dismissal": "on",
        },
    )
    assert update_response.status_code == 302

    template.refresh_from_db()
    assert template.name == "SSH Connectivity"
    assert template.severity == "critical"
    assert template.metric_type == "custom"
    assert template.metric_param == "ssh_connectivity"
    assert template.condition == "eq"
    assert template.threshold_value == 1
    assert template.reminder_interval_minutes == 30
    assert template.notify_on_dismissal is True

    delete_response = authenticated_client.post(reverse("alerts:defaults-delete", kwargs={"pk": template.id}))
    assert delete_response.status_code == 302
    assert AlertRule.objects.filter(id=template.id).exists()


@pytest.mark.django_db
def test_server_connectivity_rule_is_not_deletable(authenticated_client):
    server = Server.objects.create(
        name="ConnSrv",
        host="10.20.0.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    rule = AlertRule.objects.create(
        server=server,
        name="SSH Connectivity",
        severity="critical",
        metric_type="custom",
        metric_param="ssh_connectivity",
        condition="eq",
        threshold_value=1,
        enabled=True,
    )

    response = authenticated_client.post(reverse("alerts:delete", kwargs={"pk": rule.id}))
    assert response.status_code == 302
    assert AlertRule.objects.filter(id=rule.id).exists()
