import pytest

from apps.alerts.forms import AlertRuleForm
from apps.alerts.models import AlertRule
from apps.core.encryption import encrypt_credential
from apps.servers.models import Server


@pytest.mark.django_db
def test_byte_metric_threshold_is_converted_to_bytes():
    form = AlertRuleForm(
        data={
            "name": "Disk free too low",
            "severity": "critical",
            "metric_type": "disk_free",
            "metric_param": "/",
            "condition": "lt",
            "threshold_value": "5",
            "threshold_value_2": "",
            "threshold_unit": "GB",
            "use_dismissal_threshold": "on",
            "reminder_interval_minutes": "0",
            "notify_on_dismissal": "",
            "dismissal_threshold_value": "7",
            "dismissal_threshold_value_2": "",
            "enabled": "on",
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["threshold_value"] == 5 * 1024**3
    assert form.cleaned_data["dismissal_threshold_value"] == 7 * 1024**3


@pytest.mark.django_db
def test_edit_form_prefills_human_unit_for_byte_metric():
    server = Server.objects.create(
        name="srv",
        host="127.0.0.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pw"),
    )
    rule = AlertRule.objects.create(
        server=server,
        name="RAM used high",
        severity="warning",
        metric_type="ram_used",
        condition="gt",
        threshold_value=2 * 1024**3,
        dismissal_threshold_value=1536 * 1024**2,
    )
    form = AlertRuleForm(instance=rule)
    assert form.initial["threshold_unit"] == "GB"
    assert form.initial["threshold_value"] == 2
    assert form.initial["use_dismissal_threshold"] is True


@pytest.mark.django_db
def test_uptime_metric_threshold_is_converted_to_seconds():
    form = AlertRuleForm(
        data={
            "name": "Uptime high",
            "severity": "warning",
            "metric_type": "uptime",
            "metric_param": "",
            "condition": "gt",
            "threshold_value": "2",
            "threshold_value_2": "",
            "threshold_unit": "d",
            "use_dismissal_threshold": "on",
            "reminder_interval_minutes": "0",
            "notify_on_dismissal": "",
            "dismissal_threshold_value": "1",
            "dismissal_threshold_value_2": "",
            "enabled": "on",
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["threshold_value"] == 2 * 86400
    assert form.cleaned_data["dismissal_threshold_value"] == 86400


@pytest.mark.django_db
def test_edit_form_prefills_human_unit_for_uptime_metric():
    server = Server.objects.create(
        name="srv-up",
        host="127.0.0.2",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pw"),
    )
    rule = AlertRule.objects.create(
        server=server,
        name="Uptime old",
        severity="warning",
        metric_type="uptime",
        condition="gt",
        threshold_value=14 * 86400,
    )
    form = AlertRuleForm(instance=rule)
    assert form.initial["threshold_unit"] == "w"
    assert form.initial["threshold_value"] == 2


@pytest.mark.django_db
def test_form_allows_no_dismissal_threshold_when_toggle_is_off():
    form = AlertRuleForm(
        data={
            "name": "RAM high without hysteresis",
            "severity": "warning",
            "metric_type": "ram_percent",
            "metric_param": "",
            "condition": "gt",
            "threshold_value": "85",
            "threshold_value_2": "",
            "threshold_unit": "GB",
            "reminder_interval_minutes": "0",
            "notify_on_dismissal": "",
            "dismissal_threshold_value": "",
            "dismissal_threshold_value_2": "",
            "enabled": "on",
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["dismissal_threshold_value"] is None
    assert form.cleaned_data["dismissal_threshold_value_2"] is None
