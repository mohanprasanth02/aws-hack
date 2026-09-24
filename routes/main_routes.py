from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Meter, Reading, Anomaly, Alert, AnalysisRun, InvestigationNote, Setting, Location
import json

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('pages/landing.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    meters = Meter.query.all()
    locations = sorted(list(set(m.location for m in meters if m.location)))
    buildings = sorted(list(set(m.building for m in meters if m.building)))
    runs = AnalysisRun.query.order_by(AnalysisRun.created_at.desc()).all()
    latest_run = runs[0] if runs else None
    
    return render_template(
        'pages/dashboard.html',
        meters=meters,
        locations=locations,
        buildings=buildings,
        latest_run=latest_run
    )

@main_bp.route('/upload')
@login_required
def upload():
    return render_template('pages/upload.html')

@main_bp.route('/data')
@login_required
def data_preview():
    page = request.args.get('page', 1, type=int)
    meter_id = request.args.get('meter_id', '')
    query = Reading.query
    if meter_id:
        query = query.filter_by(meter_id=meter_id)
        
    pagination = query.order_by(Reading.timestamp.desc()).paginate(page=page, per_page=50, error_out=False)
    meters = Meter.query.all()
    
    total_records = Reading.query.count()
    unique_meters = Meter.query.count()
    first_date = db.session.query(db.func.min(Reading.timestamp)).scalar()
    last_date = db.session.query(db.func.max(Reading.timestamp)).scalar()
    
    return render_template(
        'pages/data.html',
        readings=pagination.items,
        pagination=pagination,
        meters=meters,
        selected_meter=meter_id,
        total_records=total_records,
        unique_meters=unique_meters,
        first_date=first_date,
        last_date=last_date
    )

@main_bp.route('/analysis')
@login_required
def analysis_history():
    runs = AnalysisRun.query.order_by(AnalysisRun.created_at.desc()).all()
    return render_template('pages/analysis.html', runs=runs)

@main_bp.route('/anomalies')
@login_required
def anomalies():
    severity = request.args.get('severity', '')
    meter_id = request.args.get('meter_id', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    query = Anomaly.query
    if severity:
        query = query.filter_by(severity=severity)
    if meter_id:
        query = query.filter_by(meter_id=meter_id)
    if status:
        query = query.filter_by(status=status)
        
    pagination = query.order_by(Anomaly.risk_score.desc(), Anomaly.timestamp.desc()).paginate(page=page, per_page=25, error_out=False)
    meters = Meter.query.all()
    
    return render_template(
        'pages/anomalies.html',
        anomalies=pagination.items,
        pagination=pagination,
        meters=meters,
        selected_severity=severity,
        selected_meter=meter_id,
        selected_status=status
    )

@main_bp.route('/anomalies/<int:anomaly_id>')
@login_required
def anomaly_detail(anomaly_id):
    anomaly = Anomaly.query.get_or_404(anomaly_id)
    meter = Meter.query.filter_by(meter_id=anomaly.meter_id).first()
    notes = InvestigationNote.query.filter_by(anomaly_id=anomaly_id).order_by(InvestigationNote.created_at.desc()).all()
    
    # Retrieve surrounding reading history for context chart (-12h to +12h)
    surrounding_readings = Reading.query.filter_by(meter_id=anomaly.meter_id)\
        .filter(Reading.timestamp >= anomaly.timestamp - db.func.interval('12 hour') if 'sqlite' not in str(db.engine.url) else Reading.timestamp >= anomaly.timestamp)\
        .order_by(Reading.timestamp.asc()).limit(30).all()
        
    # In SQLite, query surrounding by meter ordered near timestamp
    all_readings = Reading.query.filter_by(meter_id=anomaly.meter_id).order_by(Reading.timestamp.asc()).all()
    context_readings = []
    if all_readings:
        # Find index closest to anomaly.timestamp
        closest_idx = 0
        min_diff = None
        for i, r in enumerate(all_readings):
            diff = abs((r.timestamp - anomaly.timestamp).total_seconds())
            if min_diff is None or diff < min_diff:
                min_diff = diff
                closest_idx = i
        start_idx = max(0, closest_idx - 10)
        end_idx = min(len(all_readings), closest_idx + 11)
        context_readings = all_readings[start_idx:end_idx]
        
    chart_data = {
        'labels': [r.timestamp.strftime('%m-%d %H:%M') for r in context_readings],
        'actual': [r.usage_liters for r in context_readings],
        'baseline': [r.rolling_mean if r.rolling_mean else r.usage_liters for r in context_readings]
    }
    
    return render_template(
        'pages/anomaly_detail.html',
        anomaly=anomaly,
        meter=meter,
        notes=notes,
        causes=anomaly.get_causes(),
        evidence=anomaly.get_evidence(),
        recommendations=anomaly.get_recommendations(),
        chart_data=chart_data
    )

@main_bp.route('/telemetry')
@login_required
def telemetry():
    try:
        from modules.live_telemetry import get_engine
        engine = get_engine()
        if not engine.meters:
            engine.load_meters()
        if not engine.running:
            engine.start(mode='scenario', speed=5, scenario='mixed_risks')
    except Exception:
        pass
    meters = Meter.query.all()
    return render_template('pages/telemetry.html', meters=meters)

@main_bp.route('/map')
@login_required
def map_view():
    meters = Meter.query.all()
    locations = sorted(list(set(m.location for m in meters if m.location)))
    return render_template('pages/map.html', meters=meters, locations=locations)

@main_bp.route('/meters', methods=['GET', 'POST'])
@login_required
def meters():
    if request.method == 'POST':
        meter_id = request.form.get('meter_id', '').strip().upper()
        location = request.form.get('location', '').strip()
        building = request.form.get('building', '').strip()
        capacity = request.form.get('capacity', type=float)
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        occupancy = request.form.get('occupancy', type=int)
        
        if not meter_id or not location:
            flash('Meter ID and Location are required.', 'danger')
        elif Meter.query.filter_by(meter_id=meter_id).first():
            flash(f'Meter with ID {meter_id} already exists.', 'warning')
        else:
            meter = Meter(
                meter_id=meter_id,
                location=location,
                building=building,
                capacity=capacity,
                latitude=latitude,
                longitude=longitude,
                occupancy=occupancy,
                status='Active'
            )
            db.session.add(meter)
            db.session.commit()
            flash(f'Meter {meter_id} registered successfully.', 'success')
            return redirect(url_for('main.meters'))
            
    meters_list = Meter.query.order_by(Meter.meter_id.asc()).all()
    # Compute summary per meter
    summary = []
    for m in meters_list:
        reading_count = Reading.query.filter_by(meter_id=m.meter_id).count()
        anom_count = Anomaly.query.filter_by(meter_id=m.meter_id).count()
        last_reading = Reading.query.filter_by(meter_id=m.meter_id).order_by(Reading.timestamp.desc()).first()
        summary.append({
            'meter': m,
            'reading_count': reading_count,
            'anom_count': anom_count,
            'last_reading': last_reading.timestamp if last_reading else None,
            'last_usage': last_reading.usage_liters if last_reading else None
        })
        
    return render_template('pages/meters.html', meter_summaries=summary)

@main_bp.route('/forecast')
@login_required
def forecast():
    meters = Meter.query.all()
    return render_template('pages/forecast.html', meters=meters)

@main_bp.route('/sustainability')
@login_required
def sustainability():
    return render_template('pages/sustainability.html')

@main_bp.route('/what-if')
@login_required
def what_if():
    return render_template('pages/what_if.html')

@main_bp.route('/alerts')
@login_required
def alerts():
    severity = request.args.get('severity', '')
    status = request.args.get('status', '')
    query = Alert.query
    if severity:
        query = query.filter_by(severity=severity)
    if status:
        query = query.filter_by(status=status)
        
    alerts_list = query.order_by(Alert.timestamp.desc()).all()
    return render_template('pages/alerts.html', alerts=alerts_list, selected_severity=severity, selected_status=status)

@main_bp.route('/reports')
@login_required
def reports():
    return render_template('pages/reports.html')

@main_bp.route('/evaluation')
@login_required
def evaluation():
    return render_template('pages/evaluation.html')

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Save submitted settings
        for key in ['z_threshold', 'pct_threshold', 'iqr_multiplier', 'night_start', 'night_end', 'cost_per_kl']:
            val = request.form.get(key)
            if val is not None:
                setting = Setting.query.filter_by(key=key).first()
                if not setting:
                    setting = Setting(key=key, value=str(val))
                    db.session.add(setting)
                else:
                    setting.value = str(val)
        db.session.commit()
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('main.settings'))
        
    settings_db = {s.key: s.value for s in Setting.query.all()}
    return render_template('pages/settings.html', settings=settings_db)

@main_bp.route('/about')
def about():
    return render_template('pages/about.html')

@main_bp.route('/water-intelligence')
@login_required
def water_intelligence():
    meters = Meter.query.all()
    return render_template('pages/water_intelligence.html', meters=meters)

@main_bp.route('/work-orders')
@login_required
def work_orders():
    from models import WorkOrder
    meters = Meter.query.all()
    orders = WorkOrder.query.order_by(WorkOrder.created_at.desc()).all()
    return render_template('pages/work_orders.html', meters=meters, orders=orders)

@main_bp.route('/mobile-app')
def mobile_app():
    """Live interactive companion mobile interface matching the Flutter app."""
    return render_template('pages/mobile_worker.html')


