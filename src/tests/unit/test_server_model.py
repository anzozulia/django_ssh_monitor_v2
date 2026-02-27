import pytest
from django.db import IntegrityError

from apps.core.encryption import encrypt_credential
from apps.servers.models import ConnectionStatus, Server


@pytest.mark.django_db
def test_server_str():
    server = Server.objects.create(
        name="Prod",
        host="10.0.0.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    assert str(server) == "Prod (10.0.0.1:22)"


@pytest.mark.django_db
def test_unique_host_port_constraint():
    Server.objects.create(
        name="A",
        host="10.0.0.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    with pytest.raises(IntegrityError):
        Server.objects.create(
            name="B",
            host="10.0.0.1",
            port=22,
            ssh_username="ubuntu",
            auth_type="password",
            credentials_encrypted=encrypt_credential("pass2"),
        )


@pytest.mark.django_db
def test_default_connection_status_pending():
    server = Server.objects.create(
        name="Pending",
        host="127.0.0.1",
        port=2222,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    assert server.connection_status == ConnectionStatus.PENDING
