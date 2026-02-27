import pytest

from apps.alerts.models import AlertRule


@pytest.mark.django_db
def test_default_alert_template_model_create():
    template = AlertRule.objects.create(
        server=None,
        is_default_template=True,
        name="Disk free low",
        severity="critical",
        metric_type="disk_free_pct",
        metric_param="/",
        condition="lt",
        threshold_value=10,
        reminder_interval_minutes=30,
        notify_on_dismissal=True,
        enabled=True,
    )
    assert template.id is not None
    assert str(template) == "Disk free low"
