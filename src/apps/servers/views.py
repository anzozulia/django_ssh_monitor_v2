import json
import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, OuterRef, Q, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django_celery_beat.models import PeriodicTask

from apps.alerts.models import AlertEvent, AlertRule, EventType
from apps.servers.forms import ServerForm
from apps.servers.models import AuthType, DiskMetric, MetricSnapshot, Server
from apps.servers.services.ssh_service import SSHService
from apps.servers.tasks import collect_server_metrics, schedule_server_collection

logger = logging.getLogger(__name__)

HISTORY_RANGE_MAP = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


def _resolve_history_range(raw_range: str | None) -> str:
    if raw_range in HISTORY_RANGE_MAP:
        return raw_range
    return "24h"


def _build_history_payload(server: Server, selected_range: str) -> dict:
    now = timezone.now()
    cutoff = now - HISTORY_RANGE_MAP[selected_range]
    snapshots = list(
        server.metrics.filter(timestamp__gte=cutoff).prefetch_related("disk_metrics").order_by("timestamp")
    )
    return {
        "range": selected_range,
        "timestamps": [snap.timestamp.isoformat() for snap in snapshots],
        "load_1min": [snap.load_1min for snap in snapshots],
        "ram_percent": [snap.ram_percent for snap in snapshots],
        "swap_percent": [snap.swap_percent for snap in snapshots],
        "disk_percent": [max((disk.percent for disk in snap.disk_metrics.all()), default=None) for snap in snapshots],
    }


def _build_alert_periods(server: Server, selected_range: str) -> list[dict]:
    now = timezone.now()
    cutoff = now - HISTORY_RANGE_MAP[selected_range]
    periods: list[dict] = []
    events = (
        AlertEvent.objects.filter(
            server=server,
            event_type__in=[EventType.TRIGGERED, EventType.DISMISSED],
            created_at__lte=now,
        )
        .select_related("alert_rule")
        .order_by("alert_rule_id", "created_at")
    )
    active_starts: dict[int, tuple[object, str, str]] = {}
    for event in events:
        if event.event_type == EventType.TRIGGERED:
            active_starts[event.alert_rule_id] = (
                event.created_at,
                event.alert_rule.severity,
                event.alert_rule.name,
            )
            continue
        trigger_data = active_starts.pop(event.alert_rule_id, None)
        if not trigger_data:
            continue
        started_at, severity, rule_name = trigger_data
        period_start = max(started_at, cutoff)
        period_end = min(event.created_at, now)
        if period_end > period_start:
            periods.append(
                {
                    "start": period_start.isoformat(),
                    "end": period_end.isoformat(),
                    "severity": severity,
                    "rule_name": rule_name,
                }
            )

    active_rules = AlertRule.objects.filter(
        server=server,
        enabled=True,
        current_state="triggered",
        triggered_at__isnull=False,
    ).values("triggered_at", "severity", "name")
    for rule in active_rules:
        period_start = max(rule["triggered_at"], cutoff)
        if now > period_start:
            periods.append(
                {
                    "start": period_start.isoformat(),
                    "end": now.isoformat(),
                    "severity": rule["severity"],
                    "rule_name": rule["name"],
                }
            )
    return periods


def create_connectivity_alert_if_available(server: Server) -> None:
    """
    T042a implementation hook.
    Creates a non-configurable SSH connectivity alert when alert models are available.
    """
    try:
        from apps.alerts.models import AlertRule  # type: ignore

        AlertRule.objects.get_or_create(
            server=server,
            metric_type="custom",
            metric_param="ssh_connectivity",
            defaults={
                "name": "SSH Connectivity",
                "severity": "critical",
                "condition": "eq",
                "threshold_value": 1,
                "enabled": True,
            },
        )
    except Exception:  # noqa: BLE001
        logger.info("AlertRule model not ready yet; connectivity alert deferred for server %s", server.id)


def clone_default_alerts_if_available(server: Server) -> None:
    try:
        from apps.alerts.services.template_service import clone_default_alerts_to_server  # type: ignore

        clone_default_alerts_to_server(server)
    except Exception:  # noqa: BLE001
        logger.info("Default alert cloning skipped for server %s", server.id)


class DashboardView(LoginRequiredMixin, View):
    """
    Dashboard view showing all servers with status summaries.

    Full implementation in Phase 8 (US6). Currently a placeholder.
    """

    template_name = "servers/dashboard.html"

    def get(self, request):
        latest_snapshot_qs = MetricSnapshot.objects.filter(server=OuterRef("pk")).order_by("-timestamp")
        stats = Server.objects.aggregate(
            total_servers=Count("id"),
            online_servers=Count("id", filter=Q(connection_status="online")),
            offline_servers=Count("id", filter=Q(connection_status="unreachable")),
        )
        servers = list(
            Server.objects.annotate(
                latest_snapshot_id=Subquery(latest_snapshot_qs.values("id")[:1]),
                latest_load_value=Subquery(latest_snapshot_qs.values("load_1min")[:1]),
                latest_ram_value=Subquery(latest_snapshot_qs.values("ram_percent")[:1]),
                triggered_warning_count=Count(
                    "alert_rules",
                    filter=Q(
                        alert_rules__enabled=True,
                        alert_rules__current_state="triggered",
                        alert_rules__severity="warning",
                    ),
                    distinct=True,
                ),
                triggered_critical_count=Count(
                    "alert_rules",
                    filter=Q(
                        alert_rules__enabled=True,
                        alert_rules__current_state="triggered",
                        alert_rules__severity="critical",
                    ),
                    distinct=True,
                ),
            )
        )
        latest_snapshot_ids = [s.latest_snapshot_id for s in servers if s.latest_snapshot_id]
        disk_by_snapshot: dict[int, str] = {}
        if latest_snapshot_ids:
            disks = (
                DiskMetric.objects.filter(snapshot_id__in=latest_snapshot_ids)
                .values("snapshot_id", "mount_point", "percent")
                .order_by("snapshot_id", "-percent")
            )
            for disk in disks:
                snapshot_id = disk["snapshot_id"]
                if snapshot_id not in disk_by_snapshot:
                    disk_by_snapshot[snapshot_id] = f"{disk['mount_point']}: {disk['percent']:.2f}%"

        healthy_servers = 0
        warning_servers = 0
        critical_servers = 0
        for server in servers:
            server.latest_load = f"{server.latest_load_value:.2f}" if server.latest_load_value is not None else "-"
            server.latest_ram = f"{server.latest_ram_value:.2f}%" if server.latest_ram_value is not None else "-"
            server.latest_disk = (
                disk_by_snapshot.get(server.latest_snapshot_id, "-") if server.latest_snapshot_id else "-"
            )

            if server.triggered_critical_count > 0:
                critical_servers += 1
            elif server.triggered_warning_count > 0:
                warning_servers += 1
            else:
                healthy_servers += 1

        total_servers = stats.get("total_servers", 0) or 0
        context = {
            "servers": servers,
            "healthy_servers": healthy_servers,
            "warning_servers": warning_servers,
            "critical_servers": critical_servers,
            "healthy_pct": (healthy_servers / total_servers * 100) if total_servers else 0,
            "warning_pct": (warning_servers / total_servers * 100) if total_servers else 0,
            "critical_pct": (critical_servers / total_servers * 100) if total_servers else 0,
            **stats,
        }
        return render(request, self.template_name, context)


class ServerCreateView(LoginRequiredMixin, View):
    template_name = "servers/server_form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": ServerForm()})

    def post(self, request):
        form = ServerForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        server = form.save(commit=False)
        if server.auth_type == AuthType.GENERATED_KEY:
            ssh = SSHService(server)
            use_privileged_bootstrap = form.cleaned_data.get("use_privileged_bootstrap")
            if use_privileged_bootstrap:
                private_key = ssh.bootstrap_monitor_user_and_install_key(
                    privileged_username=form.cleaned_data["privileged_username"].strip(),
                    privileged_auth_type=form.cleaned_data["privileged_auth_type"],
                    privileged_credential_input=form.cleaned_data["privileged_credential_input"],
                    monitor_username=server.ssh_username,
                )
            else:
                private_key = ssh.install_generated_key()
            from apps.core.encryption import encrypt_credential

            server.credentials_encrypted = encrypt_credential(private_key)
        server.save()
        create_connectivity_alert_if_available(server)
        clone_default_alerts_if_available(server)
        schedule_server_collection(server)
        collect_server_metrics.delay(server.id)
        messages.success(request, "Server created successfully.")
        return redirect("servers:detail", pk=server.id)


class ServerUpdateView(LoginRequiredMixin, View):
    template_name = "servers/server_form.html"

    def get(self, request, pk: int):
        server = get_object_or_404(Server, id=pk)
        form = ServerForm(instance=server)
        return render(request, self.template_name, {"form": form, "mode": "edit", "server": server})

    def post(self, request, pk: int):
        server = get_object_or_404(Server, id=pk)
        form = ServerForm(request.POST, instance=server)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "mode": "edit", "server": server})

        updated_server = form.save()
        credential_input = form.cleaned_data.get("credential_input", "").strip()
        use_privileged_bootstrap = form.cleaned_data.get("use_privileged_bootstrap")
        if updated_server.auth_type == AuthType.GENERATED_KEY and (credential_input or use_privileged_bootstrap):
            ssh = SSHService(updated_server)
            if use_privileged_bootstrap:
                private_key = ssh.bootstrap_monitor_user_and_install_key(
                    privileged_username=form.cleaned_data["privileged_username"].strip(),
                    privileged_auth_type=form.cleaned_data["privileged_auth_type"],
                    privileged_credential_input=form.cleaned_data["privileged_credential_input"],
                    monitor_username=updated_server.ssh_username,
                )
            else:
                private_key = ssh.install_generated_key()
            from apps.core.encryption import encrypt_credential

            updated_server.credentials_encrypted = encrypt_credential(private_key)
            updated_server.save(update_fields=["credentials_encrypted", "updated_at"])

        schedule_server_collection(updated_server)
        collect_server_metrics.delay(updated_server.id)
        messages.success(request, "Server settings updated.")
        return redirect("servers:detail", pk=updated_server.id)


class ServerDetailView(LoginRequiredMixin, View):
    template_name = "servers/server_detail.html"

    def get(self, request, pk: int):
        server = get_object_or_404(Server, id=pk)
        selected_range = _resolve_history_range(request.GET.get("range"))
        latest = server.metrics.first()
        history_payload = _build_history_payload(server, selected_range)
        alert_periods = _build_alert_periods(server, selected_range)
        resource_totals = {
            "cpu_cores": latest.cpu_cores if latest else None,
            "ram_total_bytes": latest.ram_total_bytes if latest else None,
            "swap_total_bytes": latest.swap_total_bytes if latest else None,
            "disk_total_bytes": sum(d.total_bytes for d in latest.disk_metrics.all()) if latest else None,
        }
        context = {
            "server": server,
            "latest": latest,
            "disks": latest.disk_metrics.exclude(mount_point__contains="/docker/") if latest else [],
            "resource_totals": resource_totals,
            "selected_range": selected_range,
            "history_json": json.dumps(history_payload),
            "alert_periods_json": json.dumps(alert_periods),
        }
        return render(request, self.template_name, context)


class ServerMetricsView(LoginRequiredMixin, View):
    def get(self, request, pk: int):
        server = get_object_or_404(Server, id=pk)
        selected_range = _resolve_history_range(request.GET.get("range"))
        latest = server.metrics.first()
        history_payload = _build_history_payload(server, selected_range)
        alert_periods = _build_alert_periods(server, selected_range)
        if not latest:
            return JsonResponse(
                {
                    "ok": True,
                    "latest": None,
                    "history": history_payload,
                    "alert_periods": alert_periods,
                    "range": selected_range,
                }
            )
        disks = list(
            latest.disk_metrics.exclude(mount_point__contains="/docker/").values(
                "filesystem",
                "mount_point",
                "total_bytes",
                "used_bytes",
                "available_bytes",
                "percent",
            )
        )
        disk_total_bytes = sum(item["total_bytes"] for item in disks)
        return JsonResponse(
            {
                "ok": True,
                "latest": {
                    "id": latest.id,
                    "timestamp": latest.timestamp.isoformat(),
                    "collection_status": latest.collection_status,
                    "load_1min": latest.load_1min,
                    "load_5min": latest.load_5min,
                    "load_15min": latest.load_15min,
                    "cpu_cores": latest.cpu_cores,
                    "ram_total_bytes": latest.ram_total_bytes,
                    "ram_used_bytes": latest.ram_used_bytes,
                    "ram_free_bytes": latest.ram_free_bytes,
                    "ram_available_bytes": latest.ram_available_bytes,
                    "ram_cached_bytes": latest.ram_cached_bytes,
                    "ram_buffers_bytes": latest.ram_buffers_bytes,
                    "ram_shared_bytes": latest.ram_shared_bytes,
                    "ram_percent": latest.ram_percent,
                    "ram_free_percent": latest.ram_free_percent,
                    "ram_available_percent": latest.ram_available_percent,
                    "swap_total_bytes": latest.swap_total_bytes,
                    "swap_used_bytes": latest.swap_used_bytes,
                    "swap_free_bytes": latest.swap_free_bytes,
                    "swap_cached_bytes": latest.swap_cached_bytes,
                    "swap_percent": latest.swap_percent,
                    "swap_free_percent": latest.swap_free_percent,
                    "uptime_seconds": latest.uptime_seconds,
                    "error_message": latest.error_message,
                    "disks": disks,
                    "disk_total_bytes": disk_total_bytes,
                },
                "history": history_payload,
                "alert_periods": alert_periods,
                "range": selected_range,
            }
        )


class ServerMonitoringToggleView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        server = get_object_or_404(Server, id=pk)
        requested_enabled = request.POST.get("enabled")
        if requested_enabled is None:
            server.monitoring_enabled = not server.monitoring_enabled
        else:
            server.monitoring_enabled = requested_enabled.lower() in {"1", "true", "yes", "on"}
        server.save(update_fields=["monitoring_enabled", "updated_at"])
        schedule_server_collection(server)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "enabled": server.monitoring_enabled, "server_id": server.id})

        messages.success(
            request,
            f"Monitoring {'enabled' if server.monitoring_enabled else 'disabled'} for {server.name}.",
        )
        return redirect("servers:detail", pk=server.id)


class ServerDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        server = get_object_or_404(Server, id=pk)
        server_name = server.name

        PeriodicTask.objects.filter(name=f"collect_server_metrics_{server.id}").delete()
        server.delete()

        messages.success(request, f"Server '{server_name}' was removed.")
        return redirect("servers:dashboard")
