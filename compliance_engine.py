"""
compliance_engine.py — Statutory Compliance Rule Engine for MPLADS Guidelines

Evaluates projects against deterministic statutory rules based on the official
Ministry of Statistics and Programme Implementation (MoSPI) MPLADS Guidelines.

Rules:
  1. Work Eligibility Rule: Prohibited negative list (religious places, commercial/private land, memorials).
  2. Fund Limit Rule: Maximum ₹75 Lakhs limit for trusts/societies; MP annual ceiling ₹5 Crore.
  3. Implementing Agency Rule: Must be accredited government engineering/municipal agency.
  4. Statutory Deadline Rule: District Authority must sanction work within 75 days of MP recommendation.
"""

from datetime import datetime

# Authorized public implementing bodies in Maharashtra/Mumbai
ACCREDITED_AGENCIES = [
    'MCGM', 'BMC', 'MCGM ROADS DEPT', 'MCGM WATER SUPPLY DEPT',
    'MCGM STORM WATER DEPT', 'MCGM EDUCATION DEPT', 'MCGM SOLID WASTE DEPT',
    'MCGM ELECTRICAL DEPT', 'MCGM GARDENS DEPT', 'PWD MUMBAI', 'PWD',
    'MMRDA', 'BEST', 'MUMBAI POLICE', 'MHADA', 'MSRDC'
]

PROHIBITED_KEYWORDS = [
    'religious', 'temple', 'mandir', 'masjid', 'church', 'shrine',
    'memorial', 'statue', 'private building', 'commercial office',
    'commercial market', 'personal benefit', 'political party'
]

TRUST_CEILING_LAKHS = 75.0
MP_ANNUAL_CEILING_LAKHS = 500.0
SANCTION_DEADLINE_DAYS = 75


def evaluate_work_eligibility(project: dict):
    """Rule 1: Check against MPLADS Negative List (prohibited works)."""
    name = (project.get('project_name') or '').lower()
    desc = (project.get('description') or '').lower()
    b_type = (project.get('beneficiary_type') or '').lower()

    violations = []
    warnings = []

    # Prohibited keywords
    for kw in PROHIBITED_KEYWORDS:
        if kw in name or kw in desc:
            violations.append(f"Prohibited Work Type: '{kw.title()}' violates MPLADS Guideline Para 5.1 (Negative List)")

    # Beneficiary check
    if 'private' in b_type or 'commercial' in b_type:
        violations.append("Ineligible Beneficiary: Work benefits private/commercial interest rather than public community")

    return violations, warnings


def evaluate_fund_limits(project: dict, mp_cumulative_sanctions=0.0):
    """Rule 2: Check fund ceilings (₹75L Trust cap, ₹5 Cr annual MP cap)."""
    sanctioned = float(project.get('sanctioned_amount') or 0)
    b_type = (project.get('beneficiary_type') or '').lower()
    agency_type = (project.get('agency_type') or '').lower()

    violations = []
    warnings = []

    # Society/Trust ceiling (Para 3.12: max ₹75 Lakhs)
    if ('trust' in b_type or 'society' in b_type or 'trust' in agency_type) and sanctioned > TRUST_CEILING_LAKHS:
        violations.append(
            f"Trust/Society Fund Ceiling Breached: Sanctioned Rs. {sanctioned:.2f}L exceeds statutory ceiling of Rs. {TRUST_CEILING_LAKHS}L (Para 3.12)"
        )

    # Cumulative MP ceiling check
    if mp_cumulative_sanctions > MP_ANNUAL_CEILING_LAKHS:
        warnings.append(
            f"MP Annual Entitlement Exceeded: Total recommendations (Rs. {mp_cumulative_sanctions:.2f}L) exceed annual entitlement ceiling of Rs. {MP_ANNUAL_CEILING_LAKHS}L"
        )

    return violations, warnings


def evaluate_implementing_agency(project: dict):
    """Rule 3: Check whether implementing agency is accredited."""
    agency = (project.get('implementing_agency') or '').strip().upper()
    agency_type = (project.get('agency_type') or '').lower()

    violations = []
    warnings = []

    if not agency or agency == 'NONE':
        violations.append("Missing Implementing Agency: Mandatory under Para 2.4")
        return violations, warnings

    is_accredited = any(acc in agency for acc in ACCREDITED_AGENCIES)

    if not is_accredited and agency_type != 'government':
        violations.append(
            f"Unaccredited Implementing Agency: '{agency}' is not an authorized government nodal agency (Para 2.5)"
        )
    elif not is_accredited:
        warnings.append(
            f"Non-Standard Implementing Agency: '{agency}' requires special technical scrutiny by District Collector"
        )

    return violations, warnings


def evaluate_statutory_deadlines(project: dict):
    """Rule 4: Check 75-day sanction deadline and execution timeline."""
    rec_date_str = project.get('recommendation_date') or project.get('start_date')
    sanc_date_str = project.get('sanction_date')

    violations = []
    warnings = []

    if rec_date_str and sanc_date_str:
        try:
            rec_date = datetime.strptime(str(rec_date_str)[:10], '%Y-%m-%d')
            sanc_date = datetime.strptime(str(sanc_date_str)[:10], '%Y-%m-%d')
            sanction_delay = (sanc_date - rec_date).days

            if sanction_delay > SANCTION_DEADLINE_DAYS:
                warnings.append(
                    f"Statutory Sanction Delay: Sanctioned in {sanctiondelay} days (exceeds statutory 75-day DA sanctioning deadline under Para 3.3)"
                )
        except Exception:
            pass

    return violations, warnings


def evaluate_compliance(project: dict, mp_cumulative_sanctions=0.0):
    """
    Run full compliance audit on a project.
    Returns:
      compliance_status: 'PASSED' | 'WARNING' | 'VIOLATION'
      compliance_flags: List of string explanation items with guideline citations
    """
    all_violations = []
    all_warnings = []

    v1, w1 = evaluate_work_eligibility(project)
    v2, w2 = evaluate_fund_limits(project, mp_cumulative_sanctions)
    v3, w3 = evaluate_implementing_agency(project)
    v4, w4 = evaluate_statutory_deadlines(project)

    all_violations = v1 + v2 + v3 + v4
    all_warnings = w1 + w2 + w3 + w4

    if all_violations:
        status = 'VIOLATION'
        flags = [f"[VIOLATION] {v}" for v in all_violations] + [f"[WARNING] {w}" for w in all_warnings]
    elif all_warnings:
        status = 'WARNING'
        flags = [f"[WARNING] {w}" for w in all_warnings]
    else:
        status = 'PASSED'
        flags = ["[PASSED] All MPLADS Statutory Compliance Rules Verified (Eligibility, Ceilings, Agency, Timelines)"]

    return status, flags


if __name__ == '__main__':
    sample = {
        'project_name': 'Construction of Religious Community Hall',
        'sanctioned_amount': 85.0,
        'beneficiary_type': 'Private Trust',
        'implementing_agency': 'Unknown Private Contractor',
        'agency_type': 'Private',
        'start_date': '2023-01-01',
        'sanction_date': '2023-05-15'
    }
    status, flags = evaluate_compliance(sample)
    print(f"Sample Compliance Status: {status}")
    for f in flags:
        print(f" -> {f}")
