import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

def run_hybrid_anomaly_detection(df, settings=None):
    """
    Runs multi-method hybrid anomaly detection across meter records.
    
    Methods used:
      1. Rolling Baseline
      2. Z-Score Deviation
      3. IQR (Interquartile Range)
      4. Percentage Deviation
      5. Isolation Forest (with automatic fallback for small datasets)
      
    Returns:
      results_df: DataFrame with individual method flags, hybrid risk score (0-100),
                  severity category, and classified anomaly types.
    """
    if df is None or len(df) == 0:
        return df
        
    df = df.copy()
    
    # Extract configurable thresholds
    z_thresh = float(settings.get('z_threshold', 2.5) if settings else 2.5)
    pct_thresh = float(settings.get('pct_threshold', 50.0) if settings else 50.0)
    iqr_mult = float(settings.get('iqr_multiplier', 1.5) if settings else 1.5)
    iforest_contamination = float(settings.get('iforest_contamination', 0.05) if settings else 0.05)
    
    # 1. Baseline & Percentage Deviation
    df['expected_usage'] = df['rolling_mean'].fillna(df['usage_liters'])
    df['deviation_liters'] = df['usage_liters'] - df['expected_usage']
    
    # Percentage deviation safely handled
    safe_expected = df['expected_usage'].replace(0, 0.001)
    df['deviation_pct'] = ((df['usage_liters'] - safe_expected) / safe_expected) * 100.0
    
    # 2. Z-score check
    # rolling_std safely handled
    safe_std = df['rolling_std'].replace(0, 0.001)
    df['computed_z'] = (df['usage_liters'] - df['rolling_mean']) / safe_std
    df['z_score_flag'] = df['computed_z'].abs() > z_thresh
    
    # 3. IQR per meter (or globally if small)
    df['iqr_flag'] = False
    for meter_id, group in df.groupby('meter_id'):
        q1 = group['usage_liters'].quantile(0.25)
        q3 = group['usage_liters'].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            upper_bound = q3 + (iqr_mult * iqr)
            lower_bound = max(0, q1 - (iqr_mult * iqr))
            mask = (group['usage_liters'] > upper_bound) | (group['usage_liters'] < lower_bound)
            df.loc[group.index, 'iqr_flag'] = mask
        else:
            # If no variance, flag if strictly positive deviation
            df.loc[group.index, 'iqr_flag'] = group['usage_liters'] > (q3 * 1.5)
            
    # 4. Percentage threshold flag
    df['pct_flag'] = df['deviation_pct'].abs() > pct_thresh
    
    # 5. Isolation Forest
    # Check if dataset has sufficient size
    MIN_IFOREST_SAMPLES = 20
    df['iforest_flag'] = False
    df['iforest_score'] = 0.5  # default neutral score
    
    feature_cols = ['usage_liters', 'rolling_mean', 'rolling_std', 'hour', 'day_of_week', 'is_weekend', 'is_night']
    valid_features = [col for col in feature_cols if col in df.columns]
    
    if len(df) >= MIN_IFOREST_SAMPLES and len(valid_features) >= 3:
        try:
            X = df[valid_features].fillna(0.0).copy()
            # Convert boolean to numeric
            for col in ['is_weekend', 'is_night']:
                if col in X.columns:
                    X[col] = X[col].astype(int)
                    
            iso = IsolationForest(
                n_estimators=100,
                contamination=min(max(iforest_contamination, 0.01), 0.20),
                random_state=42
            )
            preds = iso.fit_predict(X)  # -1 for anomaly, 1 for inlier
            # Decision function: lower values mean more anomalous
            dec_scores = iso.decision_function(X)
            
            df['iforest_flag'] = preds == -1
            # Normalize decision score to roughly 0 (normal) - 100 (anomalous)
            # Typically decision scores range from -0.5 to +0.5
            norm_iforest = (0.5 - dec_scores) * 100.0
            df['iforest_score'] = np.clip(norm_iforest, 0, 100)
        except Exception:
            # Graceful fallback: rely on statistical methods
            df['iforest_flag'] = df['z_score_flag'] & df['iqr_flag']
            df['iforest_score'] = np.clip(df['computed_z'].abs() * 20.0, 0, 100)
    else:
        # Graceful statistical fallback
        df['iforest_flag'] = df['z_score_flag'] & df['iqr_flag']
        df['iforest_score'] = np.clip(df['computed_z'].abs() * 20.0, 0, 100)
        
    # 6. Persistence check (consecutive high anomalies within 3 reading window)
    df['persistence_score'] = 0.0
    for meter_id, group in df.groupby('meter_id'):
        is_high = (group['computed_z'] > 2.0).astype(int)
        rolling_persist = is_high.rolling(window=3, min_periods=1).sum()
        # Scale 0 to 100 based on count (1=30, 2=65, 3=100)
        p_score = (rolling_persist / 3.0) * 100.0
        df.loc[group.index, 'persistence_score'] = p_score
        
    # 7. Calculate Hybrid Risk Score (0 - 100)
    # Weights: 40% Z-score/Statistical, 30% Isolation Forest, 20% Percentage deviation, 10% Persistence
    w_stat = float(settings.get('w_stat', 0.40) if settings else 0.40)
    w_iso = float(settings.get('w_iso', 0.30) if settings else 0.30)
    w_pct = float(settings.get('w_pct', 0.20) if settings else 0.20)
    w_pers = float(settings.get('w_pers', 0.10) if settings else 0.10)
    
    # Normalize z-score to 0-100 (z=4 maps to 100)
    stat_component = np.clip((df['computed_z'].abs() / 4.0) * 100.0, 0, 100)
    pct_component = np.clip((df['deviation_pct'].abs() / 200.0) * 100.0, 0, 100)
    iso_component = np.clip(df['iforest_score'], 0, 100)
    pers_component = np.clip(df['persistence_score'], 0, 100)
    
    raw_risk = (
        (w_stat * stat_component) +
        (w_iso * iso_component) +
        (w_pct * pct_component) +
        (w_pers * pers_component)
    )
    
    # Extra boost if night-time and positive usage spike
    night_boost = (df['is_night'] & (df['deviation_pct'] > 50.0)).astype(int) * 15.0
    df['risk_score'] = np.clip(raw_risk + night_boost, 0, 100).round(1)
    
    # 8. Categorize Severity
    def categorize_severity(score):
        if score > 85:
            return 'Critical'
        elif score > 65:
            return 'High'
        elif score > 40:
            return 'Medium'
        elif score > 20:
            return 'Low'
        return 'Normal'
        
    df['severity'] = df['risk_score'].apply(categorize_severity)
    
    # 9. Classify Anomaly Type
    def classify_type(row):
        if row['severity'] == 'Normal':
            return 'Normal Consumption'
            
        z = row['computed_z']
        pct = row['deviation_pct']
        is_night = row.get('is_night', False)
        persist = row.get('persistence_score', 0)
        
        # Check repeated zero or flatline
        if row['usage_liters'] == 0 and row['rolling_mean'] > 50:
            return 'Sudden Drop'
            
        if is_night and pct > 40:
            return 'Night-time Usage'
            
        if pct > 100 and z > 3.0:
            return 'Sudden Spike'
            
        if persist >= 65 and pct > 30:
            return 'Persistent High Usage'
            
        if persist >= 65 and pct < -30:
            return 'Persistent Low Usage'
            
        if pct < -50:
            return 'Sudden Drop'
            
        if 20 <= pct <= 80 and z > 1.8:
            return 'Gradual Increase'
            
        return 'Repeated Abnormal Pattern'

    df['anomaly_type'] = df.apply(classify_type, axis=1)
    
    return df
