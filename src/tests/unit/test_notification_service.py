import pytest

from apps.alerts.models import AlertEvent, AlertRule
from apps.alerts.services.notification_service import NotificationDispatcher
from apps.core.encryption import encrypt_credential
from apps.notifications.models import ChannelType, NotificationChannel
from apps.servers.models import Server


@pytest.mark.django_db
def test_notification_dispatcher_sends_to_enabled_telegram(monkeypatch):
    server = Server.objects.create(
        name="SrvN",
        host="10.5.0.1",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    rule = AlertRule.objects.create(
        server=server,
        name="RAM > 80",
        severity="warning",
        metric_type="ram_percent",
        condition="gt",
        threshold_value=80,
    )
    event = AlertEvent.objects.create(
        alert_rule=rule,
        server=server,
        event_type="triggered",
        metric_value=90,
        threshold_value=80,
    )
    channel = NotificationChannel.objects.create(channel_type=ChannelType.TELEGRAM, enabled=True)
    channel.set_config({"bot_token": "token", "chat_id": "chat"})
    channel.save(update_fields=["config_encrypted", "updated_at"])

    monkeypatch.setattr(
        "apps.notifications.services.telegram.TelegramChannel.send",
        lambda self, message: (True, None),  # noqa: ARG005
    )

    sent, error = NotificationDispatcher().send_event(event)
    assert sent is True
    assert error is None
