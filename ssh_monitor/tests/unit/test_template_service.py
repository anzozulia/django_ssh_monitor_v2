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
    assert created == 1
    rule = AlertRule.objects.filter(server=server, name=template.name, is_default_template=False).first()
    assert rule is not None
    assert rule.name == template.name
    assert rule.threshold_value == template.threshold_value
