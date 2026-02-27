from unittest.mock import MagicMock, patch

import pytest

from apps.core.encryption import encrypt_credential
from apps.servers.models import AuthType, Server
from apps.servers.services.ssh_service import SSHService


@pytest.mark.django_db
@patch("apps.servers.services.ssh_service.paramiko.SSHClient")
def test_connect_password(mock_ssh_client):
    client = MagicMock()
    mock_ssh_client.return_value = client
    server = Server.objects.create(
        name="S",
        host="host",
        port=22,
        ssh_username="root",
        auth_type=AuthType.PASSWORD,
        credentials_encrypted=encrypt_credential("secret"),
    )
    service = SSHService(server)
    service.connect()
    client.connect.assert_called_once()


@pytest.mark.django_db
@patch("apps.servers.services.ssh_service.paramiko.SSHClient")
def test_execute_command(mock_ssh_client):
    client = MagicMock()
    mock_ssh_client.return_value = client
    stdout = MagicMock()
    stderr = MagicMock()
    stdout.channel.recv_exit_status.return_value = 0
    stdout.read.return_value = b"ok\n"
    stderr.read.return_value = b""
    client.exec_command.return_value = (None, stdout, stderr)

    server = Server.objects.create(
        name="S",
        host="host",
        port=22,
        ssh_username="root",
        auth_type=AuthType.PASSWORD,
        credentials_encrypted=encrypt_credential("secret"),
    )
    service = SSHService(server)
    service.connect()
    assert service.execute_command("echo ok") == "ok"


@pytest.mark.django_db
@patch("apps.servers.services.ssh_service.paramiko.SSHClient")
def test_connect_generated_key_uses_password_during_bootstrap(mock_ssh_client):
    client = MagicMock()
    mock_ssh_client.return_value = client
    server = Server.objects.create(
        name="S",
        host="host",
        port=22,
        ssh_username="root",
        auth_type=AuthType.GENERATED_KEY,
        credentials_encrypted=encrypt_credential("bootstrap-password"),
    )
    service = SSHService(server)
    service.connect()
    _, kwargs = client.connect.call_args
    assert kwargs["password"] == "bootstrap-password"
    assert "pkey" not in kwargs


@pytest.mark.django_db
@patch("apps.servers.services.ssh_service.paramiko.RSAKey.from_private_key")
@patch("apps.servers.services.ssh_service.paramiko.SSHClient")
def test_connect_generated_key_uses_private_key_after_install(mock_ssh_client, mock_from_private_key):
    client = MagicMock()
    mock_ssh_client.return_value = client
    mock_key = MagicMock()
    mock_from_private_key.return_value = mock_key
    server = Server.objects.create(
        name="S",
        host="host",
        port=22,
        ssh_username="root",
        auth_type=AuthType.GENERATED_KEY,
        credentials_encrypted=encrypt_credential("-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----"),
    )
    service = SSHService(server)
    service.connect()
    _, kwargs = client.connect.call_args
    assert kwargs["pkey"] is mock_key
    assert "password" not in kwargs
