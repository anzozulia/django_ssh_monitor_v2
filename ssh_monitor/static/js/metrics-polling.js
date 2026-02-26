function formatUptime(seconds) {
  if (seconds == null) return "-";
  const total = Number(seconds);
  const days = Math.floor(total / 86400);
  const hours = Math.floor((total % 86400) / 3600);
  const mins = Math.floor((total % 3600) / 60);
  return `${days}d ${hours}h ${mins}m`;
}

function formatMetricNumber(value, suffix = "") {
  if (value == null || value === "") return "-";
  const n = Number(value);
  if (Number.isNaN(n)) return "-";
  return `${n.toFixed(2)}${suffix}`;
}

function formatBytes(value) {
  if (value == null || value === "") return "-";
  const bytes = Number(value);
  if (!Number.isFinite(bytes)) return "-";
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  let unitIdx = 0;
  let scaled = bytes;
  while (scaled >= 1024 && unitIdx < units.length - 1) {
    scaled /= 1024;
    unitIdx += 1;
  }
  return `${scaled.toFixed(2)} ${units[unitIdx]}`;
}

function formatPartPercent(part, total) {
  if (part == null || total == null) return "(-)";
  const p = Number(part);
  const t = Number(total);
  if (!Number.isFinite(p) || !Number.isFinite(t) || t <= 0) return "(-)";
  return `(${((p / t) * 100).toFixed(2)}%)`;
}

function toNumericSeries(values) {
  return (values || []).map((v) => (v == null || Number.isNaN(Number(v)) ? null : Number(v)));
}

function toTimestampPoints(timestamps, values) {
  const ts = timestamps || [];
  const vals = toNumericSeries(values);
  return ts
    .map((item, idx) => {
      const x = Date.parse(item);
      const y = vals[idx];
      if (!Number.isFinite(x)) return null;
      return { x, y };
    })
    .filter((point) => point && point.y != null);
}

function ensureChartRegistry() {
  if (!window.metricsCharts) window.metricsCharts = {};
}

function buildAlertAnnotations(alertPeriods) {
  return (alertPeriods || [])
    .map((period) => {
      const x = Date.parse(period.start);
      const x2 = Date.parse(period.end);
      if (!Number.isFinite(x) || !Number.isFinite(x2)) return null;
      return {
        x,
        x2,
        borderColor: "transparent",
        // Keep overlays visible but subtle to avoid overpowering chart styling.
        fillColor: period.severity === "critical" ? "#ef4444" : "#3b82f6",
        opacity: 0.06,
      };
    })
    .filter(Boolean);
}

function createTailAdminLineChart(containerId, label, color, points, alertPeriods, suffix = "") {
  const el = document.getElementById(containerId);
  if (!el || !window.ApexCharts) return null;
  const isPercentChart = suffix === "%";
  const options = {
    chart: {
      type: "area",
      height: 220,
      fontFamily: "Outfit, sans-serif",
      toolbar: { show: false },
      zoom: { enabled: false },
      animations: { enabled: false },
    },
    series: [{ name: label, data: points.map((p) => [p.x, p.y]) }],
    stroke: { curve: "smooth", width: 2, colors: [color] },
    fill: {
      type: "gradient",
      gradient: { opacityFrom: 0.12, opacityTo: 0.01, shadeIntensity: 0.4, stops: [0, 100] },
      colors: [color],
    },
    dataLabels: { enabled: false },
    markers: { size: 0, hover: { sizeOffset: 3 } },
    grid: {
      borderColor: "#e5e7eb",
      strokeDashArray: 3,
      xaxis: { lines: { show: false } },
      yaxis: { lines: { show: true } },
    },
    xaxis: {
      type: "datetime",
      labels: {
        style: { colors: "#6b7280", fontSize: "12px" },
        datetimeUTC: false,
        datetimeFormatter: {
          year: "MMM yyyy",
          month: "dd MMM",
          day: "dd MMM",
          hour: "HH:mm",
          minute: "HH:mm",
          second: "HH:mm",
        },
      },
      axisBorder: { color: "#e5e7eb" },
      axisTicks: { color: "#e5e7eb" },
      tooltip: { enabled: false },
      crosshairs: {
        show: false,
      },
    },
    yaxis: {
      min: isPercentChart ? 0 : undefined,
      max: isPercentChart ? 100 : undefined,
      forceNiceScale: !isPercentChart,
      labels: {
        style: { colors: "#6b7280", fontSize: "12px" },
        formatter: (value) => `${Number(value).toFixed(2)}${suffix}`,
      },
    },
    tooltip: {
      x: { format: "dd MMM yyyy HH:mm" },
      y: { formatter: (value) => `${Number(value).toFixed(2)}${suffix}` },
      theme: "light",
    },
    annotations: {
      xaxis: buildAlertAnnotations(alertPeriods),
    },
    legend: { show: false },
    noData: { text: "No metrics yet" },
  };
  const chart = new window.ApexCharts(el, options);
  chart.render();
  return chart;
}

function renderMetricsChart(containerId, history, seriesKey, label, color, alertPeriods, suffix = "") {
  if (!window.ApexCharts) return;
  const el = document.getElementById(containerId);
  if (!el) return;
  const points = toTimestampPoints(history.timestamps, history[seriesKey]);
  const isPercentChart = suffix === "%";
  ensureChartRegistry();
  const existing = window.metricsCharts[containerId];
  if (existing) {
    existing.updateSeries([{ name: label, data: points.map((p) => [p.x, p.y]) }], false);
    existing.updateOptions(
      {
        annotations: { xaxis: buildAlertAnnotations(alertPeriods) },
        yaxis: {
          min: isPercentChart ? 0 : undefined,
          max: isPercentChart ? 100 : undefined,
          forceNiceScale: !isPercentChart,
          labels: {
            formatter: (value) => `${Number(value).toFixed(2)}${suffix}`,
          },
        },
        tooltip: {
          y: {
            formatter: (value) => `${Number(value).toFixed(2)}${suffix}`,
          },
        },
      },
      false,
      false,
      false
    );
    return;
  }
  window.metricsCharts[containerId] = createTailAdminLineChart(
    containerId,
    label,
    color,
    points,
    alertPeriods,
    suffix
  );
}

function renderHistoryCharts(history, alertPeriods) {
  if (!history) return;
  renderMetricsChart("chart-cpu", history, "load_1min", "CPU Load (1m)", "#3b82f6", alertPeriods);
  renderMetricsChart("chart-ram", history, "ram_percent", "RAM Usage", "#10b981", alertPeriods, "%");
  renderMetricsChart("chart-swap", history, "swap_percent", "Swap Usage", "#8b5cf6", alertPeriods, "%");
  renderMetricsChart("chart-disk", history, "disk_percent", "Top Disk Usage", "#f59e0b", alertPeriods, "%");
}

function renderMetrics(latest) {
  if (!latest) return;
  const loadEl = document.getElementById("metric-load");
  const ramEl = document.getElementById("metric-ram");
  const ramAvailableEl = document.getElementById("metric-ram-available");
  const swapEl = document.getElementById("metric-swap");
  const uptimeEl = document.getElementById("metric-uptime");
  const cpuCoresEl = document.getElementById("metric-cpu-cores");
  const ramTotalEl = document.getElementById("metric-ram-total");
  const swapTotalEl = document.getElementById("metric-swap-total");
  const diskTotalEl = document.getElementById("metric-disk-total");
  const ramUsedAbsEl = document.getElementById("metric-ram-used-abs");
  const ramUsedPctEl = document.getElementById("metric-ram-used-pct");
  const ramFreeAbsEl = document.getElementById("metric-ram-free-abs");
  const ramFreePctEl = document.getElementById("metric-ram-free-pct");
  const ramAvailableAbsEl = document.getElementById("metric-ram-available-abs");
  const ramAvailablePctEl = document.getElementById("metric-ram-available-pct");
  const ramCacheAbsEl = document.getElementById("metric-ram-cache-abs");
  const ramCachePctEl = document.getElementById("metric-ram-cache-pct");
  const disksEl = document.getElementById("disks-container");
  const statusEl = document.getElementById("metrics-status");
  const updatedEl = document.getElementById("last-updated");

  if (loadEl) loadEl.textContent = formatMetricNumber(latest.load_1min);
  if (ramEl) ramEl.textContent = formatMetricNumber(latest.ram_percent, "%");
  if (ramAvailableEl) ramAvailableEl.textContent = formatMetricNumber(latest.ram_available_percent, "%");
  if (swapEl) swapEl.textContent = formatMetricNumber(latest.swap_percent, "%");
  if (uptimeEl) uptimeEl.textContent = formatUptime(latest.uptime_seconds);
  if (cpuCoresEl) cpuCoresEl.textContent = latest.cpu_cores ?? "-";
  if (ramTotalEl) ramTotalEl.textContent = formatBytes(latest.ram_total_bytes);
  if (swapTotalEl) swapTotalEl.textContent = formatBytes(latest.swap_total_bytes);
  if (diskTotalEl) diskTotalEl.textContent = formatBytes(latest.disk_total_bytes);
  if (ramUsedAbsEl) ramUsedAbsEl.textContent = formatBytes(latest.ram_used_bytes);
  if (ramUsedPctEl) ramUsedPctEl.textContent = formatPartPercent(latest.ram_used_bytes, latest.ram_total_bytes);
  if (ramFreeAbsEl) ramFreeAbsEl.textContent = formatBytes(latest.ram_free_bytes);
  if (ramFreePctEl) ramFreePctEl.textContent = formatPartPercent(latest.ram_free_bytes, latest.ram_total_bytes);
  if (ramAvailableAbsEl) ramAvailableAbsEl.textContent = formatBytes(latest.ram_available_bytes);
  if (ramAvailablePctEl) ramAvailablePctEl.textContent = formatPartPercent(latest.ram_available_bytes, latest.ram_total_bytes);
  if (ramCacheAbsEl) ramCacheAbsEl.textContent = formatBytes(latest.ram_cached_bytes);
  if (ramCachePctEl) ramCachePctEl.textContent = formatPartPercent(latest.ram_cached_bytes, latest.ram_total_bytes);
  if (statusEl) statusEl.textContent = `Collection status: ${latest.collection_status}`;
  if (updatedEl) updatedEl.textContent = `Last updated: ${new Date(latest.timestamp).toLocaleString()}`;

  if (disksEl) {
    if (latest.disks && latest.disks.length) {
      const diskCards = latest.disks
        .map(
          (d) =>
            `<div class="rounded-lg border border-gray-100 p-3 text-sm">` +
            `<div class="flex items-center justify-between"><span class="font-medium">${d.mount_point}</span><span>${formatMetricNumber(d.percent, "%")} used</span></div>` +
            `<div class="mt-1 text-xs text-gray-500">Used: ${formatBytes(d.used_bytes)} • Free: ${formatBytes(d.available_bytes)} • Total: ${formatBytes(d.total_bytes)}</div>` +
            `</div>`
        )
        .join("");
      disksEl.innerHTML = `<div class="space-y-4">${diskCards}</div>`;
    } else {
      disksEl.innerHTML = '<div class="text-sm text-gray-500">No disk metrics yet.</div>';
    }
  }
}

function initMetricsPage(config) {
  const serverId = config.serverId;
  let selectedRange = config.selectedRange || "24h";

  renderHistoryCharts(config.initialHistory || {}, config.initialAlertPeriods || []);

  const rangeButtons = document.querySelectorAll("[data-range-value]");
  const applyRangeButtonState = () => {
    rangeButtons.forEach((btn) => {
      const isActive = btn.dataset.rangeValue === selectedRange;
      btn.classList.toggle("bg-brand-500", isActive);
      btn.classList.toggle("text-white", isActive);
      btn.classList.toggle("border-brand-500", isActive);
      btn.classList.toggle("bg-white", !isActive);
      btn.classList.toggle("text-gray-700", !isActive);
      btn.classList.toggle("border-gray-300", !isActive);
    });
  };
  applyRangeButtonState();
  rangeButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      selectedRange = btn.dataset.rangeValue || "24h";
      applyRangeButtonState();
      poll();
    });
  });

  const poll = async () => {
    try {
      const params = new URLSearchParams({ range: selectedRange });
      const resp = await fetch(`/servers/${serverId}/metrics/?${params.toString()}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!resp.ok) return;
      const data = await resp.json();
      if (data.ok) {
        renderMetrics(data.latest);
        renderHistoryCharts(data.history, data.alert_periods || []);
      }
    } catch (_err) {
      // Keep silent in UI; polling retries on next tick.
    }
  };

  poll();
  setInterval(poll, 15000);
}

window.initMetricsPage = initMetricsPage;
