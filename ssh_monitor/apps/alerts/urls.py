"""URL configuration for alerts app."""

from django.urls import path

from apps.alerts.views import (
    AlertHistoryView,
    AlertRuleCreateView,
    AlertRuleDeleteView,
    AlertRuleToggleView,
    AlertRuleUpdateView,
    DefaultAlertCreateView,
    DefaultAlertDeleteView,
    DefaultAlertListView,
    DefaultAlertUpdateView,
    ServerAlertHistoryView,
)

app_name = "alerts"

urlpatterns = [
    # US2 server rules
    path("servers/<int:server_pk>/alerts/add/", AlertRuleCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", AlertRuleUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", AlertRuleDeleteView.as_view(), name="delete"),
    path("<int:pk>/toggle/", AlertRuleToggleView.as_view(), name="toggle"),
    # Shared history/default templates
    path("history/", AlertHistoryView.as_view(), name="history"),
    path("servers/<int:server_pk>/history/", ServerAlertHistoryView.as_view(), name="server-history"),
    path("defaults/", DefaultAlertListView.as_view(), name="defaults"),
    path("defaults/add/", DefaultAlertCreateView.as_view(), name="defaults-create"),
    path("defaults/<int:pk>/edit/", DefaultAlertUpdateView.as_view(), name="defaults-update"),
    path("defaults/<int:pk>/delete/", DefaultAlertDeleteView.as_view(), name="defaults-delete"),
]
