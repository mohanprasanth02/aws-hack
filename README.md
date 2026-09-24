# AquaGuard AI — Water Usage Anomaly & Sustainability Intelligence Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Flask 3.0](https://img.shields.io/badge/framework-Flask%203.0-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Machine Learning](https://img.shields.io/badge/ML-Scikit--learn-orange.svg)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **PS-054 — Environment and Sustainability — Water Usage Anomaly Dashboard**  
> *"Build a dashboard that analyzes manually uploaded meter records, identifies unusual consumption patterns and explains possible causes without hardware integration."*

---

## 1. Executive Overview

**AquaGuard AI** is a full-stack, enterprise-grade environmental intelligence and water conservation platform. It bridges the gap between raw utility telemetry and facility management operations by detecting unexpected water loss, diagnosing potential leakages, computing empirical carbon footprints, and forecasting future demand **entirely from manual meter records or spreadsheet logs without requiring any physical IoT hardware sensors**.

---

## 2. Key Architecture & Capabilities

### Data Ingestion & Preprocessing Pipeline
- **Dual Format Support:** Accepts `.csv`, `.xlsx`, and `.xls` files up to 32MB.
- **Strict Pre-Ingestion Validation:** Detects missing required schema headers, unparseable timestamps, duplicate timestamps per meter, negative usage values, out-of-range geographic coordinates, and statistical extreme outliers.
- **Data Quality Score (0–100):** Calculates an empirical rating of dataset integrity before ingestion.
- **Derived Feature Engineering:** Computes diurnal temporal markers (`hour`, `day_of_week`, `is_weekend`, `is_night`), lag vectors, percentage changes, and 7-day rolling statistical envelopes (`rolling_mean`, `rolling_std`).

### Hybrid Anomaly Detection Engine
Combines 5 complementary detection techniques into a normalized **AquaGuard Risk Score (0–100)**:
1. **7-Day Rolling Baseline:** Evaluates local temporal window deviations per meter.
2. **Robust Z-Score:** Measures variance multiples while safely handling zero-variance floors.
3. **Interquartile Range (IQR):** Non-parametric Tukey fences resilient to heavy data skew.
4. **Percentage Departure:** Directly flags departures exceeding calibrated operational thresholds.
5. **Isolation Forest:** Unsupervised multi-dimensional tree isolation evaluating volume, temporal flags, and lagged usage.
- **Severity Tiers:** `Normal` (0–30), `Low` (31–60), `Medium` (61–80), `High` (81–95), `Critical` (96–100).
- **Archetype Classification:** Sudden Spikes, Sudden Drops, Persistent High Flow, Night-Time Flow, and Gradual Drifts.

### Explainable Root Cause Hypotheses
In adherence to domain safety standards, causes are formulated as **evidence-backed hypotheses**, never as definitive conclusions:
- **Supporting Observations (Evidence):** Explicit checklist (e.g. *"+185% above rolling baseline"*, *"+3.8 standard deviations"*, *"Observed during 02:00 quiet hours"*, *"Persisted across 6 observation cycles"*).
- **Hypotheses Formulated:** Continuous pipe/fixture leakage, cooling tower cycling, irrigation timers, flush surges, or telemetry sensor dropout.
- **Prioritized Recommendations:** Actionable physical inspection steps.

### Geospatial Surveillance (Leaflet.js)
- Color-coded risk markers (Green: Normal, Yellow: Medium, Orange: High, Red: Critical).
- Interactive telemetry popups displaying real-time flow, rolling baseline, departure, and latest alert.
- Dedicated "Location Unavailable" drawer ensuring meters without coordinates are never placed arbitrarily.

### Environmental ESG & Sustainability Analytics
- **AquaGuard Sustainability Score (0–100):** Transparent factor decomposition:
  - Anomaly Frequency (25%)
  - Load Stability / CV (20%)
  - Excess Water Control (25%)
  - Nocturnal Flow Minimization (15%)
  - Conservation Trend Direction (15%)
- **Impact Metrics:** Computes estimated excess water volume (Liters), financial utility loss ($), and embedded carbon footprint (kg CO2).

### Interactive What-If Simulator
- Sliders for **Anomaly Resolution %** and **Target Reduction %**.
- Dynamic recalculation of projected consumption, recovered volume, financial savings, and CO2 offset.

### Dynamic Model Evaluation Benchmark
- Evaluates detection performance against verified ground-truth labelled synthetic datasets.
- Dynamically computes **Precision, Recall, F1-Score, Accuracy, and Confusion Matrices** comparing Z-Score, IQR, Isolation Forest, and the AquaGuard Hybrid Ensemble.

### Executive PDF Audit & Data Export
- Real-time PDF generation using **ReportLab** with institutional header banners, KPI summaries, incident tables, and methodology limitations.
- Direct CSV and Microsoft Excel (`.xlsx`) data exports.

---

## 3. Technology Stack

- **Backend:** Python 3.11+, Flask 3.0, Flask-SQLAlchemy, Flask-Login, SQLite.
- **Data Science & ML:** Pandas, NumPy, Scikit-learn, SciPy.
- **Reporting & Spreadsheets:** ReportLab, OpenPyXL.
- **Frontend:** Modern Semantic HTML5, Vanilla CSS Design System with Glassmorphism, Bootstrap 5, Chart.js 4.4, Leaflet.js 1.9, Bootstrap Icons.

---

## 4. Installation & Local Setup

### Step 1: Clone or Navigate to Directory
```bash
cd "e:/web/class hack"
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python app.py
```
*The database (`aquaguard.db`), default settings, demo user account, and bundled benchmark datasets in `data/` are automatically initialized on first run.*

Access the dashboard at: **`http://localhost:5000`**

---

## 5. Demo Credentials

| Role | Email | Password |
|---|---|---|
| **Lead Analyst** | `demo@aquaguard.ai` | `AquaGuard2026!` |

*(A one-click "Auto-fill" button is also provided on the `/login` screen).*

---

## 6. One-Click Demo Mode

To instantly demonstrate the full platform during a hackathon evaluation:
1. Log in with the demo credentials.
2. Click **"Launch Demo"** on the top navigation bar or dashboard banner.
3. AquaGuard will:
   - Generate realistic diurnal water usage data with morning/evening peaks and weekend reductions.
   - Inject benchmark labeled anomalies (spikes, persistent nocturnal leaks, drops).
   - Execute the validation, cleaning, and hybrid ML detection pipeline.
   - Populate the live KPIs, 5 dynamic charts, geospatial map, alert center, and model evaluation metrics.

---

## 7. CSV Upload Schema

Download the pre-formatted CSV template from `/upload` or `/api/template/download`.

| Column | Type | Requirement | Description |
|---|---|---|---|
| `timestamp` | Datetime | **Required** | E.g. `2026-09-01 08:00:00` |
| `meter_id` | String | **Required** | E.g. `MTR-SCI-01` |
| `usage_liters` | Numeric | **Required** | Non-negative volume (Liters) |
| `location` | String | Optional | Campus or facility zone |
| `building` | String | Optional | Complex or building name |
| `occupancy` | Integer | Optional | Occupant count for per-capita normalization |
| `latitude` | Float | Optional | Decimal latitude (-90 to +90) |
| `longitude` | Float | Optional | Decimal longitude (-180 to +180) |
| `meter_capacity` | Float | Optional | Nominal maximum capacity (L/hr) |
| `activity_type` | String | Optional | E.g. `Academic Lab`, `Residential` |

---

## 8. REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/dashboard` | `GET` | Filtered KPIs, trends, day-of-week, and severity distribution |
| `/api/validate` | `POST` | Validates uploaded file schema, checks duplicates, returns quality index |
| `/api/upload` | `POST` | Ingests file, runs cleaning, runs hybrid detection, updates database |
| `/api/demo/launch` | `POST` | Generates benchmark synthetic data and populates surveillance records |
| `/api/forecast` | `GET` | Returns 7 or 30-day forecast trajectories with confidence envelopes |
| `/api/sustainability` | `GET` | Returns 5-factor breakdown of AquaGuard Sustainability Score |
| `/api/what-if` | `GET/POST`| Calculates water, monetary ($), and carbon savings from simulation sliders |
| `/api/evaluation` | `GET` | Computes Precision, Recall, F1, and Confusion Matrices across models |
| `/api/reports/generate`| `POST` | Compiles institutional executive PDF audit via ReportLab |
| `/api/export/csv` | `GET` | Exports sanitized readings as CSV |
| `/api/export/excel` | `GET` | Exports sanitized readings as Microsoft Excel (.xlsx) |
| `/api/meters/map` | `GET` | Returns meters geo-coordinates and real-time risk scores |
| `/api/water-intelligence/mnf` | `GET` | Minimum Night Flow (02:00–04:00 AM), background leakage floor, 14d drift |
| `/api/water-intelligence/water-balance` | `GET` | IWA Standard Water Balance: SIV, NRW %, Real vs Apparent losses, ILI score |
| `/api/water-intelligence/assets` | `GET` | Cooling tower cycles of conc, smart irrigation rain lock, cistern trickle |
| `/api/water-intelligence/stewardship` | `GET` | Alliance for Water Stewardship (AWS) Standard & LEED WE credit scorecard |
| `/api/work-orders` | `GET/POST`| Work order ticket lifecycle, field technician dispatch, water saved KPIs |
| `/api/work-orders/<id>/dispatch` | `POST` | Assign technician to work order and transition status to Dispatched |
| `/api/work-orders/<id>/resolve` | `POST` | Resolve ticket, log root cause & repair action, compute verified savings |

---

## 9. Real-World Water Engineering Capabilities

### Minimum Night Flow (MNF) Analysis (IWA Standard)
Between 02:00 AM and 04:00 AM, human activity drops to near zero. AquaGuard analyzes this nocturnal window to distinguish legitimate base demand from **Net Background Infrastructure Leakage (BIL)**, calculating the **Night-to-Day Ratio (NDR)** and tracking 14-day insidious drift.

### District Metered Area (DMA) & IWA Water Balance
Calculates Non-Revenue Water (NRW) according to the International Water Association framework:
- **System Input Volume (SIV)** vs. **Billed Authorized Consumption**
- **Real Physical Losses:** Underground fractures, burst mains, reservoir overflow
- **Apparent Losses:** Meter calibration under-registration at low flow, unauthorized usage
- **Infrastructure Leakage Index (ILI):** Rated Category A (World Class) through Category D.

### Maintenance Work Orders & Closed-Loop Remediation
Connects software insights directly to field plumbing crews:
1. Anomaly or nocturnal leak detected
2. Work order created with priority (Emergency, High, Medium, Low) and asset category
3. Technician dispatched with automated assignment
4. Technician performs physical pipe/valve repair and marks Resolved
5. System computes **Verified Water Saved (Liters)**, utility cost recovery ($), and avoided CO2 emissions.

---

## 10. Production Deployment (Docker & AWS Cloud)

### Run Locally with Docker Compose (PostgreSQL + TimescaleDB + Redis)
```bash
docker-compose up --build
```
Access the application at `http://localhost:5000`.

### AWS Cloud Architecture (ECS Fargate + RDS + S3 + SES)
The repository includes:
- `Dockerfile`: Multi-stage Python 3.11 production image with Gunicorn and health checks.
- `deploy/aws-ecs-task-definition.json`: Ready for AWS ECS Fargate serverless container deployment.
- `.env.example`: Configuration template for AWS RDS PostgreSQL, AWS S3 buckets, AWS SES email, and Twilio SMS alerts.

---

## 11. Automated Testing

Execute the test suite verifying validation, cleaning, anomaly scoring, cause engine, water intelligence, and work orders:
```bash
python -m unittest tests/test_aquaguard.py
```

---

## 12. Acceptance Checklist

- [x] Full authentication (Register, Login, Remember Me, Demo auto-fill)
- [x] Drag-and-drop CSV/Excel upload with client progress bar
- [x] Pre-ingestion validation (missing columns, duplicates, negative rejection, coords)
- [x] Data quality index (0–100) and downloadable template
- [x] Multi-method hybrid anomaly engine (Rolling baseline, Z-Score, IQR, Isolation Forest)
- [x] Normalized AquaGuard Risk Score (0–100) and severity categorizations
- [x] Explainable root cause hypotheses & evidence checklists
- [x] Minimum Night Flow (MNF) analysis with 02:00–04:00 AM quiet nocturnal window
- [x] IWA District Metered Area (DMA) Water Balance & Non-Revenue Water (NRW) calculator
- [x] Specialized asset diagnostics (Cooling towers, irrigation weather locks, restroom fixtures)
- [x] Alliance for Water Stewardship (AWS) Standard & LEED Water Efficiency scorecards
- [x] Maintenance Work Orders & field technician dispatch lifecycle
- [x] Closed-loop verified water conservation & financial savings tracking
- [x] Interactive Leaflet map with color-coded pulsing markers and unmapped drawer
- [x] Predictive forecasting (7d/30d) with confidence uncertainty bounds
- [x] AquaGuard Sustainability Score with 5 transparent factor decompositions
- [x] Interactive What-If scenario simulator
- [x] Empirical model evaluation comparing Precision, Recall, F1, and Confusion Matrices
- [x] Institutional PDF report generator via ReportLab & CSV/Excel exports
- [x] Production Dockerfile, docker-compose.yml, and AWS ECS Task Definition
- [x] Pure responsive glassmorphic dark theme respecting `prefers-reduced-motion`

