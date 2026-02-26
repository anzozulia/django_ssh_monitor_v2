from django.utils import timezone

from apps.alerts.models import AlertEvent, AlertRule
from apps.notifications.models import ChannelType, NotificationChannel
from apps.notifications.services.telegram import TelegramChannel


class NotificationDispatcher:
    @staticmethod
    def _build_message(event: AlertEvent) -> str:
        rule: AlertRule = event.alert_rule
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        return (
            f"[{event.event_type.upper()}] {rule.severity.upper()}\n"
            f"Server: {event.server.name}\n"
            f"Rule: {rule.name}\n"
            f"Metric: {rule.metric_type}\n"
            f"Condition: {rule.condition}\n"
            f"Value: {event.metric_value:.2f}\n"
            f"Threshold: {event.threshold_value:.2f}\n"
            f"Time: {timestamp}"
        )

    def _get_backends(self) -> list[TelegramChannel]:
        backends: list[TelegramChannel] = []
        for channel in NotificationChannel.objects.filter(enabled=True):
            config = channel.get_config()
            if channel.channel_type == ChannelType.TELEGRAM:
                token = config.get("bot_token", "")
                chat_id = config.get("chat_id", "")
                if token and chat_id:
                    backends.append(TelegramChannel(bot_token=token, chat_id=chat_id))
        return backends

    def send_event(self, event: AlertEvent) -> tuple[bool, str | None]:
        backends = self._get_backends()
        if not backends:
            return False, "No enabled notification channels configured."

        message = self._build_message(event)
        errors: list[str] = []
        sent_any = False
        for backend in backends:
            ok, error = backend.send(message)
            if ok:
                sent_any = True
            elif error:
                errors.append(error)

        if sent_any:
            return True, None
        return False, "; ".join(errors) if errors else "Failed to send notification."
