import json
import urllib.error
import urllib.request

from apps.notifications.services.base import NotificationChannelBackend


class TelegramChannel(NotificationChannelBackend):
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def _api_call(self, method: str, payload: dict[str, str]) -> tuple[bool, str | None]:
        url = f"https://api.telegram.org/bot{self.bot_token}/{method}"
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 - trusted host
                status = response.getcode()
                return (200 <= status < 300, None if 200 <= status < 300 else f"HTTP {status}")
        except urllib.error.HTTPError as exc:
            return False, f"HTTP {exc.code}"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)

    def send(self, message: str) -> tuple[bool, str | None]:
        return self._api_call("sendMessage", {"chat_id": self.chat_id, "text": message})

    def validate_config(self) -> tuple[bool, str | None]:
        return self.send("SSH Monitor: Telegram channel validation successful.")
