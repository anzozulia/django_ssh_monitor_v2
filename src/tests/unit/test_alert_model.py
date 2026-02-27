import pytest

from apps.alerts.models import AlertRule
from apps.core.encryption import encrypt_credential
from apps.servers.models import Server


@pytest.mark.django_db
def test_alert_rule_str():
    server = Server.objects.create(
        name="S1",
        host="10.1.1.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    rule = AlertRule.objects.create(
        server=server,
        name="RAM high",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=80,
    )
    assert "RAM high" in str(rule)


@pytest.mark.django_db
def test_alert_rule_defaults():
    server = Server.objects.create(
        name="S2",
        host="10.1.1.2",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    rule = AlertRule.objects.create(
        server=server,
        name="CPU high",
        severity="critical",
        metric_type="cpu_load_1",
        condition="gt",
        threshold_value=2,
    )
    assert rule.enabled is True
    assert rule.current_state == "normal"
