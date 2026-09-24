from datetime import datetime
import io
import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable

def generate_pdf_report(metrics_data, output_filepath):
    """
    Generates a professional multi-section executive water intelligence PDF report.
    """
    doc = SimpleDocTemplate(
        output_filepath,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Brand Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#334155')
    )
    
    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b'),
        leftIndent=12
    )

    story = []
    
    # Header Banner
    story.append(Paragraph("AquaGuard AI — Environmental Intelligence", title_style))
    story.append(Paragraph(f"Water Usage Anomaly, Leakage Risk & Sustainability Audit Report | Generated {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=15))
    
    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary", h2_style))
    total_vol = metrics_data.get('total_volume', 'N/A')
    anom_count = metrics_data.get('anomaly_count', 0)
    crit_count = metrics_data.get('critical_count', 0)
    excess_vol = metrics_data.get('excess_volume', 'N/A')
    sust_score = metrics_data.get('sustainability_score', 'N/A')
    
    summary_text = (
        f"This audit synthesizes telemetry from <b>{metrics_data.get('meters_count', 'N/A')} monitored water meters</b>. "
        f"Across the evaluation period, total cumulative consumption reached <b>{total_vol} Liters</b>. "
        f"AquaGuard AI's hybrid detection engine identified <b>{anom_count} total anomalies</b>, of which "
        f"<b>{crit_count} are classified as Critical priority</b>. Algorithmic analysis estimates an excess volume of "
        f"<b>{excess_vol} Liters</b> above standard baseline operations. The enterprise AquaGuard Sustainability Score "
        f"is benchmarked at <b>{sust_score}/100</b>."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 10))
    
    # KPI Grid Table
    kpi_data = [
        ['Metric', 'Measured Value', 'Baseline Comparison', 'Status'],
        ['Total Consumption', f"{total_vol} L", 'Historical Target', 'Normal'],
        ['Anomalies Detected', str(anom_count), 'Expected <= 5', 'Attention Needed' if anom_count > 5 else 'Optimal'],
        ['Critical Alerts', str(crit_count), 'Tolerance: 0', 'Action Required' if crit_count > 0 else 'Optimal'],
        ['Estimated Excess Volume', f"{excess_vol} L", 'Goal: Minimization', f"{metrics_data.get('excess_pct', 0)}% of total"],
        ['Sustainability Score', f"{sust_score} / 100", 'Target: > 75', metrics_data.get('sust_tier', 'Normal')],
        ['Data Quality Index', f"{metrics_data.get('data_quality_score', 100)}%", 'Target: > 85%', 'Verified']
    ]
    t_kpi = Table(kpi_data, colWidths=[2.2*inch, 1.6*inch, 1.8*inch, 1.6*inch])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
        ('ALIGN', (1,0), (2,-1), 'CENTER'),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 15))
    
    # 2. Critical Alerts & Anomalies Breakdown
    story.append(Paragraph("2. Critical Anomalies & Incident Registry", h2_style))
    anomalies_sample = metrics_data.get('recent_anomalies', [])
    if anomalies_sample:
        anom_rows = [['Timestamp', 'Meter ID', 'Location', 'Usage (L)', 'Deviation', 'Risk', 'Type']]
        for a in anomalies_sample[:6]:
            anom_rows.append([
                str(a.get('timestamp', ''))[:16],
                str(a.get('meter_id', '')),
                str(a.get('location', 'Facility')),
                f"{float(a.get('actual_usage', 0)):,.0f}",
                f"{float(a.get('deviation_pct', 0)):+.0f}%",
                f"{float(a.get('risk_score', 0)):.0f}",
                str(a.get('anomaly_type', 'Spike'))[:18]
            ])
        t_anom = Table(anom_rows, colWidths=[1.4*inch, 1.1*inch, 1.2*inch, 1.0*inch, 0.9*inch, 0.7*inch, 1.4*inch])
        t_anom.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8.5),
            ('BOTTOMPADDING', (0,0), (-1,0), 5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('ALIGN', (3,1), (5,-1), 'CENTER'),
        ]))
        story.append(t_anom)
    else:
        story.append(Paragraph("No critical anomalies logged during this reporting window.", body_style))
        
    story.append(Spacer(1, 15))
    
    # 3. Possible Causes & Explainability
    story.append(Paragraph("3. Explainable Root Cause Hypotheses", h2_style))
    story.append(Paragraph(
        "AquaGuard AI evaluates statistical deviations, nocturnal flow persistence, and occupancy ratios to generate evidence-backed hypotheses. <i>Note: All items are potential hypotheses requiring on-site operational verification.</i>",
        body_style
    ))
    story.append(Spacer(1, 4))
    
    causes_list = metrics_data.get('top_causes', [
        "Possible continuous pipe or valve leakage: Abnormal flow sustained during 01:00-04:00 quiet hours.",
        "Possible equipment cycling or flush surge: Sudden instantaneous spikes exceeding 180% baseline.",
        "Possible occupancy surge: Activity discrepancies compared with typical weekend profiles."
    ])
    for c in causes_list:
        story.append(Paragraph(f"• <b>Hypothesis:</b> {c}", bullet_style))
        story.append(Spacer(1, 2))
        
    story.append(Spacer(1, 10))
    
    # 4. Actionable Conservation Recommendations
    story.append(Paragraph("4. Prioritized Conservation Recommendations", h2_style))
    recs_list = metrics_data.get('top_recommendations', [
        "Conduct physical leak detection survey in high-risk zones flagged with persistent night consumption.",
        "Verify sub-meter calibration and pressure regulator valves on risers with recurring spikes.",
        "Implement automated nocturnal setback valves across non-residential academic facilities.",
        "Integrate facility maintenance log with AquaGuard anomaly event timestamps for cross-validation."
    ])
    for r in recs_list:
        story.append(Paragraph(f"✓ {r}", bullet_style))
        story.append(Spacer(1, 2))
        
    story.append(Spacer(1, 10))
    
    # 5. What-if Scenario & Forecasting Outlook
    story.append(Paragraph("5. What-if Scenario & Projected Conservation", h2_style))
    sim_data = metrics_data.get('what_if', {})
    sim_text = (
        f"Under an achievable <b>{sim_data.get('resolution_target_pct', 50)}% anomaly remediation target</b>, "
        f"projected water recovery is estimated at <b>{sim_data.get('total_potential_reduction_liters', 0):,.0f} Liters</b>. "
        f"This corresponds to an estimated direct utility savings of <b>${sim_data.get('estimated_cost_saved_usd', 0):,.2f}</b> "
        f"and approximately <b>{sim_data.get('estimated_co2_offset_kg', 0):,.1f} kg CO2 emission reductions</b>."
    )
    story.append(Paragraph(sim_text, body_style))
    story.append(Spacer(1, 12))
    
    # 6. Methodology & Limitations
    story.append(Paragraph("6. Methodology & Operational Limitations", h2_style))
    method_text = (
        "<b>Detection Algorithms:</b> Hybrid ensemble combining 7-Day Rolling Baseline, Robust Z-Score, Interquartile Range (IQR), and Scikit-Learn Isolation Forest.<br/>"
        "<b>Limitations:</b> AquaGuard AI analyzes manual and telemetry meter records without physical IoT hardware integration. Causes are probabilistic hypotheses based on temporal pattern heuristics and should be corroborated by facility maintenance personnel."
    )
    story.append(Paragraph(method_text, body_style))
    
    doc.build(story)
    return output_filepath

def export_readings_csv(df, filepath):
    df.to_csv(filepath, index=False)
    return filepath

def export_readings_excel(df, filepath):
    df.to_excel(filepath, index=False, engine='openpyxl')
    return filepath
