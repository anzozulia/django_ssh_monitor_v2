from django.urls import path

from apps.notifications.views import (
    ChannelListView,
    ChannelToggleView,
    TelegramConfigView,
    TelegramTestView,
)

app_name = "notifications"

urlpatterns = [
    path("", ChannelListView.as_view(), name="list"),
    path("telegram/", TelegramConfigView.as_view(), name="telegram-config"),
    path("telegram/test/", TelegramTestView.as_view(), name="telegram-test"),
    path("<int:pk>/toggle/", ChannelToggleView.as_view(), name="toggle"),
]
