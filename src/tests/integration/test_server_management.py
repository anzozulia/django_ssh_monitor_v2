import pytest
from django.urls import reverse

from apps.core.encryption import encrypt_credential
from apps.servers.models import Server


@pytest.mark.django_db
def test_server_edit_toggle_delete_flow(authenticated_client):
    server = Server.objects.create(
        name="srv-mgmt",
        host="10.0.0.81",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("secret"),
        monitoring_enabled=True,
    )

    edit_response = authenticated_client.post(
        reverse("servers:update", kwargs={"pk": server.id}),
        data={
            "name": "srv-mgmt-2",
            "host": "10.0.0.81",
            "port": 2222,
            "ssh_username": "admin",
            "auth_type": "password",
            "credential_input": "",
            "check_interval_minutes": 30,
            "monitoring_enabled": "on",
        },
    )
    assert edit_response.status_code == 302
    server.refresh_from_db()
    assert server.name == "srv-mgmt-2"
    assert server.port == 2222
    assert server.ssh_username == "admin"
    assert server.check_interval_minutes == 30

    toggle_response = authenticated_client.post(
        reverse("servers:toggle-monitoring", kwargs={"pk": server.id}),
        data={"enabled": "false"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert toggle_response.status_code == 200
    server.refresh_from_db()
    assert server.monitoring_enabled is False

    delete_response = authenticated_client.post(reverse("servers:delete", kwargs={"pk": server.id}))
    assert delete_response.status_code == 302
    assert not Server.objects.filter(id=server.id).exists()
