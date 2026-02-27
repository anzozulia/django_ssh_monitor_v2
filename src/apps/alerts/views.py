"""
Alert management views for SSH Monitor.
"""

from datetime import datetime, time

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views import View

from apps.alerts.forms import AlertRuleForm
from apps.alerts.models import AlertEvent, AlertRule, EventType, MetricType
from apps.servers.models import Server


def _to_aware_dt(date_str: str | None, *, end_of_day: bool) -> datetime | None:
    if not date_str:
        return None
    parsed = parse_date(date_str)
    if not parsed:
        return None
    target_time = time.max if end_of_day else time.min
    dt = datetime.combine(parsed, target_time)
    return timezone.make_aware(dt, timezone.get_current_timezone())


def _build_history_context(request, *, server: Server | None = None) -> dict:
    queryset = AlertEvent.objects.select_related("server", "alert_rule").all()
    if server is not None:
        queryset = queryset.filter(server=server)

    server_id = request.GET.get("server")
    if server_id and server is None:
        queryset = queryset.filter(server_id=server_id)

    event_type = request.GET.get("event_type", "").strip()
    if event_type in {choice[0] for choice in EventType.choices}:
        queryset = queryset.filter(event_type=event_type)

    metric_type = request.GET.get("metric_type", "").strip()
    if metric_type in {choice[0] for choice in MetricType.choices}:
        queryset = queryset.filter(alert_rule__metric_type=metric_type)

    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    start_dt = _to_aware_dt(date_from, end_of_day=False)
    end_dt = _to_aware_dt(date_to, end_of_day=True)
    if start_dt:
        queryset = queryset.filter(created_at__gte=start_dt)
    if end_dt:
        queryset = queryset.filter(created_at__lte=end_dt)

    paginator = Paginator(queryset.order_by("-created_at"), 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "events": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "event_type_choices": EventType.choices,
        "metric_type_choices": MetricType.choices,
        "servers": Server.objects.only("id", "name").order_by("name"),
        "filters": {
            "server": server_id if server is None else str(server.id),
            "event_type": event_type,
            "metric_type": metric_type,
            "date_from": date_from,
            "date_to": date_to,
        },
    }
    if server is not None:
        context["server"] = server
    return context


class AlertHistoryView(LoginRequiredMixin, View):
    template_name = "alerts/history.html"

    def get(self, request):
        context = _build_history_context(request)
        return render(request, self.template_name, context)


class ServerAlertHistoryView(LoginRequiredMixin, View):
    template_name = "alerts/server_history.html"

    def get(self, request, server_pk: int):
        server = get_object_or_404(Server, id=server_pk)
        context = _build_history_context(request, server=server)
        return render(request, self.template_name, context)


class DefaultAlertListView(LoginRequiredMixin, View):
    template_name = "alerts/default_list.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"templates": AlertRule.objects.filter(is_default_template=True, server__isnull=True)},
        )


class DefaultAlertCreateView(LoginRequiredMixin, View):
    template_name = "alerts/alert_form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": AlertRuleForm(), "mode": "create", "is_default_template": True},
        )

    def post(self, request):
        form = AlertRuleForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"form": form, "mode": "create", "is_default_template": True},
            )
        template = form.save(commit=False)
        template.server = None
        template.is_default_template = True
        template.enabled = True
        template.current_state = "normal"
        template.triggered_at = None
        template.last_reminder_at = None
        template.condition_cleared_at = None
        template.save()
        messages.success(request, "Default alert template created.")
        return redirect("alerts:defaults")


class DefaultAlertUpdateView(LoginRequiredMixin, View):
    template_name = "alerts/alert_form.html"

    def get(self, request, pk: int):
        template = get_object_or_404(AlertRule, id=pk, is_default_template=True, server__isnull=True)
        return render(
            request,
            self.template_name,
            {
                "form": AlertRuleForm(instance=template),
                "template_obj": template,
                "mode": "edit",
                "is_default_template": True,
            },
        )

    def post(self, request, pk: int):
        template = get_object_or_404(AlertRule, id=pk, is_default_template=True, server__isnull=True)
        form = AlertRuleForm(request.POST, instance=template)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {
                    "form": form,
                    "template_obj": template,
                    "mode": "edit",
                    "is_default_template": True,
                },
            )
        template = form.save(commit=False)
        template.server = None
        template.is_default_template = True
        template.enabled = True
        template.save()
        messages.success(request, "Default alert template updated.")
        return redirect("alerts:defaults")


class DefaultAlertDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        template = get_object_or_404(AlertRule, id=pk, is_default_template=True, server__isnull=True)
        template.delete()
        messages.success(request, "Default alert template deleted.")
        return redirect("alerts:defaults")


class AlertRuleCreateView(LoginRequiredMixin, View):
    template_name = "alerts/alert_form.html"

    def get(self, request, server_pk: int):
        server = get_object_or_404(Server, id=server_pk)
        return render(
            request,
            self.template_name,
            {"server": server, "form": AlertRuleForm(), "mode": "create"},
        )

    def post(self, request, server_pk: int):
        server = get_object_or_404(Server, id=server_pk)
        form = AlertRuleForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"server": server, "form": form, "mode": "create"},
            )
        rule = form.save(commit=False)
        rule.server = server
        rule.save()
        messages.success(request, "Alert rule created.")
        return redirect("servers:detail", pk=server.id)


class AlertRuleUpdateView(LoginRequiredMixin, View):
    template_name = "alerts/alert_form.html"

    def get(self, request, pk: int):
        rule = get_object_or_404(AlertRule, id=pk)
        return render(
            request,
            self.template_name,
            {"server": rule.server, "rule": rule, "form": AlertRuleForm(instance=rule), "mode": "edit"},
        )

    def post(self, request, pk: int):
        rule = get_object_or_404(AlertRule, id=pk)
        form = AlertRuleForm(request.POST, instance=rule)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"server": rule.server, "rule": rule, "form": form, "mode": "edit"},
            )
        form.save()
        messages.success(request, "Alert rule updated.")
        return redirect("servers:detail", pk=rule.server_id)


class AlertRuleDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        rule = get_object_or_404(AlertRule, id=pk)
        server_id = rule.server_id
        rule.delete()
        messages.success(request, "Alert rule deleted.")
        return redirect("servers:detail", pk=server_id)


class AlertRuleToggleView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        rule = get_object_or_404(AlertRule, id=pk)
        # SSH connectivity rule is non-configurable and must always stay enabled.
        if rule.metric_type == "custom" and rule.metric_param == "ssh_connectivity":
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "SSH connectivity rule cannot be disabled.",
                        "enabled": True,
                    },
                    status=400,
                )
            messages.error(request, "SSH connectivity rule cannot be disabled.")
            return redirect("servers:detail", pk=rule.server_id)

        requested_enabled = request.POST.get("enabled")
        if requested_enabled is None:
            rule.enabled = not rule.enabled
        else:
            rule.enabled = requested_enabled.lower() in {"1", "true", "yes", "on"}
        rule.save(update_fields=["enabled", "updated_at"])

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "enabled": rule.enabled, "rule_id": rule.id})

        messages.success(request, f"Alert {'enabled' if rule.enabled else 'disabled'}.")
        return redirect("servers:detail", pk=rule.server_id)
