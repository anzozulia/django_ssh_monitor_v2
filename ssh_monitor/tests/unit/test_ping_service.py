from unittest.mock import MagicMock, patch

from apps.servers.services.ping_service import PingService


@patch("apps.servers.services.ping_service.subprocess.run")
def test_ping_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    assert PingService.ping("example.com") is True


@patch("apps.servers.services.ping_service.subprocess.run")
def test_ping_failure(mock_run):
    mock_run.return_value = MagicMock(returncode=1)
    assert PingService.ping("example.com") is False
