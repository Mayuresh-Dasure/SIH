# CLAUDE.md — Complete Project Context & Developer Guide

## 📌 Project Overview
- **Project Name:** AI-Powered MPLADS Monitoring & Early Warning System
- **Hackathon:** Smart India Hackathon 2026 (SIH)
- **Problem Statement ID:** SIH26102
- **Objective:** Build an intelligent, transparent, and explainable monitoring system for the **Members of Parliament Local Area Development Scheme (MPLADS)**. The system ingests public MPLADS project data (demonstrated on Mumbai constituencies), runs multi-signal AI anomaly detection, evaluates statutory guideline compliance rules, forecasts milestone delays and fund shortfalls, and routes actionable alerts through Role-Based Access Control (RBAC).

---

## 🛠️ Technology Stack
- **Backend Framework:** Python 3.10+ / Flask 3.1
- **Machine Learning & Analytics:** Scikit-learn (Isolation Forest), Pandas, NumPy
- **Database Layer:** SQLite3 (`mplads.db`) with native JSON support
- **Frontend Architecture:** HTML5, Jinja2 Templates, Vanilla JavaScript (ES6+), Vanilla CSS3 (Custom Dark Glassmorphism Design System)
- **Geospatial & Visualizations:** Leaflet.js (Dark OpenStreetMap tiles), Chart.js (Donut & Line charts)

---

## 🏛️ Role-Based Access Control (RBAC) Architecture
The system implements strict contextual data scoping and alert routing across 4 administrative personas:
1. **Ministry (MoSPI - Central Government):** Consolidated national/state portfolio, central vigilance escalation inbox, policy-level compliance oversight.
2. **State Nodal Officer (Maharashtra):** State-wide constituency comparisons, cross-district execution performance, and district-level escalation monitoring.
3. **District Authority (District Magistrate / District Planning Officer):** Local sanction approval queues, statutory 75-day compliance audits, and physical field inspection dispatching.
4. **Member of Parliament (MP):** Constituency portfolio (*e.g., Shri Piyush Goyal, Smt. Varsha Gaikwad*), live ₹500 Lakhs annual entitlement balance tracking, and pre-milestone early warning flags.

---

## 📂 Repository File Structure & Module Responsibilities

```
d:\SIH\
├── app.py                      # Flask backend: Web routes, REST APIs, RBAC session/query handling
├── database.py                 # SQLite database layer, schema definitions, audit logging, aggregations
├── compliance_engine.py        # Deterministic Statutory Rule Engine (MoSPI Operational Guidelines)
├── anomaly_engine.py           # Multi-Signal AI Anomaly Engine & Automated Alert Routing
├── predictive_engine.py        # Velocity Burn-Rate Delay Forecasting & Spatial Duplicate Detection
├── csv_pipeline.py             # eSAKSHI CSV/Excel Ingestion Pipeline & Schema Normalizer
├── seed_data.py                # Realistic Mumbai MPLADS Dataset Generator (117+ projects)
├── test_prototype.py           # End-to-End Automated Test Suite (10 test cases)
├── sample_esakshi_mumbai.csv   # Downloadable/Uploadable Sample eSAKSHI Template
├── mplads.db                   # SQLite Database File
├── requirements.txt            # Python Dependencies
├── README.md                   # User-facing README for GitHub
├── CLAUDE.md                   # Full developer & system context specification
├── templates/
│   ├── base.html               # Base layout with interactive RBAC role switcher
│   ├── dashboard.html          # Main dashboard with 5 tabs (Overview, Alerts, KPIs, Ingestion, PS Matrix)
│   └── project_detail.html     # Deep-dive view with Compliance Checklist, Early Warning, & Auditor Card
└── static/
    ├── css/
    │   └── style.css           # Design system tokens, glassmorphism panels, responsive grid
    └── js/
        └── dashboard.js        # Tab manager, RBAC state, map renderer, charts, alerts, upload handlers
```

---

## 🧠 Core Engines & Mathematical Formulations

### 1. Multi-Signal AI Anomaly Engine (`anomaly_engine.py`)
Computes an explainable Risk Score ($0 \le S \le 100$):
- **Cost Anomaly ($Z_{\text{cost}}$):** Evaluates deviation from category median cost:
  $$Z = \frac{\text{Cost} - \mu_{\text{cat}}}{\sigma_{\text{cat}}}$$
  Flags if $Z > 1.5$ (e.g. *"Cost is 151% higher than median for School Infrastructure"*).
- **Delay Anomaly:** Evaluates overdue ratio against expected project schedule:
  $$\text{Overdue Ratio} = \frac{\text{Actual/Current Date} - \text{Expected Date}}{\text{Expected Duration}}$$
- **Utilization Mismatch:** Identifies projects older than 6 months with $<20\%$ spending, or suspiciously exact $100\%$ spending.
- **Speed Anomaly:** High-value projects ($> ₹10\text{L}$) completed in $<30\text{ days}$.
- **Isolation Forest:** Unsupervised multivariate outlier model trained on $[\text{Sanctioned}, \text{Expenditure}, \text{Utilization \%}, \text{Category Encoded}, \text{Duration}]$.
- **Score Aggregation:** Primary severity signal + secondary compound boost + duplicate boost + compliance violation boost, normalized to $[0, 100]$.

### 2. Statutory Compliance Rule Engine (`compliance_engine.py`)
Deterministic checks based on official MoSPI Operational Guidelines:
- **Work Eligibility (Guideline Para 5.1):** Checks against the prohibited Negative List (religious shrines, commercial entities, private property, memorials).
- **Fund Ceilings (Guideline Para 3.12 & 3.1):** Enforces ₹75 Lakhs cap for non-government trusts/societies; validates total recommendations against ₹500 Lakhs annual MP ceiling.
- **Agency Accreditation (Guideline Para 2.5):** Validates accredited government nodal agencies (MCGM, PWD, MMRDA, BEST, MHADA) vs. unregistered private contractors.
- **Statutory Deadlines (Guideline Para 3.3):** Audits mandatory 75-day sanction timeline from MP recommendation date.

### 3. Predictive Early Warning & Duplicate Detection (`predictive_engine.py`)
- **Expenditure Burn-Rate Velocity:**
  $$V = \frac{\text{Cumulative Expenditure}}{\text{Elapsed Days}}$$
- **Projected Completion Delay:**
  $$\text{Projected Remaining Days} = \frac{\text{Sanctioned} - \text{Expenditure}}{V}$$
  Computes predicted delay months *before* scheduled deadlines are missed.
- **Fiscal Year Utilization Shortfall:** Forecasts unspent allocation balances by March 31.
- **Early Warning Tiers:** `🟢 ON_TRACK` ($<1\text{ mo}$ delay), `🟡 AT_RISK` ($1–3\text{ mo}$ delay), `🔴 CRITICAL` ($>3\text{ mo}$ delay or stagnant spend).
- **Spatial & Semantic Duplicate Detection:** Computes Haversine distance ($d \le 250\text{m}$) and Jaccard word-token overlap ($J > 0.35$) between all project pairs to catch double-billing and overlapping community assets.

---

## 🗄️ Database Schema (`mplads.db`)

### Table: `projects`
- `id` (INTEGER PRIMARY KEY)
- `project_name` (TEXT), `category` (TEXT), `mp_name` (TEXT), `constituency` (TEXT), `district` (TEXT), `state` (TEXT)
- `sanctioned_amount` (REAL), `expenditure` (REAL), `utilization_pct` (REAL), `status` (TEXT)
- `recommendation_date` (TEXT), `sanction_date` (TEXT), `start_date` (TEXT), `expected_completion` (TEXT), `actual_completion` (TEXT)
- `latitude` (REAL), `longitude` (REAL), `implementing_agency` (TEXT), `agency_type` (TEXT), `beneficiary_type` (TEXT), `description` (TEXT)
- `risk_score` (REAL), `risk_reasons` (TEXT JSON)
- `compliance_status` (TEXT: `PASSED`, `WARNING`, `VIOLATION`), `compliance_flags` (TEXT JSON)
- `predicted_delay_months` (REAL), `early_warning_level` (TEXT: `ON_TRACK`, `AT_RISK`, `CRITICAL`), `projected_shortfall` (REAL)
- `duplicate_flag` (TEXT JSON)
- `alert_assigned_to` (TEXT: `DPO`, `DM`, `STATE_NODAL`, `MINISTRY`), `alert_status` (TEXT: `NEW`, `ASSIGNED`, `INSPECTION_ORDERED`, `RESOLVED`)

### Table: `audit_feedback` (Active Learning)
- `id` (INTEGER PRIMARY KEY), `project_id` (INTEGER), `auditor_name` (TEXT), `role` (TEXT)
- `verdict` (TEXT: `CONFIRMED`, `FALSE_POSITIVE`, `UNDER_INVESTIGATION`), `notes` (TEXT), `created_at` (TIMESTAMP)

### Table: `alert_actions`
- `id` (INTEGER PRIMARY KEY), `project_id` (INTEGER), `action_type` (TEXT: `ASSIGN_INSPECTION`, `REQUEST_EXPLANATION`, `RESOLVE`, `ESCALATE`)
- `performed_by` (TEXT), `role` (TEXT), `notes` (TEXT), `created_at` (TIMESTAMP)

---

## 🌐 REST API Specifications

| Method | Endpoint | Description | Scoped Parameters |
|---|---|---|---|
| `GET` | `/` | Main interactive dashboard | `?role=...&mp_name=...&district=...` |
| `GET` | `/project/<id>` | Project deep-dive page | `?role=...` |
| `GET` | `/api/summary` | Aggregate executive KPIs & totals | `?role=...&mp_name=...&district=...` |
| `GET` | `/api/projects` | Filtered & searched project records | `?q=...&risk=...&compliance=...&early_warning=...` |
| `GET` | `/api/map-data` | Geotagged marker records | `?role=...` |
| `GET` | `/api/alerts` | Role-routed actionable alert list | `?role=...&mp_name=...&district=...` |
| `POST` | `/api/alerts/<id>/action` | Dispatch alert action (inspect/resolve) | JSON: `{"action_type", "performed_by", "role", "notes"}` |
| `POST` | `/api/audit-feedback` | Record ground auditor verdict | JSON: `{"project_id", "auditor_name", "verdict", "notes"}` |
| `GET` | `/api/kpis` | Advanced efficiency & accuracy KPIs | None |
| `POST` | `/api/upload-csv` | Ingest eSAKSHI CSV/Excel file | Multipart form-data: `file` |
| `GET` | `/api/download-sample-csv` | Download bundled test eSAKSHI CSV | None |
| `POST` | `/api/recalculate` | Re-run AI & compliance models on DB | None |

---

## 🚀 Commands & Development Workflows

### Run Local Development Server
```bash
python app.py
# Server runs on http://127.0.0.1:5000/
```

### Re-seed Database & Re-run ML Models
```bash
python seed_data.py
python anomaly_engine.py
```

### Execute Automated Test Suite
```bash
python test_prototype.py
```

### Ingest Data via CLI / Pipeline
```bash
python csv_pipeline.py
```

---

## 🎯 SIH Problem Statement 26102 Mapping

1. **Cost Overruns:** Multi-signal Z-score deviation model + Isolation Forest in `anomaly_engine.py`.
2. **Duplicate Works:** Geospatial Haversine proximity + Jaccard token similarity in `predictive_engine.py`.
3. **Project Delays:** Progress burn-rate velocity forecasting in `predictive_engine.py`.
4. **Fund Flow & Underutilization:** Time-weighted spend ratios & FY shortfall regression in `anomaly_engine.py`.
5. **Guideline Deviations:** Negative list, ₹75L trust ceiling, ₹5 Cr MP entitlement, and 75-day sanction deadlines in `compliance_engine.py`.
6. **Active Learning Feedback:** Ground auditor verdict logging (`audit_feedback`) tuning model precision in `database.py`.
