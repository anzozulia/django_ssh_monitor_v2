import io

import pytest

from apps.notifications.services.telegram import TelegramChannel


class _FakeResponse(io.BytesIO):
    def __init__(self, status: int = 200):
        super().__init__(b"{}")
        self._status = status

    def getcode(self) -> int:
        return self._status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.mark.parametrize("method", ["send", "validate_config"])
def test_telegram_channel_success(monkeypatch, method: str):
    channel = TelegramChannel(bot_token="token", chat_id="chat")

    def fake_urlopen(request, timeout):  # noqa: ARG001
        return _FakeResponse(200)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    ok, error = getattr(channel, method)("hello") if method == "send" else getattr(channel, method)()
    assert ok is True
    assert error is None
