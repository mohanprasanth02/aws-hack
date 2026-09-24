from datetime import datetime, timedelta
import io
import json
import os
import time
import uuid
import numpy as np
import pandas as pd
from flask import Blueprint, request, jsonify, send_file, current_app, session
from flask_login import login_required, current_user
from sqlalchemy import func, case, or_
from werkzeug.utils import secure_filename

from models import db, User, Meter, Reading, Anomaly, Alert, Location, AnalysisRun, InvestigationNote, Setting, Report
from modules.validation import validate_dataframe, generate_csv_template
from modules.cleaning import clean_and_feature_engineer
from modules.anomaly_detector import run_hybrid_anomaly_detection
from modules.cause_engine import generate_cause_and_evidence
from modules.forecaster import generate_forecast
from modules.sustainability import calculate_sustainability_metrics
from modules.what_if import simulate_water_savings
from modules.demo_generator import generate_synthetic_water_dataset, save_bundled_demo_datasets
from modules.evaluation import evaluate_detection_methods
from modules.report_generator import generate_pdf_report, export_readings_csv, export_readings_excel
from modules.live_telemetry import get_engine, SCENARIOS
from modules.campus_buildings import enrich_buildings_with_meters, CAMPUS_BUILDINGS

api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_active_settings():
    settings = {}
    for s in Setting.query.all():
        try:
            settings[s.key] = float(s.value)
        except ValueError:
            settings[s.key] = s.value
    return settings

# ==========================================
# 1. DASHBOARD DATA API
# ==========================================
@api_bp.route('/dashboard')
@login_required
def get_dashboard_data():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    location = request.args.get('location')
    building = request.args.get('building')
    meter_id = request.args.get('meter_id')
    severity = request.args.get('severity')
    
    # Shared reading filters — identical semantics to the previous full-scan version,
    # but every aggregate below runs inside the database (no full-table ORM hydration).
    r_filters = []
    if meter_id:
        r_filters.append(Reading.meter_id == meter_id)

    if location or building:
        meters_filter = Meter.query
        if location:
            meters_filter = meters_filter.filter(Meter.location == location)
        if building:
            meters_filter = meters_filter.filter(Meter.building == building)
        filtered_meter_ids = [m.meter_id for m in meters_filter.all()]
        r_filters.append(Reading.meter_id.in_(filtered_meter_ids))

    if date_from:
        try:
            d_from = datetime.strptime(date_from, '%Y-%m-%d')
            r_filters.append(Reading.timestamp >= d_from)
        except Exception:
            pass

    if date_to:
        try:
            d_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            r_filters.append(Reading.timestamp < d_to)
        except Exception:
            pass

    # Single aggregate scan: totals, span, night usage, distinct meters
    agg = db.session.query(
        func.sum(Reading.usage_liters),
        func.count(Reading.id),
        func.count(func.distinct(Reading.meter_id)),
        func.min(Reading.timestamp),
        func.max(Reading.timestamp),
        func.sum(case((Reading.is_night.is_(True), Reading.usage_liters), else_=0.0)),
    ).filter(*r_filters).one()

    if int(agg[1] or 0) == 0:
        return jsonify({
            'status': 'empty',
            'kpis': {
                'total_consumption': 0,
                'avg_daily_usage': 0,
                'anomalies_detected': 0,
                'critical_anomalies': 0,
                'estimated_excess': 0,
                'meters_monitored': Meter.query.count()
            },
            'charts': {}
        })

    total_consumption = float(agg[0] or 0.0)
    meters_monitored = int(agg[2] or 0)
    min_date, max_date = agg[3], agg[4]
    days_span = max(1.0, (max_date - min_date).total_seconds() / 86400.0)
    avg_daily_usage = total_consumption / days_span
    night_total = float(agg[5] or 0.0)
    day_total = total_consumption - night_total

    # Anomaly aggregates — same filters as before
    a_filters = []
    if meter_id:
        a_filters.append(Anomaly.meter_id == meter_id)
    if severity:
        a_filters.append(Anomaly.severity == severity)

    a_agg = db.session.query(
        func.count(Anomaly.id),
        func.sum(case((Anomaly.severity == 'Critical', 1), else_=0)),
        func.sum(case((Anomaly.deviation_liters > 0, Anomaly.deviation_liters), else_=0.0)),
    ).filter(*a_filters).one()

    anomalies_detected = int(a_agg[0] or 0)
    critical_anomalies = int(a_agg[1] or 0)
    estimated_excess = float(a_agg[2] or 0.0)
    
    # Build chart data — grouped inside the database, same shapes as before
    # 1. Timeline aggregation (daily + rolling baseline with usage fallback)
    day_col = func.date(Reading.timestamp).label('day')
    base_expr = case(
        (or_(Reading.rolling_mean.is_(None), Reading.rolling_mean == 0), Reading.usage_liters),
        else_=Reading.rolling_mean,
    )
    trend_rows = db.session.query(
        day_col,
        func.sum(Reading.usage_liters),
        func.sum(base_expr),
    ).filter(*r_filters).group_by(day_col).order_by(day_col).all()

    trend_labels = [r[0] for r in trend_rows]
    trend_actual = [round(float(r[1] or 0.0), 1) for r in trend_rows]
    trend_baseline = [round(float(r[2] or 0.0), 1) for r in trend_rows]

    # 2. Anomaly Distribution by Severity (fixed label order preserved)
    severity_counts = {'Normal': 0, 'Low': 0, 'Medium': 0, 'High': 0, 'Critical': 0}
    for sev_name, sev_count in db.session.query(
        Anomaly.severity, func.count(Anomaly.id)
    ).filter(*a_filters).group_by(Anomaly.severity).all():
        severity_counts[sev_name] = severity_counts.get(sev_name, 0) + int(sev_count)

    # 3. Consumption by Location (first-seen chronological order preserved)
    loc_col = func.coalesce(Meter.location, 'Unassigned')
    loc_rows = db.session.query(
        loc_col, func.sum(Reading.usage_liters)
    ).outerjoin(Meter, Meter.meter_id == Reading.meter_id
    ).filter(*r_filters).group_by(loc_col).order_by(func.min(Reading.timestamp), loc_col).all()
    loc_labels = [r[0] for r in loc_rows]
    loc_values = [round(float(r[1] or 0.0), 1) for r in loc_rows]

    # 4. Day-of-week consumption (SQLite %w: 0=Sunday → Python Mon=0..Sun=6)
    dow_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    dow_sums = [0.0] * 7
    dow_counts = [0] * 7
    dow_col = func.strftime('%w', Reading.timestamp)
    for wd, s, c in db.session.query(
        dow_col, func.sum(Reading.usage_liters), func.count(Reading.id)
    ).filter(*r_filters).group_by(dow_col).all():
        py_wd = (int(wd) + 6) % 7
        dow_sums[py_wd] = float(s or 0.0)
        dow_counts[py_wd] = int(c or 0)
    dow_averages = [round(dow_sums[i] / max(dow_counts[i], 1), 1) for i in range(7)]
    
    # 6. Recent Alerts
    alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(6).all()
    alerts_data = [{
        'id': a.id,
        'severity': a.severity,
        'meter_id': a.meter_id,
        'location': a.location,
        'score': a.score,
        'title': a.title,
        'timestamp': a.timestamp.strftime('%Y-%m-%d %H:%M'),
        'status': a.status
    } for a in alerts]
    
    return jsonify({
        'status': 'success',
        'kpis': {
            'total_consumption': round(total_consumption, 1),
            'avg_daily_usage': round(avg_daily_usage, 1),
            'anomalies_detected': anomalies_detected,
            'critical_anomalies': critical_anomalies,
            'estimated_excess': round(estimated_excess, 1),
            'meters_monitored': meters_monitored
        },
        'charts': {
            'trend': {
                'labels': trend_labels,
                'actual': trend_actual,
                'baseline': trend_baseline
            },
            'severity_distribution': {
                'labels': list(severity_counts.keys()),
                'values': list(severity_counts.values())
            },
            'location_consumption': {
                'labels': loc_labels,
                'values': loc_values
            },
            'day_of_week': {
                'labels': dow_names,
                'values': dow_averages
            },
            'night_vs_day': {
                'labels': ['Daytime (06:00 - 22:00)', 'Night-time (22:00 - 06:00)'],
                'values': [round(day_total, 1), round(night_total, 1)]
            }
        },
        'recent_alerts': alerts_data
    })

# ==========================================
# 2. UPLOAD & VALIDATE APIS
# ==========================================
@api_bp.route('/template/download')
def download_template():
    csv_content = generate_csv_template()
    return send_file(
        io.BytesIO(csv_content.encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='aquaguard_meter_template.csv'
    )

@api_bp.route('/validate', methods=['POST'])
@login_required
def validate_uploaded_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part in the request'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected for upload'}), 400
        
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ['csv', 'xlsx', 'xls']:
        return jsonify({'status': 'error', 'message': f"Unsupported file type (.{ext}). Please upload .csv, .xlsx, or .xls"}), 400
        
    try:
        if ext == 'csv':
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error parsing file: {str(e)}"}), 400
        
    is_valid, report, valid_df = validate_dataframe(df)
    
    # Store temporary valid data in session cache if valid
    preview_data = []
    if valid_df is not None and len(valid_df) > 0:
        preview_sample = valid_df.head(20).copy()
        # Ensure timestamp is string
        preview_sample['timestamp'] = preview_sample['timestamp'].astype(str)
        preview_data = preview_sample.to_dict(orient='records')
        
    return jsonify({
        'status': 'success' if is_valid else 'invalid',
        'is_valid': is_valid,
        'report': report,
        'preview': preview_data
    })

@api_bp.route('/upload', methods=['POST'])
@login_required
def upload_and_process():
    start_time = time.time()
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400
        
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400
        
    filename = secure_filename(file.filename)
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{int(time.time())}_{filename}")
    file.save(save_path)
    
    try:
        ext = filename.rsplit('.', 1)[-1].lower()
        if ext == 'csv':
            df = pd.read_csv(save_path)
        else:
            df = pd.read_excel(save_path)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Failed to read file: {str(e)}"}), 400
        
    is_valid, val_report, valid_df = validate_dataframe(df)
    if not is_valid or valid_df is None or len(valid_df) == 0:
        return jsonify({
            'status': 'error',
            'message': 'File failed validation checks.',
            'validation_report': val_report
        }), 400
        
    # Preprocess & Clean
    settings = get_active_settings()
    cleaned_df, clean_audit = clean_and_feature_engineer(
        valid_df,
        night_start=int(settings.get('night_start', 22)),
        night_end=int(settings.get('night_end', 6))
    )
    
    # Run Anomaly Detection
    analyzed_df = run_hybrid_anomaly_detection(cleaned_df, settings=settings)
    
    # Create Analysis Run Entry
    run_code = f"RUN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
    run = AnalysisRun(
        run_code=run_code,
        filename=filename,
        records_count=val_report['records_received'],
        valid_records=val_report['valid_records'],
        invalid_records=val_report['invalid_records'],
        duplicate_records=val_report['duplicates'],
        data_quality_score=val_report['data_quality_score'],
        algorithms_used='Rolling Baseline, Z-Score, IQR, Isolation Forest, Hybrid Risk',
        parameters=json.dumps(settings),
        status='Processing'
    )
    db.session.add(run)
    db.session.flush()
    
    # Save/Update Meters & Readings in bulk
    meter_records = {}
    for _, row in analyzed_df.iterrows():
        mid = str(row['meter_id']).strip()
        if mid not in meter_records:
            meter = Meter.query.filter_by(meter_id=mid).first()
            if not meter:
                meter = Meter(
                    meter_id=mid,
                    location=str(row.get('location', 'General Facility')),
                    building=str(row.get('building', 'Main Complex')),
                    capacity=float(row.get('meter_capacity')) if pd.notnull(row.get('meter_capacity')) else 5000.0,
                    latitude=float(row.get('latitude')) if pd.notnull(row.get('latitude')) else None,
                    longitude=float(row.get('longitude')) if pd.notnull(row.get('longitude')) else None,
                    occupancy=int(row.get('occupancy')) if pd.notnull(row.get('occupancy')) else None,
                    status='Active'
                )
                db.session.add(meter)
                db.session.flush()
            meter_records[mid] = meter
            
    # Persist Readings
    readings_to_add = []
    anomalies_to_add = []
    alerts_to_add = []
    
    anomalies_count = 0
    critical_count = 0
    
    for _, row in analyzed_df.iterrows():
        r = Reading(
            meter_id=str(row['meter_id']),
            timestamp=pd.to_datetime(row['timestamp']),
            usage_liters=float(row['usage_liters']),
            occupancy=int(row['occupancy']) if pd.notnull(row.get('occupancy')) else None,
            latitude=float(row['latitude']) if pd.notnull(row.get('latitude')) else None,
            longitude=float(row.get('longitude')) if pd.notnull(row.get('longitude')) else None,
            activity_type=str(row.get('activity_type', 'General')),
            hour=int(row.get('hour', 0)),
            day_of_week=int(row.get('day_of_week', 0)),
            is_weekend=bool(row.get('is_weekend', False)),
            is_night=bool(row.get('is_night', False)),
            rolling_mean=float(row.get('rolling_mean')) if pd.notnull(row.get('rolling_mean')) else None,
            rolling_std=float(row.get('rolling_std')) if pd.notnull(row.get('rolling_std')) else None,
            pct_change=float(row.get('percentage_change')) if pd.notnull(row.get('percentage_change')) else None,
            z_score=float(row.get('computed_z')) if pd.notnull(row.get('computed_z')) else None,
            ground_truth_anomaly=bool(row.get('ground_truth_anomaly', False)),
            anomaly_type_label=str(row.get('anomaly_type_label', 'Normal')),
            run_id=run.id
        )
        db.session.add(r)
        db.session.flush()
        
        # If flagged as anomaly (risk_score >= 40 or severity != 'Normal')
        sev = str(row.get('severity', 'Normal'))
        if sev != 'Normal':
            anomalies_count += 1
            if sev == 'Critical':
                critical_count += 1
                
            causes, evidence, recs = generate_cause_and_evidence(row)
            
            anom = Anomaly(
                reading_id=r.id,
                meter_id=r.meter_id,
                timestamp=r.timestamp,
                actual_usage=r.usage_liters,
                expected_usage=float(row.get('expected_usage', r.usage_liters)),
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
                run_id=run.id
            )
            db.session.add(anom)
            db.session.flush()
            
            # Create Alert if High or Critical
            if sev in ['High', 'Critical']:
                alert = Alert(
                    anomaly_id=anom.id,
                    severity=sev,
                    meter_id=anom.meter_id,
                    location=meter_records[r.meter_id].location,
                    timestamp=anom.timestamp,
                    score=anom.risk_score,
                    title=f"{sev} {anom.anomaly_type} at {anom.meter_id}",
                    description=f"Recorded usage {anom.actual_usage:.1f} L departs {anom.deviation_pct:+.1f}% from baseline.",
                    status='Active'
                )
                db.session.add(alert)

    # Complete Run
    run.anomalies_found = anomalies_count
    run.critical_count = critical_count
    run.execution_time_seconds = round(time.time() - start_time, 2)
    run.status = 'Completed'
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'run_code': run.run_code,
        'records_processed': len(analyzed_df),
        'anomalies_detected': anomalies_count,
        'critical_anomalies': critical_count,
        'data_quality_score': val_report['data_quality_score'],
        'execution_time': run.execution_time_seconds
    })

# ==========================================
# 3. DEMO ENGINE APIS
# ==========================================
@api_bp.route('/demo/launch', methods=['POST'])
@login_required
def launch_demo():
    """One-click instant launcher that generates and loads benchmark demo dataset."""
    start_time = time.time()
    num_meters = request.json.get('num_meters', 14) if request.is_json else 14
    num_days = request.json.get('num_days', 21) if request.is_json else 21
    
    # Generate realistic data
    demo_df = generate_synthetic_water_dataset(
        num_meters=num_meters,
        num_days=num_days,
        avg_hourly_usage=420.0,
        anomaly_rate=0.06
    )
    
    # Save copy to data/
    demo_df.to_csv(os.path.join(current_app.config['DATA_FOLDER'], 'demo_water_usage.csv'), index=False)
    
    # Clear existing demo data if requested or perform clean reload
    # Run validation & cleaning
    is_valid, val_report, valid_df = validate_dataframe(demo_df)
    settings = get_active_settings()
    cleaned_df, _ = clean_and_feature_engineer(valid_df, night_start=22, night_end=6)
    analyzed_df = run_hybrid_anomaly_detection(cleaned_df, settings=settings)
    
    # Record Run
    run_code = f"DEMO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    run = AnalysisRun(
        run_code=run_code,
        filename='demo_water_usage.csv',
        records_count=len(demo_df),
        valid_records=len(valid_df),
        invalid_records=0,
        duplicate_records=0,
        data_quality_score=98.5,
        algorithms_used='Rolling Baseline, Z-Score, IQR, Isolation Forest, Hybrid Risk',
        parameters=json.dumps(settings),
        status='Completed'
    )
    db.session.add(run)
    db.session.flush()
    
    # Clear old readings to prevent duplicate stacking in demo
    Alert.query.delete()
    InvestigationNote.query.delete()
    Anomaly.query.delete()
    Reading.query.delete()
    Meter.query.delete()
    db.session.commit()
    
    # Add Meters
    meter_records = {}
    for _, row in analyzed_df.iterrows():
        mid = str(row['meter_id'])
        if mid not in meter_records:
            m = Meter(
                meter_id=mid,
                location=str(row['location']),
                building=str(row['building']),
                capacity=float(row['meter_capacity']),
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                occupancy=int(row['occupancy']),
                status='Active'
            )
            db.session.add(m)
            meter_records[mid] = m
    db.session.commit()
    
    anom_count = 0
    crit_count = 0
    
    # Insert readings and anomalies
    for _, row in analyzed_df.iterrows():
        r = Reading(
            meter_id=str(row['meter_id']),
            timestamp=pd.to_datetime(row['timestamp']),
            usage_liters=float(row['usage_liters']),
            occupancy=int(row['occupancy']),
            latitude=float(row['latitude']),
            longitude=float(row['longitude']),
            activity_type=str(row['activity_type']),
            hour=int(row['hour']),
            day_of_week=int(row['day_of_week']),
            is_weekend=bool(row['is_weekend']),
            is_night=bool(row['is_night']),
            rolling_mean=float(row['rolling_mean']),
            rolling_std=float(row['rolling_std']),
            pct_change=float(row['percentage_change']),
            z_score=float(row['computed_z']),
            is_demo=True,
            ground_truth_anomaly=bool(row['ground_truth_anomaly']),
            anomaly_type_label=str(row['anomaly_type_label']),
            run_id=run.id
        )
        db.session.add(r)
        db.session.flush()
        
        sev = str(row['severity'])
        if sev != 'Normal':
            anom_count += 1
            if sev == 'Critical':
                crit_count += 1
                
            causes, evidence, recs = generate_cause_and_evidence(row)
            
            anom = Anomaly(
                reading_id=r.id,
                meter_id=r.meter_id,
                timestamp=r.timestamp,
                actual_usage=r.usage_liters,
                expected_usage=float(row['expected_usage']),
                deviation_liters=float(row['deviation_liters']),
                deviation_pct=float(row['deviation_pct']),
                z_score=float(row['computed_z']),
                iqr_flag=bool(row['iqr_flag']),
                iforest_score=float(row['iforest_score']),
                iforest_flag=bool(row['iforest_flag']),
                risk_score=float(row['risk_score']),
                severity=sev,
                anomaly_type=str(row['anomaly_type']),
                possible_causes=json.dumps(causes),
                evidence=json.dumps(evidence),
                recommended_actions=json.dumps(recs),
                status='New',
                run_id=run.id
            )
            db.session.add(anom)
            db.session.flush()
            
            if sev in ['High', 'Critical']:
                alert = Alert(
                    anomaly_id=anom.id,
                    severity=sev,
                    meter_id=anom.meter_id,
                    location=meter_records[r.meter_id].location,
                    timestamp=anom.timestamp,
                    score=anom.risk_score,
                    title=f"{sev} {anom.anomaly_type} on {anom.meter_id}",
                    description=f"Flow of {anom.actual_usage:.1f} L is {anom.deviation_pct:+.1f}% above historical baseline.",
                    status='Active'
                )
                db.session.add(alert)
                
    run.anomalies_found = anom_count
    run.critical_count = crit_count
    run.execution_time_seconds = round(time.time() - start_time, 2)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f"Demo dataset loaded with {len(analyzed_df)} readings across {num_meters} meters.",
        'anomalies_detected': anom_count,
        'critical_anomalies': crit_count,
        'execution_time': run.execution_time_seconds
    })

# ==========================================
# 4. FORECAST API
# ==========================================
@api_bp.route('/forecast')
@login_required
def get_forecast():
    horizon = request.args.get('horizon', 7, type=int)
    method = request.args.get('method', 'exponential_smoothing')
    meter_id = request.args.get('meter_id')
    
    query = Reading.query
    if meter_id:
        query = query.filter_by(meter_id=meter_id)
        
    readings = query.order_by(Reading.timestamp.asc()).all()
    if not readings:
        return jsonify({'status': 'error', 'message': 'No data available for forecasting'})
        
    data = [{
        'timestamp': r.timestamp,
        'usage_liters': r.usage_liters
    } for r in readings]
    df = pd.DataFrame(data)
    
    forecast_result = generate_forecast(df, horizon_days=horizon, method=method)
    return jsonify(forecast_result)

# ==========================================
# 5. SUSTAINABILITY & WHAT-IF APIS
# ==========================================
@api_bp.route('/sustainability')
@login_required
def get_sustainability():
    # Column-only selects: identical DataFrames without full ORM hydration
    readings = db.session.query(
        Reading.timestamp, Reading.usage_liters, Reading.occupancy,
        Reading.is_night, Reading.rolling_mean,
    ).order_by(Reading.timestamp.asc()).all()
    anomalies = db.session.query(
        Anomaly.deviation_liters, Anomaly.risk_score).all()

    if not readings:
        return jsonify({'status': 'empty', 'sustainability_score': 70.0})

    r_df = pd.DataFrame([{
        'timestamp': r.timestamp,
        'usage_liters': r.usage_liters,
        'occupancy': r.occupancy,
        'is_night': r.is_night,
        'rolling_mean': r.rolling_mean
    } for r in readings])

    a_df = pd.DataFrame([{
        'deviation_liters': a.deviation_liters,
        'risk_score': a.risk_score
    } for a in anomalies]) if anomalies else None
    
    res = calculate_sustainability_metrics(r_df, a_df)
    return jsonify({'status': 'success', 'data': res})

@api_bp.route('/what-if', methods=['GET', 'POST'])
@login_required
def run_what_if():
    params = request.get_json(silent=True) or request.args
    res_pct = float(params.get('resolution_pct', 50.0))
    tgt_pct = float(params.get('target_reduction_pct', 10.0))
    
    total_consumption = db.session.query(db.func.sum(Reading.usage_liters)).scalar() or 0.0
    anomalies = Anomaly.query.filter(Anomaly.deviation_liters > 0).all()
    estimated_excess = sum(a.deviation_liters for a in anomalies)
    
    result = simulate_water_savings(
        total_consumption_liters=total_consumption,
        estimated_excess_liters=estimated_excess,
        resolution_pct=res_pct,
        target_reduction_pct=tgt_pct
    )
    return jsonify({'status': 'success', 'simulation': result})

# ==========================================
# 6. EVALUATION MODULE API
# ==========================================
@api_bp.route('/evaluation')
@login_required
def get_evaluation_metrics():
    # Fetch readings that have ground truth labels
    demo_readings = Reading.query.filter(Reading.ground_truth_anomaly.isnot(None)).all()
    if not demo_readings:
        # Check all readings
        demo_readings = Reading.query.all()
        
    if not demo_readings:
        return jsonify({'status': 'error', 'message': 'No readings present to evaluate.'})
        
    # Build dataframe for evaluation
    eval_records = []
    # Join with anomalies if present
    anomaly_map = {a.reading_id: a for a in Anomaly.query.all()}
    
    for r in demo_readings:
        anom = anomaly_map.get(r.id)
        eval_records.append({
            'usage_liters': r.usage_liters,
            'rolling_mean': r.rolling_mean,
            'rolling_std': r.rolling_std,
            'computed_z': r.z_score,
            'z_score': r.z_score,
            'z_score_flag': abs(r.z_score or 0) > 2.5,
            'iqr_flag': anom.iqr_flag if anom else False,
            'iforest_flag': anom.iforest_flag if anom else False,
            'risk_score': anom.risk_score if anom else (abs(r.z_score or 0) * 15),
            'severity': anom.severity if anom else 'Normal',
            'ground_truth_anomaly': bool(r.ground_truth_anomaly)
        })
        
    df = pd.DataFrame(eval_records)
    eval_result = evaluate_detection_methods(df)
    return jsonify(eval_result)

# ==========================================
# 7. MAP & METERS API
# ==========================================
@api_bp.route('/meters/map')
@login_required
def get_map_meters():
    meters = Meter.query.all()
    loc_filter = (request.args.get('location') or '').strip()
    bld_filter = (request.args.get('building') or '').strip()
    sev_filter = (request.args.get('severity') or '').strip()
    output = []

    # Bulk latest-reading / latest-anomaly lookups (single scans, no per-meter N+1)
    meter_ids = [m.meter_id for m in meters]
    latest_r, latest_a, anomaly_counts = {}, {}, {}
    if meter_ids:
        r_rank = func.row_number().over(
            partition_by=Reading.meter_id, order_by=Reading.timestamp.desc()).label('rn')
        r_sub = db.session.query(
            Reading.meter_id, Reading.usage_liters, Reading.rolling_mean, r_rank
        ).filter(Reading.meter_id.in_(meter_ids)).subquery('latest_r')
        for row in db.session.query(r_sub).filter(r_sub.c.rn == 1).all():
            latest_r[row.meter_id] = row

        a_rank = func.row_number().over(
            partition_by=Anomaly.meter_id, order_by=Anomaly.timestamp.desc()).label('rn')
        a_sub = db.session.query(
            Anomaly.meter_id, Anomaly.id, Anomaly.severity, Anomaly.risk_score,
            Anomaly.status, Anomaly.anomaly_type, Anomaly.timestamp, a_rank
        ).filter(Anomaly.meter_id.in_(meter_ids)).subquery('latest_a')
        for row in db.session.query(a_sub).filter(a_sub.c.rn == 1).all():
            latest_a[row.meter_id] = row

        for mid, cnt in db.session.query(
            Anomaly.meter_id, func.count(Anomaly.id)
        ).filter(Anomaly.meter_id.in_(meter_ids)).group_by(Anomaly.meter_id).all():
            anomaly_counts[mid] = int(cnt)

    for m in meters:
        last_r = latest_r.get(m.meter_id)
        last_a = latest_a.get(m.meter_id)
        anomaly_count = anomaly_counts.get(m.meter_id, 0)
        
        status_color = 'green'
        max_severity = 'Normal'
        risk_score = 0.0
        
        if last_a:
            max_severity = last_a.severity
            risk_score = last_a.risk_score
            if last_a.severity == 'Critical':
                status_color = 'red'
            elif last_a.severity == 'High':
                status_color = 'orange'
            elif last_a.severity == 'Medium':
                status_color = 'yellow'
        
        # Live deviation computed against the latest rolling envelope
        deviation_pct = None
        if last_r and last_r.rolling_mean and last_r.rolling_mean > 0:
            deviation_pct = round(((last_r.usage_liters - last_r.rolling_mean) / last_r.rolling_mean) * 100, 1)
        
        item = {
            'meter_id': m.meter_id,
            'location': m.location,
            'building': m.building,
            'capacity': m.capacity,
            'latitude': m.latitude,
            'longitude': m.longitude,
            'current_usage': round(last_r.usage_liters, 1) if last_r else 0,
            'baseline': round(last_r.rolling_mean, 1) if (last_r and last_r.rolling_mean) else 0,
            'deviation_pct': deviation_pct,
            'risk_score': round(risk_score, 1),
            'severity': max_severity,
            'marker_color': status_color,
            'has_coords': m.latitude is not None and m.longitude is not None,
            'anomaly_count': anomaly_count,
            'anomaly_id': last_a.id if last_a else None,
            'anomaly_status': last_a.status if last_a else None,
            'anomaly_type': last_a.anomaly_type if last_a else None,
            'anomaly_time': last_a.timestamp.strftime('%Y-%m-%d %H:%M') if last_a else None
        }
        
        if loc_filter and m.location != loc_filter:
            continue
        if bld_filter and (m.building or '') != bld_filter:
            continue
        if sev_filter and max_severity != sev_filter:
            continue
        output.append(item)
        
    # Merge live simulation overlay when the telemetry engine is running.
    overlay = get_engine().map_overlay()
    if overlay and overlay.get('simulation'):
        live_map = {m['meter_id']: m for m in overlay.get('meters', [])}
        for item in output:
            lm = live_map.get(item['meter_id'])
            if not lm:
                continue
            item['current_usage'] = lm['current_usage']
            if lm['baseline']:
                item['baseline'] = lm['baseline']
            item['deviation_pct'] = lm['deviation_pct']
            item['risk_score'] = lm['risk_score']
            item['severity'] = lm['severity']
            item['anomaly_type'] = lm['anomaly_type']
            item['live'] = True
        for item in output:
            item['marker_color'] = (
                'red' if item['severity'] in ('Critical',) else
                'orange' if item['severity'] in ('High',) else
                'yellow' if item['severity'] in ('Medium', 'Moderate') else item['marker_color']
            )

    all_locs = set(m.location for m in meters if m.location)
    all_blds = set(m.building for m in meters if m.building and m.building != 'Main Facility')
    for cb in CAMPUS_BUILDINGS:
        all_locs.add(cb['location'])
        all_blds.add(cb['name'])

    locations = sorted(list(all_locs))
    buildings = sorted(list(all_blds))
    buildings_data = enrich_buildings_with_meters(output)

    # Filter buildings_data if location or building filter is applied
    if loc_filter:
        buildings_data = [b for b in buildings_data if b['location'] == loc_filter]
    if bld_filter:
        buildings_data = [b for b in buildings_data if b['name'] == bld_filter]
    if sev_filter:
        buildings_data = [b for b in buildings_data if b['severity'].lower() == sev_filter.lower()]

    return jsonify({
        'status': 'success',
        'meters': output,
        'locations': locations,
        'buildings': buildings,
        'buildings_data': buildings_data,
        'simulation_active': bool(overlay and overlay.get('simulation')),
        'simulation_paused': bool(overlay and overlay.get('paused')),
        'sim_mode': overlay.get('mode') if overlay else None,
        'sim_time': overlay.get('sim_time') if overlay else None,
        'live_critical': overlay.get('critical_count', 0) if overlay else 0,
    })

# ==========================================
# 8. ANOMALY & ALERT ACTIONS
# ==========================================
@api_bp.route('/anomalies/latest')
@login_required
def latest_anomaly():
    """Highest-severity open anomaly with full explainable payload for the AI Insight console."""
    anomaly = Anomaly.query.order_by(Anomaly.risk_score.desc(), Anomaly.timestamp.desc()).first()
    if not anomaly:
        return jsonify({'status': 'empty'})

    meter = Meter.query.filter_by(meter_id=anomaly.meter_id).first()
    causes = anomaly.get_causes()
    evidence = anomaly.get_evidence()
    recommendations = anomaly.get_recommendations()

    return jsonify({
        'status': 'success',
        'anomaly': {
            'id': anomaly.id,
            'meter_id': anomaly.meter_id,
            'location': meter.location if meter else 'Facility',
            'building': meter.building if meter else 'Main Complex',
            'severity': anomaly.severity,
            'anomaly_type': anomaly.anomaly_type,
            'timestamp': anomaly.timestamp.strftime('%Y-%m-%d %H:%M'),
            'actual_usage': anomaly.actual_usage,
            'expected_usage': anomaly.expected_usage,
            'deviation_liters': anomaly.deviation_liters,
            'deviation_pct': anomaly.deviation_pct,
            'risk_score': anomaly.risk_score,
            'z_score': anomaly.z_score,
            'status': anomaly.status,
            'causes': causes,
            'evidence': evidence,
            'recommendations': recommendations
        }
    })

@api_bp.route('/anomalies/<int:anomaly_id>/status', methods=['POST'])
@login_required
def update_anomaly_status(anomaly_id):
    anomaly = Anomaly.query.get_or_404(anomaly_id)
    new_status = request.json.get('status')
    if new_status in ['New', 'Investigating', 'Acknowledged', 'Resolved', 'Dismissed']:
        anomaly.status = new_status
        # If alert exists, synchronize status
        alert = Alert.query.filter_by(anomaly_id=anomaly.id).first()
        if alert:
            if new_status in ['Resolved', 'Dismissed']:
                alert.status = new_status
            elif new_status in ['Investigating', 'Acknowledged']:
                alert.status = 'Acknowledged'
        db.session.commit()
        return jsonify({'status': 'success', 'new_status': anomaly.status})
    return jsonify({'status': 'error', 'message': 'Invalid status'}), 400

@api_bp.route('/anomalies/<int:anomaly_id>/note', methods=['POST'])
@login_required
def add_investigation_note(anomaly_id):
    anomaly = Anomaly.query.get_or_404(anomaly_id)
    note_text = request.json.get('note', '').strip()
    if not note_text:
        return jsonify({'status': 'error', 'message': 'Note cannot be blank'}), 400
        
    note = InvestigationNote(
        anomaly_id=anomaly.id,
        user_name=current_user.name,
        note=note_text
    )
    db.session.add(note)
    db.session.commit()
    return jsonify({
        'status': 'success',
        'note': {
            'user': note.user_name,
            'text': note.note,
            'created_at': note.created_at.strftime('%Y-%m-%d %H:%M')
        }
    })

@api_bp.route('/alerts/<int:alert_id>/status', methods=['POST'])
@login_required
def update_alert_status(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    new_status = request.json.get('status')
    if new_status in ['Active', 'Acknowledged', 'Resolved', 'Dismissed']:
        alert.status = new_status
        db.session.commit()
        return jsonify({'status': 'success', 'new_status': alert.status})
    return jsonify({'status': 'error', 'message': 'Invalid alert status'}), 400

# ==========================================
# 9. REPORT GENERATION & EXPORTS
# ==========================================
@api_bp.route('/reports/generate', methods=['POST'])
@login_required
def generate_report():
    total_vol = db.session.query(db.func.sum(Reading.usage_liters)).scalar() or 0.0
    anomalies = Anomaly.query.order_by(Anomaly.risk_score.desc()).all()
    excess_vol = sum(max(0.0, a.deviation_liters) for a in anomalies)
    crit_count = sum(1 for a in anomalies if a.severity == 'Critical')
    
    # Sustainability score
    r_all = Reading.query.all()
    r_df = pd.DataFrame([{'usage_liters': r.usage_liters, 'is_night': r.is_night, 'rolling_mean': r.rolling_mean} for r in r_all])
    a_df = pd.DataFrame([{'deviation_liters': a.deviation_liters} for a in anomalies]) if anomalies else None
    sust_metrics = calculate_sustainability_metrics(r_df, a_df)
    
    # What-if simulation
    sim = simulate_water_savings(total_vol, excess_vol, 50, 10)
    
    meter_loc_map = {m.meter_id: m.location for m in Meter.query.all()}
    recent_anom_data = [{
        'timestamp': a.timestamp.strftime('%Y-%m-%d %H:%M'),
        'meter_id': a.meter_id,
        'location': meter_loc_map.get(a.meter_id, 'Campus Zone'),
        'actual_usage': a.actual_usage,
        'deviation_pct': a.deviation_pct,
        'risk_score': a.risk_score,
        'anomaly_type': a.anomaly_type
    } for a in anomalies[:10]]
    
    metrics_payload = {
        'total_volume': f"{total_vol:,.0f}",
        'meters_count': Meter.query.count(),
        'anomaly_count': len(anomalies),
        'critical_count': crit_count,
        'excess_volume': f"{excess_vol:,.0f}",
        'excess_pct': round((excess_vol / max(total_vol, 1.0)) * 100.0, 1),
        'sustainability_score': sust_metrics['sustainability_score'],
        'sust_tier': sust_metrics['tier'],
        'data_quality_score': 96.0,
        'recent_anomalies': recent_anom_data,
        'what_if': sim
    }
    
    report_filename = f"AquaGuard_Executive_Report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(current_app.config['EXPORTS_FOLDER'], report_filename)
    
    generate_pdf_report(metrics_payload, output_path)
    
    # Save Report record in DB
    report_rec = Report(
        title="AquaGuard Executive Sustainability & Anomaly Audit",
        report_type="PDF",
        filepath=output_path,
        filesize_kb=round(os.path.getsize(output_path) / 1024.0, 1)
    )
    db.session.add(report_rec)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'download_url': f"/api/reports/download/{report_filename}",
        'filename': report_filename,
        'size_kb': report_rec.filesize_kb
    })

@api_bp.route('/reports/download/<filename>')
@login_required
def download_pdf_report(filename):
    filepath = os.path.join(current_app.config['EXPORTS_FOLDER'], secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({'status': 'error', 'message': 'Report file not found'}), 404
    return send_file(filepath, as_attachment=True, download_name=filename)

@api_bp.route('/export/<format>')
@login_required
def export_data(format):
    readings = Reading.query.order_by(Reading.timestamp.desc()).all()
    if not readings:
        return jsonify({'status': 'error', 'message': 'No data available to export'}), 400
        
    data = [{
        'timestamp': r.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'meter_id': r.meter_id,
        'usage_liters': r.usage_liters,
        'occupancy': r.occupancy,
        'latitude': r.latitude,
        'longitude': r.longitude,
        'activity_type': r.activity_type,
        'rolling_mean': r.rolling_mean,
        'z_score': r.z_score
    } for r in readings]
    df = pd.DataFrame(data)
    
    if format.lower() == 'csv':
        output = io.StringIO()
        df.to_csv(output, index=False)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"aquaguard_readings_{int(time.time())}.csv"
        )
    elif format.lower() in ['excel', 'xlsx']:
        out_bytes = io.BytesIO()
        df.to_excel(out_bytes, index=False, engine='openpyxl')
        out_bytes.seek(0)
        return send_file(
            out_bytes,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"aquaguard_readings_{int(time.time())}.xlsx"
        )
    else:
        return jsonify({'status': 'error', 'message': 'Unsupported format. Use csv or excel.'}), 400


# ==========================================
# 9. LIVE WATER TELEMETRY & RISK SIMULATION
# ==========================================
def _telemetry_snapshot():
    engine = get_engine()
    if not engine.meters:
        engine.load_meters()
    if not engine.running:
        engine.start(mode='scenario', speed=5, scenario='mixed_risks')
    return engine.snapshot()


@api_bp.route('/telemetry/status')
@login_required
def telemetry_status():
    try:
        return jsonify(_telemetry_snapshot())
    except Exception as e:  # noqa: BLE001
        return jsonify({'status': 'error', 'message': 'Unable to read telemetry state.', 'detail': str(e)}), 500


@api_bp.route('/telemetry/control', methods=['POST'])
@login_required
def telemetry_control():
    data = request.get_json(silent=True) or {}
    action = (data.get('action') or 'status').lower()
    engine = get_engine()
    try:
        if action == 'start':
            engine.load_meters()
            engine.start(mode=data.get('mode'), speed=data.get('speed'), scenario=data.get('scenario'))
        elif action == 'pause':
            engine.pause()
        elif action == 'resume':
            engine.resume()
        elif action == 'reset':
            engine.reset()
        elif action == 'speed':
            engine.set_speed(data.get('speed', 1))
        elif action == 'scenario':
            engine.set_scenario(data.get('scenario'))
        elif action == 'mode':
            engine.set_mode(data.get('mode'))
        elif action == 'preset':
            preset = (data.get('preset') or '').lower()
            if preset == 'showcase':
                engine.start(mode='scenario', speed=5, scenario='mixed_risks')
            elif preset == 'night':
                engine.start(mode='scenario', speed=2, scenario='night_flow')
            elif preset == 'burst':
                engine.start(mode='scenario', speed=2, scenario='sudden_spike')
            elif preset == 'replay':
                engine.start(mode='replay', speed=3, scenario='normal')
            elif preset == 'stress':
                engine.start(mode='scenario', speed=10, scenario='extreme')
            else:
                return jsonify({'status': 'error', 'message': 'Unknown preset.'}), 400
        elif action == 'trigger':
            ok, msg = engine.trigger_risk(data.get('meter_id'), data.get('kind'))
            if not ok:
                return jsonify({'status': 'error', 'message': msg}), 400
        else:
            return jsonify({'status': 'error', 'message': 'Unknown control action.'}), 400
        return jsonify(_telemetry_snapshot())
    except Exception as e:  # noqa: BLE001
        return jsonify({'status': 'error', 'message': 'Unable to start telemetry simulation.', 'detail': str(e)}), 500


@api_bp.route('/telemetry/ack', methods=['POST'])
@login_required
def telemetry_ack():
    data = request.get_json(silent=True) or {}
    get_engine().acknowledge_event(data.get('event_id'))
    return jsonify(_telemetry_snapshot())


@api_bp.route('/telemetry/resolve', methods=['POST'])
@login_required
def telemetry_resolve():
    data = request.get_json(silent=True) or {}
    get_engine().resolve_event(data.get('event_id'))
    return jsonify(_telemetry_snapshot())


@api_bp.route('/telemetry/save', methods=['POST'])
@login_required
def telemetry_save():
    try:
        result = get_engine().save_run()
        return jsonify({'status': 'success', 'message': 'Simulation run saved to the database.', **result})
    except Exception as e:  # noqa: BLE001
        return jsonify({'status': 'error', 'message': 'Unable to save simulation run.', 'detail': str(e)}), 500


@api_bp.route('/telemetry/history')
@login_required
def telemetry_history():
    try:
        from models import SimulationRun
        runs = []
        for r in SimulationRun.query.order_by(SimulationRun.started_at.desc()).limit(20).all():
            runs.append({
                'run_code': r.run_code,
                'started_at': r.started_at.strftime('%Y-%m-%d %H:%M:%S') if r.started_at else None,
                'duration_seconds': r.duration_seconds,
                'mode': r.mode,
                'scenario': r.scenario,
                'speed': r.speed,
                'meters_count': r.meters_count,
                'readings_generated': r.readings_generated,
                'anomalies_detected': r.anomalies_detected,
                'critical_events': r.critical_events,
                'detection_rate': r.detection_rate,
                'latency_avg_seconds': r.latency_avg_seconds,
            })
        return jsonify({'status': 'success', 'runs': runs})
    except Exception as e:  # noqa: BLE001
        return jsonify({'status': 'error', 'message': 'Unable to read simulation history.', 'detail': str(e)}), 500


# ---------------------------------------------------------------------------
# Water Intelligence & Hydraulic Engineering Endpoints
# ---------------------------------------------------------------------------

@api_bp.route('/water-intelligence/mnf')
def water_intelligence_mnf():
    try:
        from models import Reading, Meter
        from modules.water_intelligence import compute_mnf_analysis
        
        readings = Reading.query.order_by(Reading.timestamp.desc()).limit(15000).all()
        meters = Meter.query.all()
        data = compute_mnf_analysis(readings, meters)
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        from modules.water_intelligence import _fallback_mnf_data
        return jsonify({'status': 'success', 'data': _fallback_mnf_data(), 'note': str(e)})


@api_bp.route('/water-intelligence/water-balance')
def water_intelligence_water_balance():
    try:
        from models import Reading, Meter, Setting
        from modules.water_intelligence import compute_iwa_water_balance
        
        cost_setting = Setting.query.filter_by(key='cost_per_kl').first()
        cost_per_kl = float(cost_setting.value) if cost_setting else 2.50
        
        readings = Reading.query.order_by(Reading.timestamp.desc()).limit(15000).all()
        meters = Meter.query.all()
        data = compute_iwa_water_balance(readings, meters, cost_per_kl=cost_per_kl)
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        from modules.water_intelligence import _fallback_water_balance
        return jsonify({'status': 'success', 'data': _fallback_water_balance(), 'note': str(e)})


@api_bp.route('/water-intelligence/assets')
def water_intelligence_assets():
    try:
        from modules.water_intelligence import compute_asset_diagnostics
        data = compute_asset_diagnostics()
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/water-intelligence/stewardship')
def water_intelligence_stewardship():
    try:
        from modules.water_intelligence import compute_stewardship_compliance
        data = compute_stewardship_compliance()
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# Maintenance Work Orders & Field Dispatch Lifecycle Endpoints
# ---------------------------------------------------------------------------

@api_bp.route('/work-orders', methods=['GET', 'POST'])
def handle_work_orders():
    from models import db, WorkOrder, Meter, Anomaly
    import random
    from datetime import datetime
    
    if request.method == 'POST':
        try:
            body = request.get_json() or {}
            meter_id = body.get('meter_id', '').strip()
            title = body.get('title', '').strip()
            priority = body.get('priority', 'Medium')
            asset_type = body.get('asset_type', 'Mains Pipeline')
            technician = body.get('assigned_technician', 'Plumbing Dispatch Team Alpha')
            est_leak = float(body.get('estimated_leak_lph', 120.0))
            anomaly_id = body.get('anomaly_id')
            location = body.get('location', '')
            
            if not location and meter_id:
                m = Meter.query.filter_by(meter_id=meter_id).first()
                if m:
                    location = m.location
                    
            if not title:
                title = f"Urgent Water Remediation: {asset_type} at {meter_id or 'General Network'}"
                
            ticket_id = f"WO-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
            
            wo = WorkOrder(
                ticket_id=ticket_id,
                anomaly_id=anomaly_id,
                meter_id=meter_id or 'MTR-NET-01',
                location=location or 'Central Campus Zone',
                title=title,
                priority=priority,
                status='Dispatched',
                asset_type=asset_type,
                assigned_technician=technician,
                estimated_leak_lph=est_leak
            )
            db.session.add(wo)
            db.session.commit()
            return jsonify({'status': 'success', 'message': f'Work order {ticket_id} created successfully.', 'work_order': wo.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500

    # GET: return list of work orders with summary KPIs
    try:
        status_filter = request.args.get('status')
        priority_filter = request.args.get('priority')
        
        query = WorkOrder.query
        if status_filter:
            query = query.filter_by(status=status_filter)
        if priority_filter:
            query = query.filter_by(priority=priority_filter)
            
        orders = query.order_by(WorkOrder.created_at.desc()).all()
        
        # Calculate summary metrics
        total_orders = WorkOrder.query.count()
        open_count = WorkOrder.query.filter(WorkOrder.status.in_(['Open', 'Dispatched', 'In Progress'])).count()
        resolved_count = WorkOrder.query.filter_by(status='Resolved').count()
        active_orders = WorkOrder.query.filter(WorkOrder.status.in_(['Open', 'Dispatched', 'In Progress'])).all()
        active_leak_lph = sum(wo.estimated_leak_lph or 0.0 for wo in active_orders)
        resolved_orders = WorkOrder.query.filter_by(status='Resolved').all()
        total_water_saved = sum(wo.water_saved_liters or 0.0 for wo in resolved_orders)
        total_financial_saved = sum(wo.financial_savings_usd or 0.0 for wo in resolved_orders)
        
        return jsonify({
            'status': 'success',
            'work_orders': [wo.to_dict() for wo in orders],
            'kpis': {
                'total_tickets': total_orders,
                'open_tickets': open_count,
                'resolved_tickets': resolved_count,
                'active_leak_lph': round(active_leak_lph, 1),
                'total_water_saved_liters': round(total_water_saved, 1),
                'total_financial_saved_usd': round(total_financial_saved, 2)
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/work-orders/<int:order_id>/dispatch', methods=['POST'])
def dispatch_work_order(order_id):
    from models import db, WorkOrder
    try:
        wo = WorkOrder.query.get_or_404(order_id)
        body = request.get_json() or {}
        technician = body.get('technician', 'Emergency Plumbing Dispatch Unit')
        wo.assigned_technician = technician
        wo.status = 'Dispatched'
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Work order {wo.ticket_id} dispatched to {technician}.', 'work_order': wo.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/work-orders/<int:order_id>/resolve', methods=['POST'])
def resolve_work_order(order_id):
    from models import db, WorkOrder, Setting
    from datetime import datetime
    try:
        wo = WorkOrder.query.get_or_404(order_id)
        body = request.get_json() or {}
        findings = body.get('actual_findings', 'Defective valve seal identified and replaced.')
        action = body.get('action_taken', 'Replaced with industrial grade EPDM gasket, re-pressurized line, verified zero nocturnal leakage.')
        
        leak_lph = wo.estimated_leak_lph or 140.0
        water_saved = round(leak_lph * (24.0 * 7), 1)
        cost_setting = Setting.query.filter_by(key='cost_per_kl').first()
        cost_per_kl = float(cost_setting.value) if cost_setting else 2.50
        co2_setting = Setting.query.filter_by(key='co2_per_kl').first()
        co2_per_kl = float(co2_setting.value) if co2_setting else 0.35
        
        cost_saved = round((water_saved / 1000.0) * cost_per_kl, 2)
        co2_saved = round((water_saved / 1000.0) * co2_per_kl, 2)
        
        wo.status = 'Resolved'
        wo.actual_findings = findings
        wo.action_taken = action
        wo.water_saved_liters = water_saved
        wo.financial_savings_usd = cost_saved
        wo.co2_saved_kg = co2_saved
        wo.resolved_at = datetime.now()
        
        if wo.anomaly_id:
            from models import Anomaly
            anom = Anomaly.query.get(wo.anomaly_id)
            if anom:
                anom.status = 'Resolved'
                
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f'Work order {wo.ticket_id} marked as Resolved. {water_saved:,.0f} L saved!',
            'work_order': wo.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

