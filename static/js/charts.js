// ==========================================================================
// AQUAGUARD AI — MONOCHROME CHART FACTORY (Chart.js 4.4)
// White/grey line, grey dashed baselines, white circles, red-muted markers
// ==========================================================================

if (window.Chart) {
  Chart.defaults.color = '#9b9b9b';
  Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.font.size = 11.5;
  Chart.defaults.animation = { duration: 800, easing: 'easeOutQuart' };
}

const HOLO_TOOLTIP = {
  backgroundColor: 'rgba(16, 19, 22, 0.96)',
  borderColor: 'rgba(255, 255, 255, 0.14)',
  borderWidth: 1,
  padding: 14,
  cornerRadius: 12,
  titleFont: { family: "'Inter'", size: 13, weight: 'bold' },
  bodyFont: { family: "'Inter'", size: 12 },
  displayColors: true,
  boxPadding: 4
};

function destroyChart(ctx) {
  if (!ctx) return null;
  const existing = Chart.getChart(ctx);
  if (existing) existing.destroy();
  return ctx;
}

function xyGrid() {
  return {
    x: { grid: { display: false }, ticks: { maxTicksLimit: 12, color: '#5f5f5f' } },
    y: {
      grid: { color: 'rgba(255, 255, 255, 0.045)' },
      ticks: { color: '#9b9b9b', callback: v => `${(v / 1000).toFixed(0)}k L` }
    }
  };
}

/* 1. Water Flow Intelligence (Main Trend Line Chart) */
function createTrendChart(canvasId, trendData, anomalyAlerts) {
  const ctx = destroyChart(document.getElementById(canvasId));
  if (!ctx) return null;

  const cContext = ctx.getContext('2d');
  const whiteGrad = cContext.createLinearGradient(0, 0, 0, 320);
  whiteGrad.addColorStop(0, 'rgba(255, 255, 255, 0.14)');
  whiteGrad.addColorStop(0.5, 'rgba(255, 255, 255, 0.04)');
  whiteGrad.addColorStop(1, 'rgba(255, 255, 255, 0.0)');

  const labels = trendData.labels || [];
  const datasets = [
    {
      label: 'Actual Flow (Liters)',
      data: trendData.actual || [],
      borderColor: '#f5f5f5',
      backgroundColor: whiteGrad,
      fill: true,
      tension: 0.42,
      borderWidth: 2,
      pointRadius: 1.5,
      pointHoverRadius: 6,
      pointBackgroundColor: '#fff',
      pointBorderColor: '#050607',
      pointBorderWidth: 2
    },
    {
      label: 'Rolling Baseline (7-Day)',
      data: trendData.baseline || [],
      borderColor: 'rgba(160, 160, 160, 0.8)',
      borderDash: [6, 6],
      tension: 0.35,
      borderWidth: 1.6,
      pointRadius: 0,
      fill: false
    }
  ];

  // Anomaly events: white circle markers (subtle red ring when critical)
  if (anomalyAlerts && anomalyAlerts.length && labels.length) {
    const markers = [];
    const pointColors = [];
    const pointBorders = [];
    anomalyAlerts.forEach(a => {
      const day = a.timestamp ? a.timestamp.slice(0, 10) : null;
      const idx = day ? labels.indexOf(day) : -1;
      if (idx >= 0) {
        markers.push({
          x: idx,
          y: (trendData.actual || [])[idx] ?? 0,
          meter: a.meter_id,
          score: a.score,
          sev: a.severity
        });
        pointColors.push('rgba(255,255,255,0.92)');
        pointBorders.push(a.severity === 'Critical' ? '#e26d6d' : '#050607');
      }
    });
    if (markers.length) {
      datasets.push({
        type: 'scatter',
        label: 'Anomaly Events',
        data: markers,
        pointStyle: 'circle',
        pointRadius: 6,
        pointBackgroundColor: pointColors,
        pointBorderColor: pointBorders,
        pointBorderWidth: 2,
        pointHoverRadius: 8
      });
    }
  }

  return new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: { boxWidth: 12, boxHeight: 4, color: '#9b9b9b', font: { size: 11, weight: '500' } }
        },
        tooltip: {
          ...HOLO_TOOLTIP,
          callbacks: {
            label: function(context) {
              if (context.dataset.type === 'scatter') {
                const m = context.raw;
                return ` ${m.sev} anomaly · ${m.meter} · risk ${m.score.toFixed(0)}/100`;
              }
              return ` ${context.dataset.label}: ${context.parsed.y.toLocaleString()} L`;
            }
          }
        }
      },
      scales: xyGrid()
    }
  });
}

/* 2. Anomaly Severity Distribution (Doughnut) */
function createSeverityDoughnut(canvasId, distData) {
  const ctx = destroyChart(document.getElementById(canvasId));
  if (!ctx) return null;

  const colorPalette = {
    'Normal': '#e8ece9', 'Low': '#cfcfcf', 'Medium': '#9fa4a8', 'High': '#d9d9d9', 'Critical': '#e26d6d'
  };
  const bgColors = (distData.labels || []).map(l => colorPalette[l] || '#cfcfcf');

  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: distData.labels || [],
      datasets: [{
        data: distData.values || [],
        backgroundColor: bgColors,
        borderColor: '#0b0d0f',
        borderWidth: 3,
        hoverOffset: 10
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { boxWidth: 10, padding: 9, font: { size: 10.5 }, color: '#9b9b9b' }
        },
        tooltip: HOLO_TOOLTIP
      }
    }
  });
}

/* 3. Location Volume Bar Chart */
function createLocationBarChart(canvasId, locData) {
  const ctx = destroyChart(document.getElementById(canvasId));
  if (!ctx) return null;

  const cContext = ctx.getContext('2d');
  const barGrad = cContext.createLinearGradient(0, 0, 0, 260);
  barGrad.addColorStop(0, 'rgba(255, 255, 255, 0.72)');
  barGrad.addColorStop(1, 'rgba(255, 255, 255, 0.12)');

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: locData.labels || [],
      datasets: [{
        label: 'Volume (Liters)',
        data: locData.values || [],
        backgroundColor: barGrad,
        borderColor: 'rgba(255,255,255,0.6)',
        borderWidth: 1,
        borderRadius: 6,
        hoverBackgroundColor: 'rgba(255, 255, 255, 0.85)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: HOLO_TOOLTIP },
      scales: xyGrid()
    }
  });
}

/* 4. Day of Week Consumption Bar Chart */
function createDayOfWeekChart(canvasId, dowData) {
  const ctx = destroyChart(document.getElementById(canvasId));
  if (!ctx) return null;

  const labels = dowData.labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const backgrounds = labels.map((l, i) =>
    i === 5 || (l === 'Sat') || i === 6 || l === 'Sun'
      ? 'rgba(255, 255, 255, 0.42)'
      : 'rgba(255, 255, 255, 0.22)');

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Avg Daily Flow (L)',
        data: dowData.values || [],
        backgroundColor: backgrounds,
        borderColor: 'rgba(255,255,255,0.45)',
        borderWidth: 1,
        borderRadius: 5,
        hoverBackgroundColor: 'rgba(255, 255, 255, 0.7)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: HOLO_TOOLTIP },
      scales: { x: { grid: { display: false } }, y: { grid: { color: 'rgba(255, 255, 255, 0.045)' } } }
    }
  });
}

/* 5. Forecast Chart with Confidence Envelope */
function createForecastChart(canvasId, histData, foreData) {
  const ctx = destroyChart(document.getElementById(canvasId));
  if (!ctx) return null;

  const allLabels = [...histData.dates, ...foreData.dates];
  const histValues = [...histData.values, ...Array(foreData.dates.length).fill(null)];
  const lastHistVal = histData.values[histData.values.length - 1];
  const foreValues = [...Array(histData.values.length - 1).fill(null), lastHistVal, ...foreData.values];
  const upperBounds = [...Array(histData.values.length - 1).fill(null), lastHistVal, ...foreData.upper_bounds];
  const lowerBounds = [...Array(histData.values.length - 1).fill(null), lastHistVal, ...foreData.lower_bounds];

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: allLabels,
      datasets: [
        {
          label: 'Historical Observation (L)',
          data: histValues,
          borderColor: '#f5f5f5',
          borderWidth: 2,
          pointRadius: 2,
          tension: 0.35
        },
        {
          label: 'Forecast Trajectory (L)',
          data: foreValues,
          borderColor: '#d9d9d9',
          borderDash: [5, 5],
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: '#d9d9d9',
          pointBorderColor: '#050607',
          pointBorderWidth: 2,
          tension: 0.35
        },
        {
          label: 'Confidence Envelope Upper',
          data: upperBounds,
          borderColor: 'transparent',
          backgroundColor: 'rgba(255, 255, 255, 0.06)',
          fill: '+1',
          pointRadius: 0
        },
        {
          label: 'Confidence Envelope Lower',
          data: lowerBounds,
          borderColor: 'transparent',
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { labels: { color: '#9b9b9b', filter: item => !item.text.includes('Envelope') } },
        tooltip: HOLO_TOOLTIP
      },
      scales: { x: { grid: { display: false } }, y: { grid: { color: 'rgba(255, 255, 255, 0.045)' } } }
    }
  });
}