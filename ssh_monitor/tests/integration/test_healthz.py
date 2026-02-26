import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_healthz_is_public(client, monkeypatch):
    from apps.core import views

    monkeypatch.setattr(views, "_check_database", lambda: (True, "ok"))
    monkeypatch.setattr(views, "_check_redis", lambda: (True, "ok"))

    response = client.get(reverse("healthz"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_healthz_returns_expected_shape(client, monkeypatch):
    from apps.core import views

    monkeypatch.setattr(views, "_check_database", lambda: (True, "ok"))
    monkeypatch.setattr(views, "_check_redis", lambda: (True, "ok"))

    response = client.get(reverse("healthz"))
    payload = response.json()

    assert payload["status"] == "ok"
    assert "checks" in payload
    assert "database" in payload["checks"]
    assert "redis" in payload["checks"]


@pytest.mark.django_db
def test_healthz_returns_503_when_any_check_fails(client, monkeypatch):
    from apps.core import views

    monkeypatch.setattr(views, "_check_database", lambda: (False, "db down"))
    monkeypatch.setattr(views, "_check_redis", lambda: (True, "ok"))

    response = client.get(reverse("healthz"))
    payload = response.json()

    assert response.status_code == 503
    assert payload["status"] == "degraded"
