from apps.alerts.models import AlertRule, AlertState
from apps.servers.models import Server


def clone_default_alerts_to_server(server: Server) -> int:
    templates = AlertRule.objects.filter(is_default_template=True, server__isnull=True)
    created = 0
    for template in templates:
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
