from abc import ABC, abstractmethod


class NotificationChannelBackend(ABC):
    @abstractmethod
    def send(self, message: str) -> tuple[bool, str | None]:
        pass

    @abstractmethod
    def validate_config(self) -> tuple[bool, str | None]:
        pass
