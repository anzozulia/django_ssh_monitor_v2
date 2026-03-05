from apps.alerts.models import AlertRule, AlertState
from apps.servers.models import Server


def is_ssh_connectivity_rule(rule: AlertRule) -> bool:
    return rule.metric_type == "custom" and rule.metric_param == "ssh_connectivity"


def ensure_default_connectivity_template() -> AlertRule:
    template, _ = AlertRule.objects.get_or_create(
        server=None,
        is_default_template=True,
        metric_type="custom",
        metric_param="ssh_connectivity",
        defaults={
            "name": "SSH Connectivity",
            "severity": "critical",
            "condition": "eq",
            "threshold_value": 1,
            "enabled": True,
            "current_state": AlertState.NORMAL,
        },
    )
    return template


def clone_default_alerts_to_server(server: Server) -> int:
    ensure_default_connectivity_template()
    templates = AlertRule.objects.filter(is_default_template=True, server__isnull=True)
    created = 0
    for template in templates:
        if is_ssh_connectivity_rule(template):
            existing_connectivity = AlertRule.objects.filter(
                server=server,
                metric_type=template.metric_type,
                metric_param=template.metric_param,
            ).first()
            if existing_connectivity:
                existing_connectivity.name = "SSH Connectivity"
                existing_connectivity.severity = "critical"
                existing_connectivity.condition = "eq"
                existing_connectivity.threshold_value = 1
                existing_connectivity.threshold_value_2 = None
                existing_connectivity.reminder_interval_minutes = template.reminder_interval_minutes
                existing_connectivity.notify_on_dismissal = template.notify_on_dismissal
                existing_connectivity.dismissal_threshold_value = None
                existing_connectivity.dismissal_threshold_value_2 = None
                existing_connectivity.enabled = True
                existing_connectivity.current_state = AlertState.NORMAL
                existing_connectivity.triggered_at = None
                existing_connectivity.last_reminder_at = None
                existing_connectivity.condition_cleared_at = None
                existing_connectivity.save(
                    update_fields=[
                        "name",
                        "severity",
                        "condition",
                        "threshold_value",
                        "threshold_value_2",
                        "reminder_interval_minutes",
                        "notify_on_dismissal",
                        "dismissal_threshold_value",
                        "dismissal_threshold_value_2",
                        "enabled",
                        "current_state",
                        "triggered_at",
                        "last_reminder_at",
                        "condition_cleared_at",
                        "updated_at",
                    ]
                )
                continue
        AlertRule.objects.create(
            server=server,
            is_default_template=False,
            name=template.name,
            severity=template.severity,
            metric_type=template.metric_type,
            metric_param=template.metric_param,
            condition=template.condition,
            threshold_value=template.threshold_value,
            threshold_value_2=template.threshold_value_2,
            reminder_interval_minutes=template.reminder_interval_minutes,
            notify_on_dismissal=template.notify_on_dismissal,
            dismissal_threshold_value=template.dismissal_threshold_value,
            dismissal_threshold_value_2=template.dismissal_threshold_value_2,
            enabled=True,
            current_state=AlertState.NORMAL,
        )
        created += 1
    return created
