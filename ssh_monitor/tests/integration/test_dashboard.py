import pytest
from django.urls import reverse

from apps.servers.models import Server


@pytest.mark.django_db
def test_dashboard_renders_servers_table_and_clickable_row(authenticated_client):
    server = Server.objects.create(
        name="web-1",
        host="10.0.0.61",
        port=22,
        ssh_username="root",
        auth_type="password",
        credentials_encrypted="gAAAAA",
        connection_status="online",
    )
    response = authenticated_client.get(reverse("servers:dashboard"))
    assert response.status_code == 200
    content = response.content.decode()
    assert "All Servers" in content
    assert "Servers Health Overview" in content
    assert server.name in content
    assert reverse("servers:detail", kwargs={"pk": server.id}) in content
