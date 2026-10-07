"""
DepEd NetPulse Prototype Database & Seed Data Module
Provides in-memory / SQLite storage mirroring Date-Partitioned BigQuery tables:
  - 17 Philippine Regions (47,000 public schools total)
  - 5 Telecommunications Providers (ISPs) with Dual-Probe Anti-Gaming metrics
  - 5 Showcase Schools representing every BRD v2.0 & TDD v2.0 scenario
  - 5 Days of Hourly School-Hour Telemetry (07:00 AM - 05:00 PM PHT)
  - HITL SLA Rebate Approval Queue & Zero-Touch ITSM / Google Workspace Alerts
"""

import json
import os
import sqlite3
import uuid
from datetime import date, datetime, timedelta, timezone

DB_PATH = os.getenv("DEMO_DB_PATH", "/tmp/deped_netpulse_demo.db")


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force_reseed=False):
    if force_reseed and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = get_db()
    cur = conn.cursor()

    # 1. Regions Table (17 Philippine administrative regions, totaling 47,000 schools)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            region_id TEXT PRIMARY KEY,
            region_name TEXT NOT NULL,
            capital TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            total_schools INTEGER NOT NULL,
            online_schools INTEGER NOT NULL,
            compliance_pct REAL NOT NULL,
            avg_speed_mbps REAL NOT NULL,
            active_cluster_outage BOOL NOT NULL DEFAULT 0,
            outage_description TEXT
        )
    """)

    # 2. ISPs Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS isps (
            isp_id TEXT PRIMARY KEY,
            isp_name TEXT NOT NULL,
            technology TEXT NOT NULL,
            total_schools INTEGER NOT NULL,
            compliance_pct REAL NOT NULL,
            public_ref_avg_pct REAL NOT NULL,
            deped_anchor_avg_pct REAL NOT NULL,
            selective_throttling_flag BOOL NOT NULL DEFAULT 0,
            active_sla_breaches INTEGER NOT NULL,
            monthly_rebates_eligible_php REAL NOT NULL
        )
    """)

    # 3. Schools Master Metadata Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schools (
            school_id TEXT PRIMARY KEY,
            school_name TEXT NOT NULL,
            region_id TEXT NOT NULL,
            region_name TEXT NOT NULL,
            division_id TEXT NOT NULL,
            division_name TEXT NOT NULL,
            municipality TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            isp_id TEXT NOT NULL,
            isp_name TEXT NOT NULL,
            connection_type TEXT NOT NULL,
            contracted_dl_mbps REAL NOT NULL,
            contracted_ul_mbps REAL NOT NULL,
            monthly_contract_php REAL NOT NULL,
            device_id TEXT NOT NULL,
            archetype TEXT NOT NULL,
            cached_diagnosis_en TEXT,
            cached_diagnosis_tl TEXT
        )
    """)

    # 4. Measurements Table (Date-Partitioned mirror)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            event_id TEXT PRIMARY KEY,
            school_id TEXT NOT NULL,
            measured_at TEXT NOT NULL,
            test_date TEXT NOT NULL,
            test_hour INTEGER NOT NULL,
            connection_status TEXT NOT NULL,
            connection_medium TEXT NOT NULL,
            wifi_rssi_dbm INTEGER NOT NULL,
            local_gateway_reachable BOOL NOT NULL,
            local_gateway_ping_ms REAL NOT NULL,
            is_local_hop_healthy BOOL NOT NULL,
            deped_anchor_dl_mbps REAL NOT NULL,
            deped_anchor_ul_mbps REAL NOT NULL,
            deped_anchor_ping_ms REAL NOT NULL,
            deped_anchor_jitter_ms REAL NOT NULL,
            deped_anchor_loss_pct REAL NOT NULL,
            public_ref_dl_mbps REAL NOT NULL,
            dl_compliance_pct REAL NOT NULL,
            is_selective_throttling BOOL NOT NULL,
            diagnostic_category TEXT NOT NULL,
            is_sla_breach_eligible BOOL NOT NULL,
            is_backlogged_retry BOOL NOT NULL DEFAULT 0,
            signature_hmac_sha256 TEXT NOT NULL
        )
    """)

    # 5. SLA Violations & HITL Approval Ledger
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sla_violations (
            violation_id TEXT PRIMARY KEY,
            billing_month TEXT NOT NULL,
            school_id TEXT NOT NULL,
            school_name TEXT NOT NULL,
            region_id TEXT NOT NULL,
            division_id TEXT NOT NULL,
            isp_id TEXT NOT NULL,
            isp_name TEXT NOT NULL,
            breach_type TEXT NOT NULL,
            consecutive_breach_days INTEGER NOT NULL,
            avg_deped_anchor_dl_mbps REAL NOT NULL,
            avg_public_ref_dl_mbps REAL NOT NULL,
            contracted_dl_mbps REAL NOT NULL,
            monthly_contract_php REAL NOT NULL,
            calculated_rebate_php REAL NOT NULL,
            gemini_diagnostic_en TEXT NOT NULL,
            gemini_diagnostic_tl TEXT NOT NULL,
            draft_dispute_memo_md TEXT NOT NULL,
            itsm_ticket_id TEXT NOT NULL,
            hitl_approval_state TEXT NOT NULL DEFAULT 'PENDING_DITO_REVIEW',
            created_by_agent_id TEXT NOT NULL,
            approved_by_human_email TEXT,
            approved_at TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # 6. Zero-Touch Technical Tickets & Workspace Notifications
    cur.execute("""
        CREATE TABLE IF NOT EXISTS zero_touch_tickets (
            ticket_id TEXT PRIMARY KEY,
            school_id TEXT NOT NULL,
            school_name TEXT NOT NULL,
            isp_name TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            gemini_diagnosis TEXT NOT NULL,
            gmail_preview TEXT NOT NULL,
            google_chat_card TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # 7. Audit Trail
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agent_audit_trail (
            audit_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            actor_type TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            action_summary TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()

    # Check if seed data exists
    cur.execute("SELECT COUNT(*) FROM regions")
    if cur.fetchone()[0] == 0:
        seed_prototype_data(conn)


def seed_prototype_data(conn):
    cur = conn.cursor()

    # Seed 17 Philippine Regions (Sum of schools = exactly 47,000)
    regions_data = [
        ("NCR", "National Capital Region", "Manila", 14.5995, 120.9842, 3250, 3120, 94.2, 88.5, 0, None),
        ("CAR", "Cordillera Administrative Region", "Baguio", 16.4023, 120.5960, 1650, 1480, 78.4, 42.1, 0, None),
        ("R01", "Region I (Ilocos Region)", "San Fernando", 16.6159, 120.3209, 2750, 2550, 85.1, 54.3, 0, None),
        ("R02", "Region II (Cagayan Valley)", "Tuguegarao", 17.6132, 121.7270, 2450, 2190, 81.6, 48.7, 0, None),
        ("R03", "Region III (Central Luzon)", "San Fernando", 15.0286, 120.6896, 3850, 3650, 89.4, 68.2, 0, None),
        ("R04A", "Region IV-A (CALABARZON)", "Calamba", 14.2117, 121.1656, 4150, 3810, 82.1, 58.4, 0, None),
        ("R04B", "MIMAROPA Region", "Calapan", 13.4115, 121.1803, 2050, 1780, 74.5, 36.8, 0, None),
        ("R05", "Region V (Bicol Region)", "Legazpi", 13.1391, 123.7438, 3450, 3010, 76.2, 39.5, 0, None),
        ("R06", "Region VI (Western Visayas)", "Iloilo City", 10.7202, 122.5621, 3650, 3450, 88.9, 62.1, 0, None),
        ("R07", "Region VII (Central Visayas)", "Cebu City", 10.3157, 123.8854, 3550, 3280, 87.5, 64.8, 0, None),
        ("R08", "Region VIII (Eastern Visayas)", "Tacloban", 11.2444, 125.0039, 3850, 2810, 61.4, 28.5, 1, "Major Fiber Cut in Leyte Division (24 schools offline simultaneously)"),
        ("R09", "Region IX (Zamboanga Peninsula)", "Pagadian", 7.8286, 123.4354, 2150, 1920, 79.2, 41.2, 0, None),
        ("R10", "Region X (Northern Mindanao)", "Cagayan de Oro", 8.4542, 124.6319, 2350, 2120, 82.8, 51.4, 0, None),
        ("R11", "Region XI (Davao Region)", "Davao City", 7.1907, 125.4553, 2300, 2150, 86.4, 59.7, 0, None),
        ("R12", "Region XII (SOCCSKSARGEN)", "Koronadal", 6.5000, 124.8500, 1950, 1780, 77.8, 43.1, 0, None),
        ("R13", "Region XIII (Caraga)", "Butuan", 8.9475, 125.5406, 1850, 1620, 75.1, 38.6, 0, None),
        ("BARMM", "Bangsamoro Autonomous Region", "Cotabato City", 7.2236, 124.2464, 1750, 1390, 71.8, 34.2, 0, "High Starlink satellite latency & monsoon rain fade in island schools"),
    ]
    cur.executemany("INSERT INTO regions VALUES (?,?,?,?,?,?,?,?,?,?,?)", regions_data)

    # Seed 5 Telecommunications Providers
    isps_data = [
        ("ISP-PLDT", "PLDT Enterprise", "FIBER / METRO-E", 18200, 84.5, 92.1, 84.5, 0, 142, 1125000.00),
        ("ISP-CNVRG", "Converge ICT", "FIBER-TO-THE-SCHOOL", 9800, 88.0, 90.4, 88.0, 0, 68, 642500.00),
        ("ISP-GLOBE", "Globe Business", "FIBER / LTE-5G", 12400, 76.2, 89.5, 76.2, 0, 185, 1450000.00),
        ("ISP-STLK", "Starlink PH", "LEO SATELLITE (Last-Mile)", 4200, 72.4, 76.8, 72.4, 0, 31, 312000.00),
        ("ISP-SPEEDNET", "SpeedNet Regional", "LOCAL FIXED FIBER", 2400, 21.4, 95.0, 21.4, 1, 114, 1610000.00),
    ]
    cur.executemany("INSERT INTO isps VALUES (?,?,?,?,?,?,?,?,?,?)", isps_data)

    # Seed 18 Representative Showcase Schools across Luzon, Visayas, Mindanao with PH coordinates
    schools_data = [
        (
            "104512", "Bacoor National High School", "R04A", "Region IV-A (CALABARZON)", "DIV-CAVITE", "Cavite Province", "Bacoor City",
            14.4586, 120.9427, "ISP-SPEEDNET", "SpeedNet Regional", "FIBER", 100.0, 100.0, 12500.00, "DCP-WIN-104512-01", "ISP_SELECTIVE_THROTTLING",
            "Your Admin PC has a healthy 1.2ms Ethernet connection to the router. Speed to DepEd Cloud drops to 14 Mbps between 10 AM and 2 PM while public speedtest shows 95 Mbps. This confirms ISP selective throttling.",
            "Maayos ang 1.2ms Ethernet connection ng PC sa school router. Bumabagsak sa 14 Mbps ang bilis sa DepEd Cloud tuwing 10 AM-2 PM habang 95 Mbps sa public speedtest. Nagpapatunay ito ng selective throttling ng ISP.",
        ),
        (
            "104513", "Imus National High School", "R04A", "Region IV-A (CALABARZON)", "DIV-CAVITE", "Cavite Province", "Imus City",
            14.4296, 120.9367, "ISP-SPEEDNET", "SpeedNet Regional", "FIBER", 100.0, 100.0, 12500.00, "DCP-WIN-104513-01", "ISP_SELECTIVE_THROTTLING",
            "SpeedNet connection shows artificial throttling down to 15.1 Mbps during school instructional hours despite 96 Mbps public speedtest.",
            "Bumabagsak sa 15.1 Mbps ang SpeedNet tuwing oras ng klase kahit 96 Mbps sa labas.",
        ),
        (
            "104514", "Dasmariñas Integrated High School", "R04A", "Region IV-A (CALABARZON)", "DIV-CAVITE", "Cavite Province", "Dasmariñas City",
            14.3294, 120.9367, "ISP-SPEEDNET", "SpeedNet Regional", "FIBER", 100.0, 100.0, 12500.00, "DCP-WIN-104514-01", "ISP_SELECTIVE_THROTTLING",
            "Confirmed selective traffic shaping on Cavite fiber ring during peak instructional hours.",
            "Kumpirmadong traffic shaping sa Cavite fiber ring tuwing peak hours.",
        ),
        (
            "109821", "Tondo Elementary School", "NCR", "National Capital Region", "DIV-MANILA", "City of Manila", "Tondo",
            14.6159, 120.9678, "ISP-CNVRG", "Converge ICT", "FIBER", 100.0, 100.0, 11500.00, "DCP-WIN-109821-01", "LOCAL_WIFI_BOTTLENECK",
            "Your Admin PC is connected via weak Wi-Fi (-86 dBm RSSI) with 98ms router latency. The ISP fiber line is healthy. Connect your PC via an Ethernet LAN cable to restore full speed. Exempt from ISP SLA penalty.",
            "Mahina ang Wi-Fi signal (-86 dBm) ng Admin PC papunta sa router (98ms latency). Walang sira ang fiber ng ISP. Isaksak ang Ethernet cable sa PC. Hindi ito sisingilin bilang multa sa ISP.",
        ),
        (
            "109822", "Ramon Magsaysay High School", "NCR", "National Capital Region", "DIV-MANILA", "City of Manila", "Sampaloc",
            14.6062, 120.9932, "ISP-CNVRG", "Converge ICT", "FIBER", 100.0, 100.0, 11500.00, "DCP-WIN-109822-01", "HEALTHY_COMPLIANT",
            "100% compliant fiber connection in Manila Division. 97.2 Mbps average speed.",
            "100% compliant ang fiber connection sa Manila Division. 97.2 Mbps average.",
        ),
        (
            "121405", "Palo National High School", "R08", "Region VIII (Eastern Visayas)", "DIV-LEYTE", "Leyte Division", "Palo",
            11.1578, 124.9912, "ISP-PLDT", "PLDT Enterprise", "FIBER", 100.0, 100.0, 12500.00, "DCP-WIN-121405-01", "REGIONAL_FIBER_CUT",
            "School router is powered and responsive (1.4ms). 24 neighboring schools in Leyte Division dropped offline simultaneously at 10:14 AM. Classified as a Regional Fiber Backbone Cut. Master Ticket #DEPED-INC-9012 is active.",
            "Buhay at sumasagot ang router ng paaralan (1.4ms). Sabay-sabay na nawalan ng internet ang 24 na paaralan sa Leyte bandang 10:14 AM dahil sa naputol na fiber backbone. Aktibo na ang Master Ticket #DEPED-INC-9012.",
        ),
        (
            "121406", "Tanauan National High School", "R08", "Region VIII (Eastern Visayas)", "DIV-LEYTE", "Leyte Division", "Tanauan",
            11.1114, 125.0182, "ISP-PLDT", "PLDT Enterprise", "FIBER", 100.0, 100.0, 12500.00, "DCP-WIN-121406-01", "REGIONAL_FIBER_CUT",
            "Cluster fiber cut impact confirmed. Local router reachable; WAN offline.",
            "Apektado ng cluster fiber cut. Sumasagot ang router; patay ang WAN.",
        ),
        (
            "121407", "Tolosa National High School", "R08", "Region VIII (Eastern Visayas)", "DIV-LEYTE", "Leyte Division", "Tolosa",
            11.0617, 125.0347, "ISP-PLDT", "PLDT Enterprise", "FIBER", 100.0, 100.0, 12500.00, "DCP-WIN-121407-01", "REGIONAL_FIBER_CUT",
            "Cluster fiber cut impact confirmed. Correlated under Master Regional Ticket #DEPED-INC-9012.",
            "Apektado ng cluster fiber cut. Kasama sa Master Regional Ticket #DEPED-INC-9012.",
        ),
        (
            "121408", "Dulag National High School", "R08", "Region VIII (Eastern Visayas)", "DIV-LEYTE", "Leyte Division", "Dulag",
            10.9525, 125.0322, "ISP-PLDT", "PLDT Enterprise", "FIBER", 100.0, 100.0, 12500.00, "DCP-WIN-121408-01", "REGIONAL_FIBER_CUT",
            "Cluster fiber cut impact confirmed. Feeder line severed along Pan-Philippine Highway.",
            "Apektado ng cluster fiber cut kasama ng mga karatig-paaralan sa Leyte.",
        ),
        (
            "139501", "Basilan Island National High School", "BARMM", "Bangsamoro Autonomous Region", "DIV-BASILAN", "Basilan Division", "Isabela City",
            6.7042, 121.9711, "ISP-STLK", "Starlink PH", "SATELLITE_LEO", 50.0, 20.0, 9500.00, "DCP-WIN-139501-01", "RURAL_SATELLITE_WEATHER",
            "Starlink satellite connection active with 15 MB capped testing. Heavy rain-fade observed with 640ms latency and 8.5% packet loss. Normal LEO satellite weather recovery expected.",
            "Aktibo ang koneksyon ng Starlink satellite gamit ang 15 MB data-cap mode. Nakaranas ng rain-fade (640ms ping, 8.5% packet loss) dulot ng masamang panahon. Kusa itong babalik sa normal paghupa ng ulan.",
        ),
        (
            "139502", "Lamitan National High School", "BARMM", "Bangsamoro Autonomous Region", "DIV-BASILAN", "Basilan Division", "Lamitan City",
            6.6500, 122.1333, "ISP-STLK", "Starlink PH", "SATELLITE_LEO", 50.0, 20.0, 9500.00, "DCP-WIN-139502-01", "RURAL_SATELLITE_WEATHER",
            "Starlink LEO terminal experiencing tropical storm rain fade. Automated storm advisory linked.",
            "Starlink terminal nakakaranas ng rain fade dahil sa sama ng panahon sa Basilan.",
        ),
        (
            "112804", "Iloilo Central Elementary School", "R06", "Region VI (Western Visayas)", "DIV-ILOILO", "Iloilo Province", "Iloilo City",
            10.6969, 122.5644, "ISP-GLOBE", "Globe Business", "FIBER", 100.0, 100.0, 12000.00, "DCP-WIN-112804-01", "HEALTHY_COMPLIANT",
            "100% compliant fiber connection. Average download speed is 96.4 Mbps during school hours with 0.0% packet loss and 1.1ms local gateway latency. Certified for full monthly invoice release.",
            "Napakaganda ng koneksyon (100% compliant). Umaabot sa 96.4 Mbps ang average download speed sa oras ng klase na may 0.0% packet loss. Awtorisado ang buong bayad sa buwanang billing.",
        ),
        (
            "102144", "Baguio City National High School", "CAR", "Cordillera Administrative Region", "DIV-BAGUIO", "Baguio City", "Baguio City",
            16.4023, 120.5960, "ISP-PLDT", "PLDT Enterprise", "FIBER", 100.0, 100.0, 12000.00, "DCP-WIN-102144-01", "HEALTHY_COMPLIANT",
            "Highland fiber trunk running smoothly at 94.8 Mbps. Compliant SLA.",
            "Maayos ang takbo ng fiber sa Baguio City. 94.8 Mbps average.",
        ),
        (
            "103401", "San Fernando Central School", "R03", "Region III (Central Luzon)", "DIV-PAMPANGA", "Pampanga", "San Fernando",
            15.0286, 120.6896, "ISP-CNVRG", "Converge ICT", "FIBER", 100.0, 100.0, 11500.00, "DCP-WIN-103401-01", "CONGESTION_HIGH_JITTER",
            "Midday peak congestion detected with 38ms jitter and 42 Mbps throughput.",
            "Nakararanas ng pagsisikip tuwing tanghali na may 38ms jitter at 42 Mbps speed.",
        ),
        (
            "105219", "Legazpi City National High School", "R05", "Region V (Bicol Region)", "DIV-ALBAY", "Albay", "Legazpi City",
            13.1391, 123.7438, "ISP-GLOBE", "Globe Business", "FIBER", 100.0, 100.0, 12000.00, "DCP-WIN-105219-01", "CHRONIC_PACKET_LOSS",
            "Chronic packet loss (12.5%) detected on provincial uplink. Ticket dispatched to Globe.",
            "Mataas na packet loss (12.5%) sa provincial link. Nagpadala na ng tiket sa Globe.",
        ),
        (
            "107330", "Cebu City National Science High School", "R07", "Region VII (Central Visayas)", "DIV-CEBU", "Cebu City", "Cebu City",
            10.3157, 123.8854, "ISP-CNVRG", "Converge ICT", "FIBER", 100.0, 100.0, 11500.00, "DCP-WIN-107330-01", "HEALTHY_COMPLIANT",
            "Compliant Metro Cebu fiber node delivering 95.6 Mbps.",
            "Maayos ang takbo ng fiber sa Cebu City na may 95.6 Mbps.",
        ),
        (
            "108912", "Zamboanga City High School (Main)", "R09", "Region IX (Zamboanga Peninsula)", "DIV-ZAMBOANGA", "Zamboanga City", "Zamboanga City",
            6.9214, 122.0790, "ISP-PLDT", "PLDT Enterprise", "FIBER", 100.0, 100.0, 12000.00, "DCP-WIN-108912-01", "SLA_BREACH_UNDERDELIVERY",
            "Chronic under-delivery: ISP delivers only 28.5 Mbps on 100 Mbps contract. Breach penalty queued.",
            "Mabagal ang bigay ng ISP (28.5 Mbps lang sa 100 Mbps kontrata). Nakapila para sa multa.",
        ),
        (
            "110452", "Davao City National High School", "R11", "Region XI (Davao Region)", "DIV-DAVAO", "Davao City", "Davao City",
            7.0736, 125.6128, "ISP-GLOBE", "Globe Business", "FIBER", 100.0, 100.0, 12000.00, "DCP-WIN-110452-01", "HEALTHY_COMPLIANT",
            "Mindanao regional hub fiber delivering 96.1 Mbps. Compliant SLA.",
            "Maayos at mabilis ang takbo sa Davao City (96.1 Mbps).",
        ),
    ]
    cur.executemany("INSERT INTO schools VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", schools_data)

    # Seed 5 Days of Hourly School-Hour Telemetry (07:00 AM - 05:00 PM PHT)
    base_date = date.today() - timedelta(days=5)
    measurements = []

    for day_offset in range(5):
        test_day = base_date + timedelta(days=day_offset)
        if test_day.weekday() in (5, 6):
            continue
        date_str = test_day.isoformat()

        for hour in range(7, 18):  # 7 AM to 5 PM
            dt_iso = f"{date_str}T{hour:02d}:15:00Z"

            for s in schools_data:
                s_id = s[0]
                archetype = s[16]
                contracted_dl = s[12]

                if archetype == "ISP_SELECTIVE_THROTTLING":
                    is_peak = 10 <= hour <= 14
                    anchor_dl = 14.2 if is_peak else 92.5
                    public_dl = 95.8
                    is_sel = 1 if is_peak else 0
                    cat = "ISP_SELECTIVE_THROTTLING" if is_peak else "HEALTHY_COMPLIANT"
                    measurements.append((
                        f"EVT-{s_id}-{date_str}-{hour:02d}", s_id, dt_iso, date_str, hour,
                        "ONLINE", "ETHERNET", 0, 1, 1.25, 1,
                        anchor_dl, anchor_dl * 0.7, 32.4, 4.2, 0.0, public_dl, (anchor_dl / contracted_dl) * 100,
                        is_sel, cat, is_sel, 0, f"sig-mock-{s_id}"
                    ))
                elif archetype == "LOCAL_WIFI_BOTTLENECK":
                    measurements.append((
                        f"EVT-{s_id}-{date_str}-{hour:02d}", s_id, dt_iso, date_str, hour,
                        "ONLINE", "WIFI", -86, 1, 98.4, 0,
                        11.8, 8.4, 112.5, 45.2, 8.5, 12.1, 11.8,
                        0, "LOCAL_WIFI_BOTTLENECK_EXEMPT", 0, 0, f"sig-mock-{s_id}"
                    ))
                elif archetype == "REGIONAL_FIBER_CUT":
                    is_cut = (day_offset >= 3)
                    stat = "VERIFIED_WAN_OFFLINE" if is_cut else "ONLINE"
                    dl = 0.0 if is_cut else 91.2
                    cat = "VERIFIED_ISP_WAN_OFFLINE" if is_cut else "HEALTHY_COMPLIANT"
                    measurements.append((
                        f"EVT-{s_id}-{date_str}-{hour:02d}", s_id, dt_iso, date_str, hour,
                        stat, "ETHERNET", 0, 1, 1.4, 1,
                        dl, dl * 0.7, 0.0 if is_cut else 28.5, 0.0 if is_cut else 3.8, 100.0 if is_cut else 0.0,
                        dl, 0.0 if is_cut else 91.2,
                        0, cat, 1 if is_cut else 0, 1 if is_cut else 0, f"sig-mock-{s_id}"
                    ))
                elif archetype == "RURAL_SATELLITE_WEATHER":
                    is_rain = (hour in (13, 14))
                    dl = 18.5 if is_rain else 46.2
                    measurements.append((
                        f"EVT-{s_id}-{date_str}-{hour:02d}", s_id, dt_iso, date_str, hour,
                        "ONLINE", "ETHERNET", 0, 1, 2.1, 1,
                        dl, dl * 0.4, 640.0 if is_rain else 85.0, 95.0 if is_rain else 18.5, 8.5 if is_rain else 0.0,
                        dl * 1.05, (dl / contracted_dl) * 100,
                        0, "RURAL_SATELLITE_WEATHER" if is_rain else "HEALTHY_COMPLIANT", 0, 0, f"sig-mock-{s_id}"
                    ))
                elif archetype == "CONGESTION_HIGH_JITTER":
                    is_midday = (11 <= hour <= 13)
                    dl = 42.0 if is_midday else 88.5
                    measurements.append((
                        f"EVT-{s_id}-{date_str}-{hour:02d}", s_id, dt_iso, date_str, hour,
                        "ONLINE", "ETHERNET", 0, 1, 1.3, 1,
                        dl, dl * 0.6, 52.0 if is_midday else 22.0, 38.0 if is_midday else 4.0, 2.0 if is_midday else 0.0,
                        dl, (dl / contracted_dl) * 100,
                        0, "MIDDAY_CONGESTION" if is_midday else "HEALTHY_COMPLIANT", 1 if is_midday else 0, 0, f"sig-mock-{s_id}"
                    ))
                elif archetype == "CHRONIC_PACKET_LOSS":
                    measurements.append((
                        f"EVT-{s_id}-{date_str}-{hour:02d}", s_id, dt_iso, date_str, hour,
                        "ONLINE", "ETHERNET", 0, 1, 1.2, 1,
                        34.0, 22.0, 75.0, 18.0, 12.5, 35.0, 34.0,
                        0, "CHRONIC_PACKET_LOSS", 1, 0, f"sig-mock-{s_id}"
                    ))
                elif archetype == "SLA_BREACH_UNDERDELIVERY":
                    measurements.append((
                        f"EVT-{s_id}-{date_str}-{hour:02d}", s_id, dt_iso, date_str, hour,
                        "ONLINE", "ETHERNET", 0, 1, 1.2, 1,
                        28.5, 18.0, 68.0, 12.0, 3.5, 29.0, 28.5,
                        0, "SLA_BREACH_UNDERDELIVERY", 1, 0, f"sig-mock-{s_id}"
                    ))
                else:  # HEALTHY_COMPLIANT
                    measurements.append((
                        f"EVT-{s_id}-{date_str}-{hour:02d}", s_id, dt_iso, date_str, hour,
                        "ONLINE", "ETHERNET", 0, 1, 1.1, 1,
                        96.4, 88.2, 18.2, 1.8, 0.0, 97.1, 96.4,
                        0, "HEALTHY_COMPLIANT", 0, 0, f"sig-mock-{s_id}"
                    ))

    cur.executemany("INSERT INTO measurements VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", measurements)

    # Seed SLA Violations in the HITL Approval Queue
    sla_violations_data = [
        (
            "VIOL-2026-104512-OCT",
            date.today().replace(day=1).isoformat(),
            "104512",
            "Bacoor National High School",
            "R04A",
            "DIV-CAVITE",
            "ISP-SPEEDNET",
            "SpeedNet Regional",
            "ISP_SELECTIVE_THROTTLING",
            5,
            14.2,
            95.8,
            100.0,
            12500.00,
            3125.00,  # 25% mandatory rebate tier = ₱3,125.00
            "Verified ISP Selective Traffic Shaping: Throughput to DepEd Cloud Anchor throttled to 14.2 Mbps during peak school hours (10 AM-2 PM) across 5 consecutive days, while public speedtests showed 95.8 Mbps. Local LAN verified healthy.",
            "Kumpirmadong selective throttling ng ISP: Bumabagsak sa 14.2 Mbps ang bilis sa DepEd Cloud tuwing 10 AM-2 PM sa loob ng 5 magkakasunod na araw habang 95.8 Mbps sa public speedtest. Walang sira sa loob ng school.",
            "# NOTICE OF SERVICE LEVEL AGREEMENT (SLA) BREACH & MANDATORY BILLING REBATE DEDUCTION\n\n**To:** SpeedNet Regional Legal & Billing Operations\n**Contract Ref:** DEPED-DCP-FIBER-R04A-2026\n**School:** Bacoor National High School (BEIS ID: 104512)\n\nUnder Republic Act No. 12009 (NGPA) and DepEd SLA Governance Rules, this office hereby issues formal notice of mandatory billing deduction:\n\n1. **Breach Finding:** Five (5) consecutive school days of selective bandwidth throttling during instructional hours (10:00 AM - 02:00 PM).\n2. **Local Hop Proof:** Admin PC local gateway latency was 1.25ms with 0.0% loss, proving the issue is entirely on the ISP distribution network.\n3. **Mandatory Rebate Deduction:** **PHP 3,125.00** (25% penalty tier) shall be deducted from the upcoming monthly statement of account.\n\n*Pending DITO Review & Executive Sign-off.*",
            "DEPED-INC-2026-4419",
            "PENDING_DITO_REVIEW",
            "agent-sla-auditor@deped-netpulse-prod.iam.gserviceaccount.com",
            None,
            None,
            datetime.now(timezone.utc).isoformat(),
        ),
        (
            "VIOL-2026-121405-OCT",
            date.today().replace(day=1).isoformat(),
            "121405",
            "Palo National High School",
            "R08",
            "DIV-LEYTE",
            "ISP-PLDT",
            "PLDT Enterprise",
            "REGIONAL_FIBER_CUT",
            3,
            0.0,
            0.0,
            100.0,
            12500.00,
            1875.00,
            "Verified 'PC-Online / WAN-Offline' state for 3 consecutive days. Local router responded with 1.4ms latency. Correlated with 24 schools in Leyte Division suffering a cut regional fiber backbone.",
            "Kumpirmadong walang internet sa loob ng 3 araw kahit buhay ang school router (1.4ms). Bahagi ito ng naputol na regional fiber backbone na nakaapekto sa 24 na paaralan sa Leyte.",
            "# NOTICE OF SERVICE LEVEL AGREEMENT (SLA) BREACH — EXTENDED OUTAGE REBATE\n\n**To:** PLDT Enterprise Government Accounts\n**School:** Palo National High School (BEIS ID: 121405)\n\n**Rebate Deduction:** **PHP 1,875.00** for verified 3-day outage during active school hours.",
            "DEPED-INC-2026-9012",
            "PENDING_DITO_REVIEW",
            "agent-sla-auditor@deped-netpulse-prod.iam.gserviceaccount.com",
            None,
            None,
            datetime.now(timezone.utc).isoformat(),
        ),
    ]
    cur.executemany("INSERT INTO sla_violations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", sla_violations_data)

    # Seed Zero-Touch Tickets with simulated Google Workspace alerts
    tickets_data = [
        (
            "DEPED-INC-2026-4419",
            "104512",
            "Bacoor National High School",
            "SpeedNet Regional",
            "P1_CRITICAL",
            "ISP Selective Throttling during School Hours (10:00 AM - 02:00 PM)",
            "Automated detection: 5 consecutive school days where DepEd Cloud Anchor speed dropped by 85% while public reference servers remained unthrottled. Local hop verified 100% healthy.",
            "Gemini 3.8 Flash Diagnosis: ISP Selective Traffic Shaping detected. Ticket auto-dispatched to SpeedNet NOC and Cavite DITO.",
            "Subject: [Zero-Touch NetPulse Alert] Trouble Ticket #DEPED-INC-2026-4419 Opened for Bacoor NHS\nFrom: netpulse-support@deped.gov.ph\nTo: noc@speednet.ph, dito.cavite@deped.gov.ph\n\nPlease find attached the 5-day Dual-Probe verification log.",
            json.dumps({
                "header": "🚨 Zero-Touch SLA Breach Detected",
                "school": "Bacoor NHS (104512)",
                "isp": "SpeedNet Regional",
                "finding": "Throughput drops to 14.2 Mbps from 10 AM to 2 PM (Local Ethernet OK)",
                "action": "₱3,125.00 rebate deduction queued for DITO approval",
            }),
            datetime.now(timezone.utc).isoformat(),
        ),
        (
            "DEPED-INC-2026-9012",
            "121405",
            "Palo National High School",
            "PLDT Enterprise",
            "P0_EMERGENCY",
            "Cluster Outage: 24 Schools Offline in Leyte Division (Regional Fiber Cut)",
            "Vertex AI cluster correlation flagged 24 schools reporting 'PC-Online / WAN-Offline' simultaneously. Suppressed 24 individual tickets into 1 Master Regional Ticket.",
            "Gemini 3.8 Flash Diagnosis: Regional Fiber Backbone Severed. Master Regional Ticket filed with PLDT Executive NOC.",
            "Subject: [P0 MASTER EMERGENCY] Cluster Fiber Cut in Leyte Division (24 Schools Affected)\nFrom: netpulse-support@deped.gov.ph\nTo: enterprise.noc@pldt.com.ph, rito.r08@deped.gov.ph",
            json.dumps({
                "header": "🔴 Master Cluster Outage: 24 Schools Offline",
                "region": "Region VIII (Leyte Division)",
                "isp": "PLDT Enterprise",
                "root_cause": "Regional Fiber Backbone Severed at Palo Junction",
            }),
            datetime.now(timezone.utc).isoformat(),
        ),
    ]
    cur.executemany("INSERT INTO zero_touch_tickets VALUES (?,?,?,?,?,?,?,?,?,?,?)", tickets_data)

    # Seed Initial Audit Trail
    cur.execute("""
        INSERT INTO agent_audit_trail VALUES (
            'AUDIT-001', 'TICKET_AUTO_DISPATCH', 'AGENT',
            'agent-sla-auditor@deped-netpulse-prod.iam.gserviceaccount.com',
            'DEPED-INC-2026-4419', 'Dispatched Zero-Touch P1 Trouble Ticket & Google Workspace Card',
            datetime('now')
        )
    """)

    conn.commit()


# Ensure DB is created on import
init_db()
