"""
URL configuration for SSH Monitor project.

Routes are organized by app, with core templates handling base layout.
"""

from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

from apps.core.views import healthz


def redirect_to_dashboard(request):
    """Redirect root URL to dashboard or login."""
    if request.user.is_authenticated:
        return redirect("servers:dashboard")
    return redirect("accounts:login")


urlpatterns = [
    # Root redirect
    path("", redirect_to_dashboard, name="root"),
    path("healthz", healthz, name="healthz"),
    # Django admin
    path("admin/", admin.site.urls),
    # App URLs
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("servers/", include("apps.servers.urls", namespace="servers")),
    path("alerts/", include("apps.alerts.urls", namespace="alerts")),
    path("notifications/", include("apps.notifications.urls", namespace="notifications")),
]

# Debug toolbar URLs (only in development)
if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
