import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'aquaguard-secret-key-hackathon-2026-secure-jwt-token')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "aquaguard.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    EXPORTS_FOLDER = os.path.join(BASE_DIR, 'exports')
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    
    # Anomaly Engine Defaults
    DEFAULT_Z_THRESHOLD = 2.5
    DEFAULT_IQR_MULTIPLIER = 1.5
    DEFAULT_PCT_THRESHOLD = 50.0
    DEFAULT_IFOREST_CONTAMINATION = 0.05
    DEFAULT_NIGHT_START = 22
    DEFAULT_NIGHT_END = 6
    
    # Risk Score Weights
    WEIGHT_STATISTICAL = 0.40
    WEIGHT_IFOREST = 0.30
    WEIGHT_PERCENTAGE = 0.20
    WEIGHT_PERSISTENCE = 0.10
    
    # Risk Score Thresholds
    RISK_NORMAL_MAX = 30
    RISK_LOW_MAX = 60
    RISK_MEDIUM_MAX = 80
    RISK_HIGH_MAX = 95
    # 96-100 is Critical
    
    # Sustainability Benchmarks (Liters/person/day)
    BENCHMARK_L_PER_PERSON_DAY = 135.0  # Standard WHO/IS benchmark
    COST_PER_KILOLITER = 2.50  # USD or currency unit per 1000L
    CO2_KG_PER_KILOLITER = 0.35  # kg CO2 emitted per 1000L water treated/pumped
