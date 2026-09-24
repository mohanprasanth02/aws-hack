# ==========================================================================
# AQUAGUARD AI — CAMPUS BUILDINGS GEOSPATIAL INTELLIGENCE REGISTRY
# Architectural building footprints, polygons, and campus metadata for:
# SNS College of Technology (SNSCT) & SNS College of Engineering (SNSCE)
# SNS Kalvi Nagar, Sathy Main Road, Saravanampatti, Coimbatore, Tamil Nadu, India
# Latitude: 11.08420 N, Longitude: 77.01250 E
# ==========================================================================

# Realistically modeled campus buildings with architectural footprint coordinates in SNS College, Coimbatore
CAMPUS_BUILDINGS = [
    {
        'id': 'bld-sns-admin',
        'name': 'SNSCT Administrative & Main Block',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Administrative & Academic Offices',
        'icon': 'bi-building-fill',
        'center': [11.08420, 77.01250],
        'occupancy': 480,
        'area_sqm': 14500,
        'floors': 5,
        'polygon': [
            [11.08445, 77.01220],
            [11.08445, 77.01280],
            [11.08395, 77.01280],
            [11.08395, 77.01220]
        ]
    },
    {
        'id': 'bld-sns-eng',
        'name': 'Engineering & Technology Tower A',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Engineering Labs & Smart Classrooms',
        'icon': 'bi-cpu-fill',
        'center': [11.08480, 77.01280],
        'occupancy': 550,
        'area_sqm': 16000,
        'floors': 6,
        'polygon': [
            [11.08505, 77.01255],
            [11.08505, 77.01305],
            [11.08455, 77.01305],
            [11.08455, 77.01255]
        ]
    },
    {
        'id': 'bld-sns-ai-it',
        'name': 'CSE, IT & AI-DS Tech Wing',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Computing Hub & AI Labs',
        'icon': 'bi-laptop',
        'center': [11.08490, 77.01210],
        'occupancy': 600,
        'area_sqm': 13500,
        'floors': 5,
        'polygon': [
            [11.08515, 77.01185],
            [11.08515, 77.01235],
            [11.08465, 77.01235],
            [11.08465, 77.01185]
        ]
    },
    {
        'id': 'bld-sns-mech',
        'name': 'Mechanical & Mechatronics Lab Complex',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Heavy Machinery & Robotics Workshop',
        'icon': 'bi-gear-wide-connected',
        'center': [11.08370, 77.01290],
        'occupancy': 380,
        'area_sqm': 11800,
        'floors': 3,
        'polygon': [
            [11.08395, 77.01265],
            [11.08395, 77.01315],
            [11.08345, 77.01315],
            [11.08345, 77.01265]
        ]
    },
    {
        'id': 'bld-sns-lib',
        'name': 'Central Library & Resource Center',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Digital Archive & Study Center',
        'icon': 'bi-book-half',
        'center': [11.08400, 77.01180],
        'occupancy': 350,
        'area_sqm': 8500,
        'floors': 4,
        'polygon': [
            [11.08425, 77.01155],
            [11.08425, 77.01205],
            [11.08375, 77.01205],
            [11.08375, 77.01155]
        ]
    },
    {
        'id': 'bld-sns-ihub',
        'name': 'Dr. SNS Innovation & Design Thinking Hub (i-Hub)',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Incubation & Startup Accelerator',
        'icon': 'bi-lightbulb-fill',
        'center': [11.08530, 77.01270],
        'occupancy': 420,
        'area_sqm': 10500,
        'floors': 4,
        'polygon': [
            [11.08555, 77.01245],
            [11.08555, 77.01295],
            [11.08505, 77.01295],
            [11.08505, 77.01245]
        ]
    },
    {
        'id': 'bld-sns-dining',
        'name': 'Campus Cafeteria & Food Court',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Student Dining & Food Services',
        'icon': 'bi-cup-hot-fill',
        'center': [11.08350, 77.01210],
        'occupancy': 950,
        'area_sqm': 7500,
        'floors': 2,
        'polygon': [
            [11.08375, 77.01185],
            [11.08375, 77.01235],
            [11.08325, 77.01235],
            [11.08325, 77.01185]
        ]
    },
    {
        'id': 'bld-sns-hostel-b',
        'name': 'Kaveri Boys Residential Hostel',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Student Housing Block Alpha',
        'icon': 'bi-houses-fill',
        'center': [11.08310, 77.01340],
        'occupancy': 680,
        'area_sqm': 15000,
        'floors': 6,
        'polygon': [
            [11.08335, 77.01315],
            [11.08335, 77.01365],
            [11.08285, 77.01365],
            [11.08285, 77.01315]
        ]
    },
    {
        'id': 'bld-sns-hostel-g',
        'name': 'Bhavani Girls Residential Hostel',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Student Housing Block Beta',
        'icon': 'bi-houses',
        'center': [11.08330, 77.01140],
        'occupancy': 620,
        'area_sqm': 14200,
        'floors': 6,
        'polygon': [
            [11.08355, 77.01115],
            [11.08355, 77.01165],
            [11.08305, 77.01165],
            [11.08305, 77.01115]
        ]
    },
    {
        'id': 'bld-sns-sports',
        'name': 'SNS Indoor Stadium & Sports Pavilion',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Athletics & Gymnasium',
        'icon': 'bi-trophy-fill',
        'center': [11.08250, 77.01250],
        'occupancy': 350,
        'area_sqm': 18000,
        'floors': 2,
        'polygon': [
            [11.08280, 77.01220],
            [11.08280, 77.01280],
            [11.08220, 77.01280],
            [11.08220, 77.01220]
        ]
    },
    {
        'id': 'bld-sns-ro-stp',
        'name': 'Central RO Water Plant & Overhead Reservoir',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Campus Water Purification & Recycling',
        'icon': 'bi-water',
        'center': [11.08440, 77.01360],
        'occupancy': 30,
        'area_sqm': 4200,
        'floors': 2,
        'polygon': [
            [11.08465, 77.01340],
            [11.08465, 77.01380],
            [11.08415, 77.01380],
            [11.08415, 77.01340]
        ]
    },
    {
        'id': 'bld-sns-hvac',
        'name': 'Central Utility Plant & HVAC Chiller',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Central Utilities & Industrial Plant',
        'icon': 'bi-fan',
        'center': [11.08460, 77.01370],
        'occupancy': 45,
        'area_sqm': 6000,
        'floors': 2,
        'polygon': [
            [11.08485, 77.01350],
            [11.08485, 77.01390],
            [11.08435, 77.01390],
            [11.08435, 77.01350]
        ]
    },
    {
        'id': 'bld-snsce-main',
        'name': 'SNS College of Engineering (SNSCE) Main Campus',
        'location': 'Kurumbapalayam, Coimbatore',
        'type': 'Engineering & Polytechnic Campus',
        'icon': 'bi-mortarboard-fill',
        'center': [11.10220, 77.01880],
        'occupancy': 850,
        'area_sqm': 22000,
        'floors': 5,
        'polygon': [
            [11.10255, 77.01845],
            [11.10255, 77.01915],
            [11.10185, 77.01915],
            [11.10185, 77.01845]
        ]
    },
    {
        'id': 'bld-sns-health',
        'name': 'SNS Campus Health & Medical Center',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Healthcare Clinic & First Aid',
        'icon': 'bi-hospital-fill',
        'center': [11.08410, 77.01310],
        'occupancy': 120,
        'area_sqm': 4500,
        'floors': 2,
        'polygon': [
            [11.08430, 77.01290],
            [11.08430, 77.01330],
            [11.08390, 77.01330],
            [11.08390, 77.01290]
        ]
    }
]

# Legacy / Alternative Building Names mapping to SNS Campus Buildings
BUILDING_NAME_ALIASES = {
    'Science Complex': 'SNSCT Administrative & Main Block',
    'Engineering Tower': 'Engineering & Technology Tower A',
    'Bio-Tech Research Center': 'CSE, IT & AI-DS Tech Wing',
    'Student Union': 'Dr. SNS Innovation & Design Thinking Hub (i-Hub)',
    'Main Library': 'Central Library & Resource Center',
    'Dining Commons & Plaza': 'Campus Cafeteria & Food Court',
    'Residence Hall Alpha': 'Kaveri Boys Residential Hostel',
    'Residence Hall Beta': 'Bhavani Girls Residential Hostel',
    'Athletics & Aquatic Center': 'SNS Indoor Stadium & Sports Pavilion',
    'Central Plant & HVAC': 'Central RO Water Plant & Overhead Reservoir',
    'Admin Headquarters': 'SNSCT Administrative & Main Block',
    'Data Center Facility': 'Central Utility Plant & HVAC Chiller',
    'Innovation & Robotics Hub': 'SNS College of Engineering (SNSCE) Main Campus',
    'Campus Health & Medical Center': 'SNS Campus Health & Medical Center'
}


def get_building_by_name(name):
    """Retrieve building metadata by name or alias."""
    if not name:
        return None
    normalized_name = BUILDING_NAME_ALIASES.get(name, name)
    for b in CAMPUS_BUILDINGS:
        if b['name'].lower() == normalized_name.lower() or b['name'].lower() == name.lower():
            return b
    return None


def get_building_by_id(bld_id):
    """Retrieve building metadata by ID."""
    for b in CAMPUS_BUILDINGS:
        if b['id'] == bld_id:
            return b
    return None


def enrich_buildings_with_meters(meters_list):
    """
    Enriches each campus building with aggregate metrics from the meters
    physically located inside or associated with that building.
    """
    # Map meters to buildings
    meters_by_building = {}
    for m in meters_list:
        bld = m.get('building') or 'General Network'
        canonical_bld = BUILDING_NAME_ALIASES.get(bld, bld)
        meters_by_building.setdefault(canonical_bld, []).append(m)

    enriched = []
    for b in CAMPUS_BUILDINGS:
        b_meters = meters_by_building.get(b['name'], [])
        
        # Calculate aggregate usage and baseline
        total_usage = sum(m.get('current_usage') or 0.0 for m in b_meters)
        total_baseline = sum(m.get('baseline') or 0.0 for m in b_meters)
        dev_pct = round(((total_usage - total_baseline) / max(total_baseline, 1.0)) * 100.0, 1) if total_baseline > 0 else 0.0
        
        # Max risk score and severity across its meters
        max_risk = max((m.get('risk_score') or 0.0 for m in b_meters), default=0.0)
        
        severity_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Moderate': 2, 'Normal': 1, 'Low': 1}
        highest_sev = 'Normal'
        for m in b_meters:
            sev = (m.get('severity') or 'Normal').capitalize()
            if severity_order.get(sev, 1) > severity_order.get(highest_sev, 1):
                highest_sev = sev

        anomaly_count = sum(m.get('anomaly_count') or 0 for m in b_meters)

        enriched.append({
            'id': b['id'],
            'name': b['name'],
            'location': b['location'],
            'type': b['type'],
            'icon': b['icon'],
            'center': b['center'],
            'occupancy': b['occupancy'],
            'area_sqm': b['area_sqm'],
            'floors': b['floors'],
            'polygon': b['polygon'],
            'meters_count': len(b_meters),
            'meter_ids': [m.get('meter_id') for m in b_meters],
            'current_usage': round(total_usage, 1),
            'baseline': round(total_baseline, 1),
            'deviation_pct': dev_pct,
            'risk_score': round(max_risk, 1),
            'severity': highest_sev,
            'anomaly_count': anomaly_count
        })

    return enriched
