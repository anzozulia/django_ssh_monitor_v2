from datetime import timedelta

import pytest
from django.utils import timezone

from apps.alerts.models import AlertRule
from apps.alerts.services.evaluation_service import AlertEvaluationService
from apps.core.encryption import encrypt_credential
from apps.servers.models import DiskMetric, MetricSnapshot, Server


@pytest.mark.django_db
def test_resolve_metric_handles_disk_variants_and_custom_connectivity():
    server = Server.objects.create(
        name="SrvDisk",
        host="10.30.0.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    snapshot = MetricSnapshot.objects.create(
        server=server,
        collection_status="success",
        uptime_seconds=1200,
    )
    DiskMetric.objects.create(
        snapshot=snapshot,
        mount_point="/",
        filesystem="ext4",
        total_bytes=1000,
        used_bytes=800,
        available_bytes=200,
        percent=80.0,
    )
    DiskMetric.objects.create(
        snapshot=snapshot,
        mount_point="/data",
        filesystem="ext4",
        total_bytes=1000,
        used_bytes=500,
        available_bytes=500,
        percent=50.0,
    )
    svc = AlertEvaluationService()
    rule_used = AlertRule(
        server=server,
        name="DiskUsed",
        severity="warning",
        metric_type="disk_used",
        condition="gt",
        threshold_value=1,
    )
    rule_free_pct = AlertRule(
        server=server,
        name="DiskFreePct",
        severity="warning",
        metric_type="disk_free_pct",
        condition="lt",
        threshold_value=30,
    )
    rule_mount = AlertRule(
        server=server,
        name="DiskByMount",
        severity="warning",
        metric_type="disk_percent",
        metric_param="/data",
        condition="gt",
        threshold_value=70,
    )
    rule_custom = AlertRule(
        server=server,
        name="SSH",
        severity="critical",
        metric_type="custom",
        metric_param="ssh_connectivity",
        condition="eq",
        threshold_value=1,
    )
    assert svc._resolve_metric(rule_used, snapshot) == 800.0
    assert svc._resolve_metric(rule_free_pct, snapshot) == 50.0
    assert svc._resolve_metric(rule_mount, snapshot) == 50.0
    assert svc._resolve_metric(rule_custom, snapshot) == 0.0


def test_condition_and_dismissal_match_operators():
    rule = AlertRule(condition="eq", threshold_value=10, dismissal_threshold_value=2)
    assert AlertEvaluationService._condition_matches(rule, 10) is True
    assert AlertEvaluationService._dismissal_matches(rule, 11.0) is False
    assert AlertEvaluationService._dismissal_matches(rule, 12.5) is True

    rule.condition = "out_of_range"
    rule.threshold_value = 10
    rule.threshold_value_2 = 20
    rule.dismissal_threshold_value = 12
    rule.dismissal_threshold_value_2 = 18
    assert AlertEvaluationService._condition_matches(rule, 5) is True
    assert AlertEvaluationService._condition_matches(rule, 15) is False
    assert AlertEvaluationService._dismissal_matches(rule, 11) is False
    assert AlertEvaluationService._dismissal_matches(rule, 13) is True


@pytest.mark.parametrize(
    ("condition", "value", "expected"),
    [
        ("gt", 11, True),
        ("lt", 9, True),
        ("gte", 10, True),
        ("lte", 10, True),
    ],
)
def test_condition_matches_core_operators(condition, value, expected):
    rule = AlertRule(condition=condition, threshold_value=10)
    assert AlertEvaluationService._condition_matches(rule, value) is expected


def test_dismissal_matches_core_operators_without_custom_thresholds():
    rule = AlertRule(condition="gt", threshold_value=10, metric_type="ram_percent")
    assert AlertEvaluationService._dismissal_matches(rule, 10) is True
    rule.condition = "gte"
    assert AlertEvaluationService._dismissal_matches(rule, 9.9) is True
    rule.condition = "lt"
    assert AlertEvaluationService._dismissal_matches(rule, 10) is True
    rule.condition = "lte"
    assert AlertEvaluationService._dismissal_matches(rule, 10.1) is True


@pytest.mark.django_db
def test_triggered_rule_emits_reminder_when_interval_elapsed(monkeypatch):
    server = Server.objects.create(
        name="SrvReminder",
        host="10.30.0.2",
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
        reminder_interval_minutes=1,
        current_state="triggered",
        triggered_at=timezone.now(),
        last_reminder_at=timezone.now() - timedelta(minutes=2),
    )
    MetricSnapshot.objects.create(server=server, collection_status="success", ram_percent=90)

    emitted = {"count": 0}

    def fake_emit(*args, **kwargs):
        emitted["count"] += 1

    monkeypatch.setattr("apps.alerts.services.evaluation_service.AlertEvaluationService._emit_event", fake_emit)
    AlertEvaluationService().evaluate_server_alerts(server)
    rule.refresh_from_db()
    assert emitted["count"] == 1
    assert rule.last_reminder_at is not None


@pytest.mark.django_db
def test_evaluate_server_alerts_skips_when_no_snapshot():
    server = Server.objects.create(
        name="SrvNoSnap",
        host="10.30.0.10",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    AlertEvaluationService().evaluate_server_alerts(server)


@pytest.mark.django_db
def test_warning_rule_is_suppressed_when_critical_for_same_metric_is_active():
    server = Server.objects.create(
        name="SrvSeverity",
        host="10.30.0.12",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    warning_rule = AlertRule.objects.create(
        server=server,
        name="RAM warning",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=70,
        reminder_interval_minutes=1,
    )
    critical_rule = AlertRule.objects.create(
        server=server,
        name="RAM critical",
        severity="critical",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=90,
        reminder_interval_minutes=1,
    )
    MetricSnapshot.objects.create(server=server, collection_status="success", ram_percent=95)

    AlertEvaluationService().evaluate_server_alerts(server)
    warning_rule.refresh_from_db()
    critical_rule.refresh_from_db()
    assert critical_rule.current_state == "triggered"
    assert warning_rule.current_state == "normal"


@pytest.mark.django_db
def test_warning_resumes_after_critical_dismissal_for_same_metric():
    server = Server.objects.create(
        name="SrvSeverityResume",
        host="10.30.0.13",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    warning_rule = AlertRule.objects.create(
        server=server,
        name="RAM warning",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=70,
    )
    critical_rule = AlertRule.objects.create(
        server=server,
        name="RAM critical",
        severity="critical",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=90,
    )
    svc = AlertEvaluationService()

    MetricSnapshot.objects.create(server=server, collection_status="success", ram_percent=95)
    svc.evaluate_server_alerts(server)
    warning_rule.refresh_from_db()
    critical_rule.refresh_from_db()
    assert critical_rule.current_state == "triggered"
    assert warning_rule.current_state == "normal"

    MetricSnapshot.objects.create(server=server, collection_status="success", ram_percent=80)
    svc.evaluate_server_alerts(server)
    warning_rule.refresh_from_db()
    critical_rule.refresh_from_db()
    assert critical_rule.current_state == "normal"
    assert warning_rule.current_state == "triggered"


@pytest.mark.django_db
def test_resolve_metric_all_ram_swap_load_paths():
    server = Server.objects.create(
        name="SrvAll",
        host="10.30.0.11",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    snapshot = MetricSnapshot.objects.create(
        server=server,
        collection_status="success",
        load_1min=1.0,
        load_5min=2.0,
        load_15min=3.0,
        ram_percent=60.0,
        ram_used_bytes=600,
        ram_free_bytes=400,
        ram_available_bytes=500,
        ram_cached_bytes=120,
        ram_free_percent=40.0,
        ram_available_percent=50.0,
        swap_percent=10.0,
        swap_used_bytes=100,
        swap_free_bytes=900,
        swap_free_percent=90.0,
        uptime_seconds=3600,
    )
    svc = AlertEvaluationService()
    metrics = {
        "cpu_load_1": 1.0,
        "cpu_load_5": 2.0,
        "cpu_load_15": 3.0,
        "ram_percent": 60.0,
        "ram_used": 600.0,
        "ram_free": 400.0,
        "ram_available": 500.0,
        "ram_cached": 120.0,
        "ram_free_pct": 40.0,
        "ram_available_pct": 50.0,
        "swap_percent": 10.0,
        "swap_used": 100.0,
        "swap_free": 900.0,
        "swap_free_pct": 90.0,
        "uptime": 3600.0,
    }
    for metric_type, expected in metrics.items():
        rule = AlertRule(
            server=server,
            name=f"rule-{metric_type}",
            severity="warning",
            metric_type=metric_type,
            condition="gt",
            threshold_value=0,
        )
        assert svc._resolve_metric(rule, snapshot) == expected
