import pytest
from django.urls import reverse

from apps.alerts.models import AlertRule
from apps.servers.models import Server


@pytest.mark.django_db
def test_default_template_is_cloned_on_server_create(authenticated_client, disable_initial_metrics_collection):
    AlertRule.objects.create(
        server=None,
        is_default_template=True,
        name="Swap usage high",
        severity="warning",
        metric_type="swap_percent",
        condition="gt",
        threshold_value=70,
        enabled=True,
    )

    response = authenticated_client.post(
        reverse("servers:create"),
        data={
            "name": "TemplateCloneServer",
            "host": "10.8.0.1",
            "port": 22,
            "ssh_username": "root",
            "auth_type": "password",
            "credential_input": "pass12345",
            "check_interval_minutes": 5,
            "monitoring_enabled": "on",
        },
    )
    assert response.status_code == 302
    server = Server.objects.get(name="TemplateCloneServer")
    assert AlertRule.objects.filter(server=server, name="Swap usage high").exists()
