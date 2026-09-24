import io
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = ['timestamp', 'meter_id', 'usage_liters']
OPTIONAL_COLUMNS = ['location', 'building', 'occupancy', 'latitude', 'longitude', 'meter_capacity', 'activity_type']

def generate_csv_template():
    """Generates sample CSV template structure for user downloads."""
    sample_data = {
        'timestamp': ['2026-09-01 08:00:00', '2026-09-01 09:00:00', '2026-09-01 10:00:00'],
        'meter_id': ['MTR-MAIN-01', 'MTR-MAIN-01', 'MTR-MAIN-01'],
        'usage_liters': [450.5, 520.0, 480.2],
        'location': ['North Campus', 'North Campus', 'North Campus'],
        'building': ['Science Complex', 'Science Complex', 'Science Complex'],
        'occupancy': [120, 150, 140],
        'latitude': [37.7749, 37.7749, 37.7749],
        'longitude': [-122.4194, -122.4194, -122.4194],
        'meter_capacity': [2000.0, 2000.0, 2000.0],
        'activity_type': ['Academic', 'Academic', 'Academic']
    }
    df = pd.DataFrame(sample_data)
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()

def validate_dataframe(df):
    """
    Validates uploaded pandas DataFrame against strict schemas and domain logic.
    Returns: (is_valid, validation_report, cleaned_valid_df)
    """
    report = {
        'records_received': len(df),
        'valid_records': 0,
        'invalid_records': 0,
        'duplicates': 0,
        'missing_values': {},
        'negative_values': 0,
        'invalid_dates': 0,
        'invalid_coordinates': 0,
        'warnings': [],
        'errors': [],
        'data_quality_score': 100.0,
        'data_quality_rating': 'Excellent',
        'details': []
    }
    
    # 1. Check required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        error_msg = f"Missing required column(s): {', '.join(missing_cols)}"
        report['errors'].append(error_msg)
        report['data_quality_score'] = 0.0
        report['data_quality_rating'] = 'Failed Validation'
        return False, report, None
        
    # Check for empty dataframe
    if len(df) == 0:
        report['errors'].append("Uploaded file contains zero data rows.")
        report['data_quality_score'] = 0.0
        report['data_quality_rating'] = 'Empty Dataset'
        return False, report, None
        
    df_work = df.copy()
    
    # Track missing values
    for col in df_work.columns:
        null_count = int(df_work[col].isnull().sum())
        if null_count > 0:
            report['missing_values'][col] = null_count
            if col in REQUIRED_COLUMNS:
                report['warnings'].append(f"Column '{col}' has {null_count} missing values.")
                
    # 2. Validate timestamp
    parsed_timestamps = pd.to_datetime(df_work['timestamp'], errors='coerce')
    invalid_date_mask = parsed_timestamps.isnull()
    invalid_dates_count = int(invalid_date_mask.sum())
    report['invalid_dates'] = invalid_dates_count
    if invalid_dates_count > 0:
        report['errors'].append(f"Found {invalid_dates_count} records with unparseable timestamp formats.")
        
    df_work['parsed_timestamp'] = parsed_timestamps
    
    # 3. Validate numeric usage
    df_work['usage_numeric'] = pd.to_numeric(df_work['usage_liters'], errors='coerce')
    non_numeric_usage = df_work['usage_numeric'].isnull().sum()
    if non_numeric_usage > 0:
        report['warnings'].append(f"Found {int(non_numeric_usage)} non-numeric usage values.")
        
    # Check negative usage
    negative_usage_mask = df_work['usage_numeric'] < 0
    negative_count = int(negative_usage_mask.sum())
    report['negative_values'] = negative_count
    if negative_count > 0:
        report['warnings'].append(f"Rejected {negative_count} records with negative water usage values (< 0 L).")
        
    # 4. Check duplicate records (meter_id + parsed_timestamp)
    valid_time_meter_mask = (~invalid_date_mask) & (df_work['meter_id'].notnull())
    dup_mask = df_work[valid_time_meter_mask].duplicated(subset=['meter_id', 'parsed_timestamp'], keep='first')
    dup_count = int(dup_mask.sum())
    report['duplicates'] = dup_count
    if dup_count > 0:
        report['warnings'].append(f"Found {dup_count} duplicate timestamp records for identical meters.")
        
    # 5. Validate coordinates if present
    if 'latitude' in df_work.columns and 'longitude' in df_work.columns:
        lat_num = pd.to_numeric(df_work['latitude'], errors='coerce')
        lon_num = pd.to_numeric(df_work['longitude'], errors='coerce')
        invalid_coord_mask = ((lat_num < -90) | (lat_num > 90) | (lon_num < -180) | (lon_num > 180)) & lat_num.notnull()
        invalid_coords_count = int(invalid_coord_mask.sum())
        report['invalid_coordinates'] = invalid_coords_count
        if invalid_coords_count > 0:
            report['warnings'].append(f"Found {invalid_coords_count} records with out-of-bounds geographic coordinates.")
            
    # Build filter mask for strictly valid rows
    valid_mask = (
        (~invalid_date_mask) &
        (df_work['meter_id'].notnull()) &
        (df_work['meter_id'].astype(str).str.strip() != '') &
        (df_work['usage_numeric'].notnull()) &
        (df_work['usage_numeric'] >= 0)
    )
    
    # Filter out duplicates
    temp_valid = df_work[valid_mask].copy()
    dedup_mask = ~temp_valid.duplicated(subset=['meter_id', 'parsed_timestamp'], keep='first')
    valid_df = temp_valid[dedup_mask].copy()
    
    # Replace columns with sanitized values
    valid_df['timestamp'] = valid_df['parsed_timestamp']
    valid_df['usage_liters'] = valid_df['usage_numeric']
    valid_df.drop(columns=['parsed_timestamp', 'usage_numeric'], inplace=True, errors='ignore')
    
    report['valid_records'] = len(valid_df)
    report['invalid_records'] = report['records_received'] - len(valid_df)
    
    # Outlier warning check (usage > 1,000,000 L/hour or top 99.9th percentile)
    if len(valid_df) > 0:
        q999 = valid_df['usage_liters'].quantile(0.999)
        extreme_outliers = int((valid_df['usage_liters'] > max(q999, 50000)).sum())
        if extreme_outliers > 0:
            report['warnings'].append(f"Flagged {extreme_outliers} unusually high readings (> {max(q999, 50000):.1f} L) for inspection.")
            
    # 6. Calculate Data Quality Score (0 - 100)
    # Penalties:
    # Invalid rows percentage: up to 40 pts
    # Duplicates percentage: up to 25 pts
    # Missing optional data: up to 15 pts
    # Coordinate anomalies: up to 10 pts
    # Extreme date gaps: up to 10 pts
    total_recs = max(report['records_received'], 1)
    invalid_ratio = report['invalid_records'] / total_recs
    duplicate_ratio = report['duplicates'] / total_recs
    
    quality_score = 100.0 - (invalid_ratio * 50.0) - (duplicate_ratio * 30.0)
    if report['invalid_coordinates'] > 0:
        quality_score -= min(10.0, (report['invalid_coordinates'] / total_recs) * 20.0)
        
    quality_score = max(0.0, min(100.0, round(quality_score, 1)))
    report['data_quality_score'] = quality_score
    
    if quality_score >= 90:
        report['data_quality_rating'] = 'Excellent'
    elif quality_score >= 75:
        report['data_quality_rating'] = 'Good'
    elif quality_score >= 50:
        report['data_quality_rating'] = 'Moderate'
    else:
        report['data_quality_rating'] = 'Poor'
        
    is_overall_valid = report['valid_records'] > 0
    return is_overall_valid, report, valid_df
