"""
Context processors for SSH Monitor.

Provides global template context variables.
"""


def sidebar_servers(request):
    """
    Add server list to template context for sidebar navigation.

    Returns empty list if user is not authenticated or servers app
    is not yet installed.
    """
    active_server_id = None
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match is not None:
        kwargs = resolver_match.kwargs or {}
        for key in ("pk", "server_pk"):
            value = kwargs.get(key)
            if value is not None:
                try:
                    active_server_id = int(value)
                    break
                except (TypeError, ValueError):
                    pass

    if not request.user.is_authenticated:
        return {"sidebar_servers": [], "active_server_id": active_server_id}

    try:
        from apps.servers.models import Server

        servers = Server.objects.only("id", "name", "connection_status").order_by("name")[:50]  # Limit for performance

        return {"sidebar_servers": servers, "active_server_id": active_server_id}
    except Exception:
        # App not installed yet or other error
        return {"sidebar_servers": [], "active_server_id": active_server_id}
