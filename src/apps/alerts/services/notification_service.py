from apps.alerts.models import AlertEvent, AlertRule
from apps.notifications.models import ChannelType, NotificationChannel
from apps.notifications.services.telegram import TelegramChannel


class NotificationDispatcher:
    _BYTE_METRICS = {
        "ram_used",
        "ram_free",
        "ram_available",
        "ram_cached",
        "swap_used",
        "swap_free",
        "disk_used",
        "disk_free",
    }
    _PERCENT_METRICS = {
        "ram_percent",
        "ram_free_pct",
        "ram_available_pct",
        "swap_percent",
        "swap_free_pct",
        "disk_percent",
        "disk_free_pct",
    }
    _LOAD_METRICS = {"cpu_load_1", "cpu_load_5", "cpu_load_15"}
    _SEVERITY_EMOJIS = {
        "triggered:critical": "🔴",
        "triggered:warning": "🟡",
        "reminded:critical": "🔴",
        "reminded:warning": "🟡",
        "dismissed:critical": "🟢",
        "dismissed:warning": "🟢",
    }

    @classmethod
    def _format_bytes(cls, value: float) -> str:
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        size = float(value)
        idx = 0
        while abs(size) >= 1024 and idx < len(units) - 1:
            size /= 1024
            idx += 1
        return f"{size:.2f} {units[idx]}"

    @classmethod
    def _format_uptime(cls, value: float) -> str:
        seconds = int(max(value, 0))
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        if minutes > 0:
            return f"{minutes}m {secs}s"
        return f"{secs}s"

    @classmethod
    def _format_value(cls, metric_type: str, value: float) -> str:
        if metric_type in cls._BYTE_METRICS:
            return cls._format_bytes(value)
        if metric_type in cls._PERCENT_METRICS:
            return f"{value:.2f}%"
        if metric_type in cls._LOAD_METRICS:
            return f"{value:.2f}"
        if metric_type == "uptime":
            return cls._format_uptime(value)
        return f"{value:.2f}"

    @classmethod
    def _build_threshold_text(cls, rule: AlertRule) -> str:
        value_1 = cls._format_value(rule.metric_type, rule.threshold_value)
        if rule.condition in {"in_range", "out_of_range"} and rule.threshold_value_2 is not None:
            value_2 = cls._format_value(rule.metric_type, rule.threshold_value_2)
            if rule.condition == "in_range":
                return f"in range {value_1} to {value_2}"
            return f"outside {value_1} to {value_2}"

        operators = {
            "gt": f"> {value_1}",
            "gte": f"≥ {value_1}",
            "lt": f"< {value_1}",
            "lte": f"≤ {value_1}",
            "eq": f"= {value_1}",
        }
        return operators.get(rule.condition, value_1)

    @staticmethod
    def _build_message(event: AlertEvent) -> str:
        rule: AlertRule = event.alert_rule
        severity_emoji = NotificationDispatcher._SEVERITY_EMOJIS.get(
            f"{event.event_type}:{rule.severity}",
            "⚪",
        )
        metric_label = rule.get_metric_type_display()
        threshold_text = NotificationDispatcher._build_threshold_text(rule)
        rule_suffix = ""
        if event.event_type == "dismissed":
            rule_suffix = " — Dismissed"
        elif event.event_type == "reminded":
            rule_suffix = " — Reminder"

        lines = [
            f"{severity_emoji} {event.server.name}",
            f"{rule.name}{rule_suffix}",
        ]

        is_ssh_connectivity = rule.metric_type == "custom" and rule.metric_param == "ssh_connectivity"
        if not is_ssh_connectivity:
            lines.append(f"{metric_label} {threshold_text}")

        return "\n".join(lines)

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
