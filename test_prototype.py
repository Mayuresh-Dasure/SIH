"""
test_prototype.py — Comprehensive test suite for upgraded SIH26102 MPLADS Monitoring System.
"""

import urllib.request
import json
import os

BASE_URL = "http://127.0.0.1:5000"


def test_endpoint(name, url, method="GET", data=None, headers=None):
    try:
        req = urllib.request.Request(url, method=method)
        req_headers = {'User-Agent': 'Mozilla/5.0'}
        if headers:
            req_headers.update(headers)

        if data is not None:
            if isinstance(data, dict):
                req_headers['Content-Type'] = 'application/json'
                data_bytes = json.dumps(data).encode('utf-8')
            else:
                data_bytes = data
        else:
            data_bytes = None

        for k, v in req_headers.items():
            req.add_header(k, v)

        with urllib.request.urlopen(req, data=data_bytes, timeout=8) as response:
            status = response.status
            content = response.read().decode('utf-8', errors='replace')
            print(f"[PASS] {name}: Status {status}, Length {len(content)} bytes")
            return content
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        return None


def run_tests():
    print("=== Testing Upgraded SIH26102 MPLADS System ===\n")

    # 1. Main Dashboard Page
    html = test_endpoint("Dashboard (Ministry View)", f"{BASE_URL}/?role=ministry")
    assert html and "MPLADS AI Monitor" in html, "Missing dashboard header"
    assert "Active Role:" in html, "Missing RBAC role switcher"
    assert "PS26102 Mapping Matrix" in html, "Missing PS Mapping tab"
    assert "eSAKSHI CSV Ingestion" in html, "Missing Ingestion tab"

    # 2. RBAC Summary Scoping (Ministry vs MP)
    min_summary_raw = test_endpoint("Summary API (Ministry)", f"{BASE_URL}/api/summary?role=ministry")
    min_summary = json.loads(min_summary_raw)
    assert min_summary['total_projects'] > 0, "No projects in ministry summary"
    print(f"       -> Ministry Total Projects: {min_summary['total_projects']}")
    print(f"       -> Total Sanctioned: Rs. {min_summary['total_sanctioned']}L | Active Alerts: {min_summary['total_active_alerts']}")

    mp_summary_raw = test_endpoint("Summary API (MP Shri Piyush Goyal)", f"{BASE_URL}/api/summary?role=mp&mp_name=Shri%20Piyush%20Goyal")
    mp_summary = json.loads(mp_summary_raw)
    assert mp_summary['total_projects'] > 0, "No projects in MP summary"
    assert mp_summary['total_projects'] < min_summary['total_projects'], "MP scope should be a subset"
    print(f"       -> MP Portfolio Projects: {mp_summary['total_projects']} | Uncommitted: Rs. {mp_summary.get('mp_uncommitted_lakhs')}L")

    # 3. Compliance Rule Engine Verification
    comp_raw = test_endpoint("Compliance Violations Filter", f"{BASE_URL}/api/projects?compliance=VIOLATION")
    comp_projects = json.loads(comp_raw)
    assert len(comp_projects) > 0, "Expected compliance violation cases"
    print(f"       -> Flagged Compliance Violations: {len(comp_projects)} works")
    first_viol = comp_projects[0]
    print(f"          Work #{first_viol['id']}: '{first_viol['project_name'][:50]}...'")
    print(f"          Flags: {[f.replace('\u20b9', 'Rs. ') for f in first_viol['compliance_flags']]}")

    # 4. Predictive Early Warning Verification
    crit_raw = test_endpoint("Early Warning Critical Filter", f"{BASE_URL}/api/projects?early_warning=CRITICAL")
    crit_projects = json.loads(crit_raw)
    assert len(crit_projects) > 0, "Expected critical early warning cases"
    print(f"       -> Critical Early Warnings: {len(crit_projects)} works")
    first_crit = crit_projects[0]
    print(f"          Work #{first_crit['id']}: Projected Delay = +{first_crit['predicted_delay_months']} months, Shortfall = Rs. {first_crit['projected_shortfall']}L")

    # 5. Alert Inbox & Dispatch Actions
    alerts_raw = test_endpoint("Alert Inbox API", f"{BASE_URL}/api/alerts?role=ministry")
    alerts = json.loads(alerts_raw)
    assert len(alerts) > 0, "Expected routed alerts"
    print(f"       -> Total Actionable Alerts: {len(alerts)}")
    first_alert = alerts[0]
    print(f"          Top Alert Work #{first_alert['id']} (Score {first_alert['risk_score']}) -> Assigned to: {first_alert['alert_assigned_to']}")

    # Test Action Dispatch (Assign Field Inspection)
    action_res_raw = test_endpoint(
        f"Alert Action Dispatch (Work #{first_alert['id']})",
        f"{BASE_URL}/api/alerts/{first_alert['id']}/action",
        method="POST",
        data={
            'action_type': 'ASSIGN_INSPECTION',
            'performed_by': 'District Magistrate',
            'role': 'district_authority',
            'notes': 'Immediate field physical audit dispatched.'
        }
    )
    action_res = json.loads(action_res_raw)
    assert action_res.get('success') is True, "Alert action dispatch failed"

    # 6. Auditor Feedback Loop (Active Learning)
    feedback_res_raw = test_endpoint(
        f"Audit Feedback Submission (Work #{first_alert['id']})",
        f"{BASE_URL}/api/audit-feedback",
        method="POST",
        data={
            'project_id': first_alert['id'],
            'auditor_name': 'District Ground Inspector',
            'role': 'District Authority',
            'verdict': 'CONFIRMED',
            'notes': 'Site inspection confirmed abnormal material expenditure.'
        }
    )
    feedback_res = json.loads(feedback_res_raw)
    assert feedback_res.get('success') is True, "Audit feedback submission failed"

    # 7. Advanced KPIs & Efficiency Metrics
    kpis_raw = test_endpoint("KPIs & Metrics API", f"{BASE_URL}/api/kpis")
    kpis = json.loads(kpis_raw)
    assert 'alert_accuracy_pct' in kpis, "Missing alert accuracy KPI"
    assert 'audit_effort_reduction_pct' in kpis, "Missing effort reduction KPI"
    assert len(kpis['completion_trends']) > 0, "Missing completion trends data"
    print(f"       -> Alert Accuracy: {kpis['alert_accuracy_pct']}% | Mean Detection: {kpis['mean_detection_time_days']} days | Effort Saved: {kpis['audit_effort_reduction_pct']}%")

    # 8. Project Detail View
    detail_html = test_endpoint(f"Project Detail Drilldown (#{first_alert['id']})", f"{BASE_URL}/project/{first_alert['id']}")
    assert "Statutory Compliance Rule Audit" in detail_html, "Missing compliance checklist in detail"
    assert "Predictive Early Warning Forecast" in detail_html, "Missing early warning in detail"
    assert "Ground Auditor Feedback" in detail_html, "Missing feedback widget in detail"

    # 9. AI Recalculate Endpoint
    recalc_raw = test_endpoint("Recalculate Models API", f"{BASE_URL}/api/recalculate", method="POST")
    recalc = json.loads(recalc_raw)
    assert recalc.get('success') is True, "Recalculation failed"

    print("\n=== All Upgraded Verification Tests Passed Successfully! ===")


if __name__ == '__main__':
    run_tests()
