"""URL configuration for servers app."""

from django.urls import path

from apps.servers.views import (
    DashboardView,
    ServerCreateView,
    ServerDeleteView,
    ServerDetailView,
    ServerMetricsView,
    ServerMonitoringToggleView,
    ServerUpdateView,
)

app_name = "servers"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("add/", ServerCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", ServerUpdateView.as_view(), name="update"),
    path("<int:pk>/", ServerDetailView.as_view(), name="detail"),
    path("<int:pk>/delete/", ServerDeleteView.as_view(), name="delete"),
    path("<int:pk>/metrics/", ServerMetricsView.as_view(), name="metrics"),
    path("<int:pk>/toggle-monitoring/", ServerMonitoringToggleView.as_view(), name="toggle-monitoring"),
]
