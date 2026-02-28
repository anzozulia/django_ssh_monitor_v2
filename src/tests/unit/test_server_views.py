from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.core.encryption import decrypt_credential, encrypt_credential
from apps.servers.models import Server


@pytest.mark.django_db
def test_server_update_view_keeps_existing_credentials_when_input_empty(
    authenticated_client, disable_initial_metrics_collection
):
    server = Server.objects.create(
        name="srv-update",
        host="10.0.0.71",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("old-secret"),
        check_interval_minutes=5,
    )
    response = authenticated_client.post(
        reverse("servers:update", kwargs={"pk": server.id}),
        data={
            "name": "srv-update-renamed",
            "host": "10.0.0.71",
            "port": 2222,
            "ssh_username": "root",
            "auth_type": "password",
            "credential_input": "",
            "check_interval_minutes": 15,
            "monitoring_enabled": "on",
        },
    )
    assert response.status_code == 302
    server.refresh_from_db()
    assert server.name == "srv-update-renamed"
    assert server.port == 2222
    assert server.check_interval_minutes == 15
    assert decrypt_credential(server.credentials_encrypted) == "old-secret"


@pytest.mark.django_db
def test_server_delete_view_removes_server_and_redirects(authenticated_client):
    server = Server.objects.create(
        name="srv-delete",
        host="10.0.0.72",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
    )
    response = authenticated_client.post(reverse("servers:delete", kwargs={"pk": server.id}))
    assert response.status_code == 302
    assert response.url == reverse("servers:dashboard")
    assert not Server.objects.filter(id=server.id).exists()


@pytest.mark.django_db
@patch("apps.servers.views.collect_server_metrics.delay", return_value=None)
@patch("apps.servers.views.schedule_server_collection")
@patch("apps.servers.views.clone_default_alerts_if_available")
@patch("apps.servers.views.create_connectivity_alert_if_available")
@patch("apps.servers.views.SSHService.bootstrap_monitor_user_and_install_key", return_value="PRIVATE-KEY")
def test_server_create_generated_key_with_privileged_bootstrap(
    mock_bootstrap,
    _mock_connectivity,
    _mock_clone_defaults,
    _mock_schedule,
    _mock_collect,
    authenticated_client,
):
    response = authenticated_client.post(
        reverse("servers:create"),
        data={
            "name": "srv-bootstrap",
            "host": "10.0.0.99",
            "port": 22,
            "ssh_username": "ssh-monitor",
            "auth_type": "generated_key",
            "use_privileged_bootstrap": "on",
            "privileged_auth_type": "password",
            "privileged_username": "root",
            "privileged_credential_input": "root-pass",
            "check_interval_minutes": 5,
            "monitoring_enabled": "on",
        },
    )
    assert response.status_code == 302
    server = Server.objects.get(name="srv-bootstrap")
    assert server.auth_type == "generated_key"
    assert decrypt_credential(server.credentials_encrypted) == "PRIVATE-KEY"
    mock_bootstrap.assert_called_once_with(
        privileged_username="root",
        privileged_auth_type="password",
        privileged_credential_input="root-pass",
        monitor_username="ssh-monitor",
    )
