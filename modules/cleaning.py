import pandas as pd
import numpy as np

def clean_and_feature_engineer(df, night_start=22, night_end=6):
    """
    Cleans meter readings and computes derived temporal and statistical features.
    
    Returns:
        cleaned_df: DataFrame with all original and engineered features
        cleaning_audit: Dict detailing all cleaning actions taken
    """
    audit = {
        'initial_rows': len(df),
        'deduplicated_rows': 0,
        'missing_imputed': {},
        'features_created': [],
        'time_range_start': None,
        'time_range_end': None,
        'meters_count': 0
    }
    
    if df is None or len(df) == 0:
        return df, audit
        
    df = df.copy()
    
    # 1. Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
    # Drop rows where timestamp couldn't be parsed
    df = df.dropna(subset=['timestamp'])
    
    # 2. Sort by meter and timestamp
    df = df.sort_values(by=['meter_id', 'timestamp']).reset_index(drop=True)
    
    # 3. Deduplicate
    initial_len = len(df)
    df = df.drop_duplicates(subset=['meter_id', 'timestamp'], keep='first').reset_index(drop=True)
    audit['deduplicated_rows'] = initial_len - len(df)
    
    audit['time_range_start'] = str(df['timestamp'].min())
    audit['time_range_end'] = str(df['timestamp'].max())
    audit['meters_count'] = int(df['meter_id'].nunique())
    
    # 4. Handle missing optional values gracefully
    if 'location' not in df.columns:
        df['location'] = 'General Location'
    else:
        df['location'] = df['location'].fillna('Unassigned Location')
        
    if 'building' not in df.columns:
        df['building'] = 'Main Building'
    else:
        df['building'] = df['building'].fillna('Main Facility')
        
    if 'occupancy' not in df.columns:
        df['occupancy'] = None
    else:
        df['occupancy'] = pd.to_numeric(df['occupancy'], errors='coerce')
        
    if 'latitude' not in df.columns:
        df['latitude'] = None
    else:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        
    if 'longitude' not in df.columns:
        df['longitude'] = None
    else:
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        
    if 'activity_type' not in df.columns:
        df['activity_type'] = 'Standard'
    else:
        df['activity_type'] = df['activity_type'].fillna('Standard')
        
    # 5. Extract core temporal features
    df['hour'] = df['timestamp'].dt.hour
    df['day'] = df['timestamp'].dt.day
    df['day_of_week'] = df['timestamp'].dt.dayofweek  # 0=Monday, 6=Sunday
    df['week'] = df['timestamp'].dt.isocalendar().week.astype(int)
    df['month'] = df['timestamp'].dt.month
    df['is_weekend'] = df['day_of_week'].isin([5, 6])
    
    # Night time feature (e.g., 22:00 to 06:00)
    if night_start > night_end:
        df['is_night'] = (df['hour'] >= night_start) | (df['hour'] < night_end)
    else:
        df['is_night'] = (df['hour'] >= night_start) & (df['hour'] < night_end)
        
    audit['features_created'].extend(['hour', 'day', 'day_of_week', 'week', 'month', 'is_weekend', 'is_night'])
    
    # 6. Group-by meter windowed statistical features
    # Determine appropriate rolling window size based on data density
    # For hourly data, 7 days = 168 hours; for daily data, 7 days = 7 points.
    # We use a robust rolling window (min_periods=1)
    
    def compute_group_features(group):
        # Lagged usage
        group['previous_usage'] = group['usage_liters'].shift(1)
        # Percentage change
        prev = group['previous_usage'].replace(0, np.nan)
        group['percentage_change'] = ((group['usage_liters'] - prev) / prev) * 100.0
        group['percentage_change'] = group['percentage_change'].fillna(0.0)
        
        # Determine rolling window (default 24 readings or 7 periods if fewer)
        w = 24 if len(group) >= 48 else max(3, min(7, len(group)))
        
        group['rolling_mean'] = group['usage_liters'].rolling(window=w, min_periods=1).mean()
        group['rolling_std'] = group['usage_liters'].rolling(window=w, min_periods=1).std().fillna(0.0)
        
        # If std is 0 or NaN, substitute small epsilon
        std_safe = group['rolling_std'].replace(0, 0.001)
        group['z_score'] = (group['usage_liters'] - group['rolling_mean']) / std_safe
        group['z_score'] = group['z_score'].fillna(0.0)
        
        return group

    # Apply per meter preserving grouping column
    groups = []
    for mid, group in df.groupby('meter_id'):
        processed_group = compute_group_features(group.copy())
        groups.append(processed_group)
        
    if groups:
        df = pd.concat(groups, axis=0).reset_index(drop=True)
    
    audit['features_created'].extend(['previous_usage', 'percentage_change', 'rolling_mean', 'rolling_std', 'z_score'])
    audit['final_rows'] = len(df)
    
    return df, audit
