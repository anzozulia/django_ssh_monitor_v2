from datetime import timedelta

import pytest
from django.utils import timezone

from apps.servers.models import DiskMetric, MetricSnapshot, Server
from apps.servers.views import _build_history_payload, _resolve_history_range


@pytest.mark.django_db
def test_resolve_history_range_falls_back_to_default():
    assert _resolve_history_range("6h") == "6h"
    assert _resolve_history_range("weird") == "24h"
    assert _resolve_history_range(None) == "24h"


@pytest.mark.django_db
def test_build_history_payload_uses_selected_time_window_and_disk_max():
    server = Server.objects.create(
        name="hist-server",
        host="10.0.0.31",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
    )
    old = MetricSnapshot.objects.create(
        server=server,
        load_1min=0.1,
        ram_percent=10.0,
        swap_percent=1.0,
    )
    recent = MetricSnapshot.objects.create(
        server=server,
        load_1min=0.6,
        ram_percent=35.0,
        swap_percent=5.0,
    )
    DiskMetric.objects.create(
        snapshot=recent,
        mount_point="/",
        filesystem="ext4",
        total_bytes=100,
        used_bytes=30,
        available_bytes=70,
        percent=30.0,
    )
    DiskMetric.objects.create(
        snapshot=recent,
        mount_point="/var",
        filesystem="ext4",
        total_bytes=100,
        used_bytes=80,
        available_bytes=20,
        percent=80.0,
    )

    now = timezone.now()
    MetricSnapshot.objects.filter(id=old.id).update(timestamp=now - timedelta(days=2))
    MetricSnapshot.objects.filter(id=recent.id).update(timestamp=now - timedelta(hours=2))

    payload = _build_history_payload(server, "24h")
    assert payload["range"] == "24h"
    assert len(payload["timestamps"]) == 1
    assert payload["load_1min"] == [0.6]
    assert payload["ram_percent"] == [35.0]
    assert payload["swap_percent"] == [5.0]
    assert payload["disk_percent"] == [80.0]
