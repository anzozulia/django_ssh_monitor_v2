import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_core_views_require_authentication(client):
    protected_urls = [
        reverse("servers:dashboard"),
        reverse("servers:create"),
        reverse("alerts:history"),
        reverse("notifications:list"),
    ]
    for url in protected_urls:
        response = client.get(url)
        assert response.status_code in (301, 302)
        assert reverse("accounts:login") in response.url
