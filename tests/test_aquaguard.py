import io
import unittest
import pandas as pd
import numpy as np

from app import create_app
from config import Config
from models import db, User, Meter, Reading, Anomaly, Setting
from modules.validation import validate_dataframe, generate_csv_template
from modules.cleaning import clean_and_feature_engineer
from modules.anomaly_detector import run_hybrid_anomaly_detection
from modules.cause_engine import generate_cause_and_evidence
from modules.what_if import simulate_water_savings
from modules.sustainability import calculate_sustainability_metrics
from modules.forecaster import generate_forecast
from modules.demo_generator import generate_synthetic_water_dataset
from modules.evaluation import evaluate_detection_methods

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class AquaGuardTestSuite(unittest.TestCase):
    
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # 1. Validation Tests
    def test_csv_template_generator(self):
        template = generate_csv_template()
        self.assertIn('timestamp', template)
        self.assertIn('meter_id', template)
        self.assertIn('usage_liters', template)

    def test_missing_required_column_validation(self):
        # Missing 'usage_liters'
        bad_df = pd.DataFrame({
            'timestamp': ['2026-09-01 08:00:00'],
            'meter_id': ['MTR-01']
        })
        is_valid, report, valid_df = validate_dataframe(bad_df)
        self.assertFalse(is_valid)
        self.assertIn('Missing required column(s): usage_liters', report['errors'])

    def test_negative_usage_rejection(self):
        df = pd.DataFrame({
            'timestamp': ['2026-09-01 08:00:00', '2026-09-01 09:00:00'],
            'meter_id': ['MTR-01', 'MTR-01'],
            'usage_liters': [450.0, -120.0]
        })
        is_valid, report, valid_df = validate_dataframe(df)
        self.assertTrue(is_valid)  # Valid records exist
        self.assertEqual(report['negative_values'], 1)
        self.assertEqual(len(valid_df), 1)

    def test_duplicate_record_filtering(self):
        df = pd.DataFrame({
            'timestamp': ['2026-09-01 08:00:00', '2026-09-01 08:00:00'],
            'meter_id': ['MTR-01', 'MTR-01'],
            'usage_liters': [500.0, 500.0]
        })
        is_valid, report, valid_df = validate_dataframe(df)
        self.assertTrue(is_valid)
        self.assertEqual(report['duplicates'], 1)
        self.assertEqual(len(valid_df), 1)

    # 2. Cleaning & Feature Engineering Tests
    def test_cleaning_and_features(self):
        raw_df = pd.DataFrame({
            'timestamp': pd.date_range('2026-09-01', periods=10, freq='h'),
            'meter_id': ['MTR-01'] * 10,
            'usage_liters': [100.0, 105.0, 110.0, 102.0, 98.0, 250.0, 100.0, 95.0, 105.0, 110.0]
        })
        cleaned, audit = clean_and_feature_engineer(raw_df)
        self.assertIn('hour', cleaned.columns)
        self.assertIn('is_night', cleaned.columns)
        self.assertIn('rolling_mean', cleaned.columns)
        self.assertIn('z_score', cleaned.columns)
        self.assertEqual(len(cleaned), 10)

    # 3. Anomaly Detection & Scoring Tests
    def test_anomaly_detection_spike(self):
        # 30 standard readings followed by 1 massive 800% spike
        usages = [100.0] * 30 + [850.0]
        df = pd.DataFrame({
            'timestamp': pd.date_range('2026-09-01', periods=31, freq='h'),
            'meter_id': ['MTR-01'] * 31,
            'usage_liters': usages
        })
        cleaned, _ = clean_and_feature_engineer(df)
        analyzed = run_hybrid_anomaly_detection(cleaned)
        
        last_row = analyzed.iloc[-1]
        self.assertIn(last_row['severity'], ['High', 'Critical'])
        self.assertGreater(last_row['risk_score'], 60.0)

    # 4. Cause Engine Tests
    def test_cause_engine_hypotheses(self):
        row = {
            'usage_liters': 950.0,
            'expected_usage': 120.0,
            'deviation_pct': 691.0,
            'computed_z': 4.5,
            'is_night': True,
            'hour': 2,
            'anomaly_type': 'Night-time Usage',
            'persistence_score': 70.0
        }
        causes, evidence, recs = generate_cause_and_evidence(row)
        self.assertGreater(len(causes), 0)
        self.assertGreater(len(evidence), 0)
        self.assertGreater(len(recs), 0)
        # Verify causes are hypotheses
        self.assertTrue(any('Possible' in c['title'] for c in causes))

    # 5. What-If Simulator Tests
    def test_what_if_simulator(self):
        sim = simulate_water_savings(100000.0, 15000.0, resolution_pct=50, target_reduction_pct=10)
        self.assertEqual(sim['anomaly_savings_liters'], 7500.0)
        self.assertGreater(sim['total_potential_reduction_liters'], 7500.0)
        self.assertGreater(sim['estimated_cost_saved_usd'], 0.0)

    # 6. Sustainability Score Tests
    def test_sustainability_score(self):
        df = pd.DataFrame({
            'timestamp': pd.date_range('2026-09-01', periods=24, freq='h'),
            'usage_liters': [200.0] * 24,
            'occupancy': [50] * 24,
            'is_night': [False] * 24,
            'rolling_mean': [200.0] * 24
        })
        metrics = calculate_sustainability_metrics(df)
        self.assertIn('sustainability_score', metrics)
        self.assertGreaterEqual(metrics['sustainability_score'], 0.0)
        self.assertLessEqual(metrics['sustainability_score'], 100.0)

    # 7. Demo Generator & Evaluation Tests
    def test_synthetic_data_and_evaluation(self):
        demo_df = generate_synthetic_water_dataset(num_meters=2, num_days=3, anomaly_rate=0.10)
        self.assertIn('ground_truth_anomaly', demo_df.columns)
        self.assertGreater(len(demo_df), 0)

        cleaned, _ = clean_and_feature_engineer(demo_df)
        analyzed = run_hybrid_anomaly_detection(cleaned)
        eval_res = evaluate_detection_methods(analyzed)
        self.assertEqual(eval_res['status'], 'success')
        self.assertGreaterEqual(len(eval_res['comparison_table']), 4)

    # 8. Web Route Integration Tests
    def test_landing_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'AquaGuard AI', res.data)

    def test_login_page(self):
        res = self.client.get('/login', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'AquaGuard AI', res.data)

    # 9. Water Intelligence & Hydraulic Engineering Tests
    def test_water_intelligence_mnf_and_balance(self):
        from modules.water_intelligence import compute_mnf_analysis, compute_iwa_water_balance
        readings = [
            {'meter_id': 'MTR-01', 'timestamp': '2026-09-24 02:30:00', 'usage_liters': 180.0},
            {'meter_id': 'MTR-01', 'timestamp': '2026-09-24 03:15:00', 'usage_liters': 190.0},
            {'meter_id': 'MTR-01', 'timestamp': '2026-09-24 14:00:00', 'usage_liters': 650.0},
            {'meter_id': 'MTR-02', 'timestamp': '2026-09-24 02:45:00', 'usage_liters': 80.0},
            {'meter_id': 'MTR-02', 'timestamp': '2026-09-24 11:00:00', 'usage_liters': 520.0},
        ]
        mnf = compute_mnf_analysis(readings)
        self.assertIn('overall_mnf_rate_lph', mnf)
        self.assertIn('night_day_ratio', mnf)
        self.assertGreater(mnf['overall_mnf_rate_lph'], 0)

        wb = compute_iwa_water_balance(readings)
        self.assertIn('system_input_volume_liters', wb)
        self.assertIn('nrw_percentage', wb)
        self.assertIn('ili_score', wb)

    # 10. Work Order Lifecycle Integration Tests
    def test_work_order_api_lifecycle(self):
        from models import WorkOrder
        # GET work orders
        res = self.client.get('/api/work-orders')
        self.assertEqual(res.status_code, 200)
        data = res.json
        self.assertEqual(data['status'], 'success')
        self.assertIn('kpis', data)

        # POST new work order
        post_res = self.client.post('/api/work-orders', json={
            'meter_id': 'MTR-TEST-01',
            'title': 'Test Sub-surface Leak',
            'asset_type': 'Mains Pipeline',
            'priority': 'Emergency',
            'estimated_leak_lph': 350.0
        })
        self.assertEqual(post_res.status_code, 200)
        wo_obj = post_res.json['work_order']
        wo_id = wo_obj['id']

        # Dispatch work order
        disp_res = self.client.post(f'/api/work-orders/{wo_id}/dispatch', json={
            'technician': 'Test Unit Bravo'
        })
        self.assertEqual(disp_res.status_code, 200)

        # Resolve work order
        res_res = self.client.post(f'/api/work-orders/{wo_id}/resolve', json={
            'actual_findings': 'Defective coupling replaced',
            'action_taken': 'Installed new clamp and verified zero night flow'
        })
        self.assertEqual(res_res.status_code, 200)
        self.assertEqual(res_res.json['work_order']['status'], 'Resolved')
        self.assertGreater(res_res.json['work_order']['water_saved_liters'], 0)

if __name__ == '__main__':
    unittest.main()

