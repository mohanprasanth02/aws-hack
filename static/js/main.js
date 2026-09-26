// ==========================================================================
// AQUAGUARD AI — WATER INTELLIGENCE CORE CONTROLLER
// Marine atmosphere, cursor glow, liquid transitions, toasts, demo pipeline
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  initWaterAtmosphere();
  initCursorGlow();
  initWaterRipple();
  initCounters();
  initToasts();
  initLiquidNavigation();
  initSystemStatus();
  initGlobalSearch();
});

/* 1. Marine atmosphere — rising particles, bubbles, light rays */
function initWaterAtmosphere() {
  const canvas = document.getElementById('waterAtmosphereCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let width, height;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const particleCount = reduced ? 0 : (window.innerWidth < 768 ? 20 : 40);

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  }
  window.addEventListener('resize', resize);
  resize();

  const motes = [];
  const Mote = function () {
    this.reset = function () {
      this.x = Math.random() * width;
      this.y = height + Math.random() * 40;
      this.size = Math.random() * 3 + 1;
      this.speedY = Math.random() * 0.6 + 0.22;
      this.speedX = (Math.random() - 0.5) * 0.3;
      this.alpha = Math.random() * 0.35 + 0.08;
      this.isBubble = Math.random() > 0.52;
      this.hue = 0;
    };
    this.reset();
  };
  for (let i = 0; i < particleCount; i++) {
    const m = new Mote();
    m.y = Math.random() * height;
    motes.push(m);
  }

  let time = 0;
  let lastTime = performance.now();
  function frame(currentTime) {
    const now = currentTime || performance.now();
    const dt = Math.min((now - lastTime) / 16.667, 2.0) || 1.0;
    lastTime = now;

    ctx.clearRect(0, 0, width, height);
    time += 0.007 * dt;
    const ray = ctx.createLinearGradient(0, 0, 0, height * 0.7);
    ray.addColorStop(0, `rgba(255, 255, 255, ${0.028 + Math.sin(time) * 0.012})`);
    ray.addColorStop(0.5, `rgba(140, 145, 150, ${0.016 + Math.cos(time * 0.8) * 0.008})`);
    ray.addColorStop(1, 'transparent');
    ctx.fillStyle = ray;
    ctx.fillRect(0, 0, width, height);

    for (const m of motes) {
      m.y -= m.speedY * dt;
      m.x += (Math.sin(m.y * 0.008) * 0.5 + m.speedX) * dt;
      if (m.y < -30 || m.x < -30 || m.x > width + 30) m.reset();
      ctx.beginPath();
      ctx.arc(m.x, m.y, m.size, 0, Math.PI * 2);
      if (m.isBubble) {
        ctx.strokeStyle = `rgba(255, 255, 255, ${m.alpha * 0.7})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      } else {
        ctx.fillStyle = `rgba(255, 255, 255, ${m.alpha})`;
        ctx.shadowBlur = 4;
        ctx.shadowColor = 'rgba(255, 255, 255, 0.25)';
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

/* 2. Cursor ambient glow (desktop only) */
function initCursorGlow() {
  const glow = document.querySelector('.cursor-ambient-glow');
  if (!glow || window.innerWidth < 992) return;
  let mx = window.innerWidth / 2, my = window.innerHeight / 2, cx = mx, cy = my;
  window.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; });
  (function loop() {
    cx += (mx - cx) * 0.08;
    cy += (my - cy) * 0.08;
    glow.style.left = cx + 'px';
    glow.style.top = cy + 'px';
    requestAnimationFrame(loop);
  })();
}

/* 3. Click water ripple on holographic controls */
function initWaterRipple() {
  document.addEventListener('click', e => {
    const target = e.target.closest('.btn-holo, .btn-holo-alt, .btn-holo-eco, .core-kpi, .aq-pillnav-link, .report-card, .aq-icon-btn, .anom-dot');
    if (!target) return;
    const rect = target.getBoundingClientRect();
    const ripple = document.createElement('span');
    ripple.className = 'water-ripple-wave';
    const size = Math.max(rect.width, rect.height) * 1.4;
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
    ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
    target.style.position = 'relative';
    target.style.overflow = 'hidden';
    target.appendChild(ripple);
    setTimeout(() => ripple.remove(), 620);
  });
}

/* 4. Water core value updater */
function updateWaterCore(score, tier) {
  const val = document.getElementById('coreValueNum');
  const tierEl = document.getElementById('coreTierLabel');
  let target = Math.max(0, Math.min(100, Math.round(score || 0)));

  if (val) {
    val.textContent = target;
    const current = parseInt(val.getAttribute('data-shown') || '0', 10);
    if (current !== target) {
      val.setAttribute('data-shown', target);
      animateNumber(val, current, target, 1100);
    }
  }
  if (tierEl && tier) {
    tierEl.textContent = tier;
    const norm = String(tier).toLowerCase();
    tierEl.className = 'core-tier' + (/(bad|critical|high|poor|extreme|red)/.test(norm) ? ' bad' : (/(warn|moderate|medium|fair)/.test(norm) ? ' warn' : ''));
  }
  // sync any mini sphere (sustainability / simulator)
  const miniScore = document.getElementById('simScoreVal');
  if (miniScore) miniScore.textContent = target;
}

function animateNumber(el, from, to, duration) {
  const start = performance.now();
  function tick(t) {
    const p = Math.min((t - start) / duration, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(from + (to - from) * eased);
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* 5. Counters (kept for KPI values) */
function initCounters() {
  const counters = document.querySelectorAll('.counter-anim');
  counters.forEach(counter => {
    const target = parseFloat(counter.getAttribute('data-target') || '0');
    const isFloat = counter.getAttribute('data-float') === 'true';
    const duration = 1400, start = performance.now();
    (function up(t) {
      const p = Math.min((t - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      const cur = target * eased;
      counter.textContent = isFloat ? cur.toFixed(1) : Math.floor(cur).toLocaleString();
      if (p < 1) requestAnimationFrame(up);
      else counter.textContent = isFloat ? target.toFixed(1) : Math.round(target).toLocaleString();
    })(start);
  });
}

/* 6. Toasts */
function showToast(title, message, type = 'info') {
  let box = document.getElementById('toast-container');
  if (!box) {
    box = document.createElement('div');
    box.id = 'toast-container';
    box.className = 'position-fixed bottom-0 end-0 p-3';
    box.style.zIndex = '3400';
    document.body.appendChild(box);
  }
  const colorMap = { success: '#d7dad9', danger: '#e26d6d', warning: '#d9c8a3', info: '#d6d6d6' };
  const borderHex = colorMap[type] || '#d6d6d6';
  const id = 'toast_' + Date.now();
  box.insertAdjacentHTML('beforeend', `
    <div id="${id}" class="toast align-items-center text-white glass-panel mb-2" role="alert" aria-live="assertive" aria-atomic="true"
         style="border:1px solid ${borderHex}99; box-shadow:0 12px 34px rgba(0,0,0,.85);">
      <div class="toast-header bg-transparent text-white border-bottom border-secondary border-opacity-25 py-2">
        <span class="status-beacon me-2" style="background-color:${borderHex}; box-shadow:0 0 8px ${borderHex}66;"></span>
        <strong class="me-auto" style="font-family:'Space Grotesk'; font-size:12.5px;">${title}</strong>
        <small class="text-secondary" style="font-size:10px;">live</small>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
      <div class="toast-body py-2 text-light" style="font-size:12px;">${message}</div>
    </div>`);
  const el = document.getElementById(id);
  const bs = new bootstrap.Toast(el, { delay: 4500 });
  bs.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

function initToasts() {
  document.querySelectorAll('.server-flash-msg').forEach(f => {
    const cat = f.getAttribute('data-category') || 'info';
    const txt = f.getAttribute('data-message') || '';
    if (txt) showToast('AquaGuard Alert', txt, cat);
  });
}

/* 7. Liquid navigation — aqua glow expansion between pages */
function initLiquidNavigation() {
  const overlay = document.getElementById('aqTransition');
  if (!overlay) return;
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  document.querySelectorAll('a[href]').forEach(a => {
    const href = a.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('javascript:') || a.target === '_blank' || a.hasAttribute('download')) return;
    if (href.startsWith('http') || href.startsWith('/api/') || href.startsWith('/exports/')) return;
    if (a.closest('.dropdown, .alert, .page-link, .pagination')) return;
    a.addEventListener('click', e => {
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      navigateLiquid(href);
    });
  });

  // avoid double intercept: the overlay label
  function navigateLiquid(href) {
    if (prefersReduced) { window.location.href = href; return; }
    overlay.classList.add('visible');
    const label = document.getElementById('aqTransitionLabel');
    const vocab = [
      'Tuning water signatures…',
      'Compressing telemetry stream…',
      'Opening underwater channel…',
      'Calibrating holographic optics…',
      'Aligning water intelligence…'
    ];
    if (label) label.textContent = vocab[Math.floor(Math.random() * vocab.length)];
    setTimeout(() => { window.location.href = href; }, 150);
  }
  window.navigateLiquid = navigateLiquid;
}

/* 8. System status: live state from actual data */
async function initSystemStatus() {
  refreshSystemStatus();
  setInterval(refreshSystemStatus, 20000);
}

async function refreshSystemStatus() {
  const badge = document.getElementById('systemStatusBadge');
  const beacon = document.getElementById('systemStatusBeacon');
  const bell = document.getElementById('bellBadge');
  if (!badge) return;

  try {
    const res = await fetch('/api/dashboard');
    const data = await res.json();

    let label = 'SYSTEM ONLINE', cls = 'aq-status';
    beacon?.classList.remove('analyzing', 'attention');
    if (data.status === 'empty' || !data.kpis) {
      label = 'AWAITING DATA';
    } else {
      const crit = data.kpis.critical_anomalies || 0;
      label = crit > 0 ? 'ATTENTION REQUIRED' : 'SYSTEM ONLINE';
      cls = crit > 0 ? 'aq-status attention' : 'aq-status';
    }
    badge.className = cls;
    badge.innerHTML = `<span class="status-beacon" id="systemStatusBeacon"></span><span>${label}</span>`;

    // bell badge: how many active alerts
    if (bell && data.recent_alerts) {
      const active = data.recent_alerts.filter(a => a.status === 'Active').length;
      if (active > 0) {
        bell.textContent = active;
        bell.style.display = 'inline-block';
      } else {
        bell.style.display = 'none';
      }
    }
    window.dispatchEvent(new CustomEvent('aqua:dashboard', { detail: data }));
  } catch (e) {
    /* offline — keep previous state */
  }
}

/* 9. Mobile sheet toggle */
function toggleMobileSheet() {
  const sheet = document.getElementById('aqMobileSheet');
  if (sheet) sheet.classList.toggle('open');
  const btn = document.getElementById('aqBurgerBtn');
  if (btn) btn.innerHTML = sheet.classList.contains('open')
    ? '<i class="bi bi-x-lg"></i>' : '<i class="bi bi-layers"></i>';
}

/* 10. Full pipeline overlay driven by backend analysis stages */
function showPipeline(stages, headline) {
  const pipe = document.getElementById('aqPipeline');
  if (!pipe) return;
  pipe.classList.add('visible');
  const head = document.getElementById('pipelineHeadline');
  if (head) head.textContent = headline || 'ANALYZING WATER';
  const box = document.getElementById('pipelineStages');
  if (!box) return;

  box.innerHTML = stages.map((s, i) => `
    <div class="pipe-stage ${i === 0 ? 'active' : 'pending'}" data-idx="${i}">
      <span class="st-spin"></span>
      <span class="st-label">${s}</span>
    </div>`).join('');

  let idx = 0;
  const tick = () => {
    const rows = box.querySelectorAll('.pipe-stage');
    rows.forEach((r, i) => {
      r.className = 'pipe-stage ' + (i < idx ? 'done' : (i === idx ? 'active' : 'pending'));
      r.classList.remove('active', 'pending', 'done');
      if (i < idx) r.classList.add('done');
      else if (i === idx) r.classList.add('active');
      else r.classList.add('pending');
    });
  };
  tick();
  return {
    advance() { if (idx < stages.length - 1) { idx++; tick(); } return idx; },
    close() { pipe.classList.remove('visible'); },
    get done() { return idx >= stages.length - 1; }
  };
}

function hidePipeline() {
  const pipe = document.getElementById('aqPipeline');
  if (pipe) pipe.classList.remove('visible');
}

/* 11. One-click demo launcher with real pipeline + staged narrative */
async function triggerLaunchDemo(meters = 6, days = 21) {
  const stages = [
    'LOADING DEMO DATASET',
    'DETECTING CONSUMPTION PATTERNS',
    'COMPUTING ROLLING BASELINES',
    'RUNNING ANOMALY DETECTION',
    'SCORING RISK (0–100)',
    'SYNCHRONIZING WATER CORE'
  ];
  const pipe = showPipeline(stages, 'ANALYZING WATER');
  const ticker = setInterval(() => { if (pipe) pipe.advance(); }, 520);

  try {
    const res = await fetch('/api/demo/launch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_meters: meters, num_days: days })
    });
    const result = await res.json();
    clearInterval(ticker);

    if (result.status === 'success') {
      showToast('Core Synchronized', result.message, 'success');
      const overlay = document.getElementById('aqTransition');
      if (overlay) overlay.classList.add('visible');
      const label = document.getElementById('aqTransitionLabel');
      if (label) label.textContent = 'WATER CORE ONLINE';
      setTimeout(() => { window.location.href = '/dashboard'; }, 700);
    } else {
      hidePipeline();
      showToast('Engine Error', result.message || 'Failed to populate demo data', 'danger');
    }
  } catch (err) {
    clearInterval(ticker);
    hidePipeline();
    showToast('Network Error', 'Could not communicate with AquaGuard server.', 'danger');
  }
}

/* 12. Global search — meters, zones, anomalies, reports */
function initGlobalSearch() {
  const box = document.getElementById('globalSearchBox');
  const input = document.getElementById('globalSearchInput');
  const results = document.getElementById('globalSearchResults');
  if (!box || !input || !results) return;

  let registry = null;
  const quickLinks = [
    { cat: 'ANOMALIES', kw: ['anomaly', 'anomalies', 'alert', 'risk', 'leak', 'fault'], href: '/anomalies', icon: 'bi-exclamation-triangle' },
    { cat: 'TELEMETRY', kw: ['telemetry', 'live', 'stream', 'simulation'], href: '/telemetry', icon: 'bi-activity' },
    { cat: 'MAP', kw: ['map', 'geo', 'zone', 'grid', 'location', 'building'], href: '/map', icon: 'bi-geo-alt' },
    { cat: 'FORECAST', kw: ['forecast', 'future', 'predict', 'trend'], href: '/forecast', icon: 'bi-graph-up-arrow' },
    { cat: 'SUSTAINABILITY', kw: ['sustain', 'score', 'esg', 'environment'], href: '/sustainability', icon: 'bi-shield-check' },
    { cat: 'SIMULATOR', kw: ['simulator', 'what-if', 'impact', 'scenario'], href: '/what-if', icon: 'bi-sliders' },
    { cat: 'REPORTS', kw: ['report', 'pdf', 'export', 'download'], href: '/reports', icon: 'bi-file-earmark-pdf' },
    { cat: 'UPLOAD', kw: ['upload', 'csv', 'import', 'ingest'], href: '/upload', icon: 'bi-cloud-arrow-up' },
    { cat: 'ANALYTICS', kw: ['analytics', 'evaluation', 'pipeline', 'ml'], href: '/analytics', icon: 'bi-cpu' }
  ];

  async function loadRegistry() {
    if (registry) return registry;
    try {
      const res = await fetch('/api/meters/map', { headers: { 'X-Requested-With': 'fetch' } });
      const data = await res.json();
      registry = { meters: data.meters || [] };
    } catch (err) {
      registry = registry || { meters: [] };
    }
    return registry;
  }

  function meterHits(meters, ql) {
    return meters.filter(m =>
      [m.meter_id, m.location, m.building].some(v => (v || '').toLowerCase().includes(ql)));
  }

  function render(meters, ql) {
    let html = '';
    if (meters.length) {
      html += '<div class="ns-cat">METERS / ZONES</div>';
      html += meters.slice(0, 7).map(m => {
        const sev = (m.severity || 'Normal').toLowerCase();
        return '<a href="/map?locate=' + encodeURIComponent(m.meter_id) +
          '"><i class="bi bi-droplet-fill"></i><span>' + esc(m.meter_id) + '</span>' +
          '<span class="ns-meta"><span class="tt-pill ' + sev + '">' + esc(m.severity || 'Normal') +
          '</span></span></a>';
      }).join('');
    }
    const links = quickLinks.filter(l => l.kw.some(k => k.includes(ql) || ql.includes(k)));
    if (links.length) {
      html += '<div class="ns-cat">INTELLIGENCE</div>';
      html += links.map(l =>
        '<a href="' + l.href + '"><i class="bi ' + l.icon + '"></i><span>' + l.cat + '</span><span class="ns-meta">GO</span></a>').join('');
    }
    results.innerHTML = html || '<div class="ns-empty">No results for 「' + esc(ql) + '」</div>';
  }

  let timer = null;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 2) { results.classList.remove('show'); return; }
    timer = setTimeout(async () => {
      const reg = await loadRegistry();
      render(meterHits(reg.meters, q.toLowerCase()), q.toLowerCase());
      results.classList.add('show');
    }, 120);
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const first = results.querySelector('a');
      if (first) { results.classList.remove('show'); window.location.href = first.getAttribute('href'); }
    } else if (e.key === 'Escape') {
      results.classList.remove('show');
      input.blur();
    }
  });

  document.addEventListener('click', (e) => {
    if (!box.contains(e.target)) results.classList.remove('show');
  });

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }
}