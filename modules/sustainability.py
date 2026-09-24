import numpy as np
import pandas as pd

def calculate_sustainability_metrics(readings_df, anomalies_df=None):
    """
    Computes the transparent AquaGuard Sustainability Score (0-100) and contributing factors.
    Also computes estimated excess consumption, CO2 impact, and per-capita metrics.
    """
    if readings_df is None or len(readings_df) == 0:
        return {
            'sustainability_score': 70.0,
            'tier': 'Pending Data',
            'grade': 'N/A',
            'factors': {},
            'metrics': {
                'total_consumption_liters': 0,
                'estimated_excess_liters': 0,
                'excess_percentage': 0,
                'estimated_excess_cost': 0,
                'estimated_co2_kg': 0,
                'liters_per_person_day': None
            },
            'disclaimer': 'Application-defined heuristic score for operational optimization; not an official regulatory certification.'
        }
        
    total_usage = float(readings_df['usage_liters'].sum())
    total_records = max(len(readings_df), 1)
    
    # 1. Estimated Excess Consumption
    excess_liters = 0.0
    if anomalies_df is not None and len(anomalies_df) > 0:
        # Sum of positive deviations for detected anomalies
        pos_devs = anomalies_df[anomalies_df['deviation_liters'] > 0]['deviation_liters']
        excess_liters = float(pos_devs.sum())
    else:
        # Fallback estimation from readings where usage > rolling_mean
        if 'rolling_mean' in readings_df.columns:
            diff = readings_df['usage_liters'] - readings_df['rolling_mean']
            excess_liters = float(diff[diff > 0].sum()) * 0.5
            
    excess_pct = min(100.0, (excess_liters / max(total_usage, 1.0)) * 100.0)
    
    # 2. Factor 1: Anomaly Frequency (Weight: 25%)
    # Ratio of anomalous readings
    anomaly_count = len(anomalies_df) if anomalies_df is not None else 0
    anomaly_rate = anomaly_count / total_records
    # 0% anomalies = 100 pts, 10%+ anomalies = 0 pts
    score_anomaly_freq = max(0.0, 100.0 - (anomaly_rate * 1000.0))
    
    # 3. Factor 2: Consumption Stability (Weight: 20%)
    # Coefficient of variation (std / mean)
    mean_val = readings_df['usage_liters'].mean()
    std_val = readings_df['usage_liters'].std()
    cv = (std_val / mean_val) if mean_val > 0 else 0
    # CV of 0.2 -> 95 pts, CV of 1.0 -> 30 pts
    score_stability = max(0.0, min(100.0, 100.0 - (cv * 65.0)))
    
    # 4. Factor 3: Excess Water Control (Weight: 25%)
    # 0% excess = 100 pts, 25%+ excess = 0 pts
    score_excess_control = max(0.0, 100.0 - (excess_pct * 4.0))
    
    # 5. Factor 4: Night-time Usage Efficiency (Weight: 15%)
    night_mask = readings_df['is_night'] if 'is_night' in readings_df.columns else (readings_df['timestamp'].dt.hour.isin([22,23,0,1,2,3,4,5]))
    night_usage = readings_df[night_mask]['usage_liters'].sum() if len(readings_df[night_mask]) > 0 else 0
    night_ratio = night_usage / max(total_usage, 1.0)
    # Expected night ratio is ~10-15%. Over 30% indicates severe overnight losses
    score_night = max(0.0, min(100.0, 100.0 - max(0.0, (night_ratio - 0.12)) * 350.0))
    
    # 6. Factor 5: Trend Improvement (Weight: 15%)
    # Compare first half of timeline with second half
    half_pt = total_records // 2
    if half_pt > 5:
        first_half_avg = readings_df['usage_liters'].iloc[:half_pt].mean()
        second_half_avg = readings_df['usage_liters'].iloc[half_pt:].mean()
        pct_trend = ((second_half_avg - first_half_avg) / max(first_half_avg, 1.0)) * 100.0
        # If trend decreased by 10%, score=100. If increased by 20%, score drops
        score_trend = max(0.0, min(100.0, 75.0 - (pct_trend * 1.5)))
    else:
        score_trend = 75.0  # neutral
        
    # Weighted composite score
    sustainability_score = (
        (0.25 * score_anomaly_freq) +
        (0.20 * score_stability) +
        (0.25 * score_excess_control) +
        (0.15 * score_night) +
        (0.15 * score_trend)
    )
    sustainability_score = round(max(0.0, min(100.0, sustainability_score)), 1)
    
    # Tiers
    if sustainability_score >= 88:
        tier = 'Emerald Elite'
        grade = 'A+'
    elif sustainability_score >= 76:
        tier = 'Eco Leader'
        grade = 'A'
    elif sustainability_score >= 62:
        tier = 'Moderate Conservation'
        grade = 'B'
    elif sustainability_score >= 45:
        tier = 'Vulnerable Efficiency'
        grade = 'C'
    else:
        tier = 'High Waste Risk'
        grade = 'D'
        
    # Environmental & Financial Impact metrics
    cost_per_kl = 2.50  # $ / kL
    co2_kg_per_kl = 0.35  # kg CO2 / kL
    excess_cost = (excess_liters / 1000.0) * cost_per_kl
    co2_kg = (excess_liters / 1000.0) * co2_kg_per_kl
    
    # Per-capita normalization if occupancy provided
    liters_per_person_day = None
    if 'occupancy' in readings_df.columns and readings_df['occupancy'].notnull().sum() > 0:
        valid_occ = readings_df[readings_df['occupancy'] > 0]
        if len(valid_occ) > 0:
            avg_occ = valid_occ['occupancy'].mean()
            # Calculate days covered
            days = (readings_df['timestamp'].max() - readings_df['timestamp'].min()).total_seconds() / 86400.0
            days = max(1.0, days)
            liters_per_person_day = round((total_usage / avg_occ) / days, 1)
            
    return {
        'sustainability_score': sustainability_score,
        'tier': tier,
        'grade': grade,
        'factors': {
            'anomaly_frequency': {
                'score': round(score_anomaly_freq, 1),
                'weight': '25%',
                'description': 'Control of unexpected spikes and irregular departures'
            },
            'consumption_stability': {
                'score': round(score_stability, 1),
                'weight': '20%',
                'description': 'Smoothness and predictability of daily load profile'
            },
            'excess_water_control': {
                'score': round(score_excess_control, 1),
                'weight': '25%',
                'description': 'Minimization of volume lost beyond baseline thresholds'
            },
            'nighttime_efficiency': {
                'score': round(score_night, 1),
                'weight': '15%',
                'description': 'Overnight quiet-hours flow minimization'
            },
            'trend_improvement': {
                'score': round(score_trend, 1),
                'weight': '15%',
                'description': 'Progression towards lower net volumetric footprint'
            }
        },
        'metrics': {
            'total_consumption_liters': round(total_usage, 1),
            'estimated_excess_liters': round(excess_liters, 1),
            'excess_percentage': round(excess_pct, 1),
            'estimated_excess_cost': round(excess_cost, 2),
            'estimated_co2_kg': round(co2_kg, 1),
            'liters_per_person_day': liters_per_person_day
        },
        'disclaimer': 'The AquaGuard Sustainability Score is an algorithmic operational metric designed for proactive building/facility management, not an accredited statutory certification.'
    }
