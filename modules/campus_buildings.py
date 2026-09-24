# ==========================================================================
# AQUAGUARD AI — CAMPUS BUILDINGS GEOSPATIAL INTELLIGENCE REGISTRY
# Architectural building footprints, polygons, and campus metadata.
# ==========================================================================

# 14 Realistically modeled campus buildings with architectural footprint coordinates
CAMPUS_BUILDINGS = [
    {
        'id': 'bld-sci-01',
        'name': 'Science Complex',
        'location': 'North Campus',
        'type': 'Academic & Research Labs',
        'icon': 'bi-radioactive',
        'center': [37.77490, -122.41940],
        'occupancy': 450,
        'area_sqm': 12500,
        'floors': 5,
        'polygon': [
            [37.77535, -122.42010],
            [37.77535, -122.41870],
            [37.77445, -122.41870],
            [37.77445, -122.41935],
            [37.77480, -122.41935],
            [37.77480, -122.42010]
        ]
    },
    {
        'id': 'bld-eng-02',
        'name': 'Engineering Tower',
        'location': 'North Campus',
        'type': 'Engineering & Robotics Lab',
        'icon': 'bi-cpu-fill',
        'center': [37.77635, -122.41830],
        'occupancy': 520,
        'area_sqm': 14200,
        'floors': 8,
        'polygon': [
            [37.77685, -122.41895],
            [37.77685, -122.41765],
            [37.77595, -122.41765],
            [37.77595, -122.41895]
        ]
    },
    {
        'id': 'bld-bio-03',
        'name': 'Bio-Tech Research Center',
        'location': 'North Campus',
        'type': 'Genomics & Cleanrooms',
        'icon': 'bi-virus',
        'center': [37.77580, -122.41680],
        'occupancy': 340,
        'area_sqm': 9800,
        'floors': 4,
        'polygon': [
            [37.77625, -122.41735],
            [37.77625, -122.41625],
            [37.77535, -122.41625],
            [37.77535, -122.41735]
        ]
    },
    {
        'id': 'bld-stu-04',
        'name': 'Student Union',
        'location': 'Central Quad',
        'type': 'Dining, Social & Retail',
        'icon': 'bi-cup-hot-fill',
        'center': [37.77380, -122.42100],
        'occupancy': 850,
        'area_sqm': 16500,
        'floors': 3,
        'polygon': [
            [37.77425, -122.42170],
            [37.77425, -122.42030],
            [37.77335, -122.42030],
            [37.77335, -122.42170]
        ]
    },
    {
        'id': 'bld-lib-05',
        'name': 'Main Library',
        'location': 'Central Quad',
        'type': 'Academic Archives & Study',
        'icon': 'bi-book-fill',
        'center': [37.77310, -122.42250],
        'occupancy': 350,
        'area_sqm': 11200,
        'floors': 4,
        'polygon': [
            [37.77355, -122.42315],
            [37.77355, -122.42185],
            [37.77265, -122.42185],
            [37.77265, -122.42315]
        ]
    },
    {
        'id': 'bld-din-06',
        'name': 'Dining Commons & Plaza',
        'location': 'Central Quad',
        'type': 'Commercial Food Service',
        'icon': 'bi-shop',
        'center': [37.77420, -122.42220],
        'occupancy': 920,
        'area_sqm': 8900,
        'floors': 2,
        'polygon': [
            [37.77460, -122.42280],
            [37.77460, -122.42160],
            [37.77380, -122.42160],
            [37.77380, -122.42280]
        ]
    },
    {
        'id': 'bld-res-07',
        'name': 'Residence Hall Alpha',
        'location': 'South Campus',
        'type': 'Student Dormitory Alpha',
        'icon': 'bi-building-fill',
        'center': [37.77180, -122.42430],
        'occupancy': 600,
        'area_sqm': 18000,
        'floors': 7,
        'polygon': [
            [37.77225, -122.42500],
            [37.77225, -122.42360],
            [37.77135, -122.42360],
            [37.77135, -122.42500]
        ]
    },
    {
        'id': 'bld-res-08',
        'name': 'Residence Hall Beta',
        'location': 'South Campus',
        'type': 'Student Dormitory Beta',
        'icon': 'bi-house-fill',
        'center': [37.77100, -122.42320],
        'occupancy': 580,
        'area_sqm': 17500,
        'floors': 6,
        'polygon': [
            [37.77145, -122.42385],
            [37.77145, -122.42255],
            [37.77055, -122.42255],
            [37.77055, -122.42385]
        ]
    },
    {
        'id': 'bld-ath-09',
        'name': 'Athletics & Aquatic Center',
        'location': 'South Campus',
        'type': 'Olympic Pool & Sports Arena',
        'icon': 'bi-water',
        'center': [37.76980, -122.42620],
        'occupancy': 300,
        'area_sqm': 22000,
        'floors': 2,
        'polygon': [
            [37.77035, -122.42710],
            [37.77035, -122.42530],
            [37.76925, -122.42530],
            [37.76925, -122.42710]
        ]
    },
    {
        'id': 'bld-hvac-10',
        'name': 'Central Plant & HVAC',
        'location': 'East Annex',
        'type': 'Utility Chillers & Boilers',
        'icon': 'bi-gear-wide-connected',
        'center': [37.77550, -122.41500],
        'occupancy': 45,
        'area_sqm': 13500,
        'floors': 2,
        'polygon': [
            [37.77595, -122.41570],
            [37.77595, -122.41430],
            [37.77505, -122.41430],
            [37.77505, -122.41570]
        ]
    },
    {
        'id': 'bld-adm-11',
        'name': 'Admin Headquarters',
        'location': 'East Annex',
        'type': 'Executive Administration',
        'icon': 'bi-briefcase-fill',
        'center': [37.77420, -122.41620],
        'occupancy': 220,
        'area_sqm': 9200,
        'floors': 4,
        'polygon': [
            [37.77465, -122.41685],
            [37.77465, -122.41555],
            [37.77375, -122.41555],
            [37.77375, -122.41685]
        ]
    },
    {
        'id': 'bld-dat-12',
        'name': 'Data Center Facility',
        'location': 'East Annex',
        'type': 'High-Density Server Infrastructure',
        'icon': 'bi-server',
        'center': [37.77320, -122.41450],
        'occupancy': 60,
        'area_sqm': 8400,
        'floors': 3,
        'polygon': [
            [37.77365, -122.41515],
            [37.77365, -122.41385],
            [37.77275, -122.41385],
            [37.77275, -122.41515]
        ]
    },
    {
        'id': 'bld-inn-13',
        'name': 'Innovation & Robotics Hub',
        'location': 'West Wing',
        'type': 'Advanced AI Prototyping',
        'icon': 'bi-lightning-charge-fill',
        'center': [37.77700, -122.42150],
        'occupancy': 390,
        'area_sqm': 11800,
        'floors': 4,
        'polygon': [
            [37.77745, -122.42220],
            [37.77745, -122.42080],
            [37.77655, -122.42080],
            [37.77655, -122.42220]
        ]
    },
    {
        'id': 'bld-med-14',
        'name': 'Campus Health & Medical Center',
        'location': 'West Wing',
        'type': 'Clinical Healthcare & Wellness',
        'icon': 'bi-hospital-fill',
        'center': [37.77580, -122.42480],
        'occupancy': 420,
        'area_sqm': 10500,
        'floors': 3,
        'polygon': [
            [37.77625, -122.42550],
            [37.77625, -122.42410],
            [37.77535, -122.42410],
            [37.77535, -122.42550]
        ]
    }
]

BUILDING_BY_NAME = {b['name']: b for b in CAMPUS_BUILDINGS}

def get_building_meta(building_name):
    """Retrieve building metadata or generate sensible fallback."""
    if building_name in BUILDING_BY_NAME:
        return BUILDING_BY_NAME[building_name]
    
    # Fallback for dynamic/custom buildings
    return {
        'id': f"bld-{abs(hash(building_name)) % 10000:04d}",
        'name': building_name,
        'location': 'Campus Zone',
        'type': 'Facility Structure',
        'icon': 'bi-building',
        'center': [37.7749, -122.4194],
        'occupancy': 250,
        'area_sqm': 6000,
        'floors': 3,
        'polygon': [
            [37.7752, -122.4198],
            [37.7752, -122.4190],
            [37.7746, -122.4190],
            [37.7746, -122.4198]
        ]
    }

def enrich_buildings_with_meters(meters_list):
    """
    Computes aggregated water risk intelligence for each campus building based on
    the current meter telemetry list.
    """
    # Group meters by building
    meters_by_building = {}
    for m in meters_list:
        b_name = m.get('building') or 'Main Complex'
        meters_by_building.setdefault(b_name, []).append(m)

    enriched = []
    # Process all registered campus buildings
    for b in CAMPUS_BUILDINGS:
        b_name = b['name']
        b_meters = meters_by_building.get(b_name, [])
        
        total_usage = sum(m.get('current_usage') or 0 for m in b_meters)
        total_baseline = sum(m.get('baseline') or 0 for m in b_meters)
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
