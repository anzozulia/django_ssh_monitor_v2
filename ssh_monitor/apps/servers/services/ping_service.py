import platform
import subprocess


class PingService:
    @staticmethod
    def ping(host: str, timeout_seconds: int = 2) -> bool:
        system = platform.system().lower()
        if system == "darwin":
            cmd = ["ping", "-c", "1", "-W", str(timeout_seconds * 1000), host]
        else:
            cmd = ["ping", "-c", "1", "-W", str(timeout_seconds), host]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode == 0
