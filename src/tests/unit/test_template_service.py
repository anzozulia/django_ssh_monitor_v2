import pytest

from apps.alerts.models import AlertRule
from apps.alerts.services.template_service import clone_default_alerts_to_server
from apps.core.encryption import encrypt_credential
from apps.servers.models import Server


@pytest.mark.django_db
def test_clone_default_alerts_to_server_creates_server_rules_even_if_template_disabled():
    server = Server.objects.create(
        name="SrvTpl",
        host="10.7.0.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    template = AlertRule.objects.create(
        server=None,
        is_default_template=True,
        name="RAM high default",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=85,
        reminder_interval_minutes=15,
        enabled=False,
    )

    created = clone_default_alerts_to_server(server)
    assert created == 2
    rule = AlertRule.objects.filter(server=server, name=template.name, is_default_template=False).first()
    assert rule is not None
    assert rule.name == template.name
    assert rule.threshold_value == template.threshold_value
    assert AlertRule.objects.filter(
        server=server,
        is_default_template=False,
        metric_type="custom",
        metric_param="ssh_connectivity",
    ).exists()


@pytest.mark.django_db
def test_clone_default_alerts_to_server_updates_existing_server_connectivity_rule_instead_of_duplicate():
    server = Server.objects.create(
        name="SrvTplConnectivity",
        host="10.7.0.2",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    existing = AlertRule.objects.create(
        server=server,
        is_default_template=False,
        name="SSH Connectivity",
        severity="critical",
        metric_type="custom",
        metric_param="ssh_connectivity",
        condition="eq",
        threshold_value=1,
        reminder_interval_minutes=0,
        enabled=True,
    )
    AlertRule.objects.create(
        server=None,
        is_default_template=True,
        name="RAM high default",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=85,
        reminder_interval_minutes=15,
        enabled=True,
    )
    connectivity_template = AlertRule.objects.create(
        server=None,
        is_default_template=True,
        name="SSH Connectivity",
        severity="critical",
        metric_type="custom",
        metric_param="ssh_connectivity",
        condition="eq",
        threshold_value=1,
        reminder_interval_minutes=120,
        notify_on_dismissal=True,
        enabled=True,
    )

    created = clone_default_alerts_to_server(server)
    assert created == 1

    connectivity_rules = AlertRule.objects.filter(
        server=server,
        is_default_template=False,
        metric_type="custom",
        metric_param="ssh_connectivity",
    )
    assert connectivity_rules.count() == 1
    existing.refresh_from_db()
    assert existing.id == connectivity_rules.first().id
    assert existing.reminder_interval_minutes == connectivity_template.reminder_interval_minutes
    assert existing.notify_on_dismissal is True
