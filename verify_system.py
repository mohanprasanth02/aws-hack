import requests

def test_full_pipeline():
    s = requests.Session()
    base_url = 'http://127.0.0.1:5000'

    # 1. Landing page
    r1 = s.get(f'{base_url}/')
    assert r1.status_code == 200, f'Landing failed: {r1.status_code}'
    print('1. Landing page HTTP 200 OK')

    # 2. Login
    r2 = s.post(f'{base_url}/login', data={'email': 'demo@aquaguard.ai', 'password': 'AquaGuard2026!'})
    assert r2.status_code in [200, 302], f'Login failed: {r2.status_code}'
    print('2. Login successful')

    # 3. Launch Demo API
    r3 = s.post(f'{base_url}/api/demo/launch', json={'num_meters': 14, 'num_days': 21})
    assert r3.status_code == 200, f'Demo launch failed: {r3.status_code}'
    demo_res = r3.json()
    print('3. Demo API launch:', demo_res['message'])
    print(f"   Anomalies detected: {demo_res['anomalies_detected']}, Critical: {demo_res['critical_anomalies']}")

    # 4. Dashboard API
    r4 = s.get(f'{base_url}/api/dashboard')
    assert r4.status_code == 200, f'Dashboard API failed: {r4.status_code}'
    dash_data = r4.json()
    print('4. Dashboard KPIs:', dash_data['kpis'])
    print('   Charts rendered:', list(dash_data['charts'].keys()))
    print('   Recent alerts count:', len(dash_data.get('recent_alerts', [])))

    # 5. Forecasting API
    r5 = s.get(f'{base_url}/api/forecast?horizon=7&method=exponential_smoothing')
    assert r5.status_code == 200, f'Forecast API failed: {r5.status_code}'
    fore_data = r5.json()
    print('5. Forecast summary:', fore_data.get('summary'))

    # 6. Sustainability API
    r6 = s.get(f'{base_url}/api/sustainability')
    assert r6.status_code == 200, f'Sustainability API failed: {r6.status_code}'
    sust_data = r6.json()
    print('6. Sustainability score:', sust_data['data']['sustainability_score'], '| Tier:', sust_data['data']['tier'])

    # 7. What-If Simulator API
    r7 = s.get(f'{base_url}/api/what-if?resolution_pct=60&target_reduction_pct=15')
    assert r7.status_code == 200, f'What-If API failed: {r7.status_code}'
    sim_data = r7.json()
    print('7. What-If simulation water saved:', sim_data['simulation']['total_potential_reduction_liters'], 'L')

    # 8. Model Evaluation API
    r8 = s.get(f'{base_url}/api/evaluation')
    assert r8.status_code == 200, f'Evaluation API failed: {r8.status_code}'
    eval_data = r8.json()
    print('8. Model evaluation comparison:')
    for row in eval_data['comparison_table']:
        print(f"   - {row['method']}: Precision={row['precision']}%, Recall={row['recall']}%, F1={row['f1_score']}%")

    # 9. PDF Report Generation API
    r9 = s.post(f'{base_url}/api/reports/generate')
    assert r9.status_code == 200, f'Report API failed: {r9.status_code}'
    rep_data = r9.json()
    print('9. PDF Report generated:', rep_data['filename'], f"({rep_data['size_kb']} KB)")

    # 10. Map API
    r10 = s.get(f'{base_url}/api/meters/map')
    assert r10.status_code == 200, f'Map API failed: {r10.status_code}'
    map_data = r10.json()
    print('10. Map meters count:', len(map_data['meters']))

    # 11. Water Intelligence APIs (MNF & Water Balance)
    r11_mnf = s.get(f'{base_url}/api/water-intelligence/mnf')
    assert r11_mnf.status_code == 200, f'MNF API failed: {r11_mnf.status_code}'
    r11_wb = s.get(f'{base_url}/api/water-intelligence/water-balance')
    assert r11_wb.status_code == 200, f'Water Balance API failed: {r11_wb.status_code}'
    print('11. Water Intelligence APIs (MNF & IWA Water Balance) returned HTTP 200 OK!')

    # 12. Maintenance Work Orders API
    r12_wo = s.get(f'{base_url}/api/work-orders')
    assert r12_wo.status_code == 200, f'Work Orders API failed: {r12_wo.status_code}'
    wo_data = r12_wo.json()
    print(f"12. Work Orders API: {wo_data['kpis']['total_tickets']} total tickets, {wo_data['kpis']['total_water_saved_liters']:,} L verified saved!")

    # 13. Test pages
    pages = [
        '/dashboard', '/water-intelligence', '/work-orders', '/upload', '/data',
        '/analysis', '/anomalies', '/map', '/meters', '/forecast',
        '/sustainability', '/what-if', '/alerts', '/reports', '/settings', '/about'
    ]
    for page in pages:
        rp = s.get(f'{base_url}{page}')
        assert rp.status_code == 200, f'Page {page} returned {rp.status_code}'
    print(f'13. All {len(pages)} HTML application pages returned HTTP 200 OK!')

    print('\n======================================================')
    print('>>> ALL AQUAGUARD AI PIPELINES VERIFIED SUCCESSFULLY! <<<')
    print('======================================================')

if __name__ == '__main__':
    test_full_pipeline()

