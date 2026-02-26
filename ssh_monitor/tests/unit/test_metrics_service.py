from apps.servers.services.metrics_service import MetricsService


def test_parse_loadavg():
    svc = MetricsService()
    parsed = svc.parse_loadavg("0.31 0.22 0.15 1/120 3214")
    assert parsed["load_1min"] == 0.31
    assert parsed["load_5min"] == 0.22
    assert parsed["load_15min"] == 0.15


def test_parse_meminfo():
    svc = MetricsService()
    output = (
        "MemTotal:        8028160 kB\n"
        "MemFree:          928324 kB\n"
        "MemAvailable:    4625780 kB\n"
        "Buffers:          125000 kB\n"
        "Cached:          3500000 kB\n"
        "SReclaimable:     589304 kB\n"
        "Shmem:            112344 kB\n"
        "SwapCached:       111120 kB\n"
        "SwapTotal:       2097148 kB\n"
        "SwapFree:        1986028 kB\n"
    )
    parsed = svc.parse_meminfo(output)
    assert parsed["ram_total_bytes"] == 8028160 * 1024
    assert parsed["ram_available_bytes"] == 4625780 * 1024
    assert parsed["ram_free_bytes"] == 928324 * 1024
    assert parsed["ram_cached_bytes"] == (3500000 + 589304) * 1024
    assert parsed["swap_total_bytes"] == 2097148 * 1024
    assert parsed["swap_free_bytes"] == 1986028 * 1024


def test_parse_df():
    svc = MetricsService()
    output = (
        "Filesystem     Type 1024-blocks      Used Available Capacity Mounted on\n"
        "/dev/sda1      ext4   41151808  9203816  29917856      24% /\n"
        "tmpfs          tmpfs   4014080        16   4014064       1% /run\n"
    )
    disks = svc.parse_df(output)
    assert len(disks) == 2
    assert disks[0]["filesystem"] == "/dev/sda1"
    assert disks[0]["mount_point"] == "/"
    assert disks[0]["available_bytes"] == 29917856 * 1024
