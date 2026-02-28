import io
import logging
import shlex

import paramiko

from apps.core.encryption import decrypt_credential
from apps.servers.models import AuthType, Server

logger = logging.getLogger(__name__)


class SSHService:
    def __init__(self, server: Server):
        self.server = server
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._connected = False

    def connect(self) -> None:
        credential = decrypt_credential(self.server.credentials_encrypted)
        kwargs = {
            "hostname": self.server.host,
            "port": self.server.port,
            "username": self.server.ssh_username,
            "timeout": 10,
        }
        if self.server.auth_type == AuthType.PASSWORD:
            kwargs["password"] = credential
            kwargs["allow_agent"] = False
            kwargs["look_for_keys"] = False
        elif self.server.auth_type == AuthType.GENERATED_KEY:
            # During key-bootstrap this still contains a plain password.
            if "PRIVATE KEY" in credential:
                private_key = paramiko.RSAKey.from_private_key(io.StringIO(credential))
                kwargs["pkey"] = private_key
            else:
                kwargs["password"] = credential
                kwargs["allow_agent"] = False
                kwargs["look_for_keys"] = False
        elif self.server.auth_type == AuthType.KEY_FILE:
            private_key = paramiko.RSAKey.from_private_key(io.StringIO(credential))
            kwargs["pkey"] = private_key
        self.client.connect(**kwargs)
        self._connected = True

    def execute_command(self, command: str) -> str:
        if not self._connected:
            raise RuntimeError("SSH connection is not established")
        _, stdout, stderr = self.client.exec_command(command, timeout=10)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode("utf-8", errors="replace").strip()
        error = stderr.read().decode("utf-8", errors="replace").strip()
        if exit_code != 0 and error:
            raise RuntimeError(f"SSH command failed: {error}")
        return output

    def disconnect(self) -> None:
        try:
            self.client.close()
        finally:
            self._connected = False

    def generate_key_pair(self) -> tuple[str, str]:
        key = paramiko.RSAKey.generate(2048)
        private_io = io.StringIO()
        key.write_private_key(private_io)
        private_key = private_io.getvalue()
        public_key = f"{key.get_name()} {key.get_base64()}"
        return private_key, public_key

    def install_generated_key(self) -> str:
        if self.server.auth_type != AuthType.GENERATED_KEY:
            raise ValueError("install_generated_key only supports generated_key auth type")
        # Connect with password, then append generated public key.
        self.connect()
        private_key, public_key = self.generate_key_pair()
        quoted_key = shlex.quote(public_key)
        install_cmd = (
            "mkdir -p ~/.ssh && chmod 700 ~/.ssh && "
            f"grep -qxF {quoted_key} ~/.ssh/authorized_keys || "
            f"echo {quoted_key} >> ~/.ssh/authorized_keys && "
            "chmod 600 ~/.ssh/authorized_keys"
        )
        self.execute_command(install_cmd)
        self.disconnect()
        return private_key

    @staticmethod
    def _parse_private_key(private_key_text: str) -> paramiko.PKey:
        key_stream = io.StringIO(private_key_text)
        parse_attempts = (
            paramiko.RSAKey.from_private_key,
            paramiko.Ed25519Key.from_private_key,
            paramiko.ECDSAKey.from_private_key,
        )
        last_error: Exception | None = None
        for parser in parse_attempts:
            key_stream.seek(0)
            try:
                return parser(key_stream)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        raise ValueError(f"Unsupported private key format: {last_error}")

    def bootstrap_monitor_user_and_install_key(
        self,
        privileged_username: str,
        privileged_auth_type: str,
        privileged_credential_input: str,
        monitor_username: str,
    ) -> str:
        """
        Connect with temporary privileged credentials, create/update monitor user,
        and install a generated key for that user.
        """
        private_key, public_key = self.generate_key_pair()
        quoted_monitor_user = shlex.quote(monitor_username)
        quoted_public_key = shlex.quote(public_key)

        bootstrap_base_cmd = (
            f"MONITOR_USER={quoted_monitor_user}; "
            "id -u \"$MONITOR_USER\" >/dev/null 2>&1 || useradd -m -s /bin/bash \"$MONITOR_USER\"; "
            "MONITOR_HOME=\"$(getent passwd \"$MONITOR_USER\" | cut -d: -f6)\"; "
            "test -n \"$MONITOR_HOME\"; "
            "install -d -m 700 -o \"$MONITOR_USER\" -g \"$MONITOR_USER\" \"$MONITOR_HOME/.ssh\"; "
            "touch \"$MONITOR_HOME/.ssh/authorized_keys\"; "
            f"grep -qxF {quoted_public_key} \"$MONITOR_HOME/.ssh/authorized_keys\" || "
            f"echo {quoted_public_key} >> \"$MONITOR_HOME/.ssh/authorized_keys\"; "
            "chown \"$MONITOR_USER:$MONITOR_USER\" \"$MONITOR_HOME/.ssh/authorized_keys\"; "
            "chmod 600 \"$MONITOR_HOME/.ssh/authorized_keys\""
        )

        privileged_client = paramiko.SSHClient()
        privileged_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            connect_kwargs: dict[str, object] = {
                "hostname": self.server.host,
                "port": self.server.port,
                "username": privileged_username,
                "timeout": 10,
            }
            if privileged_auth_type == AuthType.KEY_FILE:
                connect_kwargs["pkey"] = self._parse_private_key(privileged_credential_input)
            else:
                connect_kwargs["password"] = privileged_credential_input
                connect_kwargs["allow_agent"] = False
                connect_kwargs["look_for_keys"] = False

            privileged_client.connect(**connect_kwargs)
            if privileged_username == "root":
                _, stdout, stderr = privileged_client.exec_command(bootstrap_base_cmd, timeout=15)
            else:
                if privileged_auth_type == AuthType.PASSWORD:
                    sudo_cmd = f"sudo -S -p '' sh -c {shlex.quote(bootstrap_base_cmd)}"
                    stdin, stdout, stderr = privileged_client.exec_command(sudo_cmd, timeout=15, get_pty=True)
                    stdin.write(f"{privileged_credential_input}\n")
                    stdin.flush()
                else:
                    sudo_cmd = f"sudo -n sh -c {shlex.quote(bootstrap_base_cmd)}"
                    _, stdout, stderr = privileged_client.exec_command(sudo_cmd, timeout=15)

            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:
                error = stderr.read().decode("utf-8", errors="replace").strip()
                if privileged_username != "root" and privileged_auth_type == AuthType.KEY_FILE:
                    raise RuntimeError(
                        "SSH bootstrap failed: non-root key auth requires passwordless sudo (NOPASSWD)."
                    )
                raise RuntimeError(f"SSH bootstrap failed: {error or 'Unknown error'}")
        finally:
            privileged_client.close()

        return private_key
