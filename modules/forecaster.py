from datetime import timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

def generate_forecast(df, horizon_days=7, method='exponential_smoothing'):
    """
    Generates water consumption forecast for specified horizon (7 or 30 days).
    Methods supported: 'exponential_smoothing', 'moving_average', 'random_forest'.
    
    Returns:
        dict containing historical timeline, forecast timeline, confidence intervals, and metrics.
    """
    if df is None or len(df) == 0:
        return {'status': 'error', 'message': 'No data available for forecasting'}
        
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp'])
    
    # Aggregate daily totals across dataset or selected meter
    daily_df = df.set_index('timestamp').resample('D')['usage_liters'].sum().reset_index()
    daily_df = daily_df.sort_values('timestamp').reset_index(drop=True)
    
    if len(daily_df) < 3:
        return {'status': 'error', 'message': 'Insufficient historical points (at least 3 days required).'}
        
    last_date = daily_df['timestamp'].max()
    historical_dates = daily_df['timestamp'].dt.strftime('%Y-%m-%d').tolist()
    historical_values = daily_df['usage_liters'].round(1).tolist()
    
    forecast_dates = [(last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, horizon_days + 1)]
    forecast_values = []
    lower_bounds = []
    upper_bounds = []
    
    # Calculate historical variance for realistic uncertainty bounds
    hist_std = float(daily_df['usage_liters'].std())
    if np.isnan(hist_std) or hist_std <= 0:
        hist_std = float(daily_df['usage_liters'].mean()) * 0.10
        
    if method == 'moving_average':
        window = min(7, len(daily_df))
        ma_val = float(daily_df['usage_liters'].tail(window).mean())
        for i in range(horizon_days):
            # Slight day-of-week factor if enough data
            day_idx = (last_date + timedelta(days=i+1)).weekday()
            dow_mult = 0.85 if day_idx in [5, 6] else 1.05
            val = max(0.0, ma_val * dow_mult)
            forecast_values.append(round(val, 1))
            uncertainty = hist_std * (1.0 + 0.05 * i)
            lower_bounds.append(round(max(0.0, val - uncertainty), 1))
            upper_bounds.append(round(val + uncertainty, 1))
            
    elif method == 'random_forest' and len(daily_df) >= 7:
        try:
            # Build feature matrix: day of week, day of month, lag 1, lag 7
            daily_df['dow'] = daily_df['timestamp'].dt.dayofweek
            daily_df['dom'] = daily_df['timestamp'].dt.day
            daily_df['lag1'] = daily_df['usage_liters'].shift(1).fillna(daily_df['usage_liters'].mean())
            daily_df['lag7'] = daily_df['usage_liters'].shift(7).fillna(daily_df['usage_liters'].mean())
            
            features = ['dow', 'dom', 'lag1', 'lag7']
            X = daily_df[features].values
            y = daily_df['usage_liters'].values
            
            rf = RandomForestRegressor(n_estimators=100, random_state=42)
            rf.fit(X, y)
            
            # Predict sequentially
            curr_lag1 = daily_df['usage_liters'].iloc[-1]
            curr_lag7 = daily_df['usage_liters'].iloc[-7] if len(daily_df) >= 7 else curr_lag1
            
            for i in range(horizon_days):
                fut_date = last_date + timedelta(days=i+1)
                dow = fut_date.weekday()
                dom = fut_date.day
                pred_input = np.array([[dow, dom, curr_lag1, curr_lag7]])
                pred_val = max(0.0, float(rf.predict(pred_input)[0]))
                forecast_values.append(round(pred_val, 1))
                
                uncertainty = hist_std * (0.8 + 0.04 * i)
                lower_bounds.append(round(max(0.0, pred_val - uncertainty), 1))
                upper_bounds.append(round(pred_val + uncertainty, 1))
                
                curr_lag7 = curr_lag1
                curr_lag1 = pred_val
        except Exception:
            # Fallback to exponential smoothing if RF fails
            return generate_forecast(df, horizon_days=horizon_days, method='exponential_smoothing')
    else:
        # Default: Exponential Smoothing (Holt-Winters style alpha=0.3)
        alpha = 0.35
        smoothed = [daily_df['usage_liters'].iloc[0]]
        for val in daily_df['usage_liters'].iloc[1:]:
            smoothed.append(alpha * val + (1 - alpha) * smoothed[-1])
            
        last_smoothed = smoothed[-1]
        # Trend estimate
        if len(smoothed) >= 4:
            trend = (smoothed[-1] - smoothed[-4]) / 4.0
        else:
            trend = 0.0
            
        # Dampened trend
        trend = np.clip(trend, -0.05 * last_smoothed, 0.05 * last_smoothed)
        
        for i in range(horizon_days):
            fut_date = last_date + timedelta(days=i+1)
            dow = fut_date.weekday()
            dow_factor = 0.88 if dow in [5, 6] else 1.04
            
            val = max(0.0, (last_smoothed + trend * (i + 1)) * dow_factor)
            forecast_values.append(round(val, 1))
            
            uncertainty = hist_std * (0.9 + 0.05 * (i + 1))
            lower_bounds.append(round(max(0.0, val - uncertainty), 1))
            upper_bounds.append(round(val + uncertainty, 1))
            
    total_forecast_liters = sum(forecast_values)
    avg_daily_forecast = total_forecast_liters / horizon_days if horizon_days > 0 else 0
    
    return {
        'status': 'success',
        'method_used': method,
        'horizon_days': horizon_days,
        'historical': {
            'dates': historical_dates[-30:],  # last 30 historical days for clarity
            'values': historical_values[-30:]
        },
        'forecast': {
            'dates': forecast_dates,
            'values': forecast_values,
            'lower_bounds': lower_bounds,
            'upper_bounds': upper_bounds
        },
        'summary': {
            'total_forecast_liters': round(total_forecast_liters, 1),
            'avg_daily_liters': round(avg_daily_forecast, 1),
            'historical_daily_avg': round(float(daily_df['usage_liters'].mean()), 1),
            'trend_direction': 'Increasing' if forecast_values[-1] > historical_values[-1] else 'Stable/Decreasing'
        }
    }
