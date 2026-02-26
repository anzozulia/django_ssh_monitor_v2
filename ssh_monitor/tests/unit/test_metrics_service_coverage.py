from apps.servers.services.metrics_service import MetricsService


class DummySsh:
    def __init__(self):
        self.responses = {
            "cat /proc/loadavg": "0.10 0.20 0.30 1/100 10",
            "nproc": "4\n",
            "cat /proc/meminfo": (
                "MemTotal: 1000 kB\n"
                "MemFree: 300 kB\n"
                "MemAvailable: 500 kB\n"
                "Buffers: 50 kB\n"
                "Cached: 100 kB\n"
                "SReclaimable: 20 kB\n"
                "Shmem: 10 kB\n"
                "SwapCached: 3 kB\n"
                "SwapTotal: 200 kB\n"
                "SwapFree: 100 kB\n"
            ),
            "df -kPT": (
                "Filesystem Type 1024-blocks Used Available Capacity Mounted on\n"
                "/dev/sda1 ext4 1000 200 800 20% /\n"
            ),
            "cat /proc/uptime | awk '{print $1}'": "123.45",
        }

    def execute_command(self, command: str) -> str:
        return self.responses[command]


def test_collect_metrics_aggregates_all_commands():
    svc = MetricsService()
    metrics = svc.collect_metrics(DummySsh())
    assert metrics["load_1min"] == 0.10
    assert metrics["cpu_cores"] == 4
    assert metrics["ram_total_bytes"] == 1000 * 1024
    assert metrics["uptime_seconds"] == 123
    assert len(metrics["disk_metrics"]) == 1


def test_parse_df_skips_invalid_rows_and_parse_uptime_seconds():
    svc = MetricsService()
    output = "Filesystem Type 1024-blocks Used Available Capacity Mounted on\nbroken row\n"
    assert svc.parse_df(output) == []
    assert svc.parse_uptime_seconds("42.8") == 42
