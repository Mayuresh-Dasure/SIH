"""
app.py — Flask application for MPLADS AI-Powered Monitoring Dashboard.
Upgraded with:
  - Role-Based Access Control (RBAC: Ministry, State Nodal, District Authority, MP)
  - Compliance Rule Engine Integration
  - Predictive Early Warning & Duplicate Detection
  - Alert Routing & Dispatch Actions
  - eSAKSHI CSV Ingestion Pipeline
  - Auditor Feedback Loop for Active Learning
  - Advanced SIH Efficiency KPIs & Completion Trends
"""

import json
import os
from flask import Flask, render_template, request, jsonify, send_file
from database import (
    init_db, get_all_projects, get_project, search_projects, get_summary_stats,
    get_map_data, get_alerts, update_alert_action, save_audit_feedback,
    get_kpis_and_audit_metrics
)
from anomaly_engine import calculate_risk_scores
from csv_pipeline import parse_and_ingest_csv, SAMPLE_CSV_PATH

app = Flask(__name__)


# ──────────────────────────────────────────────────────────────
# Page Routes
# ──────────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    """Main dashboard page supporting role context."""
    role = request.args.get('role', 'ministry')
    mp_name = request.args.get('mp_name', 'Shri Piyush Goyal')
    district = request.args.get('district', 'Mumbai Suburban')

    stats = get_summary_stats(role=role, mp_name=mp_name, district=district)
    kpis = get_kpis_and_audit_metrics()

    return render_template(
        'dashboard.html',
        stats=stats,
        kpis=kpis,
        current_role=role,
        current_mp=mp_name,
        current_district=district
    )


@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """Detailed drill-down page with compliance checklist, early warning, and auditor action card."""
    project = get_project(project_id)
    if project is None:
        return render_template('dashboard.html', stats=get_summary_stats(), kpis=get_kpis_and_audit_metrics(), error='Project not found'), 404

    # Parse JSON fields safely
    for field in ['risk_reasons', 'compliance_flags', 'duplicate_flag']:
        if isinstance(project.get(field), str):
            try:
                project[field] = json.loads(project[field])
            except Exception:
                project[field] = []

    # Risk tier styling
    score = project.get('risk_score', 0)
    if score <= 30:
        project['risk_tier'] = 'Low Risk'
        project['risk_color'] = '#10b981'
    elif score <= 60:
        project['risk_tier'] = 'Medium Risk'
        project['risk_color'] = '#f59e0b'
    else:
        project['risk_tier'] = 'High Risk'
        project['risk_color'] = '#ef4444'

    role = request.args.get('role', 'ministry')
    return render_template('project_detail.html', project=project, current_role=role)


# ──────────────────────────────────────────────────────────────
# REST API Routes
# ──────────────────────────────────────────────────────────────

@app.route('/api/projects')
def api_projects():
    """Return filtered project list scoped by role and search criteria."""
    role = request.args.get('role', None)
    mp_name = request.args.get('mp_name', None)
    district = request.args.get('district', None)
    query = request.args.get('q', None)
    status = request.args.get('status', None)
    risk = request.args.get('risk', None)
    constituency = request.args.get('constituency', None)
    category = request.args.get('category', None)
    compliance = request.args.get('compliance', None)
    early_warning = request.args.get('early_warning', None)

    projects = search_projects(
        query=query,
        status=status,
        risk=risk,
        constituency=constituency,
        category=category,
        compliance=compliance,
        early_warning=early_warning,
        role=role,
        mp_name=mp_name,
        district=district
    )

    for p in projects:
        for field in ['risk_reasons', 'compliance_flags', 'duplicate_flag']:
            if isinstance(p.get(field), str):
                try:
                    p[field] = json.loads(p[field])
                except Exception:
                    p[field] = []

    return jsonify(projects)


@app.route('/api/summary')
def api_summary():
    """Return summary statistics scoped by role."""
    role = request.args.get('role', 'ministry')
    mp_name = request.args.get('mp_name', None)
    district = request.args.get('district', None)
    stats = get_summary_stats(role=role, mp_name=mp_name, district=district)
    return jsonify(stats)


@app.route('/api/map-data')
def api_map_data():
    """Return geotagged markers scoped by role."""
    role = request.args.get('role', None)
    mp_name = request.args.get('mp_name', None)
    district = request.args.get('district', None)
    data = get_map_data(role=role, mp_name=mp_name, district=district)
    return jsonify(data)


@app.route('/api/alerts')
def api_alerts():
    """Return role-routed alerts."""
    role = request.args.get('role', 'ministry')
    mp_name = request.args.get('mp_name', None)
    district = request.args.get('district', None)

    user_context = {'mp_name': mp_name, 'district': district}
    alerts = get_alerts(role=role, user_context=user_context)
    return jsonify(alerts)


@app.route('/api/alerts/<int:project_id>/action', methods=['POST'])
def api_alert_action(project_id):
    """Execute an alert action (Assign Inspection, Request Explanation, Resolve, Escalate)."""
    data = request.get_json() or {}
    action_type = data.get('action_type', 'ASSIGN_INSPECTION')
    performed_by = data.get('performed_by', 'District Magistrate')
    role = data.get('role', 'district_authority')
    notes = data.get('notes', 'Field physical inspection ordered.')

    success = update_alert_action(project_id, action_type, performed_by, role, notes)
    return jsonify({'success': success, 'message': f'Alert action {action_type} recorded successfully.'})


@app.route('/api/audit-feedback', methods=['POST'])
def api_audit_feedback():
    """Record ground auditor feedback (CONFIRMED / FALSE_POSITIVE / UNDER_INVESTIGATION)."""
    data = request.get_json() or {}
    project_id = data.get('project_id')
    auditor_name = data.get('auditor_name', 'District Auditor')
    role = data.get('role', 'District Authority')
    verdict = data.get('verdict', 'CONFIRMED')
    notes = data.get('notes', '')

    if not project_id:
        return jsonify({'success': False, 'error': 'Missing project_id'}), 400

    save_audit_feedback(project_id, auditor_name, role, verdict, notes)
    return jsonify({'success': True, 'message': f'Audit verdict {verdict} saved.'})


@app.route('/api/kpis')
def api_kpis():
    """Return advanced SIH efficiency KPIs and completion trends."""
    kpis = get_kpis_and_audit_metrics()
    return jsonify(kpis)


@app.route('/api/upload-csv', methods=['POST'])
def api_upload_csv():
    """Ingest eSAKSHI exported CSV/Excel data."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded in request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename'}), 400

    file_bytes = file.read()
    result = parse_and_ingest_csv(file_bytes, filename=file.filename)
    return jsonify(result)


@app.route('/api/download-sample-csv')
def api_download_sample_csv():
    """Download bundled sample eSAKSHI CSV file."""
    if not os.path.exists(SAMPLE_CSV_PATH):
        from csv_pipeline import generate_sample_esakshi_csv
        generate_sample_esakshi_csv()
    return send_file(SAMPLE_CSV_PATH, as_attachment=True, download_name='sample_esakshi_mumbai.csv', mimetype='text/csv')


@app.route('/api/recalculate', methods=['POST'])
def api_recalculate():
    """Re-run AI models, compliance engine, early warning, and alert routing."""
    try:
        results = calculate_risk_scores()
        return jsonify({
            'success': True,
            'message': f'AI anomaly engine & compliance rules evaluated for {len(results)} projects.',
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ──────────────────────────────────────────────────────────────
# App Initialization
# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("Starting MPLADS AI Monitor (Upgraded)...")
    print("Dashboard: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)
