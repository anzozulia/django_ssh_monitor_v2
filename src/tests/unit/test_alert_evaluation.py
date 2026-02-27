import pytest

from apps.alerts.models import AlertEvent, AlertRule
from apps.alerts.services.evaluation_service import AlertEvaluationService
from apps.core.encryption import encrypt_credential
from apps.servers.models import MetricSnapshot, Server


@pytest.mark.django_db
def test_evaluation_triggers_event():
    server = Server.objects.create(
        name="Srv",
        host="10.2.0.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    MetricSnapshot.objects.create(server=server, collection_status="success", ram_percent=90)
    rule = AlertRule.objects.create(
        server=server,
        name="RAM > 80",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=80,
    )

    AlertEvaluationService().evaluate_server_alerts(server)

    rule.refresh_from_db()
    assert rule.current_state == "triggered"
    assert AlertEvent.objects.filter(alert_rule=rule, event_type="triggered").count() == 1


@pytest.mark.django_db
def test_evaluation_dismisses_after_recovery_threshold():
    server = Server.objects.create(
        name="Srv2",
        host="10.2.0.2",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    rule = AlertRule.objects.create(
        server=server,
        name="RAM > 80",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=80,
        notify_on_dismissal=True,
        dismissal_threshold_value=75,
    )
    # Trigger
    MetricSnapshot.objects.create(server=server, collection_status="success", ram_percent=95)
    svc = AlertEvaluationService()
    svc.evaluate_server_alerts(server)
    rule.refresh_from_db()
    assert rule.current_state == "triggered"

    # Not matching trigger condition, but not yet recovered enough for dismissal.
    MetricSnapshot.objects.create(server=server, collection_status="success", ram_percent=79)
    svc.evaluate_server_alerts(server)
    rule.refresh_from_db()
    assert rule.current_state == "triggered"

    # Recovered below dismissal threshold, should dismiss now.
    MetricSnapshot.objects.create(server=server, collection_status="success", ram_percent=70)
    svc.evaluate_server_alerts(server)
    rule.refresh_from_db()
    assert rule.current_state == "normal"
    assert AlertEvent.objects.filter(alert_rule=rule, event_type="dismissed").exists()


@pytest.mark.django_db
def test_evaluation_supports_uptime_metric():
    server = Server.objects.create(
        name="SrvUptime",
        host="10.2.0.3",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    MetricSnapshot.objects.create(server=server, collection_status="success", uptime_seconds=10 * 86400)
    rule = AlertRule.objects.create(
        server=server,
        name="Uptime > 7 days",
        severity="warning",
        metric_type="uptime",
        condition="gt",
        threshold_value=7 * 86400,
    )

    AlertEvaluationService().evaluate_server_alerts(server)

    rule.refresh_from_db()
    assert rule.current_state == "triggered"


@pytest.mark.django_db
def test_evaluation_in_range_dismisses_only_after_wider_recovery_range():
    server = Server.objects.create(
        name="SrvRange",
        host="10.2.0.4",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    rule = AlertRule.objects.create(
        server=server,
        name="In range alert",
        severity="warning",
        metric_type="ram_percent",
        condition="in_range",
        threshold_value=40,
        threshold_value_2=60,
        dismissal_threshold_value=35,
        dismissal_threshold_value_2=65,
    )
    svc = AlertEvaluationService()

    MetricSnapshot.objects.create(server=server, collection_status="success", ram_percent=50)
    svc.evaluate_server_alerts(server)
    rule.refresh_from_db()
    assert rule.current_state == "triggered"

    MetricSnapshot.objects.create(server=server, collection_status="success", ram_percent=62)
    svc.evaluate_server_alerts(server)
    rule.refresh_from_db()
    assert rule.current_state == "triggered"

    MetricSnapshot.objects.create(server=server, collection_status="success", ram_percent=66)
    svc.evaluate_server_alerts(server)
    rule.refresh_from_db()
    assert rule.current_state == "normal"
