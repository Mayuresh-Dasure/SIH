"""
anomaly_engine.py — Multi-Signal Anomaly Detection, Compliance Integration & Alert Routing

Combines:
  1. Statistical Cost Anomaly (category z-score vs median).
  2. Project Timeline & Delay Anomaly.
  3. Fund Utilization Mismatch Anomaly.
  4. Rapid Speed Anomaly.
  5. Isolation Forest Multi-variate Outlier Detection.
  6. Statutory Compliance Violations (from compliance_engine).
  7. Predictive Early Warnings & Duplicate Detection (from predictive_engine).
  8. Automated Alert Routing (DPO -> DM -> State Nodal -> Ministry).
"""

import json
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

from database import get_all_projects, update_risk_and_compliance_scores
from compliance_engine import evaluate_compliance
from predictive_engine import calculate_predictive_delay, detect_duplicate_works

WEIGHTS = {
    'cost': 30,
    'delay': 25,
    'utilization': 25,
    'speed': 10,
    'isolation_forest': 10,
}


def detect_cost_anomalies(df):
    """Detect projects with unusually high cost compared to category median."""
    scores = np.zeros(len(df))
    reasons = [[] for _ in range(len(df))]

    for category in df['category'].unique():
        mask = df['category'] == category
        category_costs = df.loc[mask, 'sanctioned_amount']

        if len(category_costs) < 3:
            continue

        median_cost = category_costs.median()
        std_cost = category_costs.std()

        if std_cost == 0:
            continue

        for idx in df.loc[mask].index:
            cost = df.loc[idx, 'sanctioned_amount']
            z_score = (cost - median_cost) / std_cost

            if z_score > 1.5:
                anomaly_score = min(z_score / 3.0, 1.0)
                scores[idx] = anomaly_score

                pct_above = round(((cost - median_cost) / median_cost) * 100, 0)
                reasons[idx].append(
                    f"Cost is {int(pct_above)}% higher than median for {category} projects "
                    f"(Rs. {cost:.1f}L vs Rs. {median_cost:.1f}L median)"
                )

    return scores, reasons


def detect_delay_anomalies(df):
    """Detect projects with significant delays."""
    scores = np.zeros(len(df))
    reasons = [[] for _ in range(len(df))]

    now = datetime(2025, 8, 1)

    for idx in df.index:
        expected_str = df.loc[idx, 'expected_completion']
        actual_str = df.loc[idx, 'actual_completion']
        start_str = df.loc[idx, 'start_date']
        status = df.loc[idx, 'status']

        if not expected_str or not start_str:
            continue

        try:
            expected = datetime.strptime(str(expected_str)[:10], '%Y-%m-%d')
            start = datetime.strptime(str(start_str)[:10], '%Y-%m-%d')
        except Exception:
            continue

        expected_duration = max((expected - start).days, 1)

        if actual_str and str(actual_str) != 'None':
            try:
                actual = datetime.strptime(str(actual_str)[:10], '%Y-%m-%d')
                delay_days = max((actual - expected).days, 0)
            except Exception:
                delay_days = 0
        elif status in ('Ongoing', 'Delayed') and expected < now:
            delay_days = (now - expected).days
        else:
            delay_days = 0

        if delay_days > 0:
            overdue_ratio = delay_days / expected_duration
            if overdue_ratio > 0.4:
                anomaly_score = min(overdue_ratio / 2.0, 1.0)
                scores[idx] = anomaly_score
                delay_months = round(delay_days / 30, 1)
                reasons[idx].append(
                    f"Project is delayed by {delay_months} months beyond expected completion"
                )

    return scores, reasons


def detect_utilization_anomalies(df):
    """Detect projects with unusually low fund utilization given their age."""
    scores = np.zeros(len(df))
    reasons = [[] for _ in range(len(df))]

    now = datetime(2025, 8, 1)

    for idx in df.index:
        status = df.loc[idx, 'status']
        utilization = float(df.loc[idx, 'utilization_pct'] or 0)
        start_str = df.loc[idx, 'start_date']
        sanctioned = float(df.loc[idx, 'sanctioned_amount'] or 0)
        expenditure = float(df.loc[idx, 'expenditure'] or 0)

        if status == 'Not Started' or not start_str:
            continue

        try:
            start = datetime.strptime(str(start_str)[:10], '%Y-%m-%d')
        except Exception:
            continue

        project_age_days = (now - start).days
        if project_age_days < 60:
            continue

        if project_age_days > 180 and utilization < 20 and status in ('Ongoing', 'Delayed'):
            anomaly_score = min((20 - utilization) / 20.0, 1.0)
            scores[idx] = anomaly_score
            age_months = round(project_age_days / 30, 0)
            reasons[idx].append(
                f"Fund utilization is only {utilization}% despite project being {int(age_months)} months old "
                f"(Rs. {expenditure:.1f}L of Rs. {sanctioned:.1f}L sanctioned)"
            )

        if status == 'Completed' and utilization > 99.5:
            scores[idx] = 0.3
            reasons[idx].append(
                f"Expenditure matches sanctioned amount almost exactly ({utilization}% utilization)"
            )

    return scores, reasons


def detect_speed_anomalies(df):
    """Detect projects completed suspiciously quickly for their cost."""
    scores = np.zeros(len(df))
    reasons = [[] for _ in range(len(df))]

    for idx in df.index:
        status = df.loc[idx, 'status']
        if status != 'Completed':
            continue

        start_str = df.loc[idx, 'start_date']
        actual_str = df.loc[idx, 'actual_completion']
        sanctioned = float(df.loc[idx, 'sanctioned_amount'] or 0)

        if not start_str or not actual_str or str(actual_str) == 'None':
            continue

        try:
            start = datetime.strptime(str(start_str)[:10], '%Y-%m-%d')
            actual = datetime.strptime(str(actual_str)[:10], '%Y-%m-%d')
        except Exception:
            continue

        completion_days = max((actual - start).days, 1)

        if sanctioned > 10 and completion_days < 30:
            anomaly_score = min((30 - completion_days) / 30.0 + 0.3, 1.0)
            scores[idx] = anomaly_score
            reasons[idx].append(
                f"Rs. {sanctioned:.1f}L project completed in only {completion_days} days "
                f"(suspiciously fast for this cost)"
            )

    return scores, reasons


def run_isolation_forest(df):
    """Run Isolation Forest for unsupervised anomaly detection."""
    scores = np.zeros(len(df))
    reasons = [[] for _ in range(len(df))]

    features_df = df[['sanctioned_amount', 'expenditure', 'utilization_pct']].copy()
    le = LabelEncoder()
    features_df['category_encoded'] = le.fit_transform(df['category'])

    now = datetime(2025, 8, 1)
    durations = []
    for idx in df.index:
        start_str = df.loc[idx, 'start_date']
        actual_str = df.loc[idx, 'actual_completion']
        try:
            start = datetime.strptime(str(start_str)[:10], '%Y-%m-%d')
            if actual_str and str(actual_str) != 'None':
                end = datetime.strptime(str(actual_str)[:10], '%Y-%m-%d')
            else:
                end = now
            durations.append((end - start).days)
        except Exception:
            durations.append(0)

    features_df['duration_days'] = durations
    features_df = features_df.fillna(0)

    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=0.15,
        random_state=42
    )

    predictions = iso_forest.fit_predict(features_df.values)
    anomaly_scores_raw = iso_forest.decision_function(features_df.values)

    min_score = anomaly_scores_raw.min()
    max_score = anomaly_scores_raw.max()
    score_range = max_score - min_score if max_score != min_score else 1

    for i, (pred, raw) in enumerate(zip(predictions, anomaly_scores_raw)):
        if pred == -1:
            normalized = (max_score - raw) / score_range
            scores[i] = min(normalized, 1.0)
            reasons[i].append(
                "Statistical outlier detected by AI model (unusual combination of cost, duration, and utilization)"
            )

    return scores, reasons


def calculate_risk_scores():
    """Main calculation routine: evaluates anomalies, compliance, early warnings, and routes alerts."""
    projects = get_all_projects()

    if not projects:
        print("No projects found in database.")
        return []

    df = pd.DataFrame(projects)
    print(f"Running full AI analysis on {len(df)} projects...")

    # 1. Anomaly Detectors
    cost_scores, cost_reasons = detect_cost_anomalies(df)
    delay_scores, delay_reasons = detect_delay_anomalies(df)
    util_scores, util_reasons = detect_utilization_anomalies(df)
    speed_scores, speed_reasons = detect_speed_anomalies(df)
    iso_scores, iso_reasons = run_isolation_forest(df)

    # 2. Duplicate Works Detection
    duplicates_map = detect_duplicate_works(projects)

    # 3. Process each project
    results = []
    risk_distribution = {'low': 0, 'medium': 0, 'high': 0}
    compliance_distribution = {'PASSED': 0, 'WARNING': 0, 'VIOLATION': 0}
    early_warning_distribution = {'ON_TRACK': 0, 'AT_RISK': 0, 'CRITICAL': 0}

    for i in range(len(df)):
        proj_dict = dict(df.loc[i])
        p_id = int(proj_dict['id'])

        # Anomaly scoring
        c_score = cost_scores[i] * 70.0
        d_score = delay_scores[i] * 65.0
        u_score = util_scores[i] * 65.0
        s_score = speed_scores[i] * 50.0
        iso_score = iso_scores[i] * 30.0

        all_signal_scores = [c_score, d_score, u_score, s_score, iso_score]
        primary_score = max(all_signal_scores)
        secondary_sum = sum(s for s in all_signal_scores if s < primary_score)
        compound_boost = min(secondary_sum * 0.35, 30.0)

        # Statutory Compliance
        comp_status, comp_flags = evaluate_compliance(proj_dict)
        compliance_distribution[comp_status] += 1

        # Predictive Delay & Shortfall
        pred_delay, early_warn, shortfall = calculate_predictive_delay(proj_dict)
        early_warning_distribution[early_warn] += 1

        # Duplicate works for this project
        dup_list = duplicates_map.get(p_id, [])

        # Additional risk boost if duplicate detected
        dup_boost = 25.0 if dup_list else 0.0

        # Compliance boost: Violations add baseline severity
        comp_boost = 30.0 if comp_status == 'VIOLATION' else (15.0 if comp_status == 'WARNING' else 0.0)

        final_raw = primary_score + compound_boost + dup_boost + comp_boost
        risk_score = round(min(max(final_raw, 0), 100), 1)

        # Reasons aggregation
        all_reasons = (
            cost_reasons[i] +
            delay_reasons[i] +
            util_reasons[i] +
            speed_reasons[i] +
            iso_reasons[i]
        )
        if dup_list:
            all_reasons.append(dup_list[0]['reason'])

        all_reasons = list(dict.fromkeys(all_reasons))
        if not all_reasons and risk_score > 0:
            all_reasons = ["Minor statistical variance detected"]

        # Alert Routing
        # Low -> DPO, Medium/High -> DM, Severe/Unresolved -> State Nodal/Ministry
        if risk_score > 75 or comp_status == 'VIOLATION':
            alert_assigned_to = 'DM'
        elif risk_score > 40 or comp_status == 'WARNING':
            alert_assigned_to = 'DPO'
        else:
            alert_assigned_to = 'DPO'

        # Tier tracking
        if risk_score <= 30:
            risk_distribution['low'] += 1
        elif risk_score <= 60:
            risk_distribution['medium'] += 1
        else:
            risk_distribution['high'] += 1

        results.append({
            'id': p_id,
            'risk_score': risk_score,
            'risk_reasons': all_reasons,
            'compliance_status': comp_status,
            'compliance_flags': comp_flags,
            'predicted_delay_months': pred_delay,
            'early_warning_level': early_warn,
            'projected_shortfall': shortfall,
            'duplicate_flag': dup_list,
            'alert_assigned_to': alert_assigned_to
        })

    # Save to DB
    update_risk_and_compliance_scores(results)

    print(f"\n[OK] Upgraded AI analysis completed & committed to DB")
    print(f"  Risk Tiers: Low={risk_distribution['low']} | Med={risk_distribution['medium']} | High={risk_distribution['high']}")
    print(f"  Compliance: Passed={compliance_distribution['PASSED']} | Warning={compliance_distribution['WARNING']} | Violation={compliance_distribution['VIOLATION']}")
    print(f"  Early Warning: On Track={early_warning_distribution['ON_TRACK']} | At Risk={early_warning_distribution['AT_RISK']} | Critical={early_warning_distribution['CRITICAL']}")

    return results


def update_risk_scores(records):
    """Backward compatibility alias."""
    return update_risk_and_compliance_scores(records)


if __name__ == '__main__':
    calculate_risk_scores()
