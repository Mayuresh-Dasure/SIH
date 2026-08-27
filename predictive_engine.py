"""
predictive_engine.py — Predictive Early Warning & Duplicate Works Detection

Provides:
  1. Burn-Rate Progress Velocity & Predicted Delay Forecasting (before milestones fail).
  2. Fiscal Year Fund Utilization Shortfall Regression.
  3. Early Warning Level Classification (ON_TRACK, AT_RISK, CRITICAL).
  4. Spatial & Semantic Duplicate / Overlapping Community Works Detection.
"""

import math
from datetime import datetime, timedelta
import pandas as pd


def haversine_distance_meters(lat1, lon1, lat2, lon2):
    """Compute Haversine distance in meters between two lat/lon points."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 999999.0

    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def calculate_predictive_delay(project: dict, reference_date=None):
    """
    Forecast expected completion delay in months using burn-rate velocity.
    """
    if reference_date is None:
        reference_date = datetime(2025, 8, 1)

    status = project.get('status')
    sanctioned = float(project.get('sanctioned_amount') or 0)
    expenditure = float(project.get('expenditure') or 0)
    start_str = project.get('start_date')
    expected_str = project.get('expected_completion')

    if not start_str or not expected_str or sanctioned <= 0:
        return 0.0, 'ON_TRACK', 0.0

    try:
        start = datetime.strptime(str(start_str)[:10], '%Y-%m-%d')
        expected = datetime.strptime(str(expected_str)[:10], '%Y-%m-%d')
    except Exception:
        return 0.0, 'ON_TRACK', 0.0

    total_expected_days = max((expected - start).days, 1)
    elapsed_days = max((reference_date - start).days, 1)

    if status == 'Completed':
        return 0.0, 'ON_TRACK', 0.0

    # Remaining work in Lakhs
    remaining_funds = max(sanctioned - expenditure, 0.0)

    # Current spending velocity (Lakhs per day)
    velocity = expenditure / elapsed_days if elapsed_days > 0 else 0.0

    # Default baseline pace if project just started
    if velocity <= 0.001:
        if elapsed_days > 90:
            # Stagnant project
            predicted_delay_months = round((elapsed_days / 30.0) * 0.8, 1)
            return predicted_delay_months, 'CRITICAL', remaining_funds
        else:
            return 0.0, 'ON_TRACK', 0.0

    # Projected days to spend remaining funds at current velocity
    projected_days_left = remaining_funds / velocity
    projected_finish = reference_date + timedelta(days=projected_days_left)

    projected_delay_days = max((projected_finish - expected).days, 0)
    predicted_delay_months = round(projected_delay_days / 30.0, 1)

    # Calculate Fiscal Shortfall (unspent at FY end)
    fy_end = datetime(2026, 3, 31)
    days_to_fy = max((fy_end - reference_date).days, 0)
    projected_fy_spend = min(expenditure + (velocity * days_to_fy), sanctioned)
    projected_shortfall = round(max(sanctioned - projected_fy_spend, 0.0), 2)

    # Categorize Early Warning Level
    if predicted_delay_months > 3.0 or (elapsed_days / total_expected_days > 0.7 and (expenditure / sanctioned) < 0.3):
        early_warning = 'CRITICAL'
    elif predicted_delay_months > 1.0 or (elapsed_days / total_expected_days > 0.5 and (expenditure / sanctioned) < 0.25):
        early_warning = 'AT_RISK'
    else:
        early_warning = 'ON_TRACK'

    return predicted_delay_months, early_warning, projected_shortfall


def detect_duplicate_works(projects: list):
    """
    Detect overlapping or duplicate projects within 250 meters
    with matching categories and high name similarity.
    """
    duplicates_map = {p['id']: [] for p in projects}

    for i in range(len(projects)):
        p1 = projects[i]
        lat1 = p1.get('latitude')
        lon1 = p1.get('longitude')
        cat1 = p1.get('category')
        words1 = set((p1.get('project_name') or '').lower().split())

        for j in range(i + 1, len(projects)):
            p2 = projects[j]
            lat2 = p2.get('latitude')
            lon2 = p2.get('longitude')
            cat2 = p2.get('category')

            if cat1 != cat2:
                continue

            dist = haversine_distance_meters(lat1, lon1, lat2, lon2)
            if dist <= 250.0:
                words2 = set((p2.get('project_name') or '').lower().split())
                overlap = len(words1.intersection(words2))
                total_unique = max(len(words1.union(words2)), 1)
                jaccard = overlap / total_unique

                if jaccard > 0.35:
                    dup_info_1 = {
                        'matched_project_id': p2['id'],
                        'matched_project_name': p2['project_name'],
                        'distance_meters': round(dist, 1),
                        'similarity_pct': round(jaccard * 100, 1),
                        'reason': f"Potential Duplicate Work: Within {dist:.0f}m of Project #{p2['id']} with {round(jaccard*100)}% descriptive overlap"
                    }
                    dup_info_2 = {
                        'matched_project_id': p1['id'],
                        'matched_project_name': p1['project_name'],
                        'distance_meters': round(dist, 1),
                        'similarity_pct': round(jaccard * 100, 1),
                        'reason': f"Potential Duplicate Work: Within {dist:.0f}m of Project #{p1['id']} with {round(jaccard*100)}% descriptive overlap"
                    }
                    duplicates_map[p1['id']].append(dup_info_1)
                    duplicates_map[p2['id']].append(dup_info_2)

    return duplicates_map


if __name__ == '__main__':
    sample = {
        'status': 'Ongoing',
        'sanctioned_amount': 25.0,
        'expenditure': 3.5,
        'start_date': '2024-01-01',
        'expected_completion': '2024-10-01'
    }
    delay, warn, shortfall = calculate_predictive_delay(sample)
    print(f"Predicted Delay: {delay} months | Warning Level: {warn} | Projected Shortfall: Rs. {shortfall}L")
