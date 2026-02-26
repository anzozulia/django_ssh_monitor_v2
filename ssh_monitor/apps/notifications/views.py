"""Notification channel views for SSH Monitor."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.notifications.forms import TelegramConfigForm
from apps.notifications.models import ChannelType, NotificationChannel, ValidationStatus
from apps.notifications.services.telegram import TelegramChannel


class ChannelListView(LoginRequiredMixin, View):
    template_name = "notifications/channel_list.html"

    def get(self, request):
        NotificationChannel.objects.get_or_create(channel_type=ChannelType.TELEGRAM)
        channels = NotificationChannel.objects.all()
        return render(request, self.template_name, {"channels": channels})


class TelegramConfigView(LoginRequiredMixin, View):
    template_name = "notifications/telegram_config.html"

    def get(self, request):
        channel, _ = NotificationChannel.objects.get_or_create(channel_type=ChannelType.TELEGRAM)
        config = channel.get_config()
        form = TelegramConfigForm(
            initial={
                "bot_token": config.get("bot_token", ""),
                "chat_id": config.get("chat_id", ""),
            }
        )
        return render(request, self.template_name, {"form": form, "channel": channel})

    def post(self, request):
        channel, _ = NotificationChannel.objects.get_or_create(channel_type=ChannelType.TELEGRAM)
        form = TelegramConfigForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "channel": channel})

        channel.set_config(
            {
                "bot_token": form.cleaned_data["bot_token"],
                "chat_id": form.cleaned_data["chat_id"],
            }
        )
        channel.validation_status = ValidationStatus.PENDING
        channel.save(update_fields=["config_encrypted", "validation_status", "updated_at"])
        messages.success(request, "Telegram configuration saved.")
        return redirect("notifications:telegram-config")


class TelegramTestView(LoginRequiredMixin, View):
    def post(self, request):
        channel = NotificationChannel.objects.filter(channel_type=ChannelType.TELEGRAM).first()
        if not channel:
            messages.error(request, "Telegram channel is not configured.")
            return redirect("notifications:telegram-config")

        config = channel.get_config()
        backend = TelegramChannel(
            bot_token=config.get("bot_token", ""),
            chat_id=config.get("chat_id", ""),
        )
        ok, error = backend.validate_config()
        channel.mark_validation(ok)
        channel.save(update_fields=["last_validated_at", "validation_status", "updated_at"])

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": ok, "error": error})

        if ok:
            messages.success(request, "Telegram test message sent successfully.")
        else:
            messages.error(request, f"Telegram test failed: {error}")
        return redirect("notifications:telegram-config")


class ChannelToggleView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        channel = get_object_or_404(NotificationChannel, id=pk)
        requested_enabled = request.POST.get("enabled")
        if requested_enabled is None:
            channel.enabled = not channel.enabled
        else:
            channel.enabled = requested_enabled.lower() in {"1", "true", "yes", "on"}
        channel.save(update_fields=["enabled", "updated_at"])

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "enabled": channel.enabled, "channel_id": channel.id})

        messages.success(
            request,
            f"{channel.get_channel_type_display()} channel {'enabled' if channel.enabled else 'disabled'}.",
        )
        return redirect("notifications:list")
