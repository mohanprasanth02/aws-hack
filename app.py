import os
from flask import Flask, render_template, request, make_response
from flask_login import LoginManager, current_user, login_user
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
    login_manager.login_view = 'main.dashboard'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Preflight OPTIONS handler for Flutter Web CORS
    @app.before_request
    def handle_options_preflight():
        if request.method == 'OPTIONS':
            res = make_response('', 200)
            res.headers['Access-Control-Allow-Origin'] = '*'
            res.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            res.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept'
            res.headers['Access-Control-Max-Age'] = '86400'
            return res

    # Global CORS headers on all responses
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept'
        return response

    # Auto-login demo user on every request so login/register is never required
    @app.before_request
    def auto_login_demo():
        if not current_user.is_authenticated:
            demo_user = User.query.filter_by(email='demo@aquaguard.ai').first()
            if not demo_user:
                demo_user = User.query.first()
            if demo_user:
                login_user(demo_user, remember=True)
        
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
                
        # Work orders start clean/empty for real-time dispatch from live risk anomalies
        db.session.commit()
        
        # Ensure bundled demo files are generated in data/
        save_bundled_demo_datasets(app.config['DATA_FOLDER'])
        
    return app


app = create_app()

if __name__ == '__main__':
    # Listen on localhost port 5000 (threaded: parallel API calls no longer queue)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
