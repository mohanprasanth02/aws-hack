from datetime import datetime, timedelta
import os
import random
import numpy as np
import pandas as pd

DEFAULT_LOCATIONS = [
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'SNSCT Administrative & Main Academic Block', 'lat': 11.10180, 'lon': 77.02750, 'capacity': 6000.0, 'occupancy': 480, 'activity': 'Academic Lab'},
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Engineering & Technology Tower A', 'lat': 11.10260, 'lon': 77.02820, 'capacity': 7000.0, 'occupancy': 550, 'activity': 'Engineering Labs'},
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'CSE, IT & AI-DS Tech Wing', 'lat': 11.10280, 'lon': 77.02680, 'capacity': 6500.0, 'occupancy': 600, 'activity': 'Computing Center'},
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Mechanical & Mechatronics Lab Complex', 'lat': 11.10100, 'lon': 77.02840, 'capacity': 8500.0, 'occupancy': 380, 'activity': 'Mechanical Workshop'},
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Central Library & Resource Center', 'lat': 11.10140, 'lon': 77.02620, 'capacity': 4000.0, 'occupancy': 350, 'activity': 'Study / Library'},
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Dr. SNS Innovation & Design Thinking Hub (i-Hub)', 'lat': 11.10330, 'lon': 77.02760, 'capacity': 7500.0, 'occupancy': 420, 'activity': 'Incubation & R&D'},
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Campus Cafeteria & Food Court', 'lat': 11.10080, 'lon': 77.02660, 'capacity': 10000.0, 'occupancy': 950, 'activity': 'Food Services'},
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Kaveri Boys Residential Hostel', 'lat': 11.09980, 'lon': 77.02880, 'capacity': 7500.0, 'occupancy': 680, 'activity': 'Residential'},
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Bhavani Girls Residential Hostel', 'lat': 11.10020, 'lon': 77.02540, 'capacity': 7200.0, 'occupancy': 620, 'activity': 'Residential'},
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'SNS Indoor Stadium & Sports Pavilion', 'lat': 11.09920, 'lon': 77.02720, 'capacity': 11000.0, 'occupancy': 350, 'activity': 'Sports & Pavilion'},
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Central RO Water Plant & Overhead Reservoir', 'lat': 11.10220, 'lon': 77.02950, 'capacity': 16000.0, 'occupancy': 30, 'activity': 'Water Treatment & Pumping'},
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'Central Utility Plant & HVAC Chiller', 'lat': 11.10250, 'lon': 77.02980, 'capacity': 14000.0, 'occupancy': 45, 'activity': 'Industrial Utilities'},
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'SNS College of Engineering (SNSCE) Main Campus', 'lat': 11.10380, 'lon': 77.02850, 'capacity': 12000.0, 'occupancy': 850, 'activity': 'Engineering Campus'},
    {'location': 'SNS Kalvi Nagar, Coimbatore', 'building': 'SNS Campus Health & Medical Center', 'lat': 11.10150, 'lon': 77.02800, 'capacity': 6500.0, 'occupancy': 120, 'activity': 'Healthcare Clinic'}
]


def generate_synthetic_water_dataset(num_meters=14, num_days=30, avg_hourly_usage=450.0, anomaly_rate=0.06, random_seed=42):
    """
    Generates realistic, diurnal, temporal water meter data with embedded ground truth anomalies.
    Returns: DataFrame ready for evaluation and analysis.
    """
    np.random.seed(random_seed)
    random.seed(random_seed)
    
    end_date = datetime.now().replace(minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=num_days)
    
    # Generate hourly timeline
    hours_total = num_days * 24
    timestamps = [start_date + timedelta(hours=i) for i in range(hours_total)]
    
    records = []
    
    # Select meter metadata
    meters_meta = []
    for i in range(num_meters):
        loc_info = DEFAULT_LOCATIONS[i % len(DEFAULT_LOCATIONS)]
        meter_id = f"MTR-{loc_info['building'][:3].upper()}-{i+1:02d}"
        meters_meta.append({
            'meter_id': meter_id,
            'location': loc_info['location'],
            'building': loc_info['building'],
            'latitude': loc_info['lat'] + (np.random.uniform(-0.001, 0.001)),
            'longitude': loc_info['lon'] + (np.random.uniform(-0.001, 0.001)),
            'meter_capacity': loc_info['capacity'],
            'occupancy': loc_info['occupancy'],
            'activity_type': loc_info['activity'],
            'base_rate': avg_hourly_usage * np.random.uniform(0.7, 1.4)
        })
        
    # Diurnal hourly profile curve (fractions of baseline)
    # 00:00 to 23:00
    hourly_profile = [
        0.15, 0.10, 0.08, 0.08, 0.12, 0.25,  # 00:00 - 05:00 (Night sleep)
        0.55, 1.35, 1.50, 1.25, 1.15, 1.30,  # 06:00 - 11:00 (Morning surge + work start)
        1.45, 1.20, 1.10, 1.05, 1.15, 1.35,  # 12:00 - 17:00 (Lunch + afternoon)
        1.40, 1.25, 1.05, 0.85, 0.50, 0.25   # 18:00 - 23:00 (Dinner + evening wind-down)
    ]
    
    for m in meters_meta:
        is_residential = 'Residential' in m['activity_type']
        
        # Track persistent anomaly state
        persistent_counter = 0
        current_anomaly_type = None
        
        for dt in timestamps:
            h = dt.hour
            dow = dt.weekday()
            is_weekend = dow in [5, 6]
            
            # Baseline calculation
            mult = hourly_profile[h]
            if is_weekend and not is_residential:
                mult *= 0.35  # closed / low activity on weekends
            elif is_weekend and is_residential:
                mult *= 1.20  # more residents home
                
            # Random natural noise (Gaussian)
            noise = np.random.normal(0, 0.08 * m['base_rate'])
            usage = max(5.0, (m['base_rate'] * mult) + noise)
            
            is_ground_truth_anomaly = False
            anomaly_label = 'Normal'
            
            # Continue persistent anomaly if active
            if persistent_counter > 0:
                is_ground_truth_anomaly = True
                anomaly_label = current_anomaly_type
                if current_anomaly_type == 'Persistent High Usage':
                    usage += m['base_rate'] * 1.8
                elif current_anomaly_type == 'Persistent Low Usage':
                    usage = max(1.0, usage * 0.15)
                persistent_counter -= 1
                if persistent_counter == 0:
                    current_anomaly_type = None
            else:
                # Decide whether to inject an anomaly based on anomaly_rate
                if np.random.rand() < (anomaly_rate / 2.0):  # scaled per hour
                    is_ground_truth_anomaly = True
                    # Pick anomaly archetype
                    rand_choice = np.random.choice(['spike', 'persistent', 'night', 'drop', 'gradual'])
                    
                    if rand_choice == 'spike':
                        anomaly_label = 'Sudden Spike'
                        usage += m['base_rate'] * np.random.uniform(2.5, 4.2)
                    elif rand_choice == 'night' and (h >= 22 or h <= 5):
                        anomaly_label = 'Night-time Usage'
                        usage += m['base_rate'] * np.random.uniform(1.5, 2.8)
                    elif rand_choice == 'drop':
                        anomaly_label = 'Sudden Drop'
                        usage = max(0.0, usage * 0.05)
                    elif rand_choice == 'persistent':
                        anomaly_label = 'Persistent High Usage'
                        usage += m['base_rate'] * 1.8
                        current_anomaly_type = 'Persistent High Usage'
                        persistent_counter = np.random.randint(4, 9)  # 4 to 8 hours duration
                    elif rand_choice == 'gradual':
                        anomaly_label = 'Gradual Increase'
                        usage += m['base_rate'] * np.random.uniform(0.6, 1.2)
                        
            records.append({
                'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'meter_id': m['meter_id'],
                'usage_liters': round(usage, 2),
                'location': m['location'],
                'building': m['building'],
                'occupancy': m['occupancy'],
                'latitude': round(m['latitude'], 6),
                'longitude': round(m['longitude'], 6),
                'meter_capacity': m['meter_capacity'],
                'activity_type': m['activity_type'],
                'ground_truth_anomaly': is_ground_truth_anomaly,
                'anomaly_type_label': anomaly_label
            })
            
    df = pd.DataFrame(records)
    return df

def save_bundled_demo_datasets(data_dir):
    """Generates and writes demo_water_usage.csv and demo_locations.csv to disk."""
    os.makedirs(data_dir, exist_ok=True)
    usage_path = os.path.join(data_dir, 'demo_water_usage.csv')
    loc_path = os.path.join(data_dir, 'demo_locations.csv')
    
    df = generate_synthetic_water_dataset(num_meters=14, num_days=21, avg_hourly_usage=420.0, anomaly_rate=0.05)
    df.to_csv(usage_path, index=False)
    
    # Unique locations summary
    loc_df = df[['location', 'building', 'latitude', 'longitude', 'occupancy']].drop_duplicates().reset_index(drop=True)
    loc_df.to_csv(loc_path, index=False)
    
    return usage_path, loc_path
