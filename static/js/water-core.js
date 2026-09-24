// ==========================================================================
// AQUAGUARD AI — WATER CORE VISUAL ENGINE
// Rising droplets, holographic connection-lines, sparklines, AI status tape
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  initCoreDroplets();
  initConnLines();
  initSparklines();
  initStatusTape();
  listenForDashboardData();
  listenForTelemetry();
});

/* 1. Rising droplets inside every .water-core-sphere */
function initCoreDroplets() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  document.querySelectorAll('.water-core-sphere').forEach(sphere => {
    for (let i = 0; i < 7; i++) {
      const d = document.createElement('span');
      d.className = 'core-droplet';
      const size = 3 + Math.random() * 4;
      d.style.width = d.style.height = size + 'px';
      d.style.left = (12 + Math.random() * 76) + '%';
      d.style.animationDelay = (Math.random() * 6) + 's';
      d.style.animationDuration = (4.5 + Math.random() * 4) + 's';
      sphere.appendChild(d);
    }
  });
}

/* 2. Holographic connection lines between KPIs and the Water Core */
function initConnLines() {
  const wrap = document.getElementById('coreConnLines');
  if (!wrap) return;
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const margin = 40, h = 470, w = 920;
  // anchor points around the sphere
  const anchors = {
    leftTop:    { x: 170, y: 120 },
    leftBot:    { x: 170, y: 320 },
    rightTop:   { x: w - 170, y: 120 },
    rightBot:   { x: w - 170, y: 320 },
    center:     { x: w / 2, y: h / 2 }
  };

  const edges = [
    { from: 'leftTop',  to: 'center' },
    { from: 'leftBot',  to: 'center' },
    { from: 'rightTop', to: 'center' },
    { from: 'rightBot', to: 'center' }
  ];

  let svg = `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="xMidYMid meet" style="width:100%; height:100%;" aria-hidden="true">`;
  edges.forEach((e, i) => {
    const a = anchors[e.from], b = anchors[e.to];
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2 - 30;
    const path = `M ${a.x} ${a.y} Q ${mx} ${my} ${b.x} ${b.y}`;
    svg += `<path class="conn-line" d="${path}" style="animation-delay:${i * -5.5}s"/>`;
    if (!prefersReduced) {
      // travelling light pulse riding the curve
      svg += `<circle class="conn-pulse" r="3" style="offset-path:path('${path}'); animation-delay:${i * 2.7}s">`;
    }
  });
  svg += `</svg>`;
  wrap.innerHTML = svg;
}

/* 3. Mini sparkline inside KPI panels */
function initSparklines() {
  document.querySelectorAll('[data-spark]').forEach(el => {
    const series = (el.getAttribute('data-spark') || '').split(',').map(Number).filter(v => !isNaN(v));
    if (series.length < 2) return;
    const svgNS = 'http://www.w3.org/2000/svg';
    el.innerHTML = '';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', '0 0 100 24');
    svg.setAttribute('preserveAspectRatio', 'none');
    const min = Math.min(...series), max = Math.max(...series);
    const pts = series.map((v, i) => {
      const x = (i / (series.length - 1)) * 100;
      const y = 22 - ((v - min) / Math.max(max - min, 1)) * 18;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');

    const poly = document.createElementNS(svgNS, 'polyline');
    poly.setAttribute('points', pts);
    poly.setAttribute('fill', 'none');
    poly.setAttribute('stroke', el.getAttribute('data-spark-color') || '#e8e8e8');
    poly.setAttribute('stroke-width', '1.6');
    poly.setAttribute('stroke-linecap', 'round');
    poly.setAttribute('stroke-linejoin', 'round');
    poly.setAttribute('vector-effect', 'non-scaling-stroke');
    poly.style.strokeWidth = '1.6';
    svg.appendChild(poly);
    el.appendChild(svg);
  });
}

/* 4. Live AI status tape — driven by real engine state */
function initStatusTape() {
  const tape = document.getElementById('aiStatusTape');
  if (!tape) return;
  tape.style.display = 'flex';
}

function listenForDashboardData() {
  window.addEventListener('aqua:dashboard', (e) => {
    const data = e.detail;
    updateStatusTape(data);
    updateBell(data);
  });
}

/* Live simulation telemetry — subtle warning ring + status tape override */
function listenForTelemetry() {
  window.addEventListener('aqua:telemetry', (e) => {
    const s = e.detail;
    if (!s || s.status !== 'success') return;
    const sphere = document.getElementById('waterCoreSphere');
    if (sphere) {
      sphere.classList.toggle('tele-critical', !!(s.active_alert || s.critical_count > 0));
      sphere.classList.toggle('tele-live', !!(s.running && !s.paused));
    }
    if (s.running && !s.paused) {
      if (s.critical_count > 0) {
        setTape(`SIMULATION LIVE — ${s.critical_count} CRITICAL EVENT${s.critical_count > 1 ? 'S' : ''}`, 'bad');
      } else if (s.anomalies_detected > 0) {
        setTape(`SIMULATION LIVE — ${s.anomalies_detected} ANOMALIES DETECTED`, '');
      } else {
        setTape('SIMULATION LIVE — ALL METERS NOMINAL', 'ok');
      }
    }
  });
}

function setTape(msg, cls) {
  const tape = document.getElementById('aiStatusTape');
  const msgEl = document.getElementById('aiStatusMsg');
  const dot = document.getElementById('aiStatusDot');
  if (!tape || !msgEl || !dot) return;
  msgEl.textContent = msg;
  msgEl.className = 'msg ' + (cls || '');
  dot.className = 'live-dot ' + (cls || '');
}

function updateStatusTape(data) {
  if (!data || data.status === 'empty') { setTape('AWAITING TELEMETRY — UPLOAD OR LAUNCH DEMO', 'ok'); return; }
  const alerts = data.recent_alerts || [];
  const top = alerts[0];

  if (data.kpis && (data.kpis.critical_anomalies || 0) > 0) {
    setTape(`ANOMALY DETECTED — ${top ? top.meter_id + ' ' + (top.deviation_pct >= 0 ? '+' : '') + (top.score || 0) + '/100 RISK' : 'CRITICAL EVENT'}`, 'bad');
  } else if (alerts.length > 0) {
    setTape(`BASELINE UPDATED — ${alerts.length} EVENTS IN WINDOW`, '');
  } else {
    setTape('ALL SYSTEMS NOMINAL — WATER INTELLIGENCE ONLINE', 'ok');
  }
}

function updateBell(data) {
  const bell = document.getElementById('bellBadge');
  if (!bell) return;
  const active = (data.recent_alerts || []).filter(a => a.status === 'Active').length;
  if (active > 0) { bell.textContent = active; bell.style.display = 'inline-block'; }
  else bell.style.display = 'none';
}

/* 5. Formatting helpers shared across pages */
function fmtLiters(v) {
  if (v == null) return '0 L';
  if (v >= 1e6) return (v / 1e6).toFixed(2) + 'M L';
  if (v >= 1e3) return (v / 1e3).toFixed(1) + 'K L';
  return v.toLocaleString() + ' L';
}
window.fmtLiters = fmtLiters;