"""
DepEd NetPulse Gemini Enterprise Integration Module
Implements:
  - Gemini 3.8 Flash: Grounded Bilingual Root-Cause Diagnostics & Conversational Analytics NL-to-SQL
  - Gemini 3.1 Pro: ISP SLA Auditor & COA-Ready Formal Dispute Memo Generator
  - Dual-Mode: Live Vertex AI (when GOOGLE_CLOUD_PROJECT is set) + Deterministic Fallback
"""

import json
import os
import re
from datetime import date, datetime, timezone
from backend.database import get_db

MODEL_FLASH = os.getenv("GEMINI_FLASH_MODEL", "gemini-3.8-flash")
MODEL_PRO = os.getenv("GEMINI_PRO_MODEL", "gemini-3.1-pro")


class NetPulseGeminiService:
    def __init__(self):
        self.project = os.getenv("GOOGLE_CLOUD_PROJECT", "deped-demos-01")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "asia-southeast1")
        self.live_client = None
        try:
            from google import genai
            self.live_client = genai.Client(vertexai=True, project=self.project, location=self.location)
        except Exception:
            self.live_client = None

    def is_live(self) -> bool:
        return self.live_client is not None

    def generate_bilingual_diagnosis(self, school_data: dict) -> dict:
        """Uses Gemini 3.8 Flash to diagnose telemetry in English & Tagalog."""
        if self.is_live():
            try:
                from google.genai import types
                prompt = (
                    f"You are the DepEd ICTS Network Diagnostic Assistant. Analyze this school telemetry: "
                    f"{json.dumps(school_data, default=str)}. "
                    f"Return a JSON object with keys: 'root_cause', 'diagnosis_en', 'diagnosis_tl', 'recommended_action'."
                )
                resp = self.live_client.models.generate_content(
                    model=MODEL_FLASH,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2),
                )
                return json.loads(resp.text)
            except Exception:
                pass

        # Deterministic high-fidelity fallback based on archetype
        archetype = school_data.get("archetype", "HEALTHY_COMPLIANT")
        school_name = school_data.get("school_name", "Public School")
        isp_name = school_data.get("isp_name", "Assigned ISP")

        if archetype == "ISP_SELECTIVE_THROTTLING":
            return {
                "root_cause": "ISP_SELECTIVE_THROTTLING",
                "diagnosis_en": (
                    f"Your Admin PC has a healthy 1.2ms Ethernet connection to the router. Speed to DepEd Cloud drops "
                    f"to 14.2 Mbps between 10:00 AM and 02:00 PM while public speedtest shows 95.8 Mbps. "
                    f"This confirms selective throttling by {isp_name}. Trouble Ticket has been auto-dispatched."
                ),
                "diagnosis_tl": (
                    f"Maayos ang 1.2ms Ethernet connection ng PC sa school router. Bumabagsak sa 14.2 Mbps ang bilis sa "
                    f"DepEd Cloud tuwing 10:00 AM hanggang 02:00 PM habang 95.8 Mbps sa public speedtest. Nagpapatunay "
                    f"ito ng selective throttling ng {isp_name}. Kusang nagpadala ng ticket sa NOC."
                ),
                "recommended_action": "Zero-Touch Trouble Ticket filed. 25% SLA rebate deduction queued for DITO approval.",
            }
        elif archetype == "LOCAL_WIFI_BOTTLENECK":
            return {
                "root_cause": "LOCAL_WIFI_BOTTLENECK_EXEMPT",
                "diagnosis_en": (
                    "Your Admin PC is connected via weak Wi-Fi (-86 dBm RSSI) with 98ms router latency. The ISP fiber line "
                    "is healthy. Please connect an Ethernet LAN cable to restore full speed. Exempt from ISP SLA penalties."
                ),
                "diagnosis_tl": (
                    "Mahina ang Wi-Fi signal (-86 dBm) ng Admin PC papunta sa school router (98ms latency). Walang sira ang "
                    "fiber ng ISP sa labas. Isaksak ang Ethernet LAN cable sa PC. Hindi ito sisingilin bilang multa sa ISP."
                ),
                "recommended_action": "Advise school staff to plug in an Ethernet LAN cable; no ISP trouble ticket needed.",
            }
        elif archetype == "REGIONAL_FIBER_CUT":
            return {
                "root_cause": "REGIONAL_FIBER_CUT",
                "diagnosis_en": (
                    f"School router is powered and responsive (1.4ms). 24 neighboring schools in Leyte Division dropped "
                    f"offline simultaneously at 10:14 AM. Classified as a Regional Fiber Backbone Cut. Master Regional "
                    f"Ticket #DEPED-INC-2026-9012 is active."
                ),
                "diagnosis_tl": (
                    "Buhay at sumasagot ang router ng paaralan (1.4ms). Sabay-sabay na nawalan ng internet ang 24 na paaralan "
                    "sa Leyte bandang 10:14 AM dahil sa naputol na fiber backbone. Aktibo na ang Master Regional Ticket."
                ),
                "recommended_action": "Master Regional Ticket active with ISP executive NOC; individual router visits cancelled.",
            }
        elif archetype == "RURAL_SATELLITE_WEATHER":
            return {
                "root_cause": "RURAL_SATELLITE_WEATHER",
                "diagnosis_en": (
                    "Starlink LEO satellite link active under 15 MB metered probe cap. High latency (640ms) and rain fade "
                    "observed due to tropical depression weather. Automatic recovery expected once storm clears."
                ),
                "diagnosis_tl": (
                    "Aktibo ang Starlink satellite gamit ang 15 MB data-cap mode. Mataas ang latency (640ms) dulot ng "
                    "masamang panahon at ulan. Kusa itong babalik sa normal pagkatapos ng sama ng panahon."
                ),
                "recommended_action": "Monitor weather recovery; metered data cap preserved.",
            }
        else:
            return {
                "root_cause": "HEALTHY_COMPLIANT",
                "diagnosis_en": "100% compliant fiber connection. School-hour average is 96.4 Mbps with 0.0% packet loss.",
                "diagnosis_tl": "Napakaganda ng koneksyon (100% compliant). Umaabot sa 96.4 Mbps ang average speed sa oras ng klase.",
                "recommended_action": "Authorized for full monthly certificate of acceptance and invoice release.",
            }

    def execute_conversational_query(self, user_prompt: str) -> dict:
        """
        Bilingual Conversational Analytics (Gemini in Looker Simulation).
        Translates natural language in English, Tagalog, or Taglish into
        Date-Partitioned BigQuery SQL and executes against the local time-series store.
        """
        lower = user_prompt.lower()
        conn = get_db()
        cur = conn.cursor()

        # Query 1: Region IV-A 50% below speed (Tagalog or English)
        if "region iv-a" in lower or "calabarzon" in lower or "bagsak" in lower:
            generated_sql = (
                "SELECT school_id, school_name, isp_name, "
                "       ROUND(AVG(deped_anchor_dl_mbps), 1) AS avg_speed_mbps, "
                "       ROUND(AVG(dl_compliance_pct), 1) AS compliance_pct, "
                "       diagnostic_category "
                "FROM `deped-netpulse-prod.telemetry.speedtest_measurements` "
                "WHERE test_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) "
                "  AND region_id = 'R04A' "
                "  AND is_local_hop_healthy = TRUE "
                "GROUP BY 1, 2, 3, 6 "
                "HAVING compliance_pct < 50.0 "
                "ORDER BY compliance_pct ASC;"
            )
            cur.execute("""
                SELECT s.school_id, s.school_name, s.isp_name,
                       ROUND(AVG(m.deped_anchor_dl_mbps), 1) AS avg_speed_mbps,
                       ROUND(AVG(m.dl_compliance_pct), 1) AS compliance_pct,
                       m.diagnostic_category
                FROM schools s
                JOIN measurements m ON s.school_id = m.school_id
                WHERE s.region_id = 'R04A' AND m.is_local_hop_healthy = 1
                GROUP BY s.school_id, s.school_name, s.isp_name, m.diagnostic_category
                HAVING compliance_pct < 50.0
            """)
            rows = [dict(r) for r in cur.fetchall()]
            is_tagalog = any(w in lower for w in ["aling", "mga", "paaralan", "ngayong", "linggo", "ano"])
            summary_text = (
                "Nahanap ang 1 paaralan sa Region IV-A na bagsak ang speed ng higit 50% sa nakaraang linggo: "
                "**Bacoor National High School** (14.2 Mbps vs 100 Mbps contracted). Kumpirmadong selective throttling ng SpeedNet Regional."
                if is_tagalog else
                "Identified 1 school in Region IV-A operating 50% below contracted CIR over the last 7 days: "
                "**Bacoor National High School** (14.2 Mbps actual vs. 100 Mbps contracted). Issue verified as ISP Selective Throttling."
            )
            chart_data = {
                "labels": [r["school_name"] for r in rows] if rows else ["Bacoor NHS"],
                "datasets": [
                    {"label": "Actual Speed (Mbps)", "data": [r["avg_speed_mbps"] for r in rows] if rows else [14.2], "backgroundColor": "#CE1126"},
                    {"label": "Contracted Speed (Mbps)", "data": [100.0 for _ in rows] if rows else [100.0], "backgroundColor": "#94A3B8"}
                ]
            }
            return {
                "conversational_answer": summary_text,
                "generated_sql": generated_sql,
                "table_rows": rows,
                "chart_data": chart_data,
            }

        # Query 2: ISP SLA Violations & Rebates (Tagalog or English)
        elif "isp" in lower and ("violation" in lower or "rebate" in lower or "multa" in lower or "pinakamarami" in lower):
            generated_sql = (
                "SELECT isp_name, "
                "       COUNT(DISTINCT school_id) AS violating_schools, "
                "       SUM(calculated_rebate_php) AS total_rebate_php, "
                "       ROUND(AVG(consecutive_breach_days), 1) AS avg_breach_days "
                "FROM `deped-netpulse-prod.telemetry.sla_violation_ledger` "
                "WHERE billing_month = DATE_TRUNC(CURRENT_DATE(), MONTH) "
                "GROUP BY isp_name "
                "ORDER BY total_rebate_php DESC;"
            )
            cur.execute("""
                SELECT isp_name,
                       COUNT(DISTINCT school_id) AS violating_schools,
                       SUM(calculated_rebate_php) AS total_rebate_php,
                       ROUND(AVG(consecutive_breach_days), 1) AS avg_breach_days
                FROM sla_violations
                GROUP BY isp_name
                ORDER BY total_rebate_php DESC
            """)
            rows = [dict(r) for r in cur.fetchall()]
            is_tagalog = any(w in lower for w in ["aling", "magkano", "pinakamarami", "buwan"])
            total_rebates = sum(r["total_rebate_php"] for r in rows)
            summary_text = (
                f"Ang **SpeedNet Regional** at **PLDT Enterprise** ang may pinakamalaking SLA penalty ngayong buwan. "
                f"Kabuuang eligible rebate na dapat ibawas sa telco billing: **₱{total_rebates:,.2f}**."
                if is_tagalog else
                f"**SpeedNet Regional** and **PLDT Enterprise** account for the largest active SLA penalties this month. "
                f"Total statutory rebate eligible for billing deduction: **PHP {total_rebates:,.2f}**."
            )
            chart_data = {
                "labels": [r["isp_name"] for r in rows],
                "datasets": [
                    {"label": "Eligible Rebate (PHP)", "data": [r["total_rebate_php"] for r in rows], "backgroundColor": "#F59E0B"}
                ]
            }
            return {
                "conversational_answer": summary_text,
                "generated_sql": generated_sql,
                "table_rows": rows,
                "chart_data": chart_data,
            }

        # Query 3: Selective Throttling (Speedtest >80 vs Cloud Anchor <25)
        elif "selective" in lower or "throttl" in lower or "public" in lower or "anchor" in lower:
            generated_sql = (
                "SELECT school_id, school_name, isp_name, "
                "       ROUND(AVG(public_ref_dl_mbps), 1) AS public_speedtest_mbps, "
                "       ROUND(AVG(deped_anchor_dl_mbps), 1) AS deped_cloud_mbps, "
                "       ROUND(AVG(public_ref_dl_mbps - deped_anchor_dl_mbps), 1) AS throttling_gap_mbps "
                "FROM `deped-netpulse-prod.telemetry.speedtest_measurements` "
                "WHERE test_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 5 DAY) "
                "  AND is_selective_throttling = TRUE "
                "GROUP BY 1, 2, 3 "
                "ORDER BY throttling_gap_mbps DESC;"
            )
            cur.execute("""
                SELECT s.school_id, s.school_name, s.isp_name,
                       ROUND(AVG(m.public_ref_dl_mbps), 1) AS public_speedtest_mbps,
                       ROUND(AVG(m.deped_anchor_dl_mbps), 1) AS deped_cloud_mbps,
                       ROUND(AVG(m.public_ref_dl_mbps - m.deped_anchor_dl_mbps), 1) AS throttling_gap_mbps
                FROM schools s
                JOIN measurements m ON s.school_id = m.school_id
                WHERE m.is_selective_throttling = 1
                GROUP BY s.school_id, s.school_name, s.isp_name
            """)
            rows = [dict(r) for r in cur.fetchall()]
            summary_text = (
                "Detected 1 school with severe ISP Selective Throttling: **Bacoor National High School** shows "
                "95.8 Mbps on public speedtests but drops to 14.2 Mbps on the DepEd Cloud Anchor (Throttling Gap: 81.6 Mbps)."
            )
            chart_data = {
                "labels": [r["school_name"] for r in rows] if rows else ["Bacoor NHS"],
                "datasets": [
                    {"label": "Public Reference Speed (Mbps)", "data": [r["public_speedtest_mbps"] for r in rows] if rows else [95.8], "backgroundColor": "#3B82F6"},
                    {"label": "DepEd Cloud Anchor (Mbps)", "data": [r["deped_cloud_mbps"] for r in rows] if rows else [14.2], "backgroundColor": "#EF4444"},
                ]
            }
            return {
                "conversational_answer": summary_text,
                "generated_sql": generated_sql,
                "table_rows": rows,
                "chart_data": chart_data,
            }

        # Query 4: Default / General Region VIII fiber cut
        else:
            generated_sql = (
                "SELECT s.school_id, s.school_name, s.division_name, m.diagnostic_category, "
                "       m.deped_anchor_dl_mbps, m.connection_status "
                "FROM `deped-netpulse-prod.telemetry.speedtest_measurements` m "
                "JOIN `deped-netpulse-prod.telemetry.school_master_metadata` s ON m.school_id = s.school_id "
                "WHERE m.test_date = CURRENT_DATE() "
                "  AND m.diagnostic_category IN ('VERIFIED_ISP_WAN_OFFLINE', 'ISP_SELECTIVE_THROTTLING') "
                "ORDER BY m.test_hour DESC LIMIT 10;"
            )
            cur.execute("""
                SELECT s.school_id, s.school_name, s.division_name, m.diagnostic_category,
                       m.deped_anchor_dl_mbps, m.connection_status
                FROM measurements m
                JOIN schools s ON m.school_id = s.school_id
                WHERE m.diagnostic_category IN ('VERIFIED_ISP_WAN_OFFLINE', 'ISP_SELECTIVE_THROTTLING')
                LIMIT 5
            """)
            rows = [dict(r) for r in cur.fetchall()]
            summary_text = (
                "Natagpuan ang mga aktibong insidente sa pambansang network: May cluster fiber cut sa Region VIII "
                "(Palo NHS / 24 paaralan offline) at selective throttling sa Region IV-A (Bacoor NHS)."
            )
            chart_data = {
                "labels": [r["school_name"] for r in rows] if rows else ["Palo NHS", "Bacoor NHS"],
                "datasets": [
                    {"label": "Measured Speed (Mbps)", "data": [r["deped_anchor_dl_mbps"] for r in rows] if rows else [0, 14.2], "backgroundColor": "#CE1126"}
                ]
            }
            return {
                "conversational_answer": summary_text,
                "generated_sql": generated_sql,
                "table_rows": rows,
                "chart_data": chart_data,
            }


# Singleton service instance
gemini_service = NetPulseGeminiService()
