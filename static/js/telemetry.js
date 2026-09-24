/* ============================================================
   LIVE WATER TELEMETRY & RISK SIMULATION — client controller
   ============================================================ */
(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);

  const SEV_COLOR = {
    Critical: '#e26d6d', High: '#d9c8a3', Moderate: '#e8ece9',
    Medium: '#e8ece9', Low: '#d6d6d6', Normal: '#d6d6d6'
  };
  const SEV_CLASS = {
    Critical: 'sev-critical', High: 'sev-high', Medium: 'sev-medium',
    Moderate: 'sev-medium', Low: 'sev-normal', Normal: 'sev-normal'
  };

  let snap = null;
  let chart = null;
  let pollTimer = null;
  let pollMs = 1000;
  let activeEvent = null;
  let triggerIdx = 0;
  let lastFingerprint = '';

  /* ---------------------------------------------------------- network */
  async function apiGet(url) {
    const res = await fetch(url, { headers: { 'X-Requested-With': 'fetch' } });
    return res.json();
  }

  async function apiPost(url, body) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' },
      body: JSON.stringify(body || {})
    });
    return res.json();
  }

  function toast(title, msg, type) {
    if (window.showToast) window.showToast(title, msg, type);
  }

  async function refresh() {
    try {
      snap = await apiGet('/api/telemetry/status');
      if (snap.status === 'success') render(snap);
    } catch (err) {
      // transient — keep poll going
    }
  }

  async function control(action, extra) {
    const out = await apiPost('/api/telemetry/control', Object.assign({ action: action }, extra || {}));
    if (out && out.status === 'success') {
      snap = out;
      render(out);
      return out;
    }
    if (out && out.message) toast('Telemetry', out.message, 'error');
    return out;
  }

  /* ---------------------------------------------------------- render */
  function render(s) {
    const running = !!s.running;
    const active = running && !s.paused;

    // Status chip
    const chip = $('simStatusChip');
    const dot = $('simStatusDot');
    const label = $('simStateLabel');
    if (chip) chip.classList.add('map-live-chip-on');
    if (dot) dot.className = 'live-dot ok';
    if (label) label.textContent = s.mode === 'replay' ? 'DATABASE REPLAY ACTIVE' : 'LIVE STREAMING ACTIVE';

    $('simTime').textContent = s.sim_time || '--:--:--';
    $('simElapsed').textContent = fmtDur(s.elapsed);

    $('statReadings').textContent = num(s.readings_generated);
    $('statAnomalies').textContent = num(s.anomalies_detected);
    $('statCritical').textContent = num(s.critical_count);
    $('statDQ').textContent = num(s.data_quality_events);

    // Controls reflect server truth
    setSel('selMode', s.mode);
    setSel('selSpeed', String(s.speed));
    setSel('selScenario', s.scenario);

    if ($('btnStart')) $('btnStart').disabled = active;
    if ($('btnPause')) $('btnPause').disabled = !running;
    if ($('btnSave')) $('btnSave').disabled = !s.readings_generated;

    // Banner
    const crit = s.active_alert;
    $('critBanner').style.display = crit ? 'flex' : 'none';
    if (crit) {
      $('critHeadline').textContent = 'CRITICAL EVENT — ' + (crit.type || 'Anomaly').toUpperCase();
      $('critMeterLine').textContent =
        crit.meter_id + ' · ' + num(crit.deviation_pct) + '% deviation · ' + num(crit.usage) + ' L vs ' + num(crit.expected) + ' L expected';
    }

    renderStream(s.stream);
    renderMeters(s.meters);
    renderChart(s);
    renderCounters(s.risk_counters);
    renderDQ(s.dq_notes);
    renderEvents(s.events);
    renderEval(s.eval, s.latency_avg);
    renderFlow(s);
  }

  /* ------------------------------------------------------ sub-renders */
  function renderStream(stream) {
    const box = $('streamList');
    const items = (stream || []).slice(0, 14);
    if (!items.length) {
      box.innerHTML = '<div class="stream-empty">Stream is idle — start the simulation to begin telemetry flow.</div>';
      return;
    }
    const html = items.map((r) => {
      const cls = SEV_CLASS[r.severity] || 'sev-normal';
      return '<div class="stream-card">' +
        '<span class="stream-time font-mono">' + esc(r.time) + '</span>' +
        '<span class="stream-meter font-mono">' + esc(r.meter_id) + '</span>' +
        '<span class="stream-usage font-mono">' + num(r.usage) + ' L</span>' +
        '<span class="stream-sev ' + cls + '">' + esc(r.severity || 'Normal') + '</span>' +
        '</div>';
    }).join('');
    box.innerHTML = html;
    animateStream(box);
  }

  function animateStream(box) {
    if (box.dataset.anim && !box.contains(document.activeElement)) return;
    const cards = box.querySelectorAll('.stream-card');
    if (!cards.length) return;
    cards.forEach((c, i) => {
      c.style.setProperty('--n', i);
      c.classList.remove('stream-in');
      void c.offsetWidth;  // restart CSS animation
      c.classList.add('stream-in');
    });
  }

  function renderMeters(meters) {
    const tb = $('metersTbody');
    if (!meters || !meters.length) {
      tb.innerHTML = '<tr><td colspan="8" class="text-secondary small">No meters loaded.</td></tr>';
      $('metersCountLabel').textContent = '0 meters';
      return;
    }
    $('metersCountLabel').textContent = meters.length + ' meters';
    tb.innerHTML = meters.map((m) => {
      const dev = m.deviation_pct;
      const devCls = Math.abs(dev) >= 100 ? 'text-danger' : (Math.abs(dev) >= 50 ? 'text-warning' : 'text-info');
      const sev = m.severity || 'Normal';
      return '<tr data-meter="' + esc(m.meter_id) + '">' +
        '<td class="font-mono text-info"><strong>' + esc(m.meter_id) + '</strong></td>' +
        '<td class="small">' + esc(m.location || '—') + '<span class="d-block text-secondary">' + esc(m.building || '') + '</span></td>' +
        '<td class="font-mono">' + num(m.current_usage) + ' L</td>' +
        '<td class="font-mono">' + num(m.baseline) + ' L</td>' +
        '<td class="font-mono ' + devCls + '">' + (fmtSigned(dev)) + '%</td>' +
        '<td><span class="risk-badge ' + SEV_CLASS[sev] + '">' + esc(sev) + '</span></td>' +
        '<td class="small">' + esc(m.status || '—') + '</td>' +
        '<td class="text-end"><button type="button" class="aq-mini" data-risk="' + esc(m.meter_id) + '" title="Inspect">' +
        '<i class="bi bi-layout-text-window-reverse"></i></button></td>' +
        '</tr>';
    }).join('');

    // only bind once (row click target delegation at container level)
    tb.querySelectorAll('button[data-risk]').forEach((b) => {
      b.onclick = (ev) => {
        ev.stopPropagation();
        const meter = meters.find((x) => x.meter_id === b.dataset.risk);
        if (meter) openMeterInspect(meter);
      };
    });

    tb.onclick = null;
    tb.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-risk]');
      const row = e.target.closest('tr[data-meter]');
      if (btn) return;
      if (row) {
        const meter = meters.find((x) => x.meter_id === row.dataset.meter);
        if (meter) openMeterInspect(meter);
      }
    });
  }

  function openMeterInspect(m) {
    openDrawer({
      id: m.meter_id + '-info',
      meter_id: m.meter_id,
      location: m.location,
      building: m.building,
      timestamp: '—',
      time: '—',
      anomaly_type: m.status || 'Nominal',
      severity: m.severity || 'Normal',
      risk_score: m.risk_score || 0,
      current_usage: m.current_usage || 0,
      expected_usage: m.expected_usage || m.baseline || 0,
      deviation_pct: m.deviation_pct || 0,
      z: null,
      is_night: false,
      method: {},
      causes: [],
      evidence: [],
      recommendations: []
    });
  }

  function renderCounters(c) {
    c = c || {};
    $('countersNormal').textContent = c.Normal || 0;
    $('countersModerate').textContent = c.Moderate || 0;
    $('countersHigh').textContent = c.High || 0;
    $('countersCritical').textContent = c.Critical || 0;
  }

  function renderDQ(notes) {
    const ul = $('dqList');
    if (!notes || !notes.length) {
      ul.innerHTML = '<li class="text-secondary small">No data quality events yet.</li>';
      return;
    }
    ul.innerHTML = notes.slice(0, 8).map((n) =>
      '<li><span class="dq-pill">' + esc(n.detail) + '</span> ' +
      '<span class="font-mono small">' + esc(n.meter_id) + '</span> ' +
      '<span class="text-secondary small">' + esc(n.timestamp) + '</span></li>').join('');
  }

  function renderEvents(events) {
    const box = $('eventsList');
    const $count = $('eventsCount');
    if (!events || !events.length) {
      box.innerHTML = '<div class="text-secondary small py-2">No risk events detected yet. Start the simulation.</div>';
      $count.textContent = '0';
      return;
    }
    $count.textContent = events.length;
    box.innerHTML = events.slice(0, 12).map((ev) => {
      const cls = SEV_CLASS[ev.severity] || 'sev-normal';
      return '<div class="ev-card ' + (ev.status === 'Open' ? 'ev-open' : '') + '" data-id="' + ev.id + '">' +
        '<div class="ev-head"><span class="ev-sev ' + cls + '">' + esc(ev.severity) + '</span>' +
        '<span class="ev-score font-mono">' + num(ev.risk_score) + '</span>' +
        '<span class="ev-time font-mono ms-auto">' + esc(ev.time || '') + '</span></div>' +
        '<div class="ev-body"><span class="font-mono text-info">' + esc(ev.meter_id) + '</span>' +
        '<span class="ev-type">' + esc(ev.anomaly_type || 'Anomaly') + '</span>' +
        '<span class="ev-dev ' + (Math.abs(ev.deviation_pct || 0) >= 50 ? 'text-warning' : 'text-info') + ' font-mono">' +
        fmtSigned(ev.deviation_pct) + '%</span></div>' +
        '<div class="ev-foot"><span class="small text-secondary">' + esc(ev.location || ev.building || '') + '</span>' +
        '<span class="badge-tag">' + esc(ev.status || 'Open') + '</span></div>' +
        '</div>';
    }).join('');
  }

  function renderEval(eval_, lat) {
    if (!eval_) {
      $('evalPrec').textContent = '—'; $('evalRec').textContent = '—'; $('evalF1').textContent = '—';
      $('evalTotal').textContent = '0'; $('evalDetail').textContent = 'Waiting for data…';
      $('evalLatency').textContent = '—';
      return;
    }
    const h = eval_.hybrid || {};
    $('evalPrec').textContent = h.precision != null ? h.precision + '%' : '—';
    $('evalRec').textContent = h.recall != null ? h.recall + '%' : '—';
    $('evalF1').textContent = h.f1 != null ? h.f1 : '—';
    $('evalTotal').textContent = eval_.total || 0;
    $('evalDetail').textContent = 'GT anomalies ' + (eval_.ground_truth_anomalies || 0) +
      ' · TP ' + (h.true_positives || 0) + ' · FP ' + (h.false_positives || 0) +
      ' · FN ' + (h.false_negatives || 0);
    $('evalLatency').textContent = lat != null ? lat + ' s' : '—';
  }

  function renderFlow(s) {
    const avg = s.meters && s.meters.length ? s.meters.reduce((a, m) => a + (m.current_usage || 0), 0) / s.meters.length : 0;
    const baseAvg = s.meters && s.meters.length ? s.meters.reduce((a, m) => a + (m.baseline || 0), 0) / s.meters.length : 1;
    const pct = baseAvg > 0 ? Math.round((avg / baseAvg) * 100) : 0;
    const fill = Math.min(100, Math.max(4, pct));
    $('flowFill').style.width = fill + '%';
    $('flowFill').style.background = pct >= 150 ? '#e26d6d' : (pct >= 110 ? '#d9c8a3' : '#d6d6d6');
    $('flowLabel').textContent = 'FLOW ' + Math.round(avg) + ' L vs ' + Math.round(baseAvg) + ' L';
  }

  /* ---------------------------------------------------------- chart */
  function buildChart() {
    const ctx = $('teleChart');
    if (!ctx) return;
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          { label: 'Usage (L)', data: [], borderColor: '#f5f5f5', backgroundColor: 'rgba(255,255,255,.05)',
            pointRadius: 0, borderWidth: 2, tension: .25, fill: true, pointBackgroundColor: [] },
          { label: 'Baseline (L)', data: [], borderColor: 'rgba(160,160,160,.55)', borderDash: [4, 4],
            pointRadius: 0, borderWidth: 1.5 }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        animation: false,
        scales: {
          x: { display: true, ticks: { color: '#6a6a6a', maxTicksLimit: 8, font: { size: 10 } },
               grid: { color: 'rgba(255,255,255,.04)' } },
          y: { display: true, ticks: { color: '#6a6a6a', font: { size: 10 } },
               grid: { color: 'rgba(255,255,255,.06)' } }
        },
        plugins: { legend: { labels: { color: '#9b9b9b', font: { size: 11 } }, display: true } }
      }
    });
  }

  function renderChart(s) {
    if (!chart) return;
    const selMeter = $('selChartMeter').value;
    const windowSize = parseInt($('selChartWindow').value, 10) || 60;
    const blocks = s.chart || {};
    const key = selMeter || (Object.keys(blocks)[0] || '');
    const block = blocks[key];
    if (!block || !block.t || !block.t.length) {
      chart.data.labels = [];
      chart.data.datasets[0].data = [];
      chart.data.datasets[0].pointBackgroundColor = [];
      chart.data.datasets[1].data = [];
      chart.update('none');
      return;
    }
    const labels = block.t.slice(-windowSize);
    const usage = block.usage.slice(-windowSize);
    const base = block.baseline && block.baseline.length ? block.baseline.slice(-windowSize) : [];
    const anom = (block.anomaly || []).slice(-windowSize);
    chart.data.labels = labels;
    chart.data.datasets[0].data = usage;
    chart.data.datasets[0].pointBackgroundColor = usage.map((u, i) => anom[i] ? '#e26d6d' : 'rgba(0,0,0,0)');
    if (base.length) { chart.data.datasets[1].data = base; chart.data.datasets[1].hidden = false; }
    else { chart.data.datasets[1].data = []; chart.data.datasets[1].hidden = true; }
    chart.update('none');
  }

  function populateChartSelect(meters) {
    const sel = $('selChartMeter');
    if (!sel) return;
    const current = sel.value;
    const keys = (meters || []).map((m) => m.meter_id);
    sel.innerHTML = keys.map((k) =>
      '<option value="' + esc(k) + '">' + esc(k) + '</option>').join('');
    if (current && keys.includes(current)) sel.value = current;
  }

  /* ---------------------------------------------------------- drawer */
  function openDrawer(ev) {
    activeEvent = ev;
    $('riskDrawer').classList.add('open');
    $('riskDrawer').setAttribute('aria-hidden', 'false');
    $('rxBackdrop').style.display = 'block';

    $('drawerMeter').textContent = ev.meter_id + ' · ' + (ev.location || ev.building || '');
    $('drawerType').textContent = (ev.anomaly_type || 'Anomaly') + (ev.is_night ? ' · SIM NIGHT' : '');
    $('drawerLoc').textContent = (ev.location || '—') + ' · ' + (ev.building || '');
    $('drawerTime').textContent = ev.timestamp || ev.time || '—';
    $('drawerSeverity').textContent = ev.severity + ' (' + num(ev.risk_score) + '/100)';
    $('drawerSeverity').className = 'rx-big ' + (SEV_CLASS[ev.severity] || 'sev-normal');
    $('drawerScore').textContent = num(ev.risk_score);
    $('drawerUsage').textContent = num(ev.current_usage) + ' L';
    $('drawerExpected').textContent = num(ev.expected_usage) + ' L';
    $('drawerDev').textContent = fmtSigned(ev.deviation_pct) + '%';
    $('drawerZ').textContent = ev.z != null ? ev.z : '—';

    const methods = ev.method || {};
    const mList = [];
    if (methods.z) mList.push('Z-Score');
    if (methods.iqr) mList.push('IQR');
    if (methods.iforest) mList.push('Isolation Forest');
    if (methods.pct) mList.push('% Deviation');
    if (methods.persistence != null && methods.persistence > 0) mList.push('Persistence ' + Math.round(methods.persistence));
    drawerList('drawerMethodLabel', mList);

    drawerList('drawerCauses', ev.causes || []);
    drawerList('drawerEvidence', ev.evidence || []);
    drawerList('drawerRecs', ev.recommendations || []);
  }

  function drawerList(id, items) {
    const el = $(id);
    if (!el) return;
    const html = (Array.isArray(items) ? items : []).map((x) => '<li>' + esc(String(x)) + '</li>').join('');
    el.innerHTML = html || '<li class="text-secondary small">—</li>';
  }

  function closeDrawer() {
    activeEvent = null;
    $('riskDrawer').classList.remove('open');
    $('riskDrawer').setAttribute('aria-hidden', 'true');
    $('rxBackdrop').style.display = 'none';
  }

  /* -------------------------------------------------- trigger plumbing */
  function pickTriggerMeter() {
    const meters = (snap && snap.meters) || [];
    if (!meters.length) return null;
    const m = meters[triggerIdx % meters.length];
    triggerIdx++;
    return m;
  }

  /* ---------------------------------------------------------- helpers */
  function num(v) {
    if (v == null || isNaN(v)) return '0';
    return Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 });
  }
  function fmtSigned(v) {
    if (v == null || isNaN(v)) return '—';
    const n = Number(v);
    return (n > 0 ? '+' : '') + n.toFixed(1);
  }
  function fmtDur(secs) {
    if (secs == null) return '0s';
    secs = Math.floor(secs);
    const h = Math.floor(secs / 3600), m = Math.floor((secs % 3600) / 60), s = secs % 60;
    return (h ? h + 'h ' : '') + (m ? m + 'm ' : '') + s + 's';
  }
  function setSel(id, val) {
    const el = $(id);
    if (el && el.value !== String(val)) el.value = String(val);
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, (c) =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  /* ---------------------------------------------------------- polling */
  function startPoll() {
    if (pollTimer) return;
    pollTimer = setInterval(() => {
      if (document.hidden) return;
      refresh();
    }, pollMs);
  }
  function stopPoll() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  }

  /* ---------------------------------------------------------- init */
  function init() {
    const selMode = $('selMode'), selSpeed = $('selSpeed'), selScenario = $('selScenario');

    if ($('btnStart')) {
      $('btnStart').addEventListener('click', async () => {
        await control('start', {
          mode: selMode ? selMode.value : 'scenario',
          speed: parseInt(selSpeed ? selSpeed.value : '5', 10) || 5,
          scenario: selScenario ? selScenario.value : 'mixed_risks'
        });
        toast('Telemetry', 'Simulation active.', 'success');
      });
    }
    if ($('btnPause')) {
      $('btnPause').addEventListener('click', async () => {
        const out = snap;
        if (out && out.running && out.paused) await control('resume');
        else await control('pause');
      });
    }
    if ($('btnReset')) {
      $('btnReset').addEventListener('click', async () => { await control('reset'); });
    }
    const btnResync = $('btnResyncDb');
    if (btnResync) {
      btnResync.addEventListener('click', async () => {
        btnResync.disabled = true;
        await control('start', {
          mode: selMode ? selMode.value : 'scenario',
          speed: parseInt(selSpeed ? selSpeed.value : '5', 10) || 5,
          scenario: selScenario ? selScenario.value : 'mixed_risks'
        });
        toast('Telemetry', 'Database meters & telemetry synchronized.', 'success');
        setTimeout(() => { btnResync.disabled = false; }, 800);
      });
    }
    if ($('btnSave')) {
      $('btnSave').addEventListener('click', async () => {
        const out = await apiPost('/api/telemetry/save', {});
        if (out.status === 'success') {
          toast('Telemetry', 'Simulation saved — run ' + out.run_code + '.', 'success');
          loadHistory();
        } else if (out.message) toast('Telemetry', out.message, 'error');
      });
    }

    if (selSpeed) selSpeed.addEventListener('change', () => control('speed', { speed: parseInt(selSpeed.value, 10) || 1 }));
    if (selScenario) selScenario.addEventListener('change', () => control('scenario', { scenario: selScenario.value }));
    if (selMode) {
      selMode.addEventListener('change', function () {
        if (snap && snap.running) control('mode', { mode: this.value });
      });
    }

    document.querySelectorAll('[data-preset]').forEach((b) => {
      b.addEventListener('click', async () => {
        await control('preset', { preset: b.dataset.preset });
        toast('Telemetry', 'Preset «' + b.textContent.trim() + '» applied.', 'success');
      });
    });

    $('btnTriggerCritical').addEventListener('click', async () => {
      const m = pickTriggerMeter();
      if (!m) return toast('Telemetry', 'No meters to trigger.', 'warning');
      const out = await control('trigger', { meter_id: m.meter_id, kind: 'extreme' });
      if (out && out.status === 'success') toast('Telemetry', 'Critical scenario applied to ' + m.meter_id + '.', 'warning');
    });

    $('btnTriggerRisk').addEventListener('click', async () => {
      const m = pickTriggerMeter();
      if (!m) return toast('Telemetry', 'No meters to trigger.', 'warning');
      const kind = $('selTriggerRisk').value;
      const out = await control('trigger', { meter_id: m.meter_id, kind: kind });
      if (out && out.status === 'success') toast('Telemetry', kind.replace(/_/g, ' ') + ' applied to ' + m.meter_id + '.', 'info');
    });

    $('btnCritView').addEventListener('click', () => {
      if (snap && snap.active_alert) {
        const ev = snap.events.find((e) => e.id === snap.active_alert.id);
        if (ev) openDrawer(ev);
      }
    });
    $('btnCritAck').addEventListener('click', async () => {
      if (snap && snap.active_alert) {
        await apiPost('/api/telemetry/ack', { event_id: snap.active_alert.id });
        await refresh();
      }
    });

    // Events list click-to-open
    $('eventsList').addEventListener('click', (e) => {
      const card = e.target.closest('.ev-card');
      if (!card) return;
      const ev = (snap && snap.events || []).find((x) => String(x.id) === card.dataset.id);
      if (ev) openDrawer(ev);
    });

    $('btnCloseDrawer').addEventListener('click', closeDrawer);
    $('rxBackdrop').addEventListener('click', closeDrawer);
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDrawer(); });

    $('btnLocate').addEventListener('click', () => {
      if (!activeEvent) return;
      window.open('/map?locate=' + encodeURIComponent(activeEvent.meter_id), '_blank');
    });
    $('btnInvestigate').addEventListener('click', () => {
      if (!activeEvent) return;
      window.open('/anomalies?meter_id=' + encodeURIComponent(activeEvent.meter_id), '_blank');
    });
    $('btnAck').addEventListener('click', async () => {
      if (!activeEvent) return;
      await apiPost('/api/telemetry/ack', { event_id: activeEvent.id });
      await refresh();
      closeDrawer();
    });
    $('btnResolve').addEventListener('click', async () => {
      if (!activeEvent) return;
      await apiPost('/api/telemetry/resolve', { event_id: activeEvent.id });
      await refresh();
      closeDrawer();
    });

    $('selChartMeter').addEventListener('change', () => renderChart(snap));
    $('selChartWindow').addEventListener('change', () => renderChart(snap));

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) stopPoll(); else startPoll();
    });

    buildChart();
    loadHistory();
    startPoll();
    refresh().then(() => {
      if (!snap || !snap.running) {
        control('start', {
          mode: (selMode && selMode.value) || 'scenario',
          speed: parseInt(selSpeed && selSpeed.value, 10) || 5,
          scenario: (selScenario && selScenario.value) || 'mixed_risks'
        });
      }
    });
  }

  async function loadHistory() {
    try {
      const out = await apiGet('/api/telemetry/history');
      const tb = $('historyBody');
      if (!tb) return;
      if (!out.runs || !out.runs.length) {
        tb.innerHTML = '<tr><td colspan="5" class="text-secondary small">No saved runs yet.</td></tr>';
        return;
      }
      tb.innerHTML = out.runs.slice(0, 8).map((r) =>
        '<tr>' +
        '<td class="font-mono text-info small">' + esc(r.run_code) + '</td>' +
        '<td class="small">' + esc(r.mode) + '</td>' +
        '<td class="font-mono small">' + num(r.readings_generated) + '</td>' +
        '<td class="font-mono small">' + num(r.anomalies_detected) + '</td>' +
        '<td class="font-mono small">' + (r.detection_rate != null ? r.detection_rate + '%' : '—') + '</td>' +
        '</tr>').join('');
    } catch (err) { /* noop */ }
  }

  // Public micro API used by the meter table row-click and map page.
  window.teleSimTrigger = function (ev) {
    if (ev && ev.meter_id) {
      openDrawer({ meter_id: ev.meter_id, timestamp: '—', time: '—', severity: '—', location: '—', building: '' });
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();