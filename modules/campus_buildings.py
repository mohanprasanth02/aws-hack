# ==========================================================================
# AQUAGUARD AI — CAMPUS BUILDINGS GEOSPATIAL INTELLIGENCE REGISTRY
# Architectural building footprints, polygons, and campus metadata for:
# SNS College of Technology (SNSCT) & SNS College of Engineering (SNSCE)
# SNS Kalvi Nagar, Sathy Main Road (NH-948 / Kurumbapalayam Rd),
# Saravanampatti, Coimbatore, Tamil Nadu 641035, India
# Latitude: 11.10180 N, Longitude: 77.02750 E
# ==========================================================================

# Realistically modeled campus buildings positioned precisely across the SNS College campus in Coimbatore
CAMPUS_BUILDINGS = [
    {
        'id': 'bld-sns-admin',
        'name': 'SNSCT Administrative & Main Academic Block',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Administrative & Academic Offices',
        'icon': 'bi-building-fill',
        'center': [11.10180, 77.02750],
        'occupancy': 480,
        'area_sqm': 14500,
        'floors': 5,
        'polygon': [
            [11.10210, 77.02710],
            [11.10210, 77.02790],
            [11.10150, 77.02790],
            [11.10150, 77.02710]
        ]
    },
    {
        'id': 'bld-sns-eng',
        'name': 'Engineering & Technology Tower A',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Engineering Labs & Smart Classrooms',
        'icon': 'bi-cpu-fill',
        'center': [11.10260, 77.02820],
        'occupancy': 550,
        'area_sqm': 16000,
        'floors': 6,
        'polygon': [
            [11.10290, 77.02790],
            [11.10290, 77.02850],
            [11.10230, 77.02850],
            [11.10230, 77.02790]
        ]
    },
    {
        'id': 'bld-sns-ai-it',
        'name': 'CSE, IT & AI-DS Tech Wing',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Computing Hub & AI Labs',
        'icon': 'bi-laptop',
        'center': [11.10280, 77.02680],
        'occupancy': 600,
        'area_sqm': 13500,
        'floors': 5,
        'polygon': [
            [11.10310, 77.02650],
            [11.10310, 77.02710],
            [11.10250, 77.02710],
            [11.10250, 77.02650]
        ]
    },
    {
        'id': 'bld-sns-mech',
        'name': 'Mechanical & Mechatronics Lab Complex',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Heavy Machinery & Robotics Workshop',
        'icon': 'bi-gear-wide-connected',
        'center': [11.10100, 77.02840],
        'occupancy': 380,
        'area_sqm': 11800,
        'floors': 3,
        'polygon': [
            [11.10130, 77.02810],
            [11.10130, 77.02870],
            [11.10070, 77.02870],
            [11.10070, 77.02810]
        ]
    },
    {
        'id': 'bld-sns-lib',
        'name': 'Central Library & Resource Center',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Digital Archive & Study Center',
        'icon': 'bi-book-half',
        'center': [11.10140, 77.02620],
        'occupancy': 350,
        'area_sqm': 8500,
        'floors': 4,
        'polygon': [
            [11.10170, 77.02590],
            [11.10170, 77.02650],
            [11.10110, 77.02650],
            [11.10110, 77.02590]
        ]
    },
    {
        'id': 'bld-sns-ihub',
        'name': 'Dr. SNS Innovation & Design Thinking Hub (i-Hub)',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Incubation & Startup Accelerator',
        'icon': 'bi-lightbulb-fill',
        'center': [11.10330, 77.02760],
        'occupancy': 420,
        'area_sqm': 10500,
        'floors': 4,
        'polygon': [
            [11.10360, 77.02730],
            [11.10360, 77.02790],
            [11.10300, 77.02790],
            [11.10300, 77.02730]
        ]
    },
    {
        'id': 'bld-sns-dining',
        'name': 'Campus Cafeteria & Food Court',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Student Dining & Food Services',
        'icon': 'bi-cup-hot-fill',
        'center': [11.10080, 77.02660],
        'occupancy': 950,
        'area_sqm': 7500,
        'floors': 2,
        'polygon': [
            [11.10110, 77.02630],
            [11.10110, 77.02690],
            [11.10050, 77.02690],
            [11.10050, 77.02630]
        ]
    },
    {
        'id': 'bld-sns-hostel-b',
        'name': 'Kaveri Boys Residential Hostel',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Student Housing Block Alpha',
        'icon': 'bi-houses-fill',
        'center': [11.09980, 77.02880],
        'occupancy': 680,
        'area_sqm': 15000,
        'floors': 6,
        'polygon': [
            [11.10010, 77.02850],
            [11.10010, 77.02910],
            [11.09950, 77.02910],
            [11.09950, 77.02850]
        ]
    },
    {
        'id': 'bld-sns-hostel-g',
        'name': 'Bhavani Girls Residential Hostel',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Student Housing Block Beta',
        'icon': 'bi-houses',
        'center': [11.10020, 77.02540],
        'occupancy': 620,
        'area_sqm': 14200,
        'floors': 6,
        'polygon': [
            [11.10050, 77.02510],
            [11.10050, 77.02570],
            [11.09990, 77.02570],
            [11.09990, 77.02510]
        ]
    },
    {
        'id': 'bld-sns-sports',
        'name': 'SNS Indoor Stadium & Sports Pavilion',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Athletics & Gymnasium',
        'icon': 'bi-trophy-fill',
        'center': [11.09920, 77.02720],
        'occupancy': 350,
        'area_sqm': 18000,
        'floors': 2,
        'polygon': [
            [11.09950, 77.02680],
            [11.09950, 77.02760],
            [11.09890, 77.02760],
            [11.09890, 77.02680]
        ]
    },
    {
        'id': 'bld-sns-ro-stp',
        'name': 'Central RO Water Plant & Overhead Reservoir',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Campus Water Purification & Recycling',
        'icon': 'bi-water',
        'center': [11.10220, 77.02950],
        'occupancy': 30,
        'area_sqm': 4200,
        'floors': 2,
        'polygon': [
            [11.10250, 77.02920],
            [11.10250, 77.02980],
            [11.10190, 77.02980],
            [11.10190, 77.02920]
        ]
    },
    {
        'id': 'bld-sns-hvac',
        'name': 'Central Utility Plant & HVAC Chiller',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Central Utilities & Industrial Plant',
        'icon': 'bi-fan',
        'center': [11.10250, 77.02980],
        'occupancy': 45,
        'area_sqm': 6000,
        'floors': 2,
        'polygon': [
            [11.10280, 77.02950],
            [11.10280, 77.03010],
            [11.10220, 77.03010],
            [11.10220, 77.02950]
        ]
    },
    {
        'id': 'bld-snsce-main',
        'name': 'SNS College of Engineering (SNSCE) Main Campus',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Engineering & Polytechnic Campus',
        'icon': 'bi-mortarboard-fill',
        'center': [11.10380, 77.02850],
        'occupancy': 850,
        'area_sqm': 22000,
        'floors': 5,
        'polygon': [
            [11.10420, 77.02810],
            [11.10420, 77.02890],
            [11.10340, 77.02890],
            [11.10340, 77.02810]
        ]
    },
    {
        'id': 'bld-sns-health',
        'name': 'SNS Campus Health & Medical Center',
        'location': 'SNS Kalvi Nagar, Coimbatore',
        'type': 'Healthcare Clinic & First Aid',
        'icon': 'bi-hospital-fill',
        'center': [11.10150, 77.02800],
        'occupancy': 120,
        'area_sqm': 4500,
        'floors': 2,
        'polygon': [
            [11.10180, 77.02770],
            [11.10180, 77.02830],
            [11.10120, 77.02830],
            [11.10120, 77.02770]
        ]
    }
]

# Legacy / Alternative Building Names mapping to SNS Campus Buildings
BUILDING_NAME_ALIASES = {
    'Science Complex': 'SNSCT Administrative & Main Academic Block',
    'Engineering Tower': 'Engineering & Technology Tower A',
    'Bio-Tech Research Center': 'CSE, IT & AI-DS Tech Wing',
    'Student Union': 'Dr. SNS Innovation & Design Thinking Hub (i-Hub)',
    'Main Library': 'Central Library & Resource Center',
    'Dining Commons & Plaza': 'Campus Cafeteria & Food Court',
    'Residence Hall Alpha': 'Kaveri Boys Residential Hostel',
    'Residence Hall Beta': 'Bhavani Girls Residential Hostel',
    'Athletics & Aquatic Center': 'SNS Indoor Stadium & Sports Pavilion',
    'Central Plant & HVAC': 'Central RO Water Plant & Overhead Reservoir',
    'Admin Headquarters': 'SNSCT Administrative & Main Academic Block',
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
