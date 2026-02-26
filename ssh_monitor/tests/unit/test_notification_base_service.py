from apps.notifications.services.base import NotificationChannelBackend


class DummyBackend(NotificationChannelBackend):
    def send(self, message: str) -> tuple[bool, str | None]:
        return super().send(message)

    def validate_config(self) -> tuple[bool, str | None]:
        return super().validate_config()


def test_notification_base_methods_are_callable_through_super():
    backend = DummyBackend()
    assert backend.send("x") is None
    assert backend.validate_config() is None
