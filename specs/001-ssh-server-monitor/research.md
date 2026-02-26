# Research: SSH Server Monitor

**Feature**: 001-ssh-server-monitor  
**Date**: 2026-02-03

## SSH Library Selection

### Decision: Paramiko

### Rationale
Paramiko is the most mature and widely-used Python SSH library. For a Django application with Celery background tasks, synchronous SSH operations are acceptable because:
1. SSH calls happen in Celery workers, not web request threads
2. Each server has its own scheduled task, providing natural parallelism
3. Simpler code without async/await complexity

### Alternatives Considered

| Library | Pros | Cons | Verdict |
|---------|------|------|---------|
| **Paramiko** | Mature, well-documented, native key generation, sync model fits Celery | Blocking I/O | ✅ Selected |
| **AsyncSSH** | Native asyncio, better for high concurrency | Requires async Django views, more complex | ❌ Overkill for 50 servers |
| **Fabric** | Higher-level API, easier commands | Less control over connections, depends on Paramiko anyway | ❌ Unnecessary abstraction |
| **parallel-ssh** | Built for parallel execution | Different use case (batch operations) | ❌ Not a fit |

### Key Paramiko Features We'll Use

```python
# Key generation
from paramiko import RSAKey
key = RSAKey.generate(4096)
key.write_private_key_file('/path/to/key')
public_key = f"ssh-rsa {key.get_base64()}"

# Password authentication
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname, port, username, password=password)

# Key file authentication
private_key = RSAKey.from_private_key_file('/path/to/key')
ssh.connect(hostname, port, username, pkey=private_key)

# Command execution
stdin, stdout, stderr = ssh.exec_command('cat /proc/loadavg')
output = stdout.read().decode()
```

## Background Task Scheduling

### Decision: Celery + django-celery-beat + Redis

### Rationale
- **Dynamic scheduling**: Each server has configurable check intervals (1 min to 24 hours)
- **Database-backed schedules**: django-celery-beat stores schedules in PostgreSQL, allowing runtime changes
- **Single scheduler**: Celery beat ensures no duplicate task execution
- **Proven stack**: Celery is the de-facto Django background task solution

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Django Web    │────▶│     Redis       │◀────│  Celery Beat    │
│   (Gunicorn)    │     │    (Broker)     │     │  (Scheduler)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │ Celery Workers  │
                        │ (SSH + Alerts)  │
                        └─────────────────┘
```

### Task Design

```python
# Per-server monitoring task
@shared_task
def collect_server_metrics(server_id: int) -> dict:
    """Collect metrics for a single server via SSH."""
    server = Server.objects.get(id=server_id)
    metrics = ssh_service.collect_metrics(server)
    MetricSnapshot.objects.create(server=server, **metrics)
    return metrics

# Dynamic scheduling via django-celery-beat
# When server is created/updated, create/update PeriodicTask
PeriodicTask.objects.update_or_create(
    name=f'monitor-server-{server.id}',
    defaults={
        'task': 'servers.tasks.collect_server_metrics',
        'interval': IntervalSchedule.objects.get_or_create(
            every=server.check_interval_minutes,
            period=IntervalSchedule.MINUTES
        )[0],
        'args': json.dumps([server.id]),
        'enabled': server.monitoring_enabled,
    }
)
```

## Frontend Stack

### Decision: Tailwind CSS + ApexCharts + Vanilla JS

### Rationale
- **Tailwind CSS**: Utility-first CSS for rapid admin panel styling
- **ApexCharts**: Better visual alignment with TailAdmin design patterns
- **Vanilla JS**: Simple polling without SPA complexity

### Tailwind Setup

Using Tailwind CSS v4 via `@tailwindcss/cli` for:
- JIT compilation during development
- Purged CSS for production builds
- Integration with Django's static files

### ApexCharts Integration

```javascript
// Unified rendering function for initial load and polling updates
function renderMetricsChart(containerId, metricsData) {
    const container = document.getElementById(containerId);
    if (!container || !window.ApexCharts) return;

    if (window.charts && window.charts[containerId]) {
        window.charts[containerId].destroy();
    }

    window.charts = window.charts || {};
    window.charts[containerId] = new ApexCharts(container, {
        chart: { type: "area", height: 220, animations: { enabled: false } },
        series: [{ name: metricsData.label, data: metricsData.points }],
        xaxis: { type: "datetime" },
        stroke: { curve: "smooth" }
    });
    window.charts[containerId].render();
}

// Polling logic
async function pollMetrics(serverId) {
    const response = await fetch(`/servers/${serverId}/metrics/`);
    const data = await response.json();
    
    // Same rendering logic for polled data
    renderMetricsChart('cpu-chart', data.cpu);
    renderMetricsChart('ram-chart', data.ram);
    // ... etc
}
```

## Metric Collection Commands

### Linux Commands for Metrics

| Metric | Command | Output Parsing |
|--------|---------|----------------|
| CPU Load | `cat /proc/loadavg` | First 3 values: 1/5/15 min averages |
| RAM/Swap | `cat /proc/meminfo` | Parse key/value lines (MemTotal, MemAvailable, SwapTotal, etc.) |
| Disk | `df -kPT` | Parse filesystem, blocks, used, available, percent, mount |
| Uptime | `cat /proc/uptime \| awk '{print $1}'` | First value in seconds |

### Example Parsing

```python
def parse_loadavg(output: str) -> dict:
    """Parse /proc/loadavg output."""
    parts = output.strip().split()
    return {
        'load_1min': float(parts[0]),
        'load_5min': float(parts[1]),
        'load_15min': float(parts[2]),
    }

def parse_free(output: str) -> dict:
    """Parse 'free -b' output."""
    lines = output.strip().split('\n')
    mem_line = [l for l in lines if l.startswith('Mem:')][0]
    parts = mem_line.split()
    return {
        'ram_total': int(parts[1]),
        'ram_used': int(parts[2]),
        'ram_free': int(parts[3]),
        'ram_percent': round(int(parts[2]) / int(parts[1]) * 100, 1),
    }
```

## Credential Encryption

### Decision: Django's Fernet-based encryption

### Implementation

```python
from cryptography.fernet import Fernet
from django.conf import settings

def encrypt_credential(plaintext: str) -> str:
    """Encrypt SSH credential for storage."""
    f = Fernet(settings.CREDENTIAL_ENCRYPTION_KEY)
    return f.encrypt(plaintext.encode()).decode()

def decrypt_credential(ciphertext: str) -> str:
    """Decrypt SSH credential for use."""
    f = Fernet(settings.CREDENTIAL_ENCRYPTION_KEY)
    return f.decrypt(ciphertext.encode()).decode()
```

Key stored in environment variable `CREDENTIAL_ENCRYPTION_KEY`.

## Ping Implementation

### Decision: Python subprocess with system ping

```python
import subprocess

def ping_server(host: str, count: int = 3, timeout: int = 5) -> dict:
    """Ping server and return results."""
    try:
        result = subprocess.run(
            ['ping', '-c', str(count), '-W', str(timeout), host],
            capture_output=True,
            text=True,
            timeout=timeout * count + 5
        )
        return {
            'reachable': result.returncode == 0,
            'output': result.stdout,
        }
    except subprocess.TimeoutExpired:
        return {'reachable': False, 'output': 'Ping timeout'}
```

## Notification Channel Architecture

### Decision: Abstract base class with concrete implementations

```python
# notifications/services/base.py
from abc import ABC, abstractmethod

class NotificationChannel(ABC):
    @abstractmethod
    def send(self, message: str, severity: str) -> bool:
        """Send notification. Returns True if successful."""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate channel configuration."""
        pass

# notifications/services/telegram.py
import requests

class TelegramChannel(NotificationChannel):
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
    
    def send(self, message: str, severity: str) -> bool:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        response = requests.post(url, json={
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML',
        })
        return response.status_code == 200
```

This architecture allows easy addition of future channels (email, Slack, Discord, etc.) by implementing the abstract base class.
