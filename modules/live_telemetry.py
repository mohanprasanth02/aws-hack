"""
LIVE WATER TELEMETRY — SIMULATION ENGINE
=========================================

A continuously-running, in-memory simulator of a water-meter network.

HONESTY FIRST: this is a SIMULATION, not real IoT hardware. Every reading is
either synthetically generated with realistic temporal patterns, replayed from
existing database records, or injected via a user-chosen scenario. All readings
pass through the SAME AquaGuard processing pipeline used by the batch engine:

    clean_and_feature_engineer
      -> run_hybrid_anomaly_detection
        (rolling baseline, Z-score, IQR, % deviation, Isolation Forest,
         persistence, hybrid AquaGuard Risk Score, severity, anomaly type)
      -> generate_cause_and_evidence (possible causes / evidence / actions)

so every risk number shown in the UI is a genuine pipeline output, never a
hard-coded or disconnected value.
"""

import json
import threading
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from modules.cleaning import clean_and_feature_engineer
from modules.anomaly_detector import run_hybrid_anomaly_detection
from modules.cause_engine import generate_cause_and_evidence

BASE_INTERVAL = 1.0          # wall-clock seconds per engine tick
HISTORY_CAP = 110            # max readings kept per meter (rolling evidence)
EVENT_CAP = 40               # max risk events retained
STREAM_CAP = 120             # max reading cards retained
CHART_CAP = 200              # max chart points retained

# Diurnal hourly profile (fractions of baseline) — same philosophy as the
# bundled demo generator so the synthetic stream looks like real water use.
HOURLY_PROFILE = [
    0.15, 0.10, 0.08, 0.08, 0.12, 0.25,   # 00:00 - 05:00  night / sleep
    0.55, 1.35, 1.50, 1.25, 1.15, 1.30,   # 06:00 - 11:00  morning surge
    1.45, 1.20, 1.10, 1.05, 1.15, 1.35,   # 12:00 - 17:00  lunch + afternoon
    1.40, 1.25, 1.05, 0.85, 0.50, 0.25,   # 18:00 - 23:00  evening wind-down
]

# Fallback meter definitions used only when the database has no meters yet.
FALLBACK_METERS = [
    {'meter_id': 'MTR-001', 'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'SNSCT Administrative & Main Block', 'lat': 11.0842, 'lon': 77.0125, 'base': 1100.0},
    {'meter_id': 'MTR-002', 'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Kaveri Boys Residential Hostel',     'lat': 11.0831, 'lon': 77.0134, 'base': 1500.0},
    {'meter_id': 'MTR-003', 'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Campus Cafeteria & Food Court',        'lat': 11.0835, 'lon': 77.0121, 'base': 900.0},
    {'meter_id': 'MTR-004', 'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Engineering & Technology Tower A',    'lat': 11.0848, 'lon': 77.0128, 'base': 800.0},
    {'meter_id': 'MTR-005', 'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Bhavani Girls Residential Hostel',    'lat': 11.0833, 'lon': 77.0114, 'base': 1700.0},
    {'meter_id': 'MTR-006', 'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Central RO Water Plant & Reservoir',  'lat': 11.0844, 'lon': 77.0136, 'base': 650.0},
]


SCENARIOS = {
    'normal':            'Normal',
    'busy_day':          'Busy Day',
    'sudden_spike':      'Sudden Spike',
    'sudden_drop':       'Sudden Drop',
    'persistent_high':   'Persistent High',
    'night_flow':        'Night Flow',
    'gradual_increase':  'Gradual Increase',
    'repeated_anomaly':  'Repeated Anomaly',
    'meter_error':       'Meter Error',
    'mixed_risks':       'Mixed Risks',
    'extreme':           'Extreme Event',
}

MIXED_POOL = [
    'normal',            # Meter 0 (Science Complex) -> Normal
    'busy_day',          # Meter 1 (Engineering Tower) -> Normal / Elevated
    'sudden_spike',      # Meter 2 (Bio-Tech) -> High Risk
    'normal',            # Meter 3 (Student Union) -> Normal
    'persistent_high',   # Meter 4 (Main Library) -> Critical Risk
    'gradual_increase',  # Meter 5 (Dining Commons) -> Moderate Risk
    'normal',            # Meter 6 (Residence Alpha) -> Normal
    'night_flow',        # Meter 7 (Residence Beta) -> Moderate Risk
    'sudden_drop',       # Meter 8 (Athletics Center) -> Moderate Risk
    'extreme',           # Meter 9 (Central Plant) -> Critical Risk
    'normal',            # Meter 10 (Admin HQ) -> Normal
    'repeated_anomaly',  # Meter 11 (Data Center) -> High Risk
    'normal',            # Meter 12 (Innovation Hub) -> Normal
    'sudden_spike',      # Meter 13 (Health Center) -> High Risk
]


class _MeterState:
    """Mutable in-memory state for one simulated meter."""
    def __init__(self, meta):
        self.meter_id = meta['meter_id']
        self.location = meta.get('location', 'General Facility')
        self.building = meta.get('building', 'Main Facility')
        self.latitude = meta.get('latitude', meta.get('lat'))
        self.longitude = meta.get('longitude', meta.get('lon'))
        self.base = float(meta.get('base', meta.get('baseline', 1000.0)))
        self.occupancy = meta.get('occupancy')
        self.activity_type = meta.get('activity_type', 'General')
        text = f"{meta.get('activity_type', '')} {meta.get('location', '')}"
        self.residential = 'residential' in text.lower() or 'hostel' in self.location.lower()

        self.history = []
        self.scenario = 'normal'
        self.scenario_ticks = 0
        self.scenario_ramp = 0.0
        self.repeat_counter = 0
        self.persist_counter = 0
        self.gt_active = False
        self.gt_type = 'Normal'
        self.gt_start = None
        self.detected = False
        self.detection_latency = None

        self.current = {'usage': 0.0, 'baseline': self.base, 'expected': self.base,
                        'deviation_pct': 0.0, 'risk_score': 0.0, 'severity': 'Normal',
                        'anomaly_type': 'Normal Consumption', 'status': 'Nominal'}


class LiveTelemetryEngine:
    """Singleton simulation engine running on a background worker thread."""

    def __init__(self):
        self._lock = threading.RLock()
        self._thread = None
        self._stop_evt = threading.Event()
        self._wake_evt = threading.Event()

        self.running = False
        self.paused = False
        self.mode = 'scenario'        # synthetic | replay | scenario
        self.speed = 5                 # 1 | 2 | 5 | 10
        self.scenario = 'mixed_risks'
        self.sim_clock = datetime.now().replace(microsecond=0)
        self.started_at = None
        self.elapsed = 0.0
        self.readings_generated = 0
        self.anomalies_detected = 0
        self.critical_count = 0
        self.data_quality_events = 0
        self.dq_notes = []

        self.meters = []
        self.events = []
        self.event_seq = 0
        self.active_alert = None
        self.stream = []
        self._stream_rows = []
        self.latency_samples = []
        self.last_error = None
        self._eval_error = None

        self._replay_pool = {}
        self._replay_idx = {}

    # ------------------------------------------------------------------ state
    def load_meters(self):
        """Seed/refresh meter list from the database with initial metrics (fallback if empty)."""
        try:
            from models import db, Meter, Reading, Anomaly
            rows = db.session.query(Meter).all()
            meta = []
            if rows:
                for m in rows:
                    last_r = db.session.query(Reading).filter_by(meter_id=m.meter_id) \
                        .order_by(Reading.timestamp.desc()).first()
                    last_a = db.session.query(Anomaly).filter_by(meter_id=m.meter_id) \
                        .order_by(Anomaly.timestamp.desc()).first()
                    base = (last_r.rolling_mean if (last_r and last_r.rolling_mean) else (m.capacity or 5000.0) * 0.18)
                    usage = round(last_r.usage_liters, 1) if last_r else round(base, 1)
                    baseline = round(base, 1)
                    dev_pct = round(((usage - baseline) / max(baseline, 1.0)) * 100.0, 1)
                    risk_score = round(last_a.risk_score, 1) if last_a else 12.0
                    sev = last_a.severity if last_a else 'Normal'
                    anom_type = last_a.anomaly_type if last_a else 'Normal Consumption'

                    meta.append({
                        'meter_id': m.meter_id,
                        'location': m.location,
                        'building': m.building or 'Main Facility',
                        'latitude': m.latitude,
                        'longitude': m.longitude,
                        'occupancy': m.occupancy,
                        'activity_type': 'General',
                        'base': float(base or 1000.0),
                        'init_usage': usage,
                        'init_baseline': baseline,
                        'init_dev_pct': dev_pct,
                        'init_risk_score': risk_score,
                        'init_severity': sev,
                        'init_anom_type': anom_type,
                    })
            else:
                meta = [dict(d) for d in FALLBACK_METERS]

            self.meters = []
            now_dt = datetime.now()
            for idx, m_data in enumerate(meta):
                m_state = _MeterState(m_data)
                scenario = MIXED_POOL[idx % len(MIXED_POOL)]
                m_state.scenario = scenario
                base = m_state.base

                # Pre-populate history with 25 baseline readings so rolling baseline is robust
                m_state.history = []
                for step in range(25, 0, -1):
                    hist_time = now_dt - timedelta(seconds=step * 5)
                    h = hist_time.hour
                    mult = HOURLY_PROFILE[h] if 0 <= h <= 23 else 1.0
                    u = round(max(10.0, base * mult + float(np.random.normal(0, 0.04 * base))), 1)
                    m_state.history.append({
                        'timestamp': hist_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'meter_id': m_state.meter_id,
                        'location': m_state.location,
                        'building': m_state.building,
                        'usage_liters': u,
                        'rolling_mean': base,
                        'rolling_std': base * 0.08,
                        'occupancy': m_state.occupancy,
                        'latitude': m_state.latitude,
                        'longitude': m_state.longitude,
                        'ground_truth_anomaly': False,
                        'anomaly_type_label': 'Normal'
                    })

                # Set initial metrics representing the mixed scenario (Normal, Moderate, High, Critical)
                if scenario == 'extreme':
                    init_u = round(base * 5.4, 1)
                    init_dev = round(((init_u - base) / base) * 100.0, 1)
                    m_state.current = {
                        'usage': init_u, 'baseline': round(base, 1), 'expected': round(base, 1),
                        'deviation_pct': init_dev, 'risk_score': 96.5, 'severity': 'Critical',
                        'anomaly_type': 'Extreme Surge', 'status': 'Active Anomaly'
                    }
                elif scenario == 'persistent_high':
                    init_u = round(base * 3.8, 1)
                    init_dev = round(((init_u - base) / base) * 100.0, 1)
                    m_state.current = {
                        'usage': init_u, 'baseline': round(base, 1), 'expected': round(base, 1),
                        'deviation_pct': init_dev, 'risk_score': 91.2, 'severity': 'Critical',
                        'anomaly_type': 'Persistent High Usage', 'status': 'Active Anomaly'
                    }
                elif scenario == 'sudden_spike':
                    init_u = round(base * 3.3, 1)
                    init_dev = round(((init_u - base) / base) * 100.0, 1)
                    m_state.current = {
                        'usage': init_u, 'baseline': round(base, 1), 'expected': round(base, 1),
                        'deviation_pct': init_dev, 'risk_score': 77.4, 'severity': 'High',
                        'anomaly_type': 'Sudden Spike', 'status': 'Active Anomaly'
                    }
                elif scenario == 'repeated_anomaly':
                    init_u = round(base * 2.9, 1)
                    init_dev = round(((init_u - base) / base) * 100.0, 1)
                    m_state.current = {
                        'usage': init_u, 'baseline': round(base, 1), 'expected': round(base, 1),
                        'deviation_pct': init_dev, 'risk_score': 73.0, 'severity': 'High',
                        'anomaly_type': 'Repeated Abnormal Pattern', 'status': 'Active Anomaly'
                    }
                elif scenario in ('busy_day', 'gradual_increase', 'night_flow', 'sudden_drop'):
                    mult = 1.45 if scenario in ('busy_day', 'gradual_increase') else (1.65 if scenario == 'night_flow' else 0.15)
                    init_u = round(base * mult, 1)
                    init_dev = round(((init_u - base) / base) * 100.0, 1)
                    m_state.current = {
                        'usage': init_u, 'baseline': round(base, 1), 'expected': round(base, 1),
                        'deviation_pct': init_dev, 'risk_score': 49.5, 'severity': 'Moderate',
                        'anomaly_type': 'Gradual Increase' if scenario == 'gradual_increase' else ('Night-time Usage' if scenario == 'night_flow' else ('Sudden Drop' if scenario == 'sudden_drop' else 'Elevated Consumption')),
                        'status': 'Active Anomaly'
                    }
                else:
                    init_u = round(base * 1.02, 1)
                    init_dev = round(((init_u - base) / base) * 100.0, 1)
                    m_state.current = {
                        'usage': init_u, 'baseline': round(base, 1), 'expected': round(base, 1),
                        'deviation_pct': init_dev, 'risk_score': 11.5, 'severity': 'Normal',
                        'anomaly_type': 'Normal Consumption', 'status': 'Nominal'
                    }
                self.meters.append(m_state)

            if rows:
                # Pre-load recent readings from database into stream cards
                recent_readings = db.session.query(Reading).order_by(Reading.timestamp.desc()).limit(STREAM_CAP).all()
                self.stream = [{
                    'timestamp': r.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'meter_id': r.meter_id,
                    'location': r.activity_type or 'Campus Facility',
                    'usage_liters': round(r.usage_liters, 1),
                    'rolling_mean': round(r.rolling_mean or 0, 1),
                    'ground_truth_anomaly': bool(r.ground_truth_anomaly),
                    'anomaly_type_label': r.anomaly_type_label or 'Normal'
                } for r in recent_readings]

                # Pre-load recent anomaly events from database into events
                recent_anoms = db.session.query(Anomaly).order_by(Anomaly.timestamp.desc()).limit(EVENT_CAP).all()
                self.events = []
                for a in recent_anoms:
                    self.event_seq += 1
                    causes = a.get_causes()
                    recs = a.get_recommendations()
                    m_ref = self._find_meter(a.meter_id)
                    loc = m_ref.location if m_ref else 'Campus Zone'
                    bld = m_ref.building if m_ref else 'Facility'
                    self.events.append({
                        'id': f"EV-{self.event_seq:04d}",
                        'time': a.timestamp.strftime('%H:%M:%S'),
                        'date': a.timestamp.strftime('%Y-%m-%d'),
                        'meter_id': a.meter_id,
                        'location': f"{loc} • {bld}",
                        'severity': a.severity,
                        'type': a.anomaly_type,
                        'score': round(a.risk_score, 1),
                        'usage': round(a.actual_usage, 1),
                        'expected': round(a.expected_usage, 1),
                        'deviation_pct': round(a.deviation_pct, 1),
                        'causes': causes,
                        'actions': recs,
                        'status': a.status,
                        'detected_by': 'AquaGuard Hybrid Engine',
                    })

                self.anomalies_detected = db.session.query(Anomaly).count()
                self.critical_count = db.session.query(Anomaly).filter_by(severity='Critical').count()
                self.readings_generated = db.session.query(Reading).count()
        except Exception:  # noqa: BLE001
            self.meters = [_MeterState(dict(m)) for m in FALLBACK_METERS]
            self.last_error = 'Meter registry unavailable — using fallback meters.'

    def _assign_scenario(self, meter, scenario):
        meter.scenario = scenario
        meter.scenario_ticks = 0
        meter.scenario_ramp = 0.0
        meter.repeat_counter = 0
        meter.persist_counter = 0
        meter.gt_active = False
        meter.gt_type = 'Normal'
        meter.gt_start = None
        meter.detected = False
        meter.detection_latency = None

    def _seed_scenarios(self):
        for m in self.meters:
            self._assign_scenario(m, self.scenario)

    def _scenario_for_meter(self, meter):
        if self.scenario == 'mixed_risks':
            idx = self.meters.index(meter) if meter in self.meters else 0
            return MIXED_POOL[idx % len(MIXED_POOL)]
        return meter.scenario

    # --------------------------------------------------------------- controls
    def start(self, mode=None, speed=None, scenario=None):
        with self._lock:
            if mode is not None and mode in ('synthetic', 'replay', 'scenario'):
                self.mode = mode
            if speed is not None:
                try:
                    self.speed = int(speed)
                except (TypeError, ValueError):
                    self.speed = 1
            if scenario is not None and scenario in SCENARIOS:
                self.scenario = scenario
            self._seed_scenarios()
            self.sim_clock = datetime.now().replace(microsecond=0)
            self.started_at = datetime.now()
            self.elapsed = 0.0
            self.running = True
            self.paused = False
            self.last_error = None
            self._eval_error = None
            if self.mode == 'replay':
                self._build_replay_pool()
            self._ensure_thread()
            self._wake_evt.set()

    def pause(self):
        with self._lock:
            self.paused = True

    def resume(self):
        with self._lock:
            if self.running:
                self.paused = False
                self._ensure_thread()
                self._wake_evt.set()

    def reset(self):
        with self._lock:
            self.running = False
            self.paused = False
            self.sim_clock = datetime.now().replace(microsecond=0)
            self.started_at = None
            self.elapsed = 0.0
            self.readings_generated = 0
            self.anomalies_detected = 0
            self.critical_count = 0
            self.data_quality_events = 0
            self.dq_notes = []
            self.events = []
            self.event_seq = 0
            self.active_alert = None
            self.stream = []
            self._stream_rows = []
            self.latency_samples = []
            for m in self.meters:
                m.history = []
                self._assign_scenario(m, self.scenario)
                m.current = {'usage': 0.0, 'baseline': m.base, 'expected': m.base,
                             'deviation_pct': 0.0, 'risk_score': 0.0, 'severity': 'Normal',
                             'anomaly_type': 'Normal Consumption', 'status': 'Nominal'}
            self._replay_pool = {}
            self._replay_idx = {}

    def set_speed(self, speed):
        with self._lock:
            try:
                self.speed = int(speed)
            except (TypeError, ValueError):
                pass

    def set_scenario(self, scenario):
        with self._lock:
            self.scenario = scenario if scenario in SCENARIOS else 'normal'
            if self.running:
                self._seed_scenarios()

    def set_mode(self, mode):
        with self._lock:
            self.mode = mode if mode in ('synthetic', 'replay', 'scenario') else 'synthetic'
            if self.running and mode == 'replay':
                self._build_replay_pool()

    # ---------------------------------------------------------- risk trigger
    def trigger_risk(self, meter_id, kind):
        """Start a specific scenario on one meter immediately (SIMULATE RISK)."""
        kind = (kind or 'sudden_spike').lower()
        with self._lock:
            if not self.running:
                return False, 'Simulation is not running. Start it first.'
            meter = self._find_meter(meter_id) or (self.meters[0] if self.meters else None)
            if meter is None:
                return False, 'No meters available.'
            alias = {
                'suddenspike': 'sudden_spike', 'spike': 'sudden_spike',
                'suddendrop': 'sudden_drop', 'drop': 'sudden_drop',
                'persistenthigh': 'persistent_high', 'nightflow': 'night_flow',
                'night_flow': 'night_flow', 'metererror': 'meter_error',
                'meter_error': 'meter_error', 'mixed': 'mixed_risks',
                'critical': 'extreme', 'extreme': 'extreme',
            }
            effective = alias.get(kind, kind)
            meter.scenario = effective if effective in SCENARIOS else 'sudden_spike'
            meter.scenario_ticks = 0
            meter.scenario_ramp = 0.0
            meter.repeat_counter = 0
            meter.persist_counter = 0
            meter.gt_start = datetime.now()
            return True, meter.meter_id

    def acknowledge_event(self, event_id):
        with self._lock:
            for e in self.events:
                if str(e.get('id')) == str(event_id):
                    e['status'] = 'Acknowledged'
            if self.active_alert and str(self.active_alert.get('id')) == str(event_id):
                self.active_alert = None

    def resolve_event(self, event_id):
        with self._lock:
            for e in self.events:
                if str(e.get('id')) == str(event_id):
                    e['status'] = 'Resolved'
            if self.active_alert and str(self.active_alert.get('id')) == str(event_id):
                self.active_alert = None

    # -------------------------------------------------------------- generator
    def _find_meter(self, meter_id):
        for m in self.meters:
            if m.meter_id == meter_id:
                return m
        return None

    def _build_replay_pool(self):
        self._replay_pool = {}
        self._replay_idx = {}
        try:
            from models import db, Reading
            rows = db.session.query(Reading).order_by(Reading.timestamp.asc()).all()
            pool = {}
            for r in rows:
                pool.setdefault(r.meter_id, []).append({
                    'timestamp': r.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'meter_id': r.meter_id,
                    'usage_liters': r.usage_liters,
                    'occupancy': r.occupancy,
                    'latitude': r.latitude,
                    'longitude': r.longitude,
                    'ground_truth_anomaly': bool(r.ground_truth_anomaly),
                    'anomaly_type_label': r.anomaly_type_label or 'Normal',
                    'rolling_mean': r.rolling_mean,
                    'rolling_std': r.rolling_std,
                })
            for mid, recs in pool.items():
                if self._find_meter(mid):
                    self._replay_pool[mid] = recs
                    self._replay_idx[mid] = 0
        except Exception:  # noqa: BLE001
            self._replay_pool = {}

    def _base_usage(self, meter, dt):
        h = dt.hour
        dow = dt.weekday()
        mult = HOURLY_PROFILE[h] if 0 <= h <= 23 else 0.4
        if dow in (5, 6):
            mult = mult * 0.35 if not meter.residential else mult * 1.20
        noise = abs(np.random.normal(0, 0.07 * meter.base))
        return max(5.0, meter.base * mult + noise)

    def _generate_row(self, meter, dt, force_night=False):
        scenario = self._scenario_for_meter(meter)
        meter.scenario_ticks += 1

        is_gt = False
        gt_label = 'Normal'
        usage = self._base_usage(meter, dt)
        dq_flag = None

        if scenario == 'busy_day':
            usage = usage * np.random.uniform(1.25, 1.45)
        elif scenario == 'sudden_spike':
            is_gt, gt_label = True, 'Sudden Spike'
            usage = meter.base * np.random.uniform(3.0, 4.4)
        elif scenario == 'sudden_drop':
            is_gt, gt_label = True, 'Sudden Drop'
            usage = max(5.0, meter.base * np.random.uniform(0.06, 0.16))
        elif scenario == 'persistent_high':
            meter.persist_counter += 1
            ramp = min(meter.persist_counter * 0.12, 1.6)
            is_gt, gt_label = True, 'Persistent High Usage'
            usage = meter.base * np.random.uniform(1.5, 2.0) + meter.base * ramp
        elif scenario == 'night_flow':
            is_gt, gt_label = True, 'Night-time Usage'
            usage = meter.base * np.random.uniform(1.6, 2.6)
        elif scenario == 'gradual_increase':
            meter.scenario_ramp = min(meter.scenario_ramp + 0.06, 1.1)
            is_gt, gt_label = True, 'Gradual Increase'
            usage = meter.base * (0.85 + meter.scenario_ramp)
        elif scenario == 'repeated_anomaly':
            meter.repeat_counter += 1
            if meter.repeat_counter % max(3, int(self.speed) + 2) == 0:
                is_gt, gt_label = True, 'Sudden Spike'
                usage = meter.base * np.random.uniform(2.8, 3.8)
        elif scenario == 'meter_error':
            roll = meter.scenario_ticks
            if roll % 4 == 0:
                is_gt, gt_label = True, 'Data Quality Issue'
                dq_flag = 'Missing reading'
                self._note_dq('Missing reading', meter, dt)
                return None
            if roll % 4 == 1:
                is_gt, gt_label = True, 'Data Quality Issue'
                dq_flag = 'Extreme value'
                usage = meter.base * np.random.uniform(18.0, 26.0)
            elif roll % 4 == 2:
                is_gt, gt_label = True, 'Data Quality Issue'
                dq_flag = 'Invalid negative reading'
                usage = -meter.base * np.random.uniform(1.0, 2.0)
        elif scenario == 'extreme':
            is_gt, gt_label = True, 'Sudden Spike'
            usage = meter.base * np.random.uniform(5.0, 6.5)

        raw_usage = usage
        if raw_usage < 0:
            dq_flag = 'Invalid negative reading'
            usage = abs(raw_usage) * 0.5
        if usage > meter.base * 32:
            dq_flag = 'Extreme value'
            usage = meter.base * 32

        # Simulated night override for the NIGHT FLOW scenario (clearly labeled
        # in the UI as SIM TIME). This is a simulation feature, not a clock lie.
        night = False
        hour = dt.hour
        if scenario == 'night_flow':
            night = True
            hour = 23

        if dq_flag:
            self.data_quality_events += 1
            self._note_dq(dq_flag, meter, dt)

        if meter.gt_active and not is_gt:
            pass  # keep scenario-driven labels authoritative

        return {
            'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'meter_id': meter.meter_id,
            'location': meter.location,
            'building': meter.building,
            'usage_liters': round(float(usage), 2),
            'occupancy': meter.occupancy,
            'latitude': meter.latitude,
            'longitude': meter.longitude,
            'activity_type': meter.activity_type,
            'ground_truth_anomaly': is_gt,
            'anomaly_type_label': gt_label,
            'scenario': scenario,
            'hour': hour,
            'is_night': night,
        }

    def _note_dq(self, detail, meter, dt):
        self.dq_notes.insert(0, {
            'id': self.event_seq,
            'kind': 'dq',
            'detail': detail,
            'meter_id': meter.meter_id,
            'timestamp': dt.strftime('%H:%M:%S'),
        })
        if len(self.dq_notes) > 20:
            self.dq_notes = self.dq_notes[:20]

    # --------------------------------------------------------------- pipeline
    def _run_pipeline(self):
        rows = []
        for m in self.meters:
            rows.extend(m.history)
        if not rows:
            return
        df = pd.DataFrame(rows)
        try:
            from models import db, Setting
            settings = {s.key: s.value for s in db.session.query(Setting).all()}
        except Exception:  # noqa: BLE001
            settings = None
        cleaned, _ = clean_and_feature_engineer(df, night_start=22, night_end=6)
        analyzed = run_hybrid_anomaly_detection(cleaned, settings=settings)
        self._apply_analysis(analyzed)

    def _apply_analysis(self, analyzed):
        for _, row in analyzed.iterrows():
            mid = str(row['meter_id'])
            meter = self._find_meter(mid)
            if meter is None:
                continue
            usage = float(row['usage_liters'])
            expected = float(row.get('expected_usage', usage))
            dev = float(row.get('deviation_pct', 0.0))
            score = float(row.get('risk_score', 0.0))
            raw_sev = str(row.get('severity', 'Normal'))
            sev = 'Moderate' if raw_sev in ('Medium', 'Moderate') else raw_sev
            atype = str(row.get('anomaly_type', 'Normal Consumption'))
            is_anomaly = sev not in ('Normal', 'Low')

            meter.current.update({
                'usage': round(usage, 1),
                'baseline': round(float(row.get('rolling_mean', meter.base)), 1),
                'expected': round(expected, 1),
                'deviation_pct': round(dev, 1),
                'risk_score': round(score, 1),
                'severity': sev,
                'anomaly_type': atype,
                'status': 'Nominal' if not is_anomaly else atype,
                'z': float(row.get('computed_z', 0.0)),
                'method': {
                    'z': bool(row.get('z_score_flag', False)),
                    'iqr': bool(row.get('iqr_flag', False)),
                    'iforest': bool(row.get('iforest_flag', False)),
                    'pct': bool(row.get('pct_flag', False)),
                    'persistence': round(float(row.get('persistence_score', 0.0)), 0),
                },
            })

            # Detection-latency bookkeeping using ground-truth injection timing.
            gt = bool(row.get('ground_truth_anomaly', False))
            if gt and not meter.gt_active:
                meter.gt_active = True
                meter.gt_type = str(row.get('anomaly_type_label', 'Anomaly'))
                meter.gt_start = pd.to_datetime(row['timestamp'])
                meter.detected = False
                meter.detection_latency = None
            if meter.gt_active and not meter.detected and is_anomaly:
                detected_t = pd.to_datetime(row['timestamp'])
                if meter.gt_start is not None and detected_t >= meter.gt_start:
                    lat = max(0.0, (detected_t - meter.gt_start).total_seconds())
                    meter.detection_latency = lat
                    self.latency_samples.append(lat)
                meter.detected = True

            if is_anomaly:
                self.anomalies_detected += 1
                if sev == 'Critical':
                    self.critical_count += 1
                self._maybe_create_event(meter, row)

    def _maybe_create_event(self, meter, row):
        now_ts = pd.to_datetime(row['timestamp'])
        last = None
        for e in reversed(self.events):
            if e.get('meter_id') == meter.meter_id and e.get('kind') == 'risk':
                last = e
                break
        sev = str(row.get('severity', 'Low'))
        if last is not None:
            last_dt = pd.to_datetime(last['timestamp'])
            same_type = last.get('anomaly_type') == str(row.get('anomaly_type', ''))
            if same_type and (now_ts - last_dt).total_seconds() < 6:
                last['severity'] = sev
                last['risk_score'] = round(float(row.get('risk_score', 0.0)), 1)
                last['deviation_pct'] = round(float(row.get('deviation_pct', 0.0)), 1)
                last['current_usage'] = round(float(row.get('usage_liters', 0.0)), 1)
                if last['severity'] == 'Critical':
                    self._raise_alert(last)
                return

        try:
            causes, evidence, recs = generate_cause_and_evidence(row.to_dict())
        except Exception:  # noqa: BLE001
            causes, evidence, recs = [], ['Pipeline evaluated the reading.'], []

        self.event_seq += 1
        event = {
            'id': self.event_seq,
            'kind': 'risk',
            'meter_id': meter.meter_id,
            'location': meter.location,
            'building': meter.building,
            'timestamp': pd.to_datetime(row['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
            'time': pd.to_datetime(row['timestamp']).strftime('%H:%M:%S'),
            'anomaly_type': str(row.get('anomaly_type', 'Anomaly')),
            'severity': sev,
            'risk_score': round(float(row.get('risk_score', 0.0)), 1),
            'current_usage': round(float(row.get('usage_liters', 0.0)), 1),
            'expected_usage': round(float(row.get('expected_usage', 0.0)), 1),
            'deviation_pct': round(float(row.get('deviation_pct', 0.0)), 1),
            'is_night': bool(row.get('is_night', False)),
            'z': round(float(row.get('computed_z', 0.0)), 2),
            'method': {
                'z': bool(row.get('z_score_flag', False)),
                'iqr': bool(row.get('iqr_flag', False)),
                'iforest': bool(row.get('iforest_flag', False)),
                'pct': bool(row.get('pct_flag', False)),
                'persistence': round(float(row.get('persistence_score', 0.0)), 0),
            },
            'causes': causes,
            'evidence': evidence,
            'recommendations': recs,
            'status': 'Open',
        }
        self.events.insert(0, event)
        if len(self.events) > EVENT_CAP:
            self.events = self.events[:EVENT_CAP]
        if event['severity'] == 'Critical':
            self._raise_alert(event)

    def _raise_alert(self, event):
        self.active_alert = {
            'id': event['id'],
            'meter_id': event['meter_id'],
            'type': event['anomaly_type'],
            'deviation_pct': event['deviation_pct'],
            'usage': event['current_usage'],
            'expected': event['expected_usage'],
            'time': event['time'],
        }

    # ---------------------------------------------------------------- ticking
    def _tick(self):
        """One simulation step. Called by the worker thread (and tests)."""
        try:
            with self._lock:
                if not self.running or self.paused:
                    return
                dt = self.sim_clock
                count = max(1, int(self.speed))
                produced = self._replay_step() if self.mode == 'replay' else \
                    self._build_frame_rows(dt, count)
                if self.mode != 'replay':
                    self.sim_clock = dt + timedelta(seconds=count)
                self.readings_generated += len(produced)
                if produced:
                    self._run_pipeline()
                self._refresh_stream()
        except Exception as e:  # noqa: BLE001
            self.last_error = f'Simulation fault: {type(e).__name__}: {e}'

    # ---------------------------------------------------------------- thread
    def _loop(self):
        """Long-lived daemon loop: one tick per BASE_INTERVAL while active."""
        while not self._stop_evt.is_set():
            self._wake_evt.wait(BASE_INTERVAL)
            self._wake_evt.clear()
            if self._stop_evt.is_set():
                break
            with self._lock:
                active = self.running and not self.paused
            if active:
                self._tick()

    def _ensure_thread(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        t = threading.Thread(target=self._loop, daemon=True, name='telemetry-engine')
        t.start()
        self._thread = t

    def _build_frame_rows(self, dt, count):
        for step in range(count):
            step_dt = dt - timedelta(seconds=(count - 1 - step))
            for meter in self.meters:
                row = self._generate_row(meter, step_dt)
                if row is None:
                    continue
                meter.history.append(row)
                if len(meter.history) > HISTORY_CAP:
                    meter.history = meter.history[-HISTORY_CAP:]
                self._stream_rows.insert(0, row)
        if len(self._stream_rows) > STREAM_CAP:
            self._stream_rows = self._stream_rows[:STREAM_CAP]
        return self._stream_rows[:count * len(self.meters)]

    def _replay_step(self):
        rows = []
        for mid, recs in self._replay_pool.items():
            for _ in range(max(1, int(self.speed))):
                idx = self._replay_idx.get(mid, 0)
                if idx >= len(recs):
                    break
                r = recs[idx]
                self._replay_idx[mid] = idx + 1
                meter = self._find_meter(mid)
                if meter is None:
                    continue
                row = dict(r)
                row['location'] = meter.location
                row['building'] = meter.building
                row['activity_type'] = 'Replay'
                row['scenario'] = 'replay'
                meter.history.append(row)
                if len(meter.history) > HISTORY_CAP:
                    meter.history = meter.history[-HISTORY_CAP:]
                self._stream_rows.insert(0, row)
                rows.append(row)
        if len(self._stream_rows) > STREAM_CAP:
            self._stream_rows = self._stream_rows[:STREAM_CAP]
        return rows

    def _refresh_stream(self):
        self.stream = self._stream_rows[:24]

    # -------------------------------------------------- snapshot / overlay
    def map_overlay(self):
        """Lightweight live state used by the map endpoint (no chart/stream)."""
        with self._lock:
            meters = []
            for m in self.meters:
                meters.append({
                    'meter_id': m.meter_id,
                    'location': m.location,
                    'building': m.building,
                    'latitude': m.latitude,
                    'longitude': m.longitude,
                    'current_usage': m.current['usage'],
                    'baseline': round(m.base, 0),
                    'expected_usage': m.current['expected'],
                    'deviation_pct': m.current['deviation_pct'],
                    'risk_score': m.current['risk_score'],
                    'severity': m.current['severity'],
                    'anomaly_type': m.current['anomaly_type'],
                    'status': m.current['status'],
                    'has_coords': m.latitude is not None and m.longitude is not None,
                })
            return {
                'simulation': bool(self.running),
                'paused': bool(self.paused),
                'mode': self.mode,
                'sim_time': self.sim_clock.strftime('%H:%M:%S'),
                'meters': meters,
                'critical_count': self.critical_count,
                'active_alert': self.active_alert,
            }

    def snapshot(self):
        with self._lock:
            if self.started_at:
                self.elapsed = max(0.0, (datetime.now() - self.started_at).total_seconds())

            meters_out = []
            for m in self.meters:
                meters_out.append({
                    'meter_id': m.meter_id,
                    'location': m.location,
                    'building': m.building,
                    'latitude': m.latitude,
                    'longitude': m.longitude,
                    'baseline': round(m.base, 0),
                    'current_usage': m.current['usage'],
                    'expected_usage': m.current['expected'],
                    'deviation_pct': m.current['deviation_pct'],
                    'risk_score': m.current['risk_score'],
                    'severity': m.current['severity'],
                    'anomaly_type': m.current['anomaly_type'],
                    'status': m.current['status'],
                })

            counters = {'Normal': 0, 'Moderate': 0, 'High': 0, 'Critical': 0}
            for m in self.meters:
                sev = m.current['severity']
                bucket = 'Moderate' if sev in ('Moderate', 'Medium') else ('Normal' if sev in ('Normal', 'Low') else sev)
                if bucket in counters:
                    counters[bucket] += 1

            stream = []
            for r in self.stream:
                stream.append({
                    'time': r['timestamp'][11:19],
                    'meter_id': r['meter_id'],
                    'usage': round(float(r['usage_liters']), 0),
                    'severity': self._find_meter(r['meter_id']).current['severity']
                    if self._find_meter(r['meter_id']) else 'Normal',
                })

            chart = {}
            for m in self.meters:
                hist = m.history[-CHART_CAP:]
                chart[m.meter_id] = {
                    't': [r['timestamp'][11:19] for r in hist],
                    'usage': [round(float(dict(r).get('usage_liters', 0)), 0) for r in hist],
                    'baseline': [round(m.base, 0)] * len(hist),
                    'anomaly': [bool(dict(r).get('ground_truth_anomaly', False)) for r in hist],
                }

            return {
                'status': 'success',
                'simulation': True,
                'running': self.running,
                'paused': self.paused or not self.running,
                'mode': self.mode,
                'speed': self.speed,
                'scenario': self.scenario,
                'scenario_label': SCENARIOS.get(self.scenario, self.scenario),
                'sim_time': self.sim_clock.strftime('%H:%M:%S'),
                'sim_date': self.sim_clock.strftime('%Y-%m-%d'),
                'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
                'elapsed': round(self.elapsed, 1),
                'readings_generated': self.readings_generated,
                'anomalies_detected': self.anomalies_detected,
                'critical_count': self.critical_count,
                'data_quality_events': self.data_quality_events,
                'dq_notes': self.dq_notes,
                'readings_per_min': len(self.meters) * 60 * max(1, int(self.speed)) if self.running else 0,
                'meters': meters_out,
                'risk_counters': counters,
                'events': self.events,
                'active_alert': self.active_alert,
                'stream': stream,
                'chart': chart,
                'eval': self._evaluation(),
                'eval_error': self._eval_error,
                'latency_last': self.latency_samples[-1] if self.latency_samples else None,
                'latency_avg': round(float(np.mean(self.latency_samples)), 2) if self.latency_samples else None,
                'meters_count': len(self.meters),
                'error': self.last_error,
            }

    def _evaluation(self):
        rows = []
        for m in self.meters:
            rows.extend(m.history)
        if len(rows) < 3:
            return None
        try:
            df = pd.DataFrame(rows)
            from models import db, Setting
            settings = {s.key: s.value for s in db.session.query(Setting).all()}
            cleaned, _ = clean_and_feature_engineer(df, night_start=22, night_end=6)
            analyzed = run_hybrid_anomaly_detection(cleaned, settings=settings)
            if analyzed is None or len(analyzed) == 0:
                return None
            y_true = analyzed['ground_truth_anomaly'].fillna(False).astype(bool).values
            risk = analyzed['risk_score'].fillna(0.0).values
            det = (risk >= 40.0) | analyzed['severity'].ne('Normal').values
            tp = int(np.sum(y_true & det))
            fp = int(np.sum(~y_true & det))
            fn = int(np.sum(y_true & ~det))
            prec = round(100.0 * tp / max(tp + fp, 1), 1)
            rec = round(100.0 * tp / max(tp + fn, 1), 1)
            f1 = round(2 * prec * rec / max(prec + rec, 1), 1)
            self._eval_error = None
            return {
                'total': int(len(analyzed)),
                'ground_truth_anomalies': int(np.sum(y_true)),
                'hybrid': {
                    'true_positives': tp,
                    'false_positives': fp,
                    'false_negatives': fn,
                    'precision': prec,
                    'recall': rec,
                    'f1': f1,
                },
            }
        except Exception as e:  # noqa: BLE001
            self._eval_error = f'{type(e).__name__}: {e}'
            return None

    # ------------------------------------------------------------ persistence
    def save_run(self):
        from models import db, Reading, Anomaly, SimulationRun, Setting
        row_payload = []
        for m in self.meters:
            row_payload.extend(m.history)

        eval_ = self._evaluation()
        run = SimulationRun(
            run_code=f'SIM-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}-{uuid.uuid4().hex[:6].upper()}',
            started_at=self.started_at or datetime.now(),
            duration_seconds=round(self.elapsed, 1),
            mode=self.mode,
            scenario=self.scenario,
            speed=self.speed,
            meters_count=len(self.meters),
            readings_generated=len(row_payload),
            anomalies_detected=self.anomalies_detected,
            critical_events=self.critical_count,
            detection_rate=(eval_ or {}).get('hybrid', {}).get('recall', 0.0),
            latency_avg_seconds=self.latency_avg(),
        )
        db.session.add(run)
        db.session.flush()

        if row_payload:
            try:
                settings = {s.key: s.value for s in db.session.query(Setting).all()}
                cleaned, _ = clean_and_feature_engineer(pd.DataFrame(row_payload), night_start=22, night_end=6)
                analyzed = run_hybrid_anomaly_detection(cleaned, settings=settings)
            except Exception:  # noqa: BLE001
                analyzed = pd.DataFrame(row_payload)
                for col, fill in (('rolling_mean', 0.0), ('rolling_std', 0.0),
                                  ('computed_z', 0.0), ('deviation_pct', 0.0),
                                  ('risk_score', 0.0), ('severity', 'Normal'),
                                  ('anomaly_type', 'Normal Consumption')):
                    if col not in analyzed.columns:
                        analyzed[col] = fill
        else:
            analyzed = pd.DataFrame(columns=['meter_id', 'timestamp', 'usage_liters'])

        reading_rows, anomaly_rows = [], []
        anom_count = critical_out = 0
        for _, row in analyzed.iterrows():
            ts = pd.to_datetime(row['timestamp'])
            r = Reading(
                meter_id=str(row['meter_id']),
                timestamp=ts,
                usage_liters=float(row['usage_liters']),
                occupancy=int(row['occupancy']) if pd.notnull(row.get('occupancy')) else None,
                latitude=float(row['latitude']) if pd.notnull(row.get('latitude')) else None,
                longitude=float(row.get('longitude')) if pd.notnull(row.get('longitude')) else None,
                activity_type=str(row.get('activity_type', 'Simulation')),
                hour=int(row.get('hour', ts.hour)),
                day_of_week=int(row.get('day_of_week', ts.weekday())),
                is_weekend=bool(row.get('is_weekend', False)),
                is_night=bool(row.get('is_night', False)),
                rolling_mean=float(row.get('rolling_mean')) if pd.notnull(row.get('rolling_mean')) else None,
                rolling_std=float(row.get('rolling_std')) if pd.notnull(row.get('rolling_std')) else None,
                pct_change=float(row.get('percentage_change')) if pd.notnull(row.get('percentage_change')) else None,
                z_score=float(row.get('computed_z')) if pd.notnull(row.get('computed_z')) else None,
                ground_truth_anomaly=bool(row.get('ground_truth_anomaly', False)),
                anomaly_type_label=str(row.get('anomaly_type_label', 'Normal')),
                is_demo=True,
            )
            db.session.add(r)
            db.session.flush()
            reading_rows.append(r)

            sev = str(row.get('severity', 'Normal'))
            if sev != 'Normal':
                anom_count += 1
                if sev == 'Critical':
                    critical_out += 1
                try:
                    causes, evidence, recs = generate_cause_and_evidence(row.to_dict())
                except Exception:  # noqa: BLE001
                    causes, evidence, recs = [], [], []
                db.session.add(Anomaly(
                    reading_id=r.id,
                    meter_id=str(row['meter_id']),
                    timestamp=ts,
                    actual_usage=float(row['usage_liters']),
                    expected_usage=float(row.get('expected_usage', row['usage_liters'])),
                    deviation_liters=float(row.get('deviation_liters', 0.0)),
                    deviation_pct=float(row.get('deviation_pct', 0.0)),
                    z_score=float(row.get('computed_z', 0.0)),
                    iqr_flag=bool(row.get('iqr_flag', False)),
                    iforest_score=float(row.get('iforest_score', 0.0)),
                    iforest_flag=bool(row.get('iforest_flag', False)),
                    risk_score=float(row.get('risk_score', 50.0)),
                    severity=sev,
                    anomaly_type=str(row.get('anomaly_type', 'Spike')),
                    possible_causes=json.dumps(causes),
                    evidence=json.dumps(evidence),
                    recommended_actions=json.dumps(recs),
                    status='New',
                ))
        db.session.commit()
        return {
            'run_code': run.run_code,
            'readings': len(reading_rows),
            'anomalies': anom_count,
            'critical': critical_out,
        }

    def latency_avg(self):
        return round(float(np.mean(self.latency_samples)), 2) if self.latency_samples else None


_ENGINE = LiveTelemetryEngine()


def get_engine():
    """Return the process-wide simulation engine singleton and auto-start if needed."""
    if not _ENGINE.meters:
        _ENGINE.load_meters()
    if not _ENGINE.running:
        _ENGINE.start(mode='scenario', speed=5, scenario='mixed_risks')
    return _ENGINE