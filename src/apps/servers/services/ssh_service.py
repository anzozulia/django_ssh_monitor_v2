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
