import time

import pytest
from django.urls import reverse

from apps.servers.models import MetricSnapshot, Server


@pytest.mark.django_db
def test_dashboard_handles_fifty_servers_without_major_delay(authenticated_client):
    servers = [
        Server(
            name=f"load-{idx}",
            host=f"10.20.0.{idx}",
            port=22,
            ssh_username="root",
            auth_type="password",
            credentials_encrypted="gAAAAA",
            connection_status="online",
        )
        for idx in range(1, 51)
    ]
    Server.objects.bulk_create(servers)
    created = list(Server.objects.all())
    MetricSnapshot.objects.bulk_create(
        [
            MetricSnapshot(
                server=server,
                load_1min=0.1,
                ram_percent=35.0,
                swap_percent=1.0,
                error_message="",
            )
            for server in created
        ]
    )

    start = time.perf_counter()
    response = authenticated_client.get(reverse("servers:dashboard"))
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    # SC-002 proxy check: dashboard remains responsive with 50 monitored servers.
    assert elapsed < 3.0
