from celery import shared_task

from apps.alerts.services.evaluation_service import AlertEvaluationService
from apps.servers.models import Server


@shared_task
def evaluate_server_alerts(server_id: int) -> None:
    server = Server.objects.get(id=server_id)
    AlertEvaluationService().evaluate_server_alerts(server)
