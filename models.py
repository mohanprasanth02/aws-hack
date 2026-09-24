from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='analyst')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Meter(db.Model):
    __tablename__ = 'meters'
    
    id = db.Column(db.Integer, primary_key=True)
    meter_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    location = db.Column(db.String(100), nullable=False, index=True)
    building = db.Column(db.String(100), nullable=True)
    capacity = db.Column(db.Float, nullable=True)  # Liters per hour or nominal max
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    installation_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Active')  # Active, Inactive, Maintenance
    occupancy = db.Column(db.Integer, nullable=True)
    area_sqm = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Reading(db.Model):
    __tablename__ = 'readings'
    
    id = db.Column(db.Integer, primary_key=True)
    meter_id = db.Column(db.String(50), db.ForeignKey('meters.meter_id', ondelete='CASCADE'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    usage_liters = db.Column(db.Float, nullable=False)
    occupancy = db.Column(db.Integer, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    activity_type = db.Column(db.String(50), nullable=True)
    
    # Preprocessed / Engineered Features
    hour = db.Column(db.Integer, nullable=True)
    day_of_week = db.Column(db.Integer, nullable=True)
    is_weekend = db.Column(db.Boolean, default=False)
    is_night = db.Column(db.Boolean, default=False)
    rolling_mean = db.Column(db.Float, nullable=True)
    rolling_std = db.Column(db.Float, nullable=True)
    pct_change = db.Column(db.Float, nullable=True)
    z_score = db.Column(db.Float, nullable=True)
    
    # Evaluation ground truth support
    is_demo = db.Column(db.Boolean, default=False)
    ground_truth_anomaly = db.Column(db.Boolean, default=False)
    anomaly_type_label = db.Column(db.String(50), nullable=True)
    
    run_id = db.Column(db.Integer, db.ForeignKey('analysis_runs.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Anomaly(db.Model):
    __tablename__ = 'anomalies'
    
    id = db.Column(db.Integer, primary_key=True)
    reading_id = db.Column(db.Integer, db.ForeignKey('readings.id', ondelete='CASCADE'), nullable=True)
    meter_id = db.Column(db.String(50), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    actual_usage = db.Column(db.Float, nullable=False)
    expected_usage = db.Column(db.Float, nullable=False)
    deviation_liters = db.Column(db.Float, nullable=False)
    deviation_pct = db.Column(db.Float, nullable=False)
    
    # Method Results
    z_score = db.Column(db.Float, nullable=True)
    iqr_flag = db.Column(db.Boolean, default=False)
    iforest_score = db.Column(db.Float, nullable=True)
    iforest_flag = db.Column(db.Boolean, default=False)
    
    # AquaGuard Hybrid Risk Score (0 - 100)
    risk_score = db.Column(db.Float, nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False, index=True)  # Normal, Low, Medium, High, Critical
    anomaly_type = db.Column(db.String(50), nullable=False)
    
    # Explainable AI JSON fields
    possible_causes = db.Column(db.Text, nullable=True)  # JSON list of hypotheses
    evidence = db.Column(db.Text, nullable=True)  # JSON list of facts/observations
    recommended_actions = db.Column(db.Text, nullable=True)  # JSON list of recommendations
    
    # Workflow status
    status = db.Column(db.String(20), default='New', index=True)  # New, Investigating, Acknowledged, Resolved, Dismissed
    run_id = db.Column(db.Integer, db.ForeignKey('analysis_runs.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def get_causes(self):
        try:
            return json.loads(self.possible_causes) if self.possible_causes else []
        except Exception:
            return []
            
    def get_evidence(self):
        try:
            return json.loads(self.evidence) if self.evidence else []
        except Exception:
            return []
            
    def get_recommendations(self):
        try:
            return json.loads(self.recommended_actions) if self.recommended_actions else []
        except Exception:
            return []

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    anomaly_id = db.Column(db.Integer, db.ForeignKey('anomalies.id', ondelete='CASCADE'), nullable=True)
    severity = db.Column(db.String(20), nullable=False, index=True)
    meter_id = db.Column(db.String(50), nullable=False, index=True)
    location = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    score = db.Column(db.Float, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Active', index=True)  # Active, Acknowledged, Resolved, Dismissed
    created_at = db.Column(db.DateTime, default=datetime.now)

class InvestigationNote(db.Model):
    __tablename__ = 'investigation_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    anomaly_id = db.Column(db.Integer, db.ForeignKey('anomalies.id', ondelete='CASCADE'), nullable=False)
    user_name = db.Column(db.String(100), default='System Analyst')
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Location(db.Model):
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    building = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class AnalysisRun(db.Model):
    __tablename__ = 'analysis_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    run_code = db.Column(db.String(64), unique=True, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    records_count = db.Column(db.Integer, default=0)
    valid_records = db.Column(db.Integer, default=0)
    invalid_records = db.Column(db.Integer, default=0)
    duplicate_records = db.Column(db.Integer, default=0)
    anomalies_found = db.Column(db.Integer, default=0)
    critical_count = db.Column(db.Integer, default=0)
    execution_time_seconds = db.Column(db.Float, default=0.0)
    data_quality_score = db.Column(db.Float, default=100.0)
    algorithms_used = db.Column(db.String(255), nullable=True)
    parameters = db.Column(db.Text, nullable=True)  # JSON parameters used
    status = db.Column(db.String(30), default='Completed')
    created_at = db.Column(db.DateTime, default=datetime.now)

class Setting(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    report_type = db.Column(db.String(50), default='PDF')  # PDF, CSV, Excel
    filepath = db.Column(db.String(255), nullable=False)
    filesize_kb = db.Column(db.Float, default=0.0)
    parameters = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class SimulationRun(db.Model):
    """Persisted record of a live-telemetry simulation run (PERSISTENT DEMO mode)."""
    __tablename__ = 'simulation_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    run_code = db.Column(db.String(64), unique=True, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    duration_seconds = db.Column(db.Float, default=0.0)
    mode = db.Column(db.String(20), default='synthetic')   # synthetic | replay | scenario
    scenario = db.Column(db.String(30), default='normal')
    speed = db.Column(db.Integer, default=1)
    meters_count = db.Column(db.Integer, default=0)
    readings_generated = db.Column(db.Integer, default=0)
    anomalies_detected = db.Column(db.Integer, default=0)
    critical_events = db.Column(db.Integer, default=0)
    detection_rate = db.Column(db.Float, default=0.0)      # hybrid recall %
    latency_avg_seconds = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
