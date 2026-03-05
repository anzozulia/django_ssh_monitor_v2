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

    sent_messages: list[str] = []

    def fake_send(self, message):  # noqa: ANN001, ANN202
        sent_messages.append(message)
        return True, None

    monkeypatch.setattr("apps.notifications.services.telegram.TelegramChannel.send", fake_send)

    sent, error = NotificationDispatcher().send_event(event)
    assert sent is True
    assert error is None
    assert len(sent_messages) == 1
    message = sent_messages[0]
    lines = message.splitlines()
    assert lines[0] == "🟡 SrvN"
    assert lines[1] == "RAM > 80"
    assert lines[2] == "RAM Usage % > 80.00%"


@pytest.mark.django_db
def test_notification_message_formats_bytes_and_range(monkeypatch):
    server = Server.objects.create(
        name="SrvBytes",
        host="10.5.0.2",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    rule = AlertRule.objects.create(
        server=server,
        name="Disk free outside range",
        severity="critical",
        metric_type="disk_free",
        condition="out_of_range",
        threshold_value=10 * 1024 * 1024 * 1024,
        threshold_value_2=20 * 1024 * 1024 * 1024,
    )
    event = AlertEvent.objects.create(
        alert_rule=rule,
        server=server,
        event_type="triggered",
        metric_value=7 * 1024 * 1024 * 1024,
        threshold_value=rule.threshold_value,
    )
    channel = NotificationChannel.objects.create(channel_type=ChannelType.TELEGRAM, enabled=True)
    channel.set_config({"bot_token": "token", "chat_id": "chat"})
    channel.save(update_fields=["config_encrypted", "updated_at"])

    sent_messages: list[str] = []

    def fake_send(self, message):  # noqa: ANN001, ANN202
        sent_messages.append(message)
        return True, None

    monkeypatch.setattr("apps.notifications.services.telegram.TelegramChannel.send", fake_send)
    sent, error = NotificationDispatcher().send_event(event)
    assert sent is True
    assert error is None

    message = sent_messages[0]
    lines = message.splitlines()
    assert lines[0] == "🔴 SrvBytes"
    assert lines[1] == "Disk free outside range"
    assert lines[2] == "Disk Free (bytes) outside 10.00 GB to 20.00 GB"


@pytest.mark.django_db
def test_notification_message_for_ssh_connectivity_skips_metric_line(monkeypatch):
    server = Server.objects.create(
        name="SrvSSH",
        host="10.5.0.3",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    rule = AlertRule.objects.create(
        server=server,
        name="SSH connectivity failed",
        severity="critical",
        metric_type="custom",
        metric_param="ssh_connectivity",
        condition="gt",
        threshold_value=0,
    )
    event = AlertEvent.objects.create(
        alert_rule=rule,
        server=server,
        event_type="triggered",
        metric_value=1,
        threshold_value=0,
    )
    channel = NotificationChannel.objects.create(channel_type=ChannelType.TELEGRAM, enabled=True)
    channel.set_config({"bot_token": "token", "chat_id": "chat"})
    channel.save(update_fields=["config_encrypted", "updated_at"])

    sent_messages: list[str] = []

    def fake_send(self, message):  # noqa: ANN001, ANN202
        sent_messages.append(message)
        return True, None

    monkeypatch.setattr("apps.notifications.services.telegram.TelegramChannel.send", fake_send)
    sent, error = NotificationDispatcher().send_event(event)
    assert sent is True
    assert error is None

    lines = sent_messages[0].splitlines()
    assert lines == ["🔴 SrvSSH", "SSH connectivity failed"]


@pytest.mark.django_db
def test_notification_message_adds_reminder_and_dismissed_suffix(monkeypatch):
    server = Server.objects.create(
        name="SrvState",
        host="10.5.0.4",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted=encrypt_credential("pass"),
    )
    rule = AlertRule.objects.create(
        server=server,
        name="RAM high",
        severity="warning",
        metric_type="ram_percent",
        condition="gte",
        threshold_value=85,
    )
    channel = NotificationChannel.objects.create(channel_type=ChannelType.TELEGRAM, enabled=True)
    channel.set_config({"bot_token": "token", "chat_id": "chat"})
    channel.save(update_fields=["config_encrypted", "updated_at"])

    sent_messages: list[str] = []

    def fake_send(self, message):  # noqa: ANN001, ANN202
        sent_messages.append(message)
        return True, None

    monkeypatch.setattr("apps.notifications.services.telegram.TelegramChannel.send", fake_send)

    reminder_event = AlertEvent.objects.create(
        alert_rule=rule,
        server=server,
        event_type="reminded",
        metric_value=90,
        threshold_value=85,
    )
    dismissed_event = AlertEvent.objects.create(
        alert_rule=rule,
        server=server,
        event_type="dismissed",
        metric_value=70,
        threshold_value=85,
    )

    NotificationDispatcher().send_event(reminder_event)
    NotificationDispatcher().send_event(dismissed_event)

    reminder_lines = sent_messages[0].splitlines()
    dismissed_lines = sent_messages[1].splitlines()
    assert reminder_lines[0] == "🟡 SrvState"
    assert reminder_lines[1] == "RAM high — Reminder"
    assert dismissed_lines[0] == "🟢 SrvState"
    assert dismissed_lines[1] == "RAM high — Dismissed"
