from unittest.mock import MagicMock, patch

import pytest

from apps.core.encryption import encrypt_credential
from apps.servers.models import AuthType, Server
from apps.servers.services.ssh_service import SSHService


@pytest.mark.django_db
@patch("apps.servers.services.ssh_service.paramiko.SSHClient")
def test_execute_command_raises_when_not_connected(mock_ssh_client):
    mock_ssh_client.return_value = MagicMock()
    server = Server.objects.create(
        name="SrvErr",
        host="10.40.0.1",
        port=22,
        ssh_username="root",
        auth_type=AuthType.PASSWORD,
        credentials_encrypted=encrypt_credential("secret"),
    )
    service = SSHService(server)
    with pytest.raises(RuntimeError, match="not established"):
        service.execute_command("uptime")


@pytest.mark.django_db
@patch("apps.servers.services.ssh_service.paramiko.SSHClient")
def test_execute_command_raises_on_nonzero_exit_and_error(mock_ssh_client):
    client = MagicMock()
    mock_ssh_client.return_value = client
    stdout = MagicMock()
    stderr = MagicMock()
    stdout.channel.recv_exit_status.return_value = 1
    stdout.read.return_value = b""
    stderr.read.return_value = b"boom"
    client.exec_command.return_value = (None, stdout, stderr)
    server = Server.objects.create(
        name="SrvCmdErr",
        host="10.40.0.2",
        port=22,
        ssh_username="root",
        auth_type=AuthType.PASSWORD,
        credentials_encrypted=encrypt_credential("secret"),
    )
    service = SSHService(server)
    service.connect()
    with pytest.raises(RuntimeError, match="boom"):
        service.execute_command("false")


@pytest.mark.django_db
@patch("apps.servers.services.ssh_service.paramiko.RSAKey.generate")
@patch("apps.servers.services.ssh_service.paramiko.SSHClient")
def test_install_generated_key_runs_expected_command(mock_ssh_client, mock_generate):
    client = MagicMock()
    mock_ssh_client.return_value = client
    fake_key = MagicMock()
    fake_key.get_name.return_value = "ssh-rsa"
    fake_key.get_base64.return_value = "ABCD1234"

    def write_private_key(target):
        target.write("PRIVATE")

    fake_key.write_private_key.side_effect = write_private_key
    mock_generate.return_value = fake_key
    stdout = MagicMock()
    stderr = MagicMock()
    stdout.channel.recv_exit_status.return_value = 0
    stdout.read.return_value = b"ok"
    stderr.read.return_value = b""
    client.exec_command.return_value = (None, stdout, stderr)

    server = Server.objects.create(
        name="SrvGen",
        host="10.40.0.3",
        port=22,
        ssh_username="root",
        auth_type=AuthType.GENERATED_KEY,
        credentials_encrypted=encrypt_credential("bootstrap-pass"),
    )
    service = SSHService(server)
    private_key = service.install_generated_key()
    assert private_key == "PRIVATE"
    client.exec_command.assert_called_once()


@pytest.mark.django_db
@patch("apps.servers.services.ssh_service.paramiko.SSHClient")
def test_install_generated_key_rejects_other_auth_types(mock_ssh_client):
    mock_ssh_client.return_value = MagicMock()
    server = Server.objects.create(
        name="SrvNoGen",
        host="10.40.0.4",
        port=22,
        ssh_username="root",
        auth_type=AuthType.PASSWORD,
        credentials_encrypted=encrypt_credential("secret"),
    )
    service = SSHService(server)
    with pytest.raises(ValueError, match="generated_key"):
        service.install_generated_key()


@pytest.mark.django_db
@patch("apps.servers.services.ssh_service.paramiko.RSAKey.generate")
@patch("apps.servers.services.ssh_service.paramiko.SSHClient")
def test_bootstrap_monitor_user_and_install_key_with_root(mock_ssh_client, mock_generate):
    privileged_client = MagicMock()
    local_client = MagicMock()
    mock_ssh_client.side_effect = [local_client, privileged_client]
    fake_key = MagicMock()
    fake_key.get_name.return_value = "ssh-rsa"
    fake_key.get_base64.return_value = "ABCD1234"

    def write_private_key(target):
        target.write("PRIVATE")

    fake_key.write_private_key.side_effect = write_private_key
    mock_generate.return_value = fake_key

    stdout = MagicMock()
    stderr = MagicMock()
    stdout.channel.recv_exit_status.return_value = 0
    stderr.read.return_value = b""
    privileged_client.exec_command.return_value = (MagicMock(), stdout, stderr)

    server = Server.objects.create(
        name="SrvBootstrap",
        host="10.40.0.5",
        port=22,
        ssh_username="monitor",
        auth_type=AuthType.GENERATED_KEY,
        credentials_encrypted=encrypt_credential("unused"),
    )
    service = SSHService(server)
    private_key = service.bootstrap_monitor_user_and_install_key(
        "root",
        AuthType.PASSWORD,
        "root-pass",
        "monitor",
    )
    assert private_key == "PRIVATE"
    privileged_client.connect.assert_called_once()
    privileged_client.exec_command.assert_called_once()


@pytest.mark.django_db
@patch("apps.servers.services.ssh_service.paramiko.RSAKey.generate")
@patch("apps.servers.services.ssh_service.paramiko.SSHClient")
def test_bootstrap_monitor_user_and_install_key_with_sudo_user(mock_ssh_client, mock_generate):
    privileged_client = MagicMock()
    local_client = MagicMock()
    mock_ssh_client.side_effect = [local_client, privileged_client]
    fake_key = MagicMock()
    fake_key.get_name.return_value = "ssh-rsa"
    fake_key.get_base64.return_value = "ABCD1234"

    def write_private_key(target):
        target.write("PRIVATE")

    fake_key.write_private_key.side_effect = write_private_key
    mock_generate.return_value = fake_key

    stdin = MagicMock()
    stdout = MagicMock()
    stderr = MagicMock()
    stdout.channel.recv_exit_status.return_value = 0
    stderr.read.return_value = b""
    privileged_client.exec_command.return_value = (stdin, stdout, stderr)

    server = Server.objects.create(
        name="SrvBootstrapSudo",
        host="10.40.0.6",
        port=22,
        ssh_username="monitor",
        auth_type=AuthType.GENERATED_KEY,
        credentials_encrypted=encrypt_credential("unused"),
    )
    service = SSHService(server)
    service.bootstrap_monitor_user_and_install_key(
        "deployer",
        AuthType.PASSWORD,
        "sudo-pass",
        "monitor",
    )
    stdin.write.assert_called_once_with("sudo-pass\n")
    privileged_client.exec_command.assert_called_once()


@pytest.mark.django_db
@patch("apps.servers.services.ssh_service.SSHService._parse_private_key")
@patch("apps.servers.services.ssh_service.paramiko.RSAKey.generate")
@patch("apps.servers.services.ssh_service.paramiko.SSHClient")
def test_bootstrap_monitor_user_and_install_key_with_privileged_key(
    mock_ssh_client, mock_generate, mock_parse_key
):
    privileged_client = MagicMock()
    local_client = MagicMock()
    mock_ssh_client.side_effect = [local_client, privileged_client]
    mock_parse_key.return_value = MagicMock()
    fake_key = MagicMock()
    fake_key.get_name.return_value = "ssh-rsa"
    fake_key.get_base64.return_value = "ABCD1234"
    fake_key.write_private_key.side_effect = lambda target: target.write("PRIVATE")
    mock_generate.return_value = fake_key

    stdout = MagicMock()
    stderr = MagicMock()
    stdout.channel.recv_exit_status.return_value = 0
    stderr.read.return_value = b""
    privileged_client.exec_command.return_value = (MagicMock(), stdout, stderr)

    server = Server.objects.create(
        name="SrvBootstrapKey",
        host="10.40.0.7",
        port=22,
        ssh_username="monitor",
        auth_type=AuthType.GENERATED_KEY,
        credentials_encrypted=encrypt_credential("unused"),
    )
    service = SSHService(server)
    service.bootstrap_monitor_user_and_install_key(
        "deployer",
        AuthType.KEY_FILE,
        "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
        "monitor",
    )
    privileged_client.connect.assert_called_once()
    _, connect_kwargs = privileged_client.connect.call_args
    assert "pkey" in connect_kwargs
