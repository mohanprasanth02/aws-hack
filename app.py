import os
from flask import Flask, render_template
from flask_login import LoginManager
from sqlalchemy import event
from config import Config, BASE_DIR
from models import db, User, Setting, WorkOrder, DistrictMeteredArea
from routes.auth_routes import auth_bp
from routes.main_routes import main_bp
from routes.api_routes import api_bp
from modules.demo_generator import save_bundled_demo_datasets

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure working directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORTS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access the AquaGuard platform.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    # Friendly Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('pages/error.html', error_code=404, error_message="The requested intelligence page could not be located."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('pages/error.html', error_code=500, error_message="An unexpected system condition occurred. Technical details have been logged safely."), 500

    # Auto-init DB and seed default demo user and settings
    with app.app_context():
        # SQLite concurrency: WAL lets readers proceed during writes,
        # busy_timeout makes transient contention wait instead of erroring.
        @event.listens_for(db.engine, 'connect')
        def _sqlite_pragmas(dbapi_conn, _conn_record):
            cur = dbapi_conn.cursor()
            cur.execute('PRAGMA journal_mode=WAL;')
            cur.execute('PRAGMA busy_timeout=10000;')
            cur.execute('PRAGMA synchronous=NORMAL;')
            cur.close()

        db.create_all()
        
        # Seed default Demo User
        demo_user = User.query.filter_by(email='demo@aquaguard.ai').first()
        if not demo_user:
            demo_user = User(
                name='AquaGuard Demo Analyst',
                email='demo@aquaguard.ai',
                role='lead_analyst'
            )
            demo_user.set_password('AquaGuard2026!')
            db.session.add(demo_user)
            
        # Seed default settings if missing
        default_settings = [
            ('z_threshold', '2.5', 'Statistical Z-score deviation boundary'),
            ('pct_threshold', '50.0', 'Percentage departure threshold from baseline'),
            ('iqr_multiplier', '1.5', 'IQR multiplier for outlier fencing'),
            ('iforest_contamination', '0.05', 'Isolation forest contamination fraction'),
            ('night_start', '22', 'Hour when nocturnal quiet monitoring begins'),
            ('night_end', '6', 'Hour when nocturnal quiet monitoring ends'),
            ('cost_per_kl', '2.50', 'Cost in USD per kiloliter of water treated/pumped'),
            ('co2_per_kl', '0.35', 'Estimated kg of CO2 emissions per kiloliter')
        ]
        for key, val, desc in default_settings:
            if not Setting.query.filter_by(key=key).first():
                s = Setting(key=key, value=val, description=desc)
                db.session.add(s)
                
        # Seed sample Work Orders if table is empty
        if WorkOrder.query.count() == 0:
            sample_orders = [
                WorkOrder(
                    ticket_id='WO-20260924-101',
                    meter_id='MTR-SCI-01',
                    location='North Campus - Science Complex',
                    title='Underground Distribution Line Pressure Departure',
                    priority='Emergency',
                    status='Dispatched',
                    asset_type='Mains Pipeline',
                    assigned_technician='Plumbing Rapid Response Team Alpha',
                    estimated_leak_lph=420.0
                ),
                WorkOrder(
                    ticket_id='WO-20260924-102',
                    meter_id='MTR-STU-04',
                    location='Central Quad - Student Union',
                    title='Continuous Cistern Float Trickle & Urinal Diaphragm Loss',
                    priority='High',
                    status='In Progress',
                    asset_type='Restroom Cistern',
                    assigned_technician='Senior Plumber Marcus Vance',
                    estimated_leak_lph=180.0
                ),
                WorkOrder(
                    ticket_id='WO-20260923-098',
                    meter_id='MTR-CEN-10',
                    location='East Annex - Central Plant & HVAC',
                    title='Evaporative Cooling Tower Blowdown Bleed Bleed-off Calibration',
                    priority='Medium',
                    status='Resolved',
                    asset_type='Cooling Tower',
                    assigned_technician='HVAC Utilities Engineer Sarah Chen',
                    estimated_leak_lph=280.0,
                    actual_findings='TDS solenoid valve was seized in partial open state.',
                    action_taken='Disassembled solenoid, flushed mineral scale, replaced pilot diaphragm, verified 4.8 Cycles of Concentration.',
                    water_saved_liters=64500.0,
                    financial_savings_usd=161.25,
                    co2_saved_kg=22.58
                ),
                WorkOrder(
                    ticket_id='WO-20260922-085',
                    meter_id='MTR-ATH-09',
                    location='South Campus - Athletics & Aquatic Center',
                    title='Sports Turf Sub-surface Irrigation Lateral Leak',
                    priority='Low',
                    status='Resolved',
                    asset_type='Irrigation Valve',
                    assigned_technician='Irrigation Tech Leo Ramirez',
                    estimated_leak_lph=150.0,
                    actual_findings='Pinhole crack on 2-inch PVC lateral line due to ground settlement.',
                    action_taken='Excavated lateral pipe, installed compression repair sleeve, pressure tested to 4.5 bar.',
                    water_saved_liters=28000.0,
                    financial_savings_usd=70.00,
                    co2_saved_kg=9.80
                )
            ]
            for wo in sample_orders:
                db.session.add(wo)

        db.session.commit()
        
        # Ensure bundled demo files are generated in data/
        save_bundled_demo_datasets(app.config['DATA_FOLDER'])
        
    return app


app = create_app()

if __name__ == '__main__':
    # Listen on localhost port 5000 (threaded: parallel API calls no longer queue)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
