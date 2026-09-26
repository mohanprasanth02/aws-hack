// ==========================================================================
// AQUAGUARD AI — WATER USAGE RISK INTELLIGENCE NETWORK
// Real geo data → architectural building footprints, custom risk markers,
// holo tooltips, spatial hot-zone clusters, live filters, search,
// basemap style switcher, and intelligence panel.
// ==========================================================================

let mapInstance = null;
let markersGroup = null;
let hotzonesGroup = null;
let buildingsGroup = null;
let allMetersData = [];
let allBuildingsData = [];
let filteredMeters = [];
let filteredBuildings = [];
let buildingPolygons = {}; // building_name -> L.polygon
let mapState = { fitDone: false, showBuildings: true, activeBasemap: 'google_hybrid' };

let liveSyncTimer = null;
let simFingerprint = '';
let locateHandled = false;

const CLASS_ORDER = ['normal', 'moderate', 'high', 'critical'];
const CLASS_COLOR = { normal: '#00f2fe', moderate: '#fbbf24', high: '#f97316', critical: '#ff0055' };

// Basemap presets — Genuine Google Maps Satellite Hybrid, Roadmap, Satellite, & Terrain
const BASEMAP_PRESETS = {
  google_hybrid: {
    name: 'Google Hybrid (Satellite + Roads)',
    layers: [
      {
        url: 'https://mt{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        options: {
          subdomains: ['0', '1', '2', '3'],
          attribution: '&copy; Google Maps',
          maxZoom: 21,
          maxNativeZoom: 20
        }
      }
    ],
    className: ''
  },
  google_streets: {
    name: 'Google Maps (Roadmap)',
    layers: [
      {
        url: 'https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        options: {
          subdomains: ['0', '1', '2', '3'],
          attribution: '&copy; Google Maps',
          maxZoom: 21,
          maxNativeZoom: 20
        }
      }
    ],
    className: ''
  },
  google_satellite: {
    name: 'Google Satellite Aerial',
    layers: [
      {
        url: 'https://mt{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        options: {
          subdomains: ['0', '1', '2', '3'],
          attribution: '&copy; Google Maps',
          maxZoom: 21,
          maxNativeZoom: 20
        }
      }
    ],
    className: ''
  },
  google_terrain: {
    name: 'Google Terrain',
    layers: [
      {
        url: 'https://mt{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
        options: {
          subdomains: ['0', '1', '2', '3'],
          attribution: '&copy; Google Maps',
          maxZoom: 21,
          maxNativeZoom: 20
        }
      }
    ],
    className: ''
  },
  dark_canvas: {
    name: 'Dark Canvas (Night Mode)',
    layers: [
      {
        url: 'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        options: { attribution: '&copy; Esri &copy; OpenStreetMap', maxZoom: 19, maxNativeZoom: 16 }
      },
      {
        url: 'https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
        options: { attribution: '', maxZoom: 19, maxNativeZoom: 16 }
      }
    ],
    className: ''
  }
};

let currentTileLayers = [];

function classifyRisk(m) {
  const d = m && m.deviation_pct != null ? Math.abs(m.deviation_pct) : 0;
  if (d >= 100) return 'critical';
  if (d >= 50) return 'high';
  if (d >= 20) return 'moderate';
  return 'normal';
}

// ---------------------------------------------------------------------------
// BOOT
// ---------------------------------------------------------------------------
function initAquaMap() {
  const mapContainer = document.getElementById('map');
  if (!mapContainer) return;

  // Set default center on exact SNS College of Technology & Engineering Campus, Coimbatore
  mapInstance = L.map('map', {
    zoomControl: false,
    minZoom: 3
  }).setView([11.1018, 77.0275], 17);

  // Initialize real Google Maps Hybrid basemap by default
  setBasemap('google_hybrid');


  // Custom zoom control
  mapInstance.zoomControlRemove = mapInstance.zoomControlRemove || {};
  try { mapInstance.removeControl(mapInstance.zoomControl); } catch (e) { /* already disabled */ }

  // Layer ordering: buildings (bottom) -> hotzones -> meters (top)
  buildingsGroup = L.layerGroup().addTo(mapInstance);
  hotzonesGroup = L.layerGroup().addTo(mapInstance);
  markersGroup = L.layerGroup().addTo(mapInstance);

  wireMapUi();
  populateSeverityOptions();
  loadMetersGeoData();
  setTimeout(() => { if (mapInstance) mapInstance.invalidateSize(); }, 60);
  setTimeout(() => { if (mapInstance) mapInstance.invalidateSize(); }, 300);
}

function setBasemap(styleKey) {
  if (!mapInstance || !BASEMAP_PRESETS[styleKey]) return;
  const cfg = BASEMAP_PRESETS[styleKey];

  // Remove existing tile layers
  currentTileLayers.forEach(l => {
    try { mapInstance.removeLayer(l); } catch (e) {}
  });
  currentTileLayers = [];

  // Toggle CSS filter classes on map container
  const mapEl = document.getElementById('map');
  if (mapEl) {
    mapEl.classList.remove('cyber-dark-tiles');
    if (cfg.className) mapEl.classList.add(cfg.className);
  }

  // Add new tile layers
  cfg.layers.forEach(item => {
    const layer = L.tileLayer(item.url, item.options).addTo(mapInstance);
    if (layer.bringToBack) layer.bringToBack();
    currentTileLayers.push(layer);
  });

  mapState.activeBasemap = styleKey;

  // Update UI options in menu
  document.querySelectorAll('.bm-opt').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-style') === styleKey);
  });
}

function wireMapUi() {
  const bind = (id, fn) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('click', fn);
  };
  const bindInput = (id, fn) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', fn);
  };

  bind('btnZoomIn', () => mapInstance && mapInstance.zoomIn());
  bind('btnZoomOut', () => mapInstance && mapInstance.zoomOut());
  bind('btnResetView', () => {
    if (!mapInstance) return;
    const pts = visibleMeters().filter(m => m.has_coords).map(m => [m.latitude, m.longitude]);
    if (pts.length > 0) {
      fitToPoints(pts, 'preserve');
    } else {
      mapInstance.setView([11.1018, 77.0275], 17);
    }
  });
  bind('btnCritical', showCriticalMeters);
  bind('btnFullscreen', toggleMapFullscreen);
  bind('btnExitFsBanner', toggleMapFullscreen);
  bind('btnToggleIntel', toggleFsIntel);

  // Buildings layer toggle
  bind('btnToggleBuildings', toggleBuildingsLayer);

  // Basemap switcher
  bind('btnBasemapSelect', toggleBasemapMenu);
  bind('btnBasemapClose', closeBasemapMenu);

  document.querySelectorAll('.bm-opt').forEach(btn => {
    btn.addEventListener('click', () => {
      const style = btn.getAttribute('data-style');
      if (style) {
        setBasemap(style);
        closeBasemapMenu();
      }
    });
  });

  bind('mapFilterToggle', () => {
    const bar = document.getElementById('mapFilterBar');
    if (bar) bar.classList.toggle('open');
  });

  bind('btnApplyFilters', applyMapFilters);

  bindInput('mapSearchInput', () => applyMapFilters(true));
  const searchInput = document.getElementById('mapSearchInput');
  if (searchInput) {
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') selectFirstSearchResult();
    });
  }

  ['filterLocation', 'filterSeverity'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', () => onFilterChange(true));
  });

  const bldSel = document.getElementById('filterBuilding');
  if (bldSel) {
    bldSel.addEventListener('change', () => {
      const bldName = bldSel.value;
      if (bldName) {
        const b = allBuildingsData.find(x => x.name === bldName);
        if (b) {
          selectBuilding(b, false);
          return;
        }
      }
      onFilterChange(true);
    });
  }
}

function toggleBuildingsLayer() {
  mapState.showBuildings = !mapState.showBuildings;
  const btn = document.getElementById('btnToggleBuildings');
  if (btn) btn.classList.toggle('active', mapState.showBuildings);
  renderBuildings(filteredBuildings.length ? filteredBuildings : allBuildingsData);
}

function toggleBasemapMenu() {
  const menu = document.getElementById('basemapMenu');
  if (!menu) return;
  menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
}

function closeBasemapMenu() {
  const menu = document.getElementById('basemapMenu');
  if (menu) menu.style.display = 'none';
}

function onFilterChange(preserveView) {
  applyMapFilters(preserveView);
}

function populateSeverityOptions() {
  const sel = document.getElementById('filterSeverity');
  if (!sel || sel.hasAttribute('data-seeded')) return;
  sel.setAttribute('data-seeded', 'true');
  sel.innerHTML = '';
  const base = document.createElement('option');
  base.value = ''; base.textContent = 'All Risk';
  sel.appendChild(base);
  [['normal', 'Normal'], ['moderate', 'Moderate'], ['high', 'High'], ['critical', 'Critical']].forEach(([v, label]) => {
    const o = document.createElement('option');
    o.value = v; o.textContent = label;
    sel.appendChild(o);
  });
}

// ---------------------------------------------------------------------------
// DATA INGESTION
// ---------------------------------------------------------------------------
async function loadMetersGeoData() {
  try {
    const res = await fetch('/api/meters/map');
    const data = await res.json();
    if (data.status !== 'success') throw new Error('Map API failed');
    ingestMapData(data);
  } catch (e) {
    console.error('Failed to load map meters data', e);
    if (typeof showToast === 'function') {
      showToast('Map Error', 'Could not load meter geospatial data', 'danger');
    }
  }
}

function ingestMapData(data) {
  allMetersData = data.meters || [];
  allBuildingsData = data.buildings_data || [];
  populateFilterOptions(data.locations || [], data.buildings || []);

  const latest = latestAnalysisTime(allMetersData);
  const lastEl = document.getElementById('mapLastAnalysis');
  if (lastEl) lastEl.textContent = latest ? `Last analysis: ${latest}` : 'Last analysis: —';

  const active = !!data.simulation_active;
  setLiveChips(active, data.sim_mode, data.sim_time, data.live_critical, data.simulation_paused);

  const fp = liveFingerprint(data);
  const changed = fp !== simFingerprint;
  simFingerprint = fp;

  renderAll(active);

  const panelCount = document.getElementById('panelMeterCount');
  if (panelCount) panelCount.textContent = `${filteredMeters.length} meters`;

  handleLocateParam(data);

  if (active) {
    startLiveSync();
  } else {
    if (liveSyncTimer) { clearInterval(liveSyncTimer); liveSyncTimer = null; }
    simFingerprint = '';
  }
}

function liveFingerprint(data) {
  return (data.meters || []).map((m) =>
    `${m.meter_id}:${Math.round(m.current_usage || 0)}:${m.severity || 'Normal'}:${Math.round(m.risk_score || 0)}`
  ).join('|');
}

function startLiveSync() {
  if (liveSyncTimer) return;
  liveSyncTimer = setInterval(async () => {
    try {
      const res = await fetch('/api/meters/map');
      if (!res.ok) return;
      const data = await res.json();
      if (data.status === 'success') {
        allMetersData = data.meters || [];
        allBuildingsData = data.buildings_data || allBuildingsData;
        const active = !!data.simulation_active;
        setLiveChips(active, data.sim_mode, data.sim_time, data.live_critical, data.simulation_paused);
        const fp = liveFingerprint(data);
        if (fp !== simFingerprint) {
          simFingerprint = fp;
          renderAll(true);
        }
        if (!active) {
          clearInterval(liveSyncTimer);
          liveSyncTimer = null;
        }
      }
    } catch (e) {
      /* network slip; retry next tick */
    }
  }, 2200);
}

function setLiveChips(active, mode, time, critical, paused) {
  ['mapLiveLabel', 'mapStageLiveLabel'].forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    const dot = el.parentElement ? el.parentElement.querySelector('.live-dot') : null;
    if (active) {
      el.textContent = `SIMULATION ${paused ? 'PAUSED' : 'LIVE'}` + (paused ? '' : ` · ${time || ''}`) + (critical ? ` · ${critical} CRIT` : '');
      if (dot) dot.classList.remove('idle');
    } else {
      el.textContent = 'DATA READY';
      if (dot) dot.classList.add('idle');
    }
  });
}

function handleLocateParam(data) {
  if (locateHandled) return;
  const q = new URLSearchParams(window.location.search);
  const raw = (q.get('locate') || '').trim();
  if (!raw) return;
  locateHandled = true;
  const needle = raw.toLowerCase();
  const m = (data.meters || []).find((x) =>
    [x.meter_id, x.location, x.building].some((v) => (v || '').toLowerCase().includes(needle)));
  if (!m || !m.has_coords) {
    if (!document.getElementById('mapProcResults')) {
      const toast = document.createElement('span');
      toast.className = 'server-flash-msg d-none';
      toast.setAttribute('data-category', 'info');
      toast.setAttribute('data-message', 'No coordinate match for «' + raw + '». Showing full grid.');
      document.body.appendChild(toast);
      if (window.showToast) window.showToast('Water Map', 'No coordinate match for «' + raw + '». Showing full grid.', 'info');
    }
    return;
  }
  mapInstance.flyTo([m.latitude, m.longitude], 16, { duration: 0.8 });
  setTimeout(() => showMeterPanel(m), 850);
}

function latestAnalysisTime(meters) {
  const times = meters
    .map(m => m.anomaly_time)
    .filter(Boolean)
    .sort((a, b) => (a < b ? 1 : -1));
  if (!times.length) return null;
  const d = new Date(times[0].replace(' ', 'T'));
  if (isNaN(d)) return times[0];
  return d.toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function populateFilterOptions(locations, buildings) {
  const locSel = document.getElementById('filterLocation');
  if (locSel) {
    const currentLoc = locSel.value;
    locSel.innerHTML = '';
    const base = document.createElement('option'); base.value = ''; base.textContent = 'All Locations';
    locSel.appendChild(base);
    locations.forEach(l => {
      const o = document.createElement('option'); o.value = l; o.textContent = l;
      if (l === currentLoc) o.selected = true;
      locSel.appendChild(o);
    });
  }
  const bldSel = document.getElementById('filterBuilding');
  if (bldSel) {
    const currentBld = bldSel.value;
    bldSel.innerHTML = '';
    const base = document.createElement('option'); base.value = ''; base.textContent = 'All Buildings';
    bldSel.appendChild(base);
    buildings.forEach(b => {
      const o = document.createElement('option'); o.value = b; o.textContent = b;
      if (b === currentBld) o.selected = true;
      bldSel.appendChild(o);
    });
  }
}

// ---------------------------------------------------------------------------
// FILTER RENDERING
// ---------------------------------------------------------------------------
function currentFilters() {
  return {
    location: document.getElementById('filterLocation')?.value || '',
    building: document.getElementById('filterBuilding')?.value || '',
    severity: document.getElementById('filterSeverity')?.value || '',
    search: (document.getElementById('mapSearchInput')?.value || '').toLowerCase().trim()
  };
}

function filterMetersList() {
  const f = currentFilters();
  const q = f.search;
  return allMetersData.filter(m => {
    if (f.location && m.location !== f.location) return false;
    if (f.building && (m.building || '') !== f.building) return false;
    if (f.severity && getSeverityClass(m) !== f.severity) return false;
    if (q) {
      const hay = `${m.meter_id} ${m.location} ${m.building || ''}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

function filterBuildingsList() {
  const f = currentFilters();
  const q = f.search;
  return allBuildingsData.filter(b => {
    if (f.location && b.location !== f.location) return false;
    if (f.building && b.name !== f.building) return false;
    if (f.severity && (b.severity || 'Normal').toLowerCase() !== f.severity) return false;
    if (q) {
      const hay = `${b.name} ${b.location} ${b.type || ''}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

function visibleMeters() {
  return filteredMeters && filteredMeters.length ? filteredMeters : allMetersData;
}

function renderAll(preserveView) {
  filteredMeters = filterMetersList();
  filteredBuildings = filterBuildingsList();
  const overlaid = applyFilterOverlays();

  if (!mapState.fitDone && !preserveView) {
    const pts = overlaid.filter(m => m.has_coords).map(m => [m.latitude, m.longitude]);
    fitToPoints(pts.length ? pts : validCoordsAll(), 'first');
    mapState.fitDone = true;
  }

  renderBuildings(filteredBuildings.length ? filteredBuildings : allBuildingsData);
  renderMapMarkers(overlaid);
  renderHotZones(overlaid);
  updateMapStats(overlaid);
  renderRegistry(overlaid);

  const panelCount = document.getElementById('panelMeterCount');
  if (panelCount) panelCount.textContent = `${overlaid.length} meter${overlaid.length === 1 ? '' : 's'}`;
}

function applyFilterOverlays() {
  const f = currentFilters();
  const stage = document.getElementById('mapStage');
  const active = Boolean(f.location || f.building || f.severity || f.search);
  if (stage) stage.classList.toggle('filtered', active);
  return filteredMeters;
}

function applyMapFilters() {
  renderAll(true);
}

function resetMapFilters() {
  window.__mapSelected = false;
  ['filterLocation', 'filterBuilding', 'filterSeverity'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  const si = document.getElementById('mapSearchInput');
  if (si) si.value = '';
  filteredMeters = allMetersData;
  filteredBuildings = allBuildingsData;
  renderAll(false);
}

// ---------------------------------------------------------------------------
// BUILDINGS LAYER (Architectural Footprints & Landmark Badges)
// ---------------------------------------------------------------------------
function renderBuildings(buildings) {
  if (!buildingsGroup) return;
  buildingsGroup.clearLayers();
  buildingPolygons = {};

  if (!mapState.showBuildings || !buildings || !buildings.length) return;

  buildings.forEach(b => {
    if (!b.polygon || !b.polygon.length) return;

    const sev = (b.severity || 'Normal').toLowerCase();
    const color = CLASS_COLOR[sev] || '#b0b3b6';
    const isCrit = sev === 'critical';
    const isHigh = sev === 'high';

    // 1. Building polygon footprint
    const poly = L.polygon(b.polygon, {
      color: color,
      weight: isCrit ? 2.4 : (isHigh ? 2.0 : 1.6),
      opacity: 0.9,
      fillColor: color,
      fillOpacity: isCrit ? 0.24 : (isHigh ? 0.20 : 0.13),
      className: `building-polygon ${isCrit ? 'bld-crit-glow' : ''}`
    });

    const dev = b.deviation_pct != null ? `${b.deviation_pct >= 0 ? '+' : ''}${b.deviation_pct}%` : '—';

    poly.bindTooltip(`
      <div class="aq-bld-tt">
        <div class="aq-bld-tt-head">
          <strong><i class="bi ${b.icon || 'bi-building'} me-1 text-info"></i>${b.name}</strong>
          <span class="tt-pill ${sev}">${sev.toUpperCase()}</span>
        </div>
        <div class="aq-bld-tt-type">${b.location} • ${b.type || 'Campus Facility'}</div>
        <div class="aq-bld-tt-row"><span>Active Meters</span><b>${b.meters_count}</b></div>
        <div class="aq-bld-tt-row"><span>Total Flow</span><b>${Math.round(b.current_usage || 0).toLocaleString()} L</b></div>
        <div class="aq-bld-tt-row"><span>Deviation</span><b class="${dev.startsWith('+') ? 'text-danger' : ''}">${dev}</b></div>
        <div class="aq-bld-tt-row"><span>Risk Score</span><b>${Math.round(b.risk_score || 0)} / 100</b></div>
      </div>`, {
      className: 'aq-building-tooltip',
      direction: 'top',
      offset: [0, -10],
      opacity: 1
    });

    poly.on('click', () => selectBuilding(b));
    buildingsGroup.addLayer(poly);
    buildingPolygons[b.name] = poly;

    // 2. Interactive building landmark badge at center
    if (b.center && b.center.length === 2) {
      const badgeIcon = L.divIcon({
        className: 'bld-badge-wrap',
        html: `
          <div class="bld-badge bld-${sev}" title="${b.name} (${sev.toUpperCase()})">
            <i class="bi ${b.icon || 'bi-building'}"></i>
            <span>${b.name}</span>
          </div>`,
        iconSize: [0, 0],
        iconAnchor: [0, 0]
      });

      const badgeMarker = L.marker(b.center, { icon: badgeIcon, interactive: true });
      badgeMarker.on('click', () => selectBuilding(b));
      buildingsGroup.addLayer(badgeMarker);
    }
  });
}

function selectBuilding(b, updateDropdown = true) {
  if (!b) return;
  window.__mapSelected = true;

  if (updateDropdown) {
    const sel = document.getElementById('filterBuilding');
    if (sel) sel.value = b.name;
  }

  // Highlight polygon
  Object.values(buildingPolygons).forEach(p => {
    const el = p.getElement();
    if (el) el.classList.remove('bld-focused');
  });

  const targetPoly = buildingPolygons[b.name];
  if (targetPoly) {
    const el = targetPoly.getElement();
    if (el) el.classList.add('bld-focused');
    mapInstance.flyToBounds(targetPoly.getBounds(), { padding: [70, 70], maxZoom: 17, duration: 0.7 });
  } else if (b.center) {
    mapInstance.flyTo(b.center, 16, { duration: 0.7 });
  }

  showBuildingPanel(b);

  // Filter meters display to this building
  filteredMeters = allMetersData.filter(m => (m.building || '') === b.name);
  renderMapMarkers(filteredMeters);
  renderHotZones(filteredMeters);
  updateMapStats(filteredMeters);

  const panelCount = document.getElementById('panelMeterCount');
  if (panelCount) panelCount.textContent = `${filteredMeters.length} meter${filteredMeters.length === 1 ? '' : 's'}`;
}

function showBuildingPanel(b) {
  const body = document.getElementById('mapIntelBody');
  if (!body) return;

  const sev = (b.severity || 'Normal').toLowerCase();
  const dev = b.deviation_pct != null ? `${b.deviation_pct >= 0 ? '+' : ''}${b.deviation_pct}%` : '—';
  const risk = b.risk_score != null ? Math.round(b.risk_score) : 0;
  const pct = Math.min(100, Math.max(5, risk));

  const buildingMeters = allMetersData.filter(m => (m.building || '') === b.name);
  const meterRows = buildingMeters.map(m => `
    <div class="reg-row">
      <div class="d-flex align-items-center justify-content-between gap-2">
        <div>
          <strong class="text-white font-mono small">${m.meter_id}</strong>
          <div class="reg-sub">${Math.round(m.current_usage || 0).toLocaleString()} L · ${m.activity_type || m.location}</div>
        </div>
        <span class="pill-severity pill-${getSeverityClass(m)}">${getSeverityClass(m).toUpperCase()}</span>
      </div>
      <div class="d-flex gap-2 mt-2">
        <button type="button" class="aq-btn aq-btn-ghost btn-sm w-100" onclick="showMeterPanel(findMeterById('${m.meter_id}'))">
          <i class="bi bi-speedometer2 me-1"></i>Inspect Telemetry
        </button>
      </div>
    </div>
  `).join('') || `<div class="reg-none text-secondary small">No discrete meters mapped to this facility.</div>`;

  body.classList.remove('swap');
  void body.offsetWidth;
  body.classList.add('swap');

  body.innerHTML = `
    <div class="mt-head">
      <div class="mt-title"><i class="bi ${b.icon || 'bi-building'} me-2 text-info"></i>Building Intelligence</div>
      <div class="d-flex align-items-center gap-1">
        <button type="button" class="aq-btn aq-btn-icon btn-sm" onclick="backToRegistry()" title="Back to registry"><i class="bi bi-arrow-left"></i></button>
        <button type="button" class="aq-btn aq-btn-ghost btn-sm fs-intel-close-btn" onclick="toggleFsIntel()" title="Hide panel"><i class="bi bi-x-lg"></i></button>
      </div>
    </div>
    <div class="mt-body">
      <div class="mt-meter-head">
        <div class="d-flex align-items-center justify-content-between gap-2">
          <strong class="mt-meter-id font-mono">${b.name}</strong>
          <span class="pill-severity pill-${sev}">${sev.toUpperCase()}</span>
        </div>
        <div class="mt-meter-loc">
          <span class="badge bg-dark border border-secondary text-info me-1">${b.location}</span>
          ${b.type || 'Facility'} · ${b.occupancy || '—'} occupants
        </div>
      </div>

      <div class="mt-grid">
        <div class="mt-cell"><span class="mt-cell-label">TOTAL FLOW</span><span class="mt-cell-val">${Math.round(b.current_usage || 0).toLocaleString()} L</span></div>
        <div class="mt-cell"><span class="mt-cell-label">BASELINE</span><span class="mt-cell-val">${Math.round(b.baseline || 0).toLocaleString()} L</span></div>
        <div class="mt-cell"><span class="mt-cell-label">DEVIATION</span><span class="mt-cell-val ${dev.startsWith('+') ? 'text-danger' : 'text-success'}">${dev}</span></div>
      </div>

      <div class="mt-section">
        <div class="mt-sec-label">CAMPUS RISK INDEX</div>
        <div class="d-flex align-items-center gap-2 mb-1">
          <div class="mt-risk-track"><div class="mt-risk-fill" style="width:${pct}%; background:${CLASS_COLOR[sev] || '#b0b3b6'};"></div></div>
          <strong class="font-mono">${risk}<small class="text-secondary">/100</small></strong>
        </div>
        <div class="d-flex justify-content-between small text-secondary">
          <span>Active Anomalies</span>
          <strong class="text-white">${b.anomaly_count || 0} registered</strong>
        </div>
      </div>

      <div class="mt-section">
        <div class="mt-sec-label">MONITORED METERS (${buildingMeters.length})</div>
        <div class="reg-list" style="max-height: 240px; overflow-y: auto;">${meterRows}</div>
      </div>

      <div class="d-flex gap-2 mt-3">
        <button type="button" class="aq-btn aq-btn-ghost flex-grow-1" onclick="focusBuilding('${b.name}')">
          <i class="bi bi-crosshair me-1"></i>Focus Footprint
        </button>
        <a class="aq-btn flex-grow-1 text-center" href="/anomalies?building=${encodeURIComponent(b.name)}">
          <i class="bi bi-search me-1"></i>Anomalies
        </a>
      </div>
    </div>`;

  const intel = document.getElementById('mapIntel');
  if (intel) {
    intel.classList.add('open');
    intel.classList.remove('collapsed');
  }
}

function focusBuilding(name) {
  const p = buildingPolygons[name];
  if (p && mapInstance) {
    mapInstance.flyToBounds(p.getBounds(), { padding: [60, 60], maxZoom: 17, duration: 0.8 });
  }
}

// ---------------------------------------------------------------------------
// METERS MARKERS
// ---------------------------------------------------------------------------
function getSeverityClass(m) {
  return classifyRisk(m);
}

function markerSizeFor(m) {
  const map = { 'normal': 12, 'moderate': 15, 'high': 18, 'critical': 22 };
  return map[getSeverityClass(m)] || 12;
}

function getRiskMarkerIcon(meter, delayMs) {
  const cls = getSeverityClass(meter);
  const s = markerSizeFor(meter);
  const color = CLASS_COLOR[cls] || '#b0b3b6';
  const crit = cls === 'critical';
  const high = cls === 'high';

  return L.divIcon({
    className: 'risk-marker-wrap',
    html: `
      <div class="risk-marker ${cls}" style="--d:${delayMs}ms; --c:${color}; --s:${s}px;">
        <span class="marker-ring r1"></span>
        <span class="marker-ring r2"></span>
        <span class="marker-core"></span>
        ${crit ? '<span class="marker-ring r3"></span>' : ''}
        ${high ? '<span class="marker-core-halo"></span>' : ''}
      </div>`,
    iconSize: [s * 3, s * 3],
    iconAnchor: [s * 1.5, s * 1.5]
  });
}

function markerTooltipHtml(m) {
  const cls = getSeverityClass(m);
  const dev = m.deviation_pct != null ? `${m.deviation_pct >= 0 ? '+' : ''}${m.deviation_pct.toFixed(1)}%` : '0.0%';
  const risk = m.risk_score != null ? Math.round(m.risk_score) : 24;
  const usage = (m.current_usage || 0).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const base = (m.baseline || (m.current_usage ? m.current_usage * 0.85 : 420.0)).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  
  let sevColor = '#00f2fe';
  let statusLabel = 'Optimal Flow';
  if (cls === 'critical') { sevColor = '#ff0055'; statusLabel = 'Critical Loss'; }
  else if (cls === 'high') { sevColor = '#f97316'; statusLabel = 'Surge Departure'; }
  else if (cls === 'moderate') { sevColor = '#fbbf24'; statusLabel = 'Moderate Departure'; }
  
  const estPressure = (3.2 + ((m.risk_score || 20) % 7) * 0.1).toFixed(1);

  return `
    <div style="min-width: 250px; padding: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
      <!-- Live Beacon Header -->
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.12);">
        <div style="display: flex; align-items: center; gap: 6px;">
          <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${sevColor}; box-shadow: 0 0 8px ${sevColor};"></span>
          <strong style="color: #ffffff; font-family: monospace; font-size: 13px;">${m.meter_id}</strong>
        </div>
        <span style="background: ${sevColor}25; color: ${sevColor}; border: 1px solid ${sevColor}55; border-radius: 6px; padding: 2px 7px; font-size: 10px; font-weight: 700; text-transform: uppercase;">${statusLabel}</span>
      </div>
      
      <!-- Facility & Location -->
      <div style="color: #ffffff; font-weight: 600; font-size: 12px; margin-bottom: 2px;">
        <i class="bi bi-geo-alt-fill" style="color: #00f2fe; margin-right: 4px;"></i>${m.building || 'Campus Facility'}
      </div>
      <div style="color: #94a3b8; font-size: 10.5px; margin-bottom: 10px;">${m.location || 'SNS Kalvi Nagar, Coimbatore'}</div>
      
      <!-- Live Real-Time Usage Card -->
      <div style="background: rgba(255,255,255,0.06); border-radius: 8px; padding: 8px 10px; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.08);">
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
          <span style="color: #94a3b8; font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">LIVE TELEMETRY FLOW</span>
          <span style="font-family: monospace; font-weight: 700; font-size: 15px; color: ${sevColor};">${usage} <small style="font-size: 10px; color: #94a3b8;">L/h</small></span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 5px; padding-top: 5px; border-top: 1px solid rgba(255,255,255,0.06); font-size: 11px;">
          <span style="color: #94a3b8;">Baseline: <b style="color: #fff; font-family: monospace;">${base} L/h</b></span>
          <span style="font-family: monospace; font-weight: 700; color: ${dev.startsWith('+') ? '#fbbf24' : '#10b981'};">${dev}</span>
        </div>
      </div>

      <!-- Advanced Sensor Diagnostics -->
      <div style="display: flex; justify-content: space-between; align-items: center; color: #94a3b8; font-size: 11px; margin-bottom: 6px;">
        <span>Pressure: <b style="color: #ffffff; font-family: monospace;">${estPressure} bar</b></span>
        <span>Risk: <b style="font-family: monospace; color: ${sevColor};">${risk} / 100</b></span>
      </div>

      <!-- Risk Meter Bar -->
      <div style="height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; overflow: hidden;">
        <div style="width: ${Math.min(100, Math.max(8, risk))}%; height: 100%; background: ${sevColor}; box-shadow: 0 0 6px ${sevColor};"></div>
      </div>
    </div>`;
}

function renderMapMarkers(meters) {
  if (!markersGroup) return;
  markersGroup.clearLayers();

  const valid = meters.filter(m => m.has_coords);
  const ordered = valid.slice().sort((a, b) => CLASS_ORDER.indexOf(getSeverityClass(a)) - CLASS_ORDER.indexOf(getSeverityClass(b)));

  ordered.forEach((m, idx) => {
    const tierBase = CLASS_ORDER.indexOf(getSeverityClass(m)) * 160;
    const delay = Math.min(tierBase + idx * 12, 700);

    const marker = L.marker([m.latitude, m.longitude], {
      icon: getRiskMarkerIcon(m, delay),
      title: `${m.meter_id} — ${getSeverityClass(m)}`
    });

    marker.bindTooltip(markerTooltipHtml(m), {
      className: 'aq-marker-tooltip',
      direction: 'top',
      offset: [0, -26],
      opacity: 1
    });

    marker.on('click', () => {
      showMeterPanel(m);
      focusMarker(marker);
    });

    markersGroup.addLayer(marker);
  });
}

function focusMarker(marker) {
  if (!mapInstance || !marker) return;
  const el = marker.getElement();
  if (el) {
    el.classList.add('focused');
    setTimeout(() => el.classList.remove('focused'), 900);
  }
}

// ---------------------------------------------------------------------------
// HOT-ZONE CLUSTERING
// ---------------------------------------------------------------------------
function haversineKm(aLat, aLng, bLat, bLng) {
  const R = 6371;
  const dLat = (bLat - aLat) * Math.PI / 180;
  const dLng = (bLng - aLng) * Math.PI / 180;
  const x = Math.sin(dLat / 2) ** 2 +
    Math.cos(aLat * Math.PI / 180) * Math.cos(bLat * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(x));
}

function buildRiskZones(meters) {
  const risk = meters.filter(m => m.has_coords && ['moderate', 'high', 'critical'].includes(getSeverityClass(m)));
  if (risk.length < 2) return [];

  const CLUSTER_RADIUS_KM = 0.9;
  const parent = risk.map((_, i) => i);
  const find = x => (parent[x] === x ? x : (parent[x] = find(parent[x])));
  const union = (a, b) => { parent[find(a)] = find(b); };

  for (let i = 0; i < risk.length; i++) {
    for (let j = i + 1; j < risk.length; j++) {
      if (haversineKm(risk[i].latitude, risk[i].longitude, risk[j].latitude, risk[j].longitude) <= CLUSTER_RADIUS_KM) {
        union(i, j);
      }
    }
  }

  const groups = {};
  risk.forEach((m, i) => {
    const root = find(i);
    (groups[root] = groups[root] || []).push(m);
  });

  const zones = [];
  Object.values(groups).forEach(group => {
    if (group.length < 2) return;
    let cLat = 0, cLng = 0;
    group.forEach(m => { cLat += m.latitude; cLng += m.longitude; });
    cLat /= group.length; cLng /= group.length;

    let maxSpread = 0;
    group.forEach(m => {
      maxSpread = Math.max(maxSpread, haversineKm(cLat, cLng, m.latitude, m.longitude) * 1000);
    });

    const critical = group.some(m => getSeverityClass(m) === 'critical');
    const high = group.some(m => getSeverityClass(m) === 'high');
    zones.push({
      lat: cLat,
      lng: cLng,
      radius: Math.max(maxSpread + 220, 420),
      color: critical ? '#e26d6d' : (high ? '#b0b3b6' : '#e8ece9'),
      count: group.length,
      label: critical ? 'Possible high-risk consumption zone' : 'Anomaly concentration zone'
    });
  });

  return zones;
}

function renderHotZones(meters) {
  if (!hotzonesGroup) return;
  hotzonesGroup.clearLayers();

  const zones = buildRiskZones(meters);
  zones.forEach(z => {
    const zone = L.circle([z.lat, z.lng], {
      radius: z.radius,
      color: z.color,
      weight: 1.1,
      opacity: 0.55,
      dashArray: '6 8',
      fillColor: z.color,
      fillOpacity: 0.08,
      interactive: false
    });
    zone.bindTooltip(`${z.label} — ${z.count} risk meters`, {
      className: 'aq-zone-tooltip',
      direction: 'center',
      opacity: 1
    });
    hotzonesGroup.addLayer(zone);

    const tag = L.marker([z.lat, z.lng], {
      icon: L.divIcon({
        className: 'zone-tag',
        html: `<span class="zone-tag-inner" style="--c:${z.color};">RISK ZONE×${z.count}</span>`,
        iconSize: [0, 0],
        iconAnchor: [0, 0]
      }),
      interactive: false
    });
    hotzonesGroup.addLayer(tag);
  });
}

// ---------------------------------------------------------------------------
// MAP STATUS PANEL
// ---------------------------------------------------------------------------
function updateMapStats(meters) {
  const set = (id, v) => {
    const el = document.getElementById(id);
    if (el) el.textContent = v;
  };
  const valid = meters.filter(m => m.has_coords);
  set('statMeters', valid.length);
  set('statAnomalies', meters.reduce((s, m) => s + (m.anomaly_count || 0), 0));
  set('statHigh', meters.filter(m => getSeverityClass(m) === 'high').length);
  set('statCritical', meters.filter(m => getSeverityClass(m) === 'critical').length);
}

// ---------------------------------------------------------------------------
// RIGHT INTELLIGENCE / REGISTRY PANEL
// ---------------------------------------------------------------------------
function showRegistryView(meters) {
  const body = document.getElementById('mapIntelBody');
  if (!body) return;

  const missing = meters.filter(m => !m.has_coords);
  const summary = missing.length === 0
    ? `<div class="reg-ok"><i class="bi bi-check-circle-fill"></i> All meters have valid coordinates.</div>`
    : `<div class="reg-warn"><i class="bi bi-exclamation-triangle-fill"></i> ${missing.length} meter${missing.length === 1 ? '' : 's'} need coordinates.</div>`;

  const rows = missing.map(m => `
    <div class="reg-row">
      <div class="d-flex align-items-center justify-content-between gap-2">
        <div>
          <strong class="text-white font-mono small">${m.meter_id}</strong>
          <div class="reg-sub">${m.location}${m.building ? ' • ' + m.building : ''}</div>
        </div>
        <span class="reg-tag-unmapped">No coordinates</span>
      </div>
      <div class="d-flex gap-2 mt-2">
        <button type="button" class="aq-btn aq-btn-ghost btn-sm" onclick="showMeterPanel(findMeterById('${m.meter_id}'))">View</button>
        <a class="aq-btn aq-btn-ghost btn-sm text-info" href="/meters" title="Assign coordinates in the meter registry">Add Coordinates</a>
      </div>
    </div>`).join('') || `<div class="reg-none"><i class="bi bi-pin-map"></i> All meters are geospatially pinned.</div>`;

  body.innerHTML = `
    <div class="mt-head">
      <div class="d-flex flex-column">
        <div class="mt-title"><i class="bi bi-diagram-3 me-2"></i>Registry</div>
        <small class="font-mono text-muted">CAMPUS GEOMETRY</small>
      </div>
      <button type="button" class="aq-btn aq-btn-ghost btn-sm fs-intel-close-btn" onclick="toggleFsIntel()" title="Hide panel"><i class="bi bi-x-lg"></i></button>
    </div>
    <div class="mt-body">
      <p class="reg-copy">Click any building or meter marker on the map to inspect live consumption telemetry, baseline deviations, and anomaly records.</p>
      ${summary}
      <div class="reg-list">${rows}</div>
      <a class="aq-btn aq-btn-ghost w-100 text-center" href="/meters"><i class="bi bi-sliders me-1"></i> Manage Meter Registry</a>
    </div>`;
}

function findMeterById(id) {
  return allMetersData.find(m => m.meter_id === id) || null;
}

function showMeterPanel(meter) {
  if (!meter) return;
  const body = document.getElementById('mapIntelBody');
  if (!body) return;
  window.__mapSelected = true;

  const sevCls = getSeverityClass(meter);
  const dev = meter.deviation_pct != null
    ? `${meter.deviation_pct >= 0 ? '+' : ''}${meter.deviation_pct.toFixed(0)}%`
    : '—';
  const usage = Math.round(meter.current_usage || 0).toLocaleString();
  const base = Math.round(meter.baseline || 0).toLocaleString();
  const risk = meter.risk_score != null ? meter.risk_score.toFixed(0) : '—';
  const pct = Math.min(100, Math.max(0, meter.risk_score || 0));
  const anomalyBlock = meter.anomaly_id
    ? `<div class="mt-section">
         <div class="mt-sec-label">LATEST ANOMALY</div>
         <div class="mt-anom">
           <div class="mt-anom-type">${meter.anomaly_type || 'Detected deviation'}</div>
           <div class="d-flex justify-content-between small text-secondary mt-1">
             <span><i class="bi bi-clock me-1"></i>${meter.anomaly_time || '—'}</span>
             <span class="badge bg-secondary font-mono">${meter.anomaly_status || 'New'}</span>
           </div>
         </div>
       </div>`
    : `<div class="mt-section"><div class="mt-sec-label">LATEST ANOMALY</div><div class="text-secondary small text-success"><i class="bi bi-check-circle-fill me-1"></i> No anomalies registered.</div></div>`;

  const center = document.createElement('a');
  center.href = meter.anomaly_id
    ? `/anomalies/${meter.anomaly_id}`
    : `/anomalies?meter_id=${encodeURIComponent(meter.meter_id)}`;

  body.classList.remove('swap');
  void body.offsetWidth;
  body.classList.add('swap');

  body.innerHTML = `
    <div class="mt-head">
      <div>
        <div class="mt-title"><i class="bi bi-droplet-half me-2"></i>Meter Intelligence</div>
      </div>
      <div class="d-flex align-items-center gap-1">
        <button type="button" class="aq-btn aq-btn-ghost btn-sm py-0 px-2" onclick="backToRegistry()" title="Back to registry"><i class="bi bi-arrow-left me-1"></i>Registry</button>
        <button type="button" class="aq-btn aq-btn-ghost btn-sm fs-intel-close-btn" onclick="toggleFsIntel()" title="Hide panel"><i class="bi bi-x-lg"></i></button>
      </div>
    </div>
    <div class="mt-body">
      <div class="mt-meter-head">
        <div class="d-flex align-items-center justify-content-between gap-2">
          <strong class="mt-meter-id font-mono">${meter.meter_id}</strong>
          <span class="pill-severity pill-${sevCls}" title="Live risk class from current deviation vs baseline">${sevCls.toUpperCase()}</span>
        </div>
        <div class="mt-meter-loc">${meter.location}${meter.building && meter.building !== 'Main Facility' ? ' • ' + meter.building : ''}
          <span class="reg-sub ms-1">· severity: ${meter.severity || '—'}</span>
        </div>
      </div>

      <div class="mt-grid">
        <div class="mt-cell"><span class="mt-cell-label">CURRENT</span><span class="mt-cell-val">${usage} L</span></div>
        <div class="mt-cell"><span class="mt-cell-label">BASELINE</span><span class="mt-cell-val">${base} L</span></div>
        <div class="mt-cell"><span class="mt-cell-label">DEVIATION</span><span class="mt-cell-val ${dev.startsWith('+') ? 'text-danger' : ''}">${dev}</span></div>
      </div>

      <div class="mt-section">
        <div class="mt-sec-label">AQUAGUARD RISK SCORE</div>
        <div class="d-flex align-items-center gap-2 mb-1">
          <div class="mt-risk-track"><div class="mt-risk-fill" style="width:${pct}%; background:${CLASS_COLOR[sevCls] || '#b0b3b6'};"></div></div>
          <strong class="font-mono">${risk}<small class="text-secondary">/100</small></strong>
        </div>
        <div class="d-flex justify-content-between small">
          <span class="text-secondary">Status</span>
          <strong class="text-white">${meter.anomaly_status || 'Nominal'}</strong>
        </div>
      </div>

      ${anomalyBlock}

      <div class="d-flex gap-2 mt-3">
        <a class="aq-btn aq-btn-ghost flex-grow-1 text-center text-danger" href="/anomalies?meter_id=${encodeURIComponent(meter.meter_id)}" title="All anomalies for this meter"><i class="bi bi-shield-exclamation me-1"></i>History</a>
      </div>
      <div class="mt-invest">
        <a class="aq-btn w-100 text-center" id="mapInvestigateLink" href="${center.href}"><i class="bi bi-search me-1"></i> Investigate</a>
      </div>
    </div>`;

  const intel = document.getElementById('mapIntel');
  if (intel) {
    intel.classList.add('open');
    intel.classList.remove('collapsed');
  }
}

function backToRegistry() {
  window.__mapSelected = false;
  showRegistryView(filteredMeters && filteredMeters.length ? filteredMeters : allMetersData);
  closeMeterPanel();
}

function closeMeterPanel() {
  const intel = document.getElementById('mapIntel');
  if (intel) intel.classList.remove('open');
}

function renderRegistry(meters) {
  const hasSelection = window.__mapSelected;
  if (!hasSelection) showRegistryView(meters);
}

// ---------------------------------------------------------------------------
// MAP ACTIONS
// ---------------------------------------------------------------------------
function fitToPoints(pts, mode) {
  if (!mapInstance || !pts.length) return;
  if (pts.length === 1) {
    mapInstance.setView(pts[0], mode === 'preserve' ? mapInstance.getZoom() : 15, { animate: true });
    return;
  }
  mapInstance.fitBounds(pts, { padding: [60, 60], maxZoom: 16 });
}

function validCoordsAll() {
  return allMetersData.filter(m => m.has_coords).map(m => [m.latitude, m.longitude]);
}

function showCriticalMeters() {
  const critical = filterMetersList().filter(m => getSeverityClass(m) === 'critical' && m.has_coords);
  if (!critical.length) {
    if (typeof showToast === 'function') {
      showToast('No Critical Meters', 'No critical-meter risk in the selected dataset.', 'warning');
    }
    return;
  }
  const sel = document.getElementById('filterSeverity');
  if (sel) sel.value = 'critical';
  filteredMeters = critical;
  renderMapMarkers(critical);
  renderHotZones(critical);
  updateMapStats(critical);
  const panelCount = document.getElementById('panelMeterCount');
  if (panelCount) panelCount.textContent = `${critical.length} meter${critical.length === 1 ? '' : 's'}`;
  fitToPoints(critical.map(m => [m.latitude, m.longitude]), 'critical');
  const stage = document.getElementById('mapStage');
  if (stage) stage.classList.add('filtered');
}

function selectFirstSearchResult() {
  const q = (document.getElementById('mapSearchInput')?.value || '').toLowerCase().trim();
  if (!q) return;

  // Check buildings first
  const bHit = allBuildingsData.find(b =>
    (`${b.name} ${b.location} ${b.type || ''}`.toLowerCase().includes(q))
  );
  if (bHit) {
    selectBuilding(bHit);
    return;
  }

  // Check meters
  const hit = filteredMeters.find(m => m.has_coords &&
    (`${m.meter_id} ${m.location} ${m.building || ''}`.toLowerCase().includes(q)));
  if (!hit) return;
  if (mapInstance) mapInstance.flyTo([hit.latitude, hit.longitude], Math.max(mapInstance.getZoom(), 16), { duration: 0.7 });
  showMeterPanel(hit);
}

// ---------------------------------------------------------------------------
// FULLSCREEN CONTROLLER & RESPONSIVE ADAPTATION
// ---------------------------------------------------------------------------
function isMapFullscreenActive() {
  const stage = document.getElementById('mapStage');
  if (!stage) return false;
  return Boolean(
    document.fullscreenElement === stage ||
    document.webkitFullscreenElement === stage ||
    document.mozFullScreenElement === stage ||
    document.msFullscreenElement === stage ||
    stage.classList.contains('fs')
  );
}

function enterMapFullscreen() {
  const stage = document.getElementById('mapStage');
  if (!stage) return;

  const requestFn = stage.requestFullscreen ||
                    stage.webkitRequestFullscreen ||
                    stage.mozRequestFullScreen ||
                    stage.msRequestFullscreen;

  if (requestFn) {
    try {
      const p = requestFn.call(stage);
      if (p && p.catch) {
        p.catch(() => applyFullscreenUI(true));
      } else {
        applyFullscreenUI(true);
      }
    } catch (e) {
      applyFullscreenUI(true);
    }
  } else {
    applyFullscreenUI(true);
  }
}

function exitMapFullscreen() {
  const stage = document.getElementById('mapStage');
  if (!stage) return;

  const isNative = Boolean(
    document.fullscreenElement ||
    document.webkitFullscreenElement ||
    document.mozFullScreenElement ||
    document.msFullscreenElement
  );

  if (isNative) {
    const exitFn = document.exitFullscreen ||
                   document.webkitExitFullscreen ||
                   document.mozCancelFullScreen ||
                   document.msExitFullscreen;
    if (exitFn) {
      try {
        const p = exitFn.call(document);
        if (p && p.catch) p.catch(() => {});
      } catch (e) {}
    }
  }
  applyFullscreenUI(false);
}

function toggleMapFullscreen() {
  if (isMapFullscreenActive()) {
    exitMapFullscreen();
  } else {
    enterMapFullscreen();
  }
}

function applyFullscreenUI(active) {
  const stage = document.getElementById('mapStage');
  const btn = document.getElementById('btnFullscreen');
  const exitBanner = document.getElementById('btnExitFsBanner');
  const intel = document.getElementById('mapIntel');
  const panelCol = document.getElementById('mapPanelCol');

  if (!stage) return;

  if (active) {
    stage.classList.add('fs');
    document.body.classList.add('map-fullscreen-active');
    if (btn) {
      btn.innerHTML = '<i class="bi bi-fullscreen-exit"></i>';
      btn.title = 'Exit Fullscreen (Esc)';
      btn.setAttribute('aria-label', 'Exit Fullscreen');
      btn.classList.add('active');
    }
    if (exitBanner) exitBanner.style.display = 'inline-flex';

    // Dock intel panel inside fullscreen stage so user can view/inspect meters
    if (intel && !stage.contains(intel)) {
      stage.appendChild(intel);
    }
    if (intel) {
      intel.classList.remove('collapsed');
    }
  } else {
    stage.classList.remove('fs');
    document.body.classList.remove('map-fullscreen-active');
    if (btn) {
      btn.innerHTML = '<i class="bi bi-arrows-fullscreen"></i>';
      btn.title = 'Fullscreen';
      btn.setAttribute('aria-label', 'Toggle fullscreen');
      btn.classList.remove('active');
    }
    if (exitBanner) exitBanner.style.display = 'none';

    // Restore intel panel back to right sidebar column
    if (intel && panelCol && !panelCol.contains(intel)) {
      panelCol.appendChild(intel);
    }
    if (intel) {
      intel.classList.remove('collapsed');
    }
  }

  // Trigger leaflet redraw at multiple intervals to guarantee smooth rendering
  const triggerResize = () => {
    if (mapInstance) {
      mapInstance.invalidateSize();
    }
  };
  triggerResize();
  setTimeout(triggerResize, 80);
  setTimeout(triggerResize, 200);
  setTimeout(triggerResize, 450);
}

function toggleFsIntel() {
  const intel = document.getElementById('mapIntel');
  if (!intel) return;
  intel.classList.toggle('collapsed');
}

// Sync with browser native fullscreen change events (e.g., when user presses Escape key)
['fullscreenchange', 'webkitfullscreenchange', 'mozfullscreenchange', 'MSFullscreenChange'].forEach(evt => {
  document.addEventListener(evt, () => {
    const stage = document.getElementById('mapStage');
    const isNativeFs = Boolean(
      document.fullscreenElement === stage ||
      document.webkitFullscreenElement === stage ||
      document.mozFullScreenElement === stage ||
      document.msFullscreenElement === stage
    );
    applyFullscreenUI(isNativeFs);
  });
});

// Escape key listener for CSS fullscreen fallback
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' || e.key === 'Esc') {
    if (isMapFullscreenActive()) {
      exitMapFullscreen();
    }
  }
});

// Window resize listener
window.addEventListener('resize', () => {
  if (mapInstance) {
    mapInstance.invalidateSize();
  }
});

// Auto-bootstrap map if #map exists on page
if (document.getElementById('map')) {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      if (!mapInstance) initAquaMap();
    });
  } else {
    if (!mapInstance) initAquaMap();
  }
}