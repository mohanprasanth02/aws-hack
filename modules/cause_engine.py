def generate_cause_and_evidence(row, history_context=None):
    """
    Generates explainable, hypothesis-based possible causes, supporting observations (evidence),
    and actionable recommendations for an identified anomaly.
    
    Adheres strictly to the requirement that causes are presented as hypotheses,
    never as definitive conclusions.
    """
    actual = float(row.get('usage_liters', 0))
    expected = float(row.get('expected_usage', actual))
    pct = float(row.get('deviation_pct', 0))
    z = float(row.get('computed_z', row.get('z_score', 0)))
    is_night = bool(row.get('is_night', False))
    is_weekend = bool(row.get('is_weekend', False))
    hour = int(row.get('hour', 12)) if row.get('hour') is not None else 12
    anomaly_type = str(row.get('anomaly_type', 'Spike'))
    occupancy = row.get('occupancy')
    persist = float(row.get('persistence_score', 0))
    
    evidence = []
    causes = []
    recommendations = []
    
    # 1. Gather Concrete Evidence / Supporting Observations
    if pct > 0:
        evidence.append(f"Recorded usage ({actual:,.1f} L) is {abs(pct):.1f}% above the expected rolling baseline ({expected:,.1f} L).")
    else:
        evidence.append(f"Recorded usage ({actual:,.1f} L) is {abs(pct):.1f}% below the expected rolling baseline ({expected:,.1f} L).")
        
    if abs(z) >= 2.0:
        evidence.append(f"Statistical Z-score deviation reached {z:+.2f} standard deviations from mean.")
        
    if is_night:
        evidence.append(f"Observation occurred during designated night quiet hours ({hour:02d}:00).")
        
    if persist >= 50:
        evidence.append("Elevated consumption pattern persisted across multiple consecutive observation intervals.")
        
    if is_weekend:
        evidence.append("Reading occurred over the weekend when facility occupancy is typically reduced.")
        
    if occupancy is not None and not pd_isna(occupancy):
        occ_val = float(occupancy)
        if occ_val > 0:
            per_capita = actual / occ_val
            evidence.append(f"Normalized rate of {per_capita:.1f} L per occupant differs from expected benchmark.")
            
    # 2. Formulate Possible Causes (Hypotheses)
    if is_night and pct > 35:
        causes.append({
            'title': 'Possible continuous pipe or fixture leakage',
            'confidence': 'High' if persist >= 60 else 'Medium',
            'rationale': 'Significant water consumption recorded during late-night hours when standard facility human usage is near zero.'
        })
        causes.append({
            'title': 'Possible automated irrigation or nocturnal cooling tower cycling',
            'confidence': 'Medium',
            'rationale': 'Timed nocturnal automated systems may have activated outside standard operating schedules.'
        })
        recommendations.append("Dispatch facility technician to inspect overnight mains, sub-meters, and restroom flush valves.")
        recommendations.append("Cross-reference automated landscape irrigation and cooling tower timer logs.")
        
    elif anomaly_type == 'Sudden Spike' or pct > 120:
        causes.append({
            'title': 'Possible high-capacity equipment flush or pipe rupture',
            'confidence': 'High',
            'rationale': 'Instantaneous surge far exceeding 100% of rolling baseline with sudden onset.'
        })
        causes.append({
            'title': 'Possible unscheduled high-occupancy event or gathering',
            'confidence': 'Medium',
            'rationale': 'Temporary localized population spike leading to simultaneous fixture utilization.'
        })
        recommendations.append("Perform emergency visual check of mechanical rooms and primary water distribution risers.")
        recommendations.append("Confirm with facility management if unlogged maintenance or deep-cleaning took place at this hour.")
        
    elif anomaly_type == 'Persistent High Usage' or persist >= 65:
        causes.append({
            'title': 'Possible running toilet, stuck solenoid valve, or bypass valve left open',
            'confidence': 'High',
            'rationale': 'Elevated consumption maintained continuously without dropping back to baseline floor.'
        })
        causes.append({
            'title': 'Possible permanent change in facility operations or tenant occupancy',
            'confidence': 'Moderate',
            'rationale': 'New ongoing water-intensive activities or new laboratory/kitchen equipment installation.'
        })
        recommendations.append("Conduct an acoustic leak detection survey across restrooms and utility closets.")
        recommendations.append("Verify whether tenant activities or mechanical schedule changed permanently.")
        
    elif anomaly_type == 'Sudden Drop' or pct < -60:
        causes.append({
            'title': 'Possible upstream valve closure or municipal supply interruption',
            'confidence': 'High',
            'rationale': 'Immediate steep drop in recorded flow below historical operational floor.'
        })
        causes.append({
            'title': 'Possible meter telemetry or flow sensor malfunction',
            'confidence': 'Medium',
            'rationale': 'Flow sensor impeller blockage, power outage, or dead telemetry battery.'
        })
        recommendations.append("Check inlet pressure gauges and verify if upstream isolation valves were closed.")
        recommendations.append("Inspect physical water meter display to verify mechanical register matches logged data.")
        
    else:
        causes.append({
            'title': 'Possible operational variance or shift change activity',
            'confidence': 'Medium',
            'rationale': 'Variance in staff routine or routine deep-cleaning cycles.'
        })
        causes.append({
            'title': 'Possible meter reading noise or transient pressure surge',
            'confidence': 'Low',
            'rationale': 'Hydraulic transient causing temporary air passage or pulse counter jitter.'
        })
        recommendations.append("Monitor meter readings over next 24-48 hours to determine if pattern is self-correcting.")
        recommendations.append("Log observation in facility maintenance logbook.")

    # Ensure at least 1 recommendation and cause
    if not recommendations:
        recommendations.append("Review meter readings and verify physical site conditions.")
        
    return causes, evidence, recommendations

def pd_isna(val):
    if val is None:
        return True
    try:
        import numpy as np
        return np.isnan(val)
    except Exception:
        return False
