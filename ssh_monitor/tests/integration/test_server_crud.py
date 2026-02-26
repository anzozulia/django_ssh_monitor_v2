import pytest
from django.urls import reverse

from apps.core.encryption import decrypt_credential, encrypt_credential
from apps.servers.models import Server


@pytest.mark.django_db
def test_create_server_flow(authenticated_client):
    response = authenticated_client.post(
        reverse("servers:create"),
        data={
            "name": "Test server",
            "host": "127.0.0.1",
            "port": 22,
            "ssh_username": "root",
            "auth_type": "password",
            "credential_input": "pass12345",
            "check_interval_minutes": 5,
            "monitoring_enabled": "on",
        },
    )
    assert response.status_code == 302
    assert Server.objects.filter(name="Test server").exists()


@pytest.mark.django_db
def test_server_detail_page(authenticated_client):
    server = Server.objects.create(
        name="Demo",
        host="10.0.0.10",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",  # not decrypted in detail view
    )
    response = authenticated_client.get(reverse("servers:detail", kwargs={"pk": server.id}))
    assert response.status_code == 200


@pytest.mark.django_db
def test_metrics_endpoint_empty(authenticated_client):
    server = Server.objects.create(
        name="Demo",
        host="10.0.0.11",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
    )
    response = authenticated_client.get(reverse("servers:metrics", kwargs={"pk": server.id}))
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True


@pytest.mark.django_db
def test_update_server_allows_interval_change_without_new_credential(authenticated_client):
    server = Server.objects.create(
        name="Editable",
        host="10.0.0.12",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("old-pass"),
        check_interval_minutes=5,
        monitoring_enabled=True,
    )

    response = authenticated_client.post(
        reverse("servers:update", kwargs={"pk": server.id}),
        data={
            "name": "Editable",
            "host": "10.0.0.12",
            "port": 2222,
            "ssh_username": "root",
            "auth_type": "password",
            "credential_input": "",
            "check_interval_minutes": 30,
            "monitoring_enabled": "on",
        },
    )
    assert response.status_code == 302

    server.refresh_from_db()
    assert server.port == 2222
    assert server.check_interval_minutes == 30
    assert decrypt_credential(server.credentials_encrypted) == "old-pass"
