# Graph Report - C:\Users\Sairaj\Documents\GitHub\SIH  (2026-08-28)

## Corpus Check
- Corpus is ~15,033 words - fits in a single context window. You may not need a graph.

## Summary
- 132 nodes · 251 edges · 7 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6

## God Nodes (most connected - your core abstractions)
1. `calculate_risk_scores()` - 16 edges
2. `get_connection()` - 16 edges
3. `evaluate_compliance()` - 11 edges
4. `parse_and_ingest_csv()` - 9 edges
5. `get_summary_stats()` - 7 edges
6. `calculate_predictive_delay()` - 7 edges
7. `detect_duplicate_works()` - 7 edges
8. `insert_projects_bulk()` - 6 edges
9. `get_all_projects()` - 6 edges
10. `get_kpis_and_audit_metrics()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `calculate_risk_scores()` --calls--> `evaluate_compliance()`  [EXTRACTED]
  anomaly_engine.py → compliance_engine.py
- `calculate_risk_scores()` --calls--> `calculate_predictive_delay()`  [EXTRACTED]
  anomaly_engine.py → predictive_engine.py
- `calculate_risk_scores()` --calls--> `detect_duplicate_works()`  [EXTRACTED]
  anomaly_engine.py → predictive_engine.py
- `api_recalculate()` --calls--> `calculate_risk_scores()`  [EXTRACTED]
  app.py → anomaly_engine.py
- `parse_and_ingest_csv()` --calls--> `calculate_risk_scores()`  [EXTRACTED]
  csv_pipeline.py → anomaly_engine.py

## Import Cycles
- None detected.

## Communities (7 total, 0 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (26): api_alert_action(), api_alerts(), api_audit_feedback(), api_download_sample_csv(), api_kpis(), api_map_data(), api_projects(), api_recalculate() (+18 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (23): project_detail(), Detailed drill-down page with compliance checklist, early warning, and auditor…, clear_projects(), get_alerts(), get_connection(), get_map_data(), get_project(), get_summary_stats() (+15 more)

### Community 2 - "Community 2"
Cohesion: 0.17
Nodes (20): bindFilters(), bindSort(), escapeHtml(), fetchAlerts(), fetchProjects(), fetchSummary(), getFilterParams(), getRiskClass() (+12 more)

### Community 3 - "Community 3"
Cohesion: 0.15
Nodes (17): generate_sample_esakshi_csv(), normalize_column_name(), parse_and_ingest_csv(), csv_pipeline.py — Realistic eSAKSHI CSV/Excel Ingestion Pipeline Accepts…, Create a sample downloadable eSAKSHI format CSV file., Map arbitrary column header to standard field name., Parse uploaded CSV or Excel file, validate schema, evaluate AI models, and…, insert_projects_bulk() (+9 more)

### Community 4 - "Community 4"
Cohesion: 0.14
Nodes (19): calculate_risk_scores(), detect_cost_anomalies(), detect_delay_anomalies(), detect_speed_anomalies(), detect_utilization_anomalies(), anomaly_engine.py — Multi-Signal Anomaly Detection, Compliance Integration &…, Detect projects with unusually low fund utilization given their age., Detect projects completed suspiciously quickly for their cost. (+11 more)

### Community 5 - "Community 5"
Cohesion: 0.23
Nodes (11): evaluate_compliance(), evaluate_fund_limits(), evaluate_implementing_agency(), evaluate_statutory_deadlines(), evaluate_work_eligibility(), compliance_engine.py — Statutory Compliance Rule Engine for MPLADS Guidelines…, Rule 4: Check 75-day sanction deadline and execution timeline., Run full compliance audit on a project. Returns: compliance_status: 'PASSED' |… (+3 more)

### Community 6 - "Community 6"
Cohesion: 0.67
Nodes (3): test_prototype.py — Comprehensive test suite for upgraded SIH26102 MPLADS…, run_tests(), test_endpoint()

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `calculate_risk_scores()` connect `Community 4` to `Community 0`, `Community 3`, `Community 5`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `evaluate_compliance()` connect `Community 5` to `Community 3`, `Community 4`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `get_connection()` connect `Community 1` to `Community 0`, `Community 3`, `Community 4`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.10826210826210826 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.11956521739130435 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.14761904761904762 - nodes in this community are weakly interconnected._
- **Should `Community 4` be split into smaller, more focused modules?**
  _Cohesion score 0.14210526315789473 - nodes in this community are weakly interconnected._