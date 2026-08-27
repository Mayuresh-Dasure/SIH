"""
csv_pipeline.py — Realistic eSAKSHI CSV/Excel Ingestion Pipeline

Accepts official eSAKSHI exported tabular files or custom project spreadsheets,
validates column schemas, standardizes data, runs compliance & anomaly scoring,
and commits directly into the SQLite database.
"""

import os
import io
import csv
import pandas as pd
from database import get_connection, insert_projects_bulk
from compliance_engine import evaluate_compliance
from predictive_engine import calculate_predictive_delay, detect_duplicate_works

SAMPLE_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_esakshi_mumbai.csv')

# Standard eSAKSHI column mappings
COLUMN_ALIASES = {
    'work_name': ['project_name', 'work_name', 'work name', 'name of work', 'project'],
    'category': ['category', 'sector', 'work_category', 'project_type'],
    'mp_name': ['mp_name', 'mp name', 'name of mp', 'honorable mp', 'member of parliament'],
    'constituency': ['constituency', 'constituency_name', 'parliamentary_constituency', 'lok sabha constituency'],
    'district': ['district', 'district_name', 'nodal_district'],
    'state': ['state', 'state_name'],
    'sanctioned_amount': ['sanctioned_amount', 'sanctioned amount', 'amount_sanctioned', 'cost_in_lakhs', 'sanctioned (lakhs)'],
    'expenditure': ['expenditure', 'amount_spent', 'cumulative_expenditure', 'expenditure_lakhs', 'spent'],
    'status': ['status', 'work_status', 'project_status'],
    'start_date': ['start_date', 'commencement_date', 'date_of_commencement', 'work_order_date'],
    'expected_completion': ['expected_completion', 'target_date', 'completion_target_date', 'scheduled_completion'],
    'actual_completion': ['actual_completion', 'completion_date', 'date_of_completion'],
    'latitude': ['latitude', 'lat', 'geo_lat'],
    'longitude': ['longitude', 'lng', 'long', 'geo_lng'],
    'implementing_agency': ['implementing_agency', 'agency', 'executing_agency', 'nodal_agency'],
    'beneficiary_type': ['beneficiary_type', 'beneficiary', 'target_group']
}


def normalize_column_name(col: str) -> str:
    """Map arbitrary column header to standard field name."""
    clean = str(col).strip().lower().replace('_', ' ').replace('-', ' ')
    for standard, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if clean == alias or alias in clean:
                return standard
    return col.strip().lower().replace(' ', '_')


def parse_and_ingest_csv(file_stream, filename='upload.csv'):
    """
    Parse uploaded CSV or Excel file, validate schema, evaluate AI models,
    and persist into database.
    """
    try:
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(file_stream)
        else:
            if isinstance(file_stream, bytes):
                file_stream = io.BytesIO(file_stream)
            df = pd.read_csv(file_stream)
    except Exception as e:
        return {'success': False, 'error': f"Failed to parse file format: {str(e)}"}

    if df.empty:
        return {'success': False, 'error': 'Uploaded file is empty.'}

    # Normalize column names
    col_map = {orig: normalize_column_name(orig) for orig in df.columns}
    df = df.rename(columns=col_map)

    # Ensure required columns
    if 'work_name' in df.columns:
        df['project_name'] = df['work_name']

    if 'project_name' not in df.columns:
        return {'success': False, 'error': "Missing mandatory column: 'Project Name' or 'Work Name'"}

    # Fill defaults
    if 'sanctioned_amount' not in df.columns:
        df['sanctioned_amount'] = 10.0
    if 'expenditure' not in df.columns:
        df['expenditure'] = 0.0
    if 'category' not in df.columns:
        df['category'] = 'Community Infrastructure'
    if 'mp_name' not in df.columns:
        df['mp_name'] = 'Honorable MP'
    if 'constituency' not in df.columns:
        df['constituency'] = 'Mumbai North'
    if 'status' not in df.columns:
        df['status'] = 'Ongoing'

    projects_to_insert = []
    for _, row in df.iterrows():
        sanctioned = float(row.get('sanctioned_amount') or 10.0)
        expenditure = float(row.get('expenditure') or 0.0)
        utilization = round((expenditure / sanctioned * 100) if sanctioned > 0 else 0, 1)

        p = {
            'project_name': str(row.get('project_name') or 'MPLADS Project'),
            'category': str(row.get('category') or 'Community Infrastructure'),
            'mp_name': str(row.get('mp_name') or 'Honorable MP'),
            'constituency': str(row.get('constituency') or 'Mumbai North'),
            'district': str(row.get('district') or 'Mumbai Suburban'),
            'state': str(row.get('state') or 'Maharashtra'),
            'sanctioned_amount': sanctioned,
            'expenditure': expenditure,
            'utilization_pct': utilization,
            'status': str(row.get('status') or 'Ongoing'),
            'recommendation_date': str(row.get('start_date') or '2024-01-01')[:10],
            'sanction_date': str(row.get('start_date') or '2024-02-01')[:10],
            'start_date': str(row.get('start_date') or '2024-03-01')[:10],
            'expected_completion': str(row.get('expected_completion') or '2024-12-31')[:10],
            'actual_completion': str(row.get('actual_completion'))[:10] if pd.notna(row.get('actual_completion')) else None,
            'latitude': float(row.get('latitude')) if pd.notna(row.get('latitude')) else 19.12,
            'longitude': float(row.get('longitude')) if pd.notna(row.get('longitude')) else 72.85,
            'implementing_agency': str(row.get('implementing_agency') or 'MCGM'),
            'agency_type': 'Government',
            'beneficiary_type': 'Public Community',
            'description': str(row.get('description') or row.get('project_name')),
            'risk_score': 0.0,
            'risk_reasons': [],
            'compliance_status': 'PASSED',
            'compliance_flags': [],
            'predicted_delay_months': 0.0,
            'early_warning_level': 'ON_TRACK',
            'projected_shortfall': 0.0,
            'duplicate_flag': [],
            'alert_assigned_to': 'DPO',
            'alert_status': 'NEW'
        }

        # Run Compliance Evaluation
        comp_status, comp_flags = evaluate_compliance(p)
        p['compliance_status'] = comp_status
        p['compliance_flags'] = comp_flags

        # Run Predictive Delay
        pred_delay, early_warn, shortfall = calculate_predictive_delay(p)
        p['predicted_delay_months'] = pred_delay
        p['early_warning_level'] = early_warn
        p['projected_shortfall'] = shortfall

        projects_to_insert.append(p)

    # Insert into DB
    insert_projects_bulk(projects_to_insert)

    # Trigger re-scoring across all projects
    from anomaly_engine import calculate_risk_scores
    calculate_risk_scores()

    return {
        'success': True,
        'count': len(projects_to_insert),
        'message': f"Successfully processed and ingested {len(projects_to_insert)} eSAKSHI project records into database."
    }


def generate_sample_esakshi_csv():
    """Create a sample downloadable eSAKSHI format CSV file."""
    sample_records = [
        {
            'Work ID': 'MH-MUM-2024-001',
            'Work Name': 'Construction of Community Recreation Center at Borivali',
            'Category': 'Community Hall',
            'Honorable MP': 'Shri Piyush Goyal',
            'Constituency': 'Mumbai North',
            'District': 'Mumbai Suburban',
            'State': 'Maharashtra',
            'Sanctioned Amount (Lakhs)': 42.5,
            'Cumulative Expenditure (Lakhs)': 38.2,
            'Status': 'Completed',
            'Work Order Date': '2024-01-15',
            'Scheduled Completion': '2024-11-30',
            'Date of Completion': '2024-11-20',
            'Latitude': 19.2288,
            'Longitude': 72.8541,
            'Implementing Agency': 'MCGM',
            'Beneficiary Type': 'Public Community'
        },
        {
            'Work ID': 'MH-MUM-2024-002',
            'Work Name': 'Installation of High-Mast Solar Lighting at Goregaon East',
            'Category': 'Solar Lighting',
            'Honorable MP': 'Shri Ravindra Waikar',
            'Constituency': 'Mumbai North West',
            'District': 'Mumbai Suburban',
            'State': 'Maharashtra',
            'Sanctioned Amount (Lakhs)': 8.2,
            'Cumulative Expenditure (Lakhs)': 1.4,
            'Status': 'Ongoing',
            'Work Order Date': '2024-02-10',
            'Scheduled Completion': '2024-06-30',
            'Date of Completion': '',
            'Latitude': 19.1663,
            'Longitude': 72.8526,
            'Implementing Agency': 'MCGM Electrical Dept',
            'Beneficiary Type': 'Public Community'
        },
        {
            'Work ID': 'MH-MUM-2024-003',
            'Work Name': 'Modern Public Sanitation Block Construction at Kurla Station',
            'Category': 'Public Toilet',
            'Honorable MP': 'Smt. Varsha Gaikwad',
            'Constituency': 'Mumbai North Central',
            'District': 'Mumbai Suburban',
            'State': 'Maharashtra',
            'Sanctioned Amount (Lakhs)': 16.5,
            'Cumulative Expenditure (Lakhs)': 2.1,
            'Status': 'Delayed',
            'Work Order Date': '2023-08-01',
            'Scheduled Completion': '2024-02-28',
            'Date of Completion': '',
            'Latitude': 19.0688,
            'Longitude': 72.8804,
            'Implementing Agency': 'MCGM Solid Waste Dept',
            'Beneficiary Type': 'Public Community'
        },
        {
            'Work ID': 'MH-MUM-2024-004',
            'Work Name': 'School Laboratory & Digital Library Upgrade at Colaba',
            'Category': 'School Infrastructure',
            'Honorable MP': 'Shri Arvind Sawant',
            'Constituency': 'Mumbai South',
            'District': 'Mumbai City',
            'State': 'Maharashtra',
            'Sanctioned Amount (Lakhs)': 88.0,
            'Cumulative Expenditure (Lakhs)': 87.5,
            'Status': 'Completed',
            'Work Order Date': '2024-03-01',
            'Scheduled Completion': '2024-08-30',
            'Date of Completion': '2024-08-15',
            'Latitude': 18.9152,
            'Longitude': 72.8258,
            'Implementing Agency': 'MCGM Education Dept',
            'Beneficiary Type': 'Public Community'
        }
    ]

    df = pd.DataFrame(sample_records)
    df.to_csv(SAMPLE_CSV_PATH, index=False)
    print(f"[OK] Generated sample eSAKSHI CSV at {SAMPLE_CSV_PATH}")


if __name__ == '__main__':
    generate_sample_esakshi_csv()
