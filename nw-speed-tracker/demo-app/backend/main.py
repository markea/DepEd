"""
DepEd NetPulse Interactive Prototype - Main FastAPI Application
Serves the 5-Tab Executive Showcase, REST APIs, and Gemini Enterprise Workflows
"""

import hashlib
import json
import os
import uuid
from datetime import date, datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.database import get_db, init_db
from backend.gemini_agents import gemini_service
from backend.simulator import trigger_scenario
from backend.sla_engine import evaluate_telemetry_sample

app = FastAPI(
    title="DepEd National Network Speed Tracker & SLA Governance Platform",
    description="Interactive Full-Stack Prototype implementing BRD v2.0 and TDD v2.0",
    version="2.0.0-PROTOTYPE",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
async def health_check():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM measurements")
    measurement_count = cur.fetchone()[0]
    return {
        "status": "HEALTHY",
        "app_version": "2.0.0-PROTOTYPE",
        "gemini_mode": "VERTEX_AI_LIVE" if gemini_service.is_live() else "SANDBOX_DETERMINISTIC_FALLBACK",
        "project": gemini_service.project,
        "region": gemini_service.location,
        "date_partitioned_records": measurement_count,
        "enrolled_schools": 47000,
    }


@app.get("/api/v1/national/summary")
async def get_national_summary():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM regions ORDER BY compliance_pct DESC")
    regions = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM isps ORDER BY monthly_rebates_eligible_php DESC")
    isps = [dict(r) for r in cur.fetchall()]

    total_schools = sum(r["total_schools"] for r in regions)
    total_online = sum(r["online_schools"] for r in regions)
    total_rebates = sum(i["monthly_rebates_eligible_php"] for i in isps)
    avg_speed = round(sum(r["avg_speed_mbps"] * r["total_schools"] for r in regions) / total_schools, 1)

    return {
        "kpis": {
            "total_schools": total_schools,
            "online_schools": total_online,
            "uptime_pct": round((total_online / total_schools) * 100.0, 1),
            "national_avg_speed_mbps": avg_speed,
            "national_cir_compliance_pct": 78.2,
            "total_monthly_sla_rebates_php": total_rebates,
            "active_cluster_outages": sum(1 for r in regions if r["active_cluster_outage"] == 1),
        },
        "regions": regions,
        "isps": isps,
    }


@app.get("/api/v1/divisions")
async def get_divisions():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM schools ORDER BY school_id ASC")
    schools = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM zero_touch_tickets ORDER BY created_at DESC")
    tickets = [dict(r) for r in cur.fetchall()]

    return {
        "schools_watchlist": schools,
        "cluster_alerts": [
            {
                "division_id": "DIV-LEYTE",
                "division_name": "Leyte Division",
                "region_id": "R08",
                "affected_schools": 24,
                "isp_name": "PLDT Enterprise",
                "cluster_type": "REGIONAL_FIBER_BACKBONE_CUT",
                "master_ticket_id": "DEPED-INC-2026-9012",
                "detected_at": "10:14 AM PHT",
                "suppression_summary": "24 individual school router alarms suppressed into 1 Master Regional Ticket.",
            }
        ],
        "active_tickets": tickets,
    }


class EnrollmentRequest(BaseModel):
    school_id: str
    target_os: str = "windows"


@app.post("/api/v1/devices/enrollment-command")
async def generate_enrollment_command(req: EnrollmentRequest):
    token = f"OTK-DEPED-{uuid.uuid4().hex[:8].upper()}"
    if req.target_os.lower() == "windows":
        cmd = f'msiexec.exe /i deped-netpulse-agent.msi /quiet SCHOOL_ID="{req.school_id}" ENROLL_TOKEN="{token}"'
    else:
        cmd = f'curl -sSL https://get.netpulse.deped.gov.ph | sudo bash -s -- --school-id="{req.school_id}" --token="{token}"'

    return {
        "school_id": req.school_id,
        "enrollment_token": token,
        "target_os": req.target_os,
        "command": cmd,
        "expires_in_hours": 24,
    }


@app.get("/api/v1/schools/{school_id}")
async def get_school_portal_data(school_id: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM schools WHERE school_id = ?", (school_id,))
    school_row = cur.fetchone()
    if not school_row:
        raise HTTPException(status_code=404, detail="School not found")
    school = dict(school_row)

    cur.execute("""
        SELECT * FROM measurements
        WHERE school_id = ?
        ORDER BY measured_at ASC
    """, (school_id,))
    measurements = [dict(m) for m in cur.fetchall()]

    latest = measurements[-1] if measurements else {}
    diagnosis = gemini_service.generate_bilingual_diagnosis(school)

    return {
        "school_metadata": school,
        "latest_telemetry": latest,
        "bilingual_diagnosis": diagnosis,
        "time_series_records": measurements,
        "date_partition_cache_info": {
            "cached_ttl_seconds": 900,
            "bytes_scanned_estimate": "4.2 KB",
            "per_seat_bi_license_cost_usd": 0.0,
        },
    }


@app.get("/api/v1/schools/{school_id}/certificate")
async def get_speed_certificate(school_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM schools WHERE school_id = ?", (school_id,))
    school = cur.fetchone()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    s = dict(school)

    cur.execute("SELECT AVG(deped_anchor_dl_mbps), AVG(deped_anchor_loss_pct), AVG(deped_anchor_ping_ms) FROM measurements WHERE school_id = ?", (school_id,))
    avg_speed, avg_loss, avg_ping = cur.fetchone()

    cert_hash = hashlib.sha256(f"DEPED-CERT-{school_id}-{avg_speed}-{date.today()}".encode("utf-8")).hexdigest()

    return {
        "certificate_id": f"DEPED-CERT-{date.today().year}-{school_id}",
        "issued_date": date.today().isoformat(),
        "school_id": s["school_id"],
        "school_name": s["school_name"],
        "region_name": s["region_name"],
        "division_name": s["division_name"],
        "isp_name": s["isp_name"],
        "contracted_cir_mbps": s["contracted_dl_mbps"],
        "measured_5day_avg_speed_mbps": round(avg_speed or 0, 1),
        "measured_5day_avg_loss_pct": round(avg_loss or 0, 2),
        "measured_5day_avg_ping_ms": round(avg_ping or 0, 1),
        "local_hop_verified": True,
        "compliance_status": "COMPLIANT" if (avg_speed or 0) >= (s["contracted_dl_mbps"] * 0.8) else "SLA_BREACH_VERIFIED",
        "qr_verification_url": f"https://netpulse.deped.gov.ph/verify/{cert_hash[:16]}",
        "hmac_sha256_seal": cert_hash,
    }


class ConversationalQueryRequest(BaseModel):
    prompt: str


@app.post("/api/v1/gemini/conversational-query")
async def execute_conversational_query(req: ConversationalQueryRequest):
    result = gemini_service.execute_conversational_query(req.prompt)
    return result


@app.get("/api/v1/governance/dashboard")
async def get_governance_dashboard():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM sla_violations ORDER BY created_at DESC")
    violations = [dict(v) for v in cur.fetchall()]

    cur.execute("SELECT * FROM zero_touch_tickets ORDER BY created_at DESC")
    tickets = [dict(t) for t in cur.fetchall()]

    cur.execute("SELECT * FROM agent_audit_trail ORDER BY timestamp DESC LIMIT 20")
    audit = [dict(a) for a in cur.fetchall()]

    return {
        "hitl_rebate_queue": violations,
        "zero_touch_tickets": tickets,
        "audit_trail": audit,
    }


class ApproveRebateRequest(BaseModel):
    approver_email: str = "dito.cavite@deped.gov.ph"


@app.post("/api/v1/governance/rebates/{violation_id}/approve")
async def approve_rebate(violation_id: str, req: ApproveRebateRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM sla_violations WHERE violation_id = ?", (violation_id,))
    viol = cur.fetchone()
    if not viol:
        raise HTTPException(status_code=404, detail="Violation record not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    cur.execute("""
        UPDATE sla_violations
        SET hitl_approval_state = 'APPROVED_FOR_REBATE',
            approved_by_human_email = ?,
            approved_at = ?
        WHERE violation_id = ?
    """, (req.approver_email, now_iso, violation_id))

    audit_id = f"AUDIT-{uuid.uuid4().hex[:6].upper()}"
    cur.execute("""
        INSERT INTO agent_audit_trail VALUES (
            ?, 'HITL_REBATE_APPROVED', 'HUMAN', ?, ?, ?, ?
        )
    """, (
        audit_id,
        req.approver_email,
        violation_id,
        f"Approved statutory billing rebate deduction of ₱{viol['calculated_rebate_php']:,.2f} for {viol['school_name']}",
        now_iso,
    ))
    conn.commit()

    return {
        "status": "APPROVED",
        "violation_id": violation_id,
        "new_state": "APPROVED_FOR_REBATE",
        "approved_by": req.approver_email,
        "timestamp": now_iso,
        "message": f"Successfully approved ₱{viol['calculated_rebate_php']:,.2f} deduction for {viol['school_name']}. Voucher queued for DepEd Finance billing release.",
    }


class SimulatorRequest(BaseModel):
    scenario_id: str


@app.post("/api/v1/simulator/trigger")
async def trigger_simulation_endpoint(req: SimulatorRequest):
    res = trigger_scenario(req.scenario_id)
    return res
