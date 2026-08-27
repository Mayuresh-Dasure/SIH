"""
seed_data.py — Generate realistic Mumbai MPLADS project data with compliance cases,
early warning scenarios, and duplicate works for SIH26102.
"""

import random
import json
from datetime import datetime, timedelta
from database import init_db, clear_projects, insert_projects_bulk
from compliance_engine import evaluate_compliance
from predictive_engine import calculate_predictive_delay, detect_duplicate_works

random.seed(42)

CONSTITUENCIES = {
    'Mumbai North': {
        'mp': 'Shri Piyush Goyal',
        'party': 'BJP',
        'district': 'Mumbai Suburban',
        'lat_range': (19.18, 19.26),
        'lng_range': (72.82, 72.89),
    },
    'Mumbai North West': {
        'mp': 'Shri Ravindra Waikar',
        'party': 'Shiv Sena',
        'district': 'Mumbai Suburban',
        'lat_range': (19.11, 19.17),
        'lng_range': (72.81, 72.87),
    },
    'Mumbai North East': {
        'mp': 'Shri Sanjay Dina Patil',
        'party': 'Shiv Sena (UBT)',
        'district': 'Mumbai Suburban',
        'lat_range': (19.09, 19.16),
        'lng_range': (72.88, 72.95),
    },
    'Mumbai North Central': {
        'mp': 'Smt. Varsha Gaikwad',
        'party': 'INC',
        'district': 'Mumbai Suburban',
        'lat_range': (19.04, 19.10),
        'lng_range': (72.82, 72.88),
    },
    'Mumbai South Central': {
        'mp': 'Shri Anil Desai',
        'party': 'Shiv Sena (UBT)',
        'district': 'Mumbai City',
        'lat_range': (18.98, 19.05),
        'lng_range': (72.81, 72.87),
    },
    'Mumbai South': {
        'mp': 'Shri Arvind Sawant',
        'party': 'Shiv Sena (UBT)',
        'district': 'Mumbai City',
        'lat_range': (18.90, 18.98),
        'lng_range': (72.80, 72.86),
    },
}

CATEGORIES = {
    'Community Hall': {
        'cost_range': (15, 45),
        'duration_range': (180, 365),
        'agencies': ['MCGM', 'PWD Mumbai'],
        'descriptions': ['Community recreation hall for local residents', 'Multipurpose public community centre', 'Community hall with cultural facilities']
    },
    'Road Construction': {
        'cost_range': (8, 35),
        'duration_range': (90, 270),
        'agencies': ['MCGM Roads Dept', 'PWD Mumbai', 'MMRDA'],
        'descriptions': ['Cement concrete road construction with pavers', 'Internal link road widening and asphalting', 'Approach road with stormwater drain']
    },
    'Drainage & Stormwater': {
        'cost_range': (5, 25),
        'duration_range': (60, 180),
        'agencies': ['MCGM Storm Water Dept', 'MCGM'],
        'descriptions': ['Underground stormwater drainage pipeline', 'Nallah desilting and retaining wall construction', 'Stormwater channel with RCC box culvert']
    },
    'Water Supply': {
        'cost_range': (3, 20),
        'duration_range': (45, 150),
        'agencies': ['MCGM Water Supply Dept', 'MCGM'],
        'descriptions': ['Drinking water pipeline augmentation network', 'Overhead water distribution tank and feeder pipeline', 'Water supply valve replacement and pipeline upgrade']
    },
    'School Infrastructure': {
        'cost_range': (10, 50),
        'duration_range': (120, 300),
        'agencies': ['MCGM Education Dept', 'PWD Mumbai'],
        'descriptions': ['Construction of additional classrooms in municipal school', 'Municipal school digital lab and roof waterproofing', 'School playground development and perimeter wall']
    },
    'Bus Shelter': {
        'cost_range': (1.5, 5),
        'duration_range': (30, 90),
        'agencies': ['MCGM', 'BEST'],
        'descriptions': ['Stainless steel passenger bus shelter with seating', 'Covered public transit bus shelter', 'Passenger waiting shed near residential area']
    },
    'CCTV Installation': {
        'cost_range': (3, 15),
        'duration_range': (30, 90),
        'agencies': ['Mumbai Police', 'MCGM'],
        'descriptions': ['High-definition CCTV surveillance camera network', 'Public safety CCTV monitoring system', 'CCTV cameras with central monitoring control']
    },
    'Solar Lighting': {
        'cost_range': (2, 12),
        'duration_range': (30, 90),
        'agencies': ['MCGM Electrical Dept', 'MCGM'],
        'descriptions': ['Solar powered LED street light installation', 'Energy efficient solar illumination in residential lanes', 'Solar lighting system for public garden']
    },
    'Public Toilet': {
        'cost_range': (5, 20),
        'duration_range': (60, 150),
        'agencies': ['MCGM Solid Waste Dept', 'MCGM'],
        'descriptions': ['Public community toilet block with running water', 'Modern public sanitation facility with disabled access', 'Community hygiene and toilet complex']
    },
    'Garden & Park': {
        'cost_range': (5, 30),
        'duration_range': (90, 240),
        'agencies': ['MCGM Gardens Dept', 'MCGM'],
        'descriptions': ['Public garden development with jogging pathway', 'Children park beautification and fitness equipment', 'Green open space development with sitting benches']
    },
}

WARDS = ['Andheri East', 'Andheri West', 'Borivali West', 'Dahisar East', 'Goregaon West',
         'Malad West', 'Kandivali East', 'Jogeshwari', 'Bandra East', 'Bandra West',
         'Kurla West', 'Ghatkopar East', 'Mulund West', 'Vikhroli', 'Powai', 'Chembur',
         'Wadala', 'Worli Seaface', 'Dadar West', 'Parel', 'Colaba', 'Fort', 'Matunga', 'Sion', 'Dharavi']


def generate_all_projects():
    projects = []
    idx = 1
    now = datetime(2025, 8, 1)

    # 1. Generate ~100 normal compliant projects
    for const_name, const_info in CONSTITUENCIES.items():
        for _ in range(16):
            cat_name = random.choice(list(CATEGORIES.keys()))
            cat_info = CATEGORIES[cat_name]
            ward = random.choice(WARDS)

            cost_min, cost_max = cat_info['cost_range']
            sanctioned = round(random.uniform(cost_min, cost_max), 2)
            duration = random.randint(*cat_info['duration_range'])

            start = now - timedelta(days=random.randint(100, 600))
            expected = start + timedelta(days=duration)
            rec_date = start - timedelta(days=random.randint(20, 60))
            sanc_date = start - timedelta(days=random.randint(5, 20))

            if expected < now:
                status = 'Completed'
                actual = expected + timedelta(days=random.randint(-15, 25))
                expenditure = round(sanctioned * random.uniform(0.88, 0.98), 2)
            else:
                status = 'Ongoing'
                actual = None
                elapsed_ratio = (now - start).days / duration
                expenditure = round(sanctioned * min(elapsed_ratio, 1.0) * random.uniform(0.7, 0.95), 2)

            utilization = round((expenditure / sanctioned * 100) if sanctioned > 0 else 0, 1)

            lat = round(random.uniform(*const_info['lat_range']), 6)
            lng = round(random.uniform(*const_info['lng_range']), 6)

            p = {
                'id': idx,
                'project_name': f"{random.choice(cat_info['descriptions'])} at {ward}",
                'category': cat_name,
                'mp_name': const_info['mp'],
                'constituency': const_name,
                'district': const_info['district'],
                'state': 'Maharashtra',
                'sanctioned_amount': sanctioned,
                'expenditure': expenditure,
                'utilization_pct': utilization,
                'status': status,
                'recommendation_date': rec_date.strftime('%Y-%m-%d'),
                'sanction_date': sanc_date.strftime('%Y-%m-%d'),
                'start_date': start.strftime('%Y-%m-%d'),
                'expected_completion': expected.strftime('%Y-%m-%d'),
                'actual_completion': actual.strftime('%Y-%m-%d') if actual else None,
                'latitude': lat,
                'longitude': lng,
                'implementing_agency': random.choice(cat_info['agencies']),
                'agency_type': 'Government',
                'beneficiary_type': 'Public Community',
                'description': f"{random.choice(cat_info['descriptions'])} in {ward}, {const_name}.",
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
            projects.append(p)
            idx += 1

    # 2. Injected Cost Anomalies (8 projects)
    for _ in range(8):
        c_name = random.choice(list(CONSTITUENCIES.keys()))
        c_info = CONSTITUENCIES[c_name]
        cat_name = random.choice(['School Infrastructure', 'Community Hall', 'Road Construction', 'Water Supply'])
        cat_info = CATEGORIES[cat_name]
        ward = random.choice(WARDS)
        inflated = round(cat_info['cost_range'][1] * random.uniform(1.5, 1.9), 2)
        start = now - timedelta(days=220)
        expected = start + timedelta(days=200)

        p = {
            'id': idx,
            'project_name': f"Special {cat_name} Construction at {ward}",
            'category': cat_name,
            'mp_name': c_info['mp'],
            'constituency': c_name,
            'district': c_info['district'],
            'state': 'Maharashtra',
            'sanctioned_amount': inflated,
            'expenditure': round(inflated * 0.99, 2),
            'utilization_pct': 99.0,
            'status': 'Completed',
            'recommendation_date': (start - timedelta(days=40)).strftime('%Y-%m-%d'),
            'sanction_date': (start - timedelta(days=10)).strftime('%Y-%m-%d'),
            'start_date': start.strftime('%Y-%m-%d'),
            'expected_completion': expected.strftime('%Y-%m-%d'),
            'actual_completion': (expected + timedelta(days=10)).strftime('%Y-%m-%d'),
            'latitude': round(random.uniform(*c_info['lat_range']), 6),
            'longitude': round(random.uniform(*c_info['lng_range']), 6),
            'implementing_agency': random.choice(cat_info['agencies']),
            'agency_type': 'Government',
            'beneficiary_type': 'Public Community',
            'description': f"High expenditure {cat_name} in {ward}.",
            'risk_score': 0.0,
            'risk_reasons': [],
            'compliance_status': 'PASSED',
            'compliance_flags': [],
            'predicted_delay_months': 0.0,
            'early_warning_level': 'ON_TRACK',
            'projected_shortfall': 0.0,
            'duplicate_flag': [],
            'alert_assigned_to': 'DM',
            'alert_status': 'NEW'
        }
        projects.append(p)
        idx += 1

    # 3. Injected Predictive Early Warning & Stagnant Projects (7 projects)
    for _ in range(7):
        c_name = random.choice(list(CONSTITUENCIES.keys()))
        c_info = CONSTITUENCIES[c_name]
        cat_name = random.choice(['Drainage & Stormwater', 'Public Toilet', 'Road Construction'])
        ward = random.choice(WARDS)
        sanctioned = round(random.uniform(20.0, 40.0), 2)
        start = now - timedelta(days=240)
        expected = start + timedelta(days=300)

        p = {
            'id': idx,
            'project_name': f"Pending {cat_name} Works at {ward}",
            'category': cat_name,
            'mp_name': c_info['mp'],
            'constituency': c_name,
            'district': c_info['district'],
            'state': 'Maharashtra',
            'sanctioned_amount': sanctioned,
            'expenditure': round(sanctioned * 0.12, 2), # only 12% spent after 8 months
            'utilization_pct': 12.0,
            'status': 'Ongoing',
            'recommendation_date': (start - timedelta(days=45)).strftime('%Y-%m-%d'),
            'sanction_date': (start - timedelta(days=15)).strftime('%Y-%m-%d'),
            'start_date': start.strftime('%Y-%m-%d'),
            'expected_completion': expected.strftime('%Y-%m-%d'),
            'actual_completion': None,
            'latitude': round(random.uniform(*c_info['lat_range']), 6),
            'longitude': round(random.uniform(*c_info['lng_range']), 6),
            'implementing_agency': 'MCGM',
            'agency_type': 'Government',
            'beneficiary_type': 'Public Community',
            'description': f"Delayed execution of {cat_name} in {ward}.",
            'risk_score': 0.0,
            'risk_reasons': [],
            'compliance_status': 'PASSED',
            'compliance_flags': [],
            'predicted_delay_months': 4.5,
            'early_warning_level': 'CRITICAL',
            'projected_shortfall': round(sanctioned * 0.7, 2),
            'duplicate_flag': [],
            'alert_assigned_to': 'DM',
            'alert_status': 'NEW'
        }
        projects.append(p)
        idx += 1

    # 4. Injected Statutory Compliance Violations (6 projects)
    compliance_cases = [
        {
            'name': 'Construction of Religious Prayer Hall and Shrine at Bandra',
            'cat': 'Community Hall',
            'const': 'Mumbai North Central',
            'amt': 35.0,
            'agency': 'MCGM',
            'agency_type': 'Government',
            'b_type': 'Religious Community'
        },
        {
            'name': 'Trust Hospital Ambulance & Medical Center Asset Building',
            'cat': 'School Infrastructure',
            'const': 'Mumbai South',
            'amt': 92.0, # Exceeds ₹75L Trust Ceiling!
            'agency': 'Private Trust Welfare Association',
            'agency_type': 'Private Trust',
            'b_type': 'Private Trust'
        },
        {
            'name': 'Commercial Shopping Complex Paver Block Pavement at Malad',
            'cat': 'Road Construction',
            'const': 'Mumbai North',
            'amt': 28.0,
            'agency': 'Unregistered Construction Agency',
            'agency_type': 'Private Contractor',
            'b_type': 'Commercial Entity'
        },
        {
            'name': 'Memorial Statue Installation & Landscaping at Dadar',
            'cat': 'Garden & Park',
            'const': 'Mumbai South Central',
            'amt': 22.0,
            'agency': 'MCGM Gardens Dept',
            'agency_type': 'Government',
            'b_type': 'Public Community'
        }
    ]

    for case in compliance_cases:
        c_info = CONSTITUENCIES[case['const']]
        start = now - timedelta(days=120)
        expected = start + timedelta(days=180)

        p = {
            'id': idx,
            'project_name': case['name'],
            'category': case['cat'],
            'mp_name': c_info['mp'],
            'constituency': case['const'],
            'district': c_info['district'],
            'state': 'Maharashtra',
            'sanctioned_amount': case['amt'],
            'expenditure': round(case['amt'] * 0.45, 2),
            'utilization_pct': 45.0,
            'status': 'Ongoing',
            'recommendation_date': (start - timedelta(days=95)).strftime('%Y-%m-%d'), # Sanction delay > 75 days!
            'sanction_date': start.strftime('%Y-%m-%d'),
            'start_date': start.strftime('%Y-%m-%d'),
            'expected_completion': expected.strftime('%Y-%m-%d'),
            'actual_completion': None,
            'latitude': round(random.uniform(*c_info['lat_range']), 6),
            'longitude': round(random.uniform(*c_info['lng_range']), 6),
            'implementing_agency': case['agency'],
            'agency_type': case['agency_type'],
            'beneficiary_type': case['b_type'],
            'description': f"Non-compliant proposal: {case['name']}",
            'risk_score': 0.0,
            'risk_reasons': [],
            'compliance_status': 'VIOLATION',
            'compliance_flags': [],
            'predicted_delay_months': 1.0,
            'early_warning_level': 'AT_RISK',
            'projected_shortfall': 0.0,
            'duplicate_flag': [],
            'alert_assigned_to': 'DM',
            'alert_status': 'NEW'
        }
        projects.append(p)
        idx += 1

    # 5. Injected Duplicate Works Pair (2 projects with same location & category)
    dup_lat = 19.1135
    dup_lng = 72.8420
    p_dup1 = {
        'id': idx,
        'project_name': 'Construction of Public Sanitation Toilet Complex at Andheri West Station',
        'category': 'Public Toilet',
        'mp_name': 'Shri Ravindra Waikar',
        'constituency': 'Mumbai North West',
        'district': 'Mumbai Suburban',
        'state': 'Maharashtra',
        'sanctioned_amount': 18.5,
        'expenditure': 17.2,
        'utilization_pct': 93.0,
        'status': 'Completed',
        'recommendation_date': '2024-01-10',
        'sanction_date': '2024-02-15',
        'start_date': '2024-03-01',
        'expected_completion': '2024-09-30',
        'actual_completion': '2024-09-20',
        'latitude': dup_lat,
        'longitude': dup_lng,
        'implementing_agency': 'MCGM Solid Waste Dept',
        'agency_type': 'Government',
        'beneficiary_type': 'Public Community',
        'description': 'Public toilet complex at Andheri station west.',
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
    idx += 1

    p_dup2 = {
        'id': idx,
        'project_name': 'Public Sanitation and Community Toilet Complex at Andheri West Station',
        'category': 'Public Toilet',
        'mp_name': 'Shri Ravindra Waikar',
        'constituency': 'Mumbai North West',
        'district': 'Mumbai Suburban',
        'state': 'Maharashtra',
        'sanctioned_amount': 19.2, # Duplicate work billing!
        'expenditure': 8.5,
        'utilization_pct': 44.3,
        'status': 'Ongoing',
        'recommendation_date': '2024-04-10',
        'sanction_date': '2024-05-15',
        'start_date': '2024-06-01',
        'expected_completion': '2024-12-31',
        'actual_completion': None,
        'latitude': dup_lat + 0.0008, # ~85 meters away
        'longitude': dup_lng + 0.0006,
        'implementing_agency': 'MCGM',
        'agency_type': 'Government',
        'beneficiary_type': 'Public Community',
        'description': 'Identical overlapping toilet complex sanction in same station area.',
        'risk_score': 0.0,
        'risk_reasons': [],
        'compliance_status': 'PASSED',
        'compliance_flags': [],
        'predicted_delay_months': 2.0,
        'early_warning_level': 'AT_RISK',
        'projected_shortfall': 5.0,
        'duplicate_flag': [],
        'alert_assigned_to': 'DM',
        'alert_status': 'NEW'
    }
    projects.extend([p_dup1, p_dup2])

    print(f"[OK] Generated {len(projects)} realistic upgraded projects")
    return projects


if __name__ == '__main__':
    print("Initializing upgraded database...")
    init_db()
    print("Clearing old data...")
    clear_projects()
    print("Generating comprehensive Mumbai dataset...")
    projects = generate_all_projects()
    print("Inserting projects into database...")
    insert_projects_bulk(projects)
    print(f"[OK] Seeded {len(projects)} projects into mplads.db")

    # Generate sample CSV as well
    from csv_pipeline import generate_sample_esakshi_csv
    generate_sample_esakshi_csv()
