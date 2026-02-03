# URL Contracts: SSH Server Monitor

**Feature**: 001-ssh-server-monitor  
**Date**: 2026-02-03

## Overview

This document defines all URL routes for the SSH Server Monitor application. Since this is an SSR monolith (no external API), these are internal view contracts.

## Authentication URLs

**App**: `apps.accounts`  
**Prefix**: `/accounts/`

| Method | URL | View | Description |
|--------|-----|------|-------------|
| GET | `/accounts/login/` | `LoginView` | Login page |
| POST | `/accounts/login/` | `LoginView` | Process login |
| GET/POST | `/accounts/logout/` | `LogoutView` | Logout user |

## Dashboard URLs

**App**: `apps.servers`  
**Prefix**: `/`

| Method | URL | View | Description |
|--------|-----|------|-------------|
| GET | `/` | `DashboardView` | Main dashboard with all servers |

## Server Management URLs

**App**: `apps.servers`  
**Prefix**: `/servers/`

| Method | URL | View | Description |
|--------|-----|------|-------------|
| GET | `/servers/` | `ServerListView` | List all servers |
| GET | `/servers/add/` | `ServerCreateView` | Add server form |
| POST | `/servers/add/` | `ServerCreateView` | Create server |
| GET | `/servers/<int:pk>/` | `ServerDetailView` | Server detail page with metrics |
| GET | `/servers/<int:pk>/edit/` | `ServerUpdateView` | Edit server form |
| POST | `/servers/<int:pk>/edit/` | `ServerUpdateView` | Update server |
| POST | `/servers/<int:pk>/delete/` | `ServerDeleteView` | Delete server |
| POST | `/servers/<int:pk>/toggle/` | `ServerToggleView` | Toggle monitoring on/off |

### Server Metrics Polling Endpoint

| Method | URL | View | Response |
|--------|-----|------|----------|
| GET | `/servers/<int:pk>/metrics/` | `ServerMetricsView` | JSON |

**Response Format**:
```json
{
  "server_id": 1,
  "timestamp": "2026-02-03T12:00:00Z",
  "connection_status": "online",
  "current": {
    "load_1min": 0.5,
    "load_5min": 0.4,
    "load_15min": 0.3,
    "ram_percent": 65.2,
    "ram_used_bytes": 4294967296,
    "ram_total_bytes": 8589934592,
    "swap_percent": 10.0,
    "uptime_seconds": 864000,
    "disks": [
      {"mount_point": "/", "percent": 45.0, "used_bytes": 10737418240, "total_bytes": 21474836480},
      {"mount_point": "/home", "percent": 60.0, "used_bytes": 32212254720, "total_bytes": 53687091200}
    ]
  },
  "history": {
    "timestamps": ["2026-02-03T11:00:00Z", "2026-02-03T11:05:00Z", "..."],
    "load_1min": [0.4, 0.5, "..."],
    "ram_percent": [64.0, 65.2, "..."]
  },
  "alerts": {
    "active_count": 1,
    "warnings": 1,
    "criticals": 0
  }
}
```

## Alert Management URLs

**App**: `apps.alerts`  
**Prefix**: `/alerts/`

### Server-Specific Alerts

| Method | URL | View | Description |
|--------|-----|------|-------------|
| GET | `/servers/<int:server_pk>/alerts/` | `ServerAlertListView` | List alerts for server |
| GET | `/servers/<int:server_pk>/alerts/add/` | `AlertRuleCreateView` | Add alert form |
| POST | `/servers/<int:server_pk>/alerts/add/` | `AlertRuleCreateView` | Create alert |
| GET | `/alerts/<int:pk>/edit/` | `AlertRuleUpdateView` | Edit alert form |
| POST | `/alerts/<int:pk>/edit/` | `AlertRuleUpdateView` | Update alert |
| POST | `/alerts/<int:pk>/delete/` | `AlertRuleDeleteView` | Delete alert |
| POST | `/alerts/<int:pk>/toggle/` | `AlertRuleToggleView` | Toggle alert enabled |

### Default Alert Templates

| Method | URL | View | Description |
|--------|-----|------|-------------|
| GET | `/alerts/defaults/` | `DefaultAlertListView` | List default templates |
| GET | `/alerts/defaults/add/` | `DefaultAlertCreateView` | Add template form |
| POST | `/alerts/defaults/add/` | `DefaultAlertCreateView` | Create template |
| GET | `/alerts/defaults/<int:pk>/edit/` | `DefaultAlertUpdateView` | Edit template form |
| POST | `/alerts/defaults/<int:pk>/edit/` | `DefaultAlertUpdateView` | Update template |
| POST | `/alerts/defaults/<int:pk>/delete/` | `DefaultAlertDeleteView` | Delete template |

### Alert History

| Method | URL | View | Description |
|--------|-----|------|-------------|
| GET | `/alerts/history/` | `AlertHistoryView` | Global alert history |
| GET | `/servers/<int:server_pk>/alerts/history/` | `ServerAlertHistoryView` | Server alert history |

**Query Parameters for History Views**:
- `server` (int): Filter by server ID
- `event_type` (str): `triggered`, `reminded`, `dismissed`
- `metric_type` (str): `cpu_load_1`, `ram_percent`, etc.
- `date_from` (date): Start date
- `date_to` (date): End date
- `page` (int): Pagination

## Notification Channel URLs

**App**: `apps.notifications`  
**Prefix**: `/notifications/`

| Method | URL | View | Description |
|--------|-----|------|-------------|
| GET | `/notifications/channels/` | `ChannelListView` | List notification channels |
| GET | `/notifications/channels/telegram/` | `TelegramConfigView` | Telegram config form |
| POST | `/notifications/channels/telegram/` | `TelegramConfigView` | Save Telegram config |
| POST | `/notifications/channels/telegram/test/` | `TelegramTestView` | Send test message |
| POST | `/notifications/channels/<int:pk>/toggle/` | `ChannelToggleView` | Toggle channel enabled |

## Settings URLs

**App**: `apps.core`  
**Prefix**: `/settings/`

| Method | URL | View | Description |
|--------|-----|------|-------------|
| GET | `/settings/` | `SettingsView` | Settings overview/redirect |

## URL Configuration

### Project URLs (`ssh_monitor/urls.py`)

```python
from django.contrib import admin
from django.urls import path, include
from apps.servers.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='dashboard'),
    path('accounts/', include('apps.accounts.urls')),
    path('servers/', include('apps.servers.urls')),
    path('alerts/', include('apps.alerts.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('settings/', include('apps.core.urls')),
]
```

### App URL Examples

```python
# apps/servers/urls.py
from django.urls import path
from . import views

app_name = 'servers'

urlpatterns = [
    path('', views.ServerListView.as_view(), name='list'),
    path('add/', views.ServerCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ServerDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ServerUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ServerDeleteView.as_view(), name='delete'),
    path('<int:pk>/toggle/', views.ServerToggleView.as_view(), name='toggle'),
    path('<int:pk>/metrics/', views.ServerMetricsView.as_view(), name='metrics'),
    path('<int:pk>/alerts/', views.ServerAlertListView.as_view(), name='alerts'),
    path('<int:pk>/alerts/add/', views.AlertRuleCreateView.as_view(), name='alert-create'),
    path('<int:pk>/alerts/history/', views.ServerAlertHistoryView.as_view(), name='alert-history'),
]
```

## Template URL References

Use Django's `{% url %}` tag for all internal links:

```html
<!-- Dashboard link -->
<a href="{% url 'dashboard' %}">Dashboard</a>

<!-- Server detail -->
<a href="{% url 'servers:detail' pk=server.pk %}">{{ server.name }}</a>

<!-- Add alert to server -->
<a href="{% url 'servers:alert-create' pk=server.pk %}">Add Alert</a>

<!-- Global alert history -->
<a href="{% url 'alerts:history' %}">Alert History</a>
```

## Authentication Requirements

All URLs except `/accounts/login/` require authentication. Use Django's `LoginRequiredMixin` for class-based views:

```python
from django.contrib.auth.mixins import LoginRequiredMixin

class ServerListView(LoginRequiredMixin, ListView):
    model = Server
    template_name = 'servers/list.html'
```
