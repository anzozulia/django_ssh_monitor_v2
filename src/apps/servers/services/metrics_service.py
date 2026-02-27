from typing import Any

from apps.servers.services.ssh_service import SSHService


class MetricsService:
    @staticmethod
    def parse_loadavg(output: str) -> dict[str, float]:
        parts = output.strip().split()
        return {
            "load_1min": float(parts[0]),
            "load_5min": float(parts[1]),
            "load_15min": float(parts[2]),
        }

    @staticmethod
    def parse_meminfo(output: str) -> dict[str, int | float]:
        values_kb: dict[str, int] = {}
        for line in output.splitlines():
            if ":" not in line:
                continue
            key, raw_value = line.split(":", 1)
            number_part = raw_value.strip().split()[0]
            if number_part.isdigit():
                values_kb[key] = int(number_part)

        mem_total = values_kb.get("MemTotal", 0) * 1024
        mem_free = values_kb.get("MemFree", 0) * 1024
        mem_available = values_kb.get("MemAvailable", 0) * 1024
        mem_buffers = values_kb.get("Buffers", 0) * 1024
        mem_cached = (values_kb.get("Cached", 0) + values_kb.get("SReclaimable", 0)) * 1024
        mem_shared = values_kb.get("Shmem", 0) * 1024
        mem_used = max(mem_total - mem_available, 0)

        swap_total = values_kb.get("SwapTotal", 0) * 1024
        swap_free = values_kb.get("SwapFree", 0) * 1024
        swap_cached = values_kb.get("SwapCached", 0) * 1024
        swap_used = max(swap_total - swap_free, 0)

        return {
            "ram_total_bytes": mem_total,
            "ram_used_bytes": mem_used,
            "ram_free_bytes": mem_free,
            "ram_available_bytes": mem_available,
            "ram_cached_bytes": mem_cached,
            "ram_buffers_bytes": mem_buffers,
            "ram_shared_bytes": mem_shared,
            "ram_percent": (mem_used / mem_total * 100) if mem_total else 0.0,
            "ram_free_percent": (mem_free / mem_total * 100) if mem_total else 0.0,
            "ram_available_percent": (mem_available / mem_total * 100) if mem_total else 0.0,
            "swap_total_bytes": swap_total,
            "swap_used_bytes": swap_used,
            "swap_free_bytes": swap_free,
            "swap_cached_bytes": swap_cached,
            "swap_percent": (swap_used / swap_total * 100) if swap_total else 0.0,
            "swap_free_percent": (swap_free / swap_total * 100) if swap_total else 0.0,
        }

    @staticmethod
    def parse_df(output: str) -> list[dict[str, Any]]:
        disks: list[dict[str, Any]] = []
        for line in output.splitlines()[1:]:
            parts = line.split()
            if len(parts) < 7:
                continue
            filesystem = parts[0]
            total_kb = int(parts[2])
            used_kb = int(parts[3])
            available_kb = int(parts[4])
            percent = float(parts[5].rstrip("%"))
            mount = parts[6]
            disks.append(
                {
                    "filesystem": filesystem,
                    "mount_point": mount,
                    "total_bytes": total_kb * 1024,
                    "used_bytes": used_kb * 1024,
                    "available_bytes": available_kb * 1024,
                    "percent": percent,
                }
            )
        return disks

    @staticmethod
    def parse_uptime_seconds(output: str) -> int:
        return int(float(output.strip()))

    def collect_metrics(self, ssh_service: SSHService) -> dict[str, Any]:
        load_out = ssh_service.execute_command("cat /proc/loadavg")
        cpu_cores_out = ssh_service.execute_command("nproc")
        meminfo_out = ssh_service.execute_command("cat /proc/meminfo")
        df_out = ssh_service.execute_command("df -kPT")
        uptime_out = ssh_service.execute_command("cat /proc/uptime | awk '{print $1}'")

        metrics = {}
        metrics.update(self.parse_loadavg(load_out))
        metrics["cpu_cores"] = int(cpu_cores_out.strip())
        metrics.update(self.parse_meminfo(meminfo_out))
        metrics["uptime_seconds"] = self.parse_uptime_seconds(uptime_out)
        metrics["disk_metrics"] = self.parse_df(df_out)
        return metrics
