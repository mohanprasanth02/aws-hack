def simulate_water_savings(total_consumption_liters, estimated_excess_liters, resolution_pct=50, target_reduction_pct=10, cost_per_kl=2.50, co2_per_kl=0.35):
    """
    Simulates water, monetary, and carbon savings from resolving anomalies and conservation targets.
    
    All outputs are explicitly labeled as algorithmic estimates.
    """
    total = max(0.0, float(total_consumption_liters))
    excess = max(0.0, min(float(estimated_excess_liters), total))
    res_pct = max(0.0, min(100.0, float(resolution_pct)))
    tgt_pct = max(0.0, min(50.0, float(target_reduction_pct)))
    
    # 1. Savings from resolving flagged anomalies (e.g. fixing leaks, correcting valves)
    anomaly_reduction = excess * (res_pct / 100.0)
    
    # 2. General conservation reduction applied to standard baseline consumption
    standard_consumption = total - excess
    conservation_reduction = standard_consumption * (tgt_pct / 100.0)
    
    total_reduction = anomaly_reduction + conservation_reduction
    projected_consumption = max(0.0, total - total_reduction)
    
    net_savings_percentage = (total_reduction / total * 100.0) if total > 0 else 0.0
    cost_saved = (total_reduction / 1000.0) * cost_per_kl
    co2_saved = (total_reduction / 1000.0) * co2_per_kl
    
    return {
        'current_consumption_liters': round(total, 1),
        'estimated_excess_liters': round(excess, 1),
        'resolution_target_pct': res_pct,
        'conservation_target_pct': tgt_pct,
        'anomaly_savings_liters': round(anomaly_reduction, 1),
        'conservation_savings_liters': round(conservation_reduction, 1),
        'total_potential_reduction_liters': round(total_reduction, 1),
        'projected_consumption_liters': round(projected_consumption, 1),
        'net_reduction_percentage': round(net_savings_percentage, 1),
        'estimated_cost_saved_usd': round(cost_saved, 2),
        'estimated_co2_offset_kg': round(co2_saved, 1),
        'notice': 'All simulated figures are prospective estimates based on historical baseline comparisons.'
    }
