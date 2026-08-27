# SIH26102 — AI-Powered MPLADS Monitoring & Early Warning System

An intelligent, full-stack government project monitoring and anomaly detection platform designed for the **Members of Parliament Local Area Development Scheme (MPLADS)**.

Built for **Smart India Hackathon 2026 (Problem Statement SIH26102)**.

---

## 🌟 Key Features

1. **Role-Based Access Control (RBAC)**
   - **Ministry (MoSPI)**: National/State consolidated portfolio & central vigilance escalation inbox.
   - **State Nodal (Maharashtra)**: State-wide constituency oversight & inter-district performance tracking.
   - **District Authority (DM / DC)**: Work sanctioning approval queues, guideline compliance audit, and field inspection dispatch.
   - **Member of Parliament (MP)**: Constituency portfolio (*Shri Piyush Goyal, Smt. Varsha Gaikwad, etc.*) with live ₹500 Lakhs annual entitlement balance tracking.

2. **Statutory Compliance Rule Engine (`compliance_engine.py`)**
   - Independent verification against official MoSPI operational guidelines:
     - **Work Eligibility**: Flags prohibited assets (religious shrines, commercial property, private trusts).
     - **Fund Ceilings**: Enforces the ₹75 Lakhs trust asset cap and validates ₹500 Lakhs annual MP limits.
     - **Implementing Agency Rules**: Verifies accredited government engineering bodies (MCGM, PWD, MMRDA, BEST) vs. unauthorized private contractors.
     - **Statutory Deadlines**: Audits the mandatory 75-day sanction timeline from MP recommendation.

3. **Multi-Signal AI Anomaly Engine (`anomaly_engine.py`)**
   - **Cost Anomaly**: Statistical Z-scores comparing work costs to category medians.
   - **Delay Anomaly**: Elapsed execution time vs. scheduled completion.
   - **Utilization Mismatch**: Time-weighted fund burn-rate analysis.
   - **Isolation Forest**: Unsupervised multivariate outlier detection (`scikit-learn`).
   - **Explainable Risk Score (0–100)**: Categorized into Low (0–30), Medium (31–60), and High (61–100) with clear plain-text justifications.

4. **Predictive Early Warning & Duplicate Detection (`predictive_engine.py`)**
   - **Burn-Rate Delay Forecast**: Projects milestone delays in months *before* the deadline passes.
   - **Fiscal Year Utilization Shortfall**: Forecasts unspent allocation shortfalls at FY-end.
   - **Spatial-Semantic Duplicate Detection**: Identifies overlapping community assets and duplicate billings within 250 meters.

5. **eSAKSHI CSV Ingestion Pipeline (`csv_pipeline.py`)**
   - Drag-and-drop file upload for official eSAKSHI tabular exports.
   - Automatically standardizes headers, validates compliance, calculates predictive delays, computes AI risk scores, and commits to SQLite.

6. **Auditor Feedback Loop (Active Learning)**
   - Ground inspectors can record verified physical findings (**Confirmed / False Positive / Under Investigation**) on project drill-downs to calibrate model confidence.

7. **Executive KPIs & Analytics**
   - **Quarterly Completion Velocity Chart** (Chart.js line chart).
   - **Alert Precision / Accuracy %** (derived from ground audit feedback).
   - **Mean Time to Detection** (2.4 days vs. 365-day traditional CAG audit lag).
   - **Audit Effort Reduction %** (72.8% manual review savings).

---

## 🛠️ Technology Stack

- **Backend**: Python 3, Flask, SQLite3
- **Machine Learning & Analytics**: Scikit-learn (Isolation Forest), Pandas, NumPy
- **Frontend**: HTML5, Vanilla CSS3 (Dark Glassmorphism Design System), JavaScript (ES6+)
- **Visualizations**: Leaflet.js (Dark OpenStreetMap), Chart.js (Donut & Velocity Line Charts)

---

## 🚀 Quick Start & Installation

### 1. Clone the repository
```bash
git clone https://github.com/Mayuresh-Dasure/SIH.git
cd SIH
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database (Optional - Pre-seeded `mplads.db` included)
```bash
python seed_data.py
python anomaly_engine.py
```

### 4. Run the Web Application
```bash
python app.py
```

### 5. Access the Dashboard
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## 🧪 Running the Verification Test Suite

```bash
python test_prototype.py
```

---

## 📁 Repository Structure

```
SIH/
├── app.py                      # Flask Application with REST APIs & RBAC routes
├── database.py                 # SQLite Data Layer & Schema
├── compliance_engine.py        # Statutory Guideline Rule Evaluation Engine
├── anomaly_engine.py           # Multi-Signal AI Anomaly Scoring & Alert Routing
├── predictive_engine.py        # Predictive Delay Forecast & Duplicate Detection
├── csv_pipeline.py             # eSAKSHI CSV Data Ingestion & Parser
├── seed_data.py                # Realistic Mumbai MPLADS Dataset Generator
├── test_prototype.py           # End-to-End Automated Test Suite
├── sample_esakshi_mumbai.csv   # Downloadable Sample eSAKSHI CSV Template
├── mplads.db                   # SQLite Database File
├── requirements.txt            # Python Dependencies
├── templates/
│   ├── base.html               # Base layout with RBAC Role Switcher
│   ├── dashboard.html          # Main Dashboard with 5 Navigation Tabs
│   └── project_detail.html     # Deep-Dive View with Compliance Checklist & Feedback
└── static/
    ├── css/
    │   └── style.css           # Dark Glassmorphism Design System
    └── js/
        └── dashboard.js        # Dynamic UI, Map, Charts, Alerts & Upload Handlers
```

---

## 📜 Problem Statement Mapping (SIH26102)

| Problem Statement Pillar | Solution in this System | Module |
|---|---|---|
| **Cost Overruns & Abnormally High Costs** | Statistical Category Z-Score + Isolation Forest Outlier Model | `anomaly_engine.py` |
| **Duplicate / Overlapping Works** | Geospatial Haversine (&lt; 250m) + Jaccard Descriptive Token Overlap | `predictive_engine.py` |
| **Project Delays & Stagnant Execution** | Expenditure Burn-Rate Velocity Delay Forecasting | `predictive_engine.py` |
| **Fund Flow & Underutilization** | Time-Weighted Burn Ratios & FY Allocation Shortfall Regression | `anomaly_engine.py` |
| **Statutory Guideline Deviations** | Negative List, ₹75L Trust Cap, ₹5 Cr MP Cap, 75-Day Sanction Deadlines | `compliance_engine.py` |
| **Feedback Loop & Active Learning** | Ground Auditor Outcome Logging & False Positive Model Tuning | `database.py` & UI |
