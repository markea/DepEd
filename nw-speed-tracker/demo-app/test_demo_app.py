"""
Automated Pytest Suite for DepEd NetPulse Interactive Prototype
Validates all 5 Tabs, Dual-Probe Anti-Gaming, Bilingual Conversational Analytics,
Local Hop Wi-Fi Exemption, and HITL Rebate Approval Workflows.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    init_db(force_reseed=True)


def test_01_health_and_partitioned_seed():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["enrolled_schools"] == 47000
    assert data["date_partitioned_records"] > 0


def test_02_national_summary_kpis():
    response = client.get("/api/v1/national/summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data["regions"]) == 17
    assert data["kpis"]["total_schools"] == 47000
    assert data["kpis"]["total_monthly_sla_rebates_php"] > 0

    # Verify Dual-Probe Anti-Gaming flag on SpeedNet Regional
    speednet = next(i for i in data["isps"] if i["isp_id"] == "ISP-SPEEDNET")
    assert speednet["selective_throttling_flag"] == 1
    assert speednet["public_ref_avg_pct"] > 90.0
    assert speednet["deped_anchor_avg_pct"] < 30.0


def test_03_division_watchlist_and_enrollment():
    res = client.get("/api/v1/divisions")
    assert res.status_code == 200
    data = res.json()
    assert len(data["schools_watchlist"]) >= 5
    assert len(data["cluster_alerts"]) >= 1
    assert data["cluster_alerts"][0]["cluster_type"] == "REGIONAL_FIBER_BACKBONE_CUT"

    # Test 1-Click Enrollment Command Generator
    enroll_res = client.post("/api/v1/devices/enrollment-command", json={"school_id": "104512", "target_os": "windows"})
    assert enroll_res.status_code == 200
    enroll_data = enroll_res.json()
    assert "msiexec.exe" in enroll_data["command"]
    assert "OTK-DEPED-" in enroll_data["enrollment_token"]


def test_04_school_portal_dual_probe_and_bilingual_diag():
    res = client.get("/api/v1/schools/104512")
    assert res.status_code == 200
    data = res.json()
    assert data["school_metadata"]["school_name"] == "Bacoor National High School"
    assert len(data["time_series_records"]) > 0

    # Verify Bilingual Diagnosis
    diag = data["bilingual_diagnosis"]
    assert "diagnosis_en" in diag
    assert "diagnosis_tl" in diag
    assert "selective throttling" in diag["diagnosis_en"].lower()
    assert "selective throttling" in diag["diagnosis_tl"].lower() or "throttling" in diag["diagnosis_tl"].lower()


def test_05_qr_speed_certificate():
    res = client.get("/api/v1/schools/104512/certificate")
    assert res.status_code == 200
    data = res.json()
    assert data["school_id"] == "104512"
    assert len(data["hmac_sha256_seal"]) == 64
    assert "DEPED-CERT-" in data["certificate_id"]


def test_06_bilingual_conversational_analytics():
    # English Query
    en_res = client.post("/api/v1/gemini/conversational-query", json={"prompt": "Which schools in Region IV-A have been 50% below their contracted speed this week?"})
    assert en_res.status_code == 200
    en_data = en_res.json()
    assert "Bacoor National High School" in en_data["conversational_answer"]
    assert "WHERE test_date >=" in en_data["generated_sql"]

    # Tagalog Query
    tl_res = client.post("/api/v1/gemini/conversational-query", json={"prompt": "Aling mga ISP ang may pinakamaraming SLA violation ngayong buwan?"})
    assert tl_res.status_code == 200
    tl_data = tl_res.json()
    assert "SpeedNet Regional" in tl_data["conversational_answer"]
    assert "WHERE billing_month =" in tl_data["generated_sql"]


def test_07_split_governance_hitl_approval():
    gov_res = client.get("/api/v1/governance/dashboard")
    assert gov_res.status_code == 200
    gov_data = gov_res.json()
    assert len(gov_data["hitl_rebate_queue"]) >= 2
    assert len(gov_data["zero_touch_tickets"]) >= 2

    # Approve first pending rebate
    target_viol = gov_data["hitl_rebate_queue"][0]
    viol_id = target_viol["violation_id"]
    assert target_viol["hitl_approval_state"] == "PENDING_DITO_REVIEW"

    appr_res = client.post(f"/api/v1/governance/rebates/{viol_id}/approve", json={"approver_email": "dito.cavite@deped.gov.ph"})
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["status"] == "APPROVED"
    assert appr_data["new_state"] == "APPROVED_FOR_REBATE"


def test_08_simulator_scenarios():
    # Scenario 2: Weak Local Wi-Fi (Should be EXEMPTED from SLA penalty)
    wifi_res = client.post("/api/v1/simulator/trigger", json={"scenario_id": "weak_wifi"})
    assert wifi_res.status_code == 200
    wifi_data = wifi_res.json()
    assert wifi_data["diagnostic_category"] == "LOCAL_WIFI_BOTTLENECK_EXEMPT"
    assert wifi_data["is_sla_breach_eligible"] is False

    # Scenario 3: Selective Throttling (Should be CONFIRMED ISP breach)
    thr_res = client.post("/api/v1/simulator/trigger", json={"scenario_id": "selective_throttling"})
    assert thr_res.status_code == 200
    thr_data = thr_res.json()
    assert thr_data["is_selective_throttling"] is True
    assert thr_data["is_sla_breach_eligible"] is True


def test_09_geospatial_school_map_issues():
    # 1. Fetch All Features
    res = client.get("/api/v1/schools/map-issues")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["filtered_count"] >= 18
    assert "summary" in data
    assert data["summary"]["outages"] >= 4
    assert data["summary"]["throttling"] >= 1

    # Verify Philippine Bounding Box for all coordinates
    for feat in data["features"]:
        assert 4.5 <= feat["latitude"] <= 21.5, f"Lat out of PH bounds: {feat['latitude']}"
        assert 116.0 <= feat["longitude"] <= 127.0, f"Lon out of PH bounds: {feat['longitude']}"
        assert "heat_weight" in feat
        assert 0.0 <= feat["heat_weight"] <= 1.0

    # 2. Filter by OUTAGE
    outage_res = client.get("/api/v1/schools/map-issues?issue_type=OUTAGE")
    assert outage_res.status_code == 200
    outage_data = outage_res.json()
    assert outage_data["filtered_count"] >= 4
    for feat in outage_data["features"]:
        assert feat["issue_category"] == "OUTAGE"
        assert feat["severity"] == "CRITICAL"

    # 3. Filter by Region R08 (Leyte)
    r08_res = client.get("/api/v1/schools/map-issues?region_id=R08")
    assert r08_res.status_code == 200
    r08_data = r08_res.json()
    assert r08_data["filtered_count"] >= 4
    assert all(f["region_id"] == "R08" for f in r08_data["features"])

