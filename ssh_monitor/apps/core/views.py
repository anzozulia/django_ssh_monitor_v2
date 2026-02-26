from __future__ import annotations

import redis
from django.conf import settings
from django.db import connections
from django.http import JsonResponse


def _check_database() -> tuple[bool, str]:
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
        return True, "ok"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _check_redis() -> tuple[bool, str]:
    broker_url = getattr(settings, "CELERY_BROKER_URL", "")
    if not broker_url:
        return False, "CELERY_BROKER_URL is empty"

    try:
        client = redis.from_url(broker_url)
        if client.ping():
            return True, "ok"
        return False, "ping failed"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def healthz(request):
    db_ok, db_message = _check_database()
    redis_ok, redis_message = _check_redis()

    overall_ok = db_ok and redis_ok
    payload = {
        "status": "ok" if overall_ok else "degraded",
        "checks": {
            "database": {"ok": db_ok, "message": db_message},
            "redis": {"ok": redis_ok, "message": redis_message},
        },
    }
    return JsonResponse(payload, status=200 if overall_ok else 503)
