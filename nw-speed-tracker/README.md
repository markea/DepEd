# DepEd National Network Speed Tracker & Autonomous ISP SLA Governance Platform

[![Status](https://img.shields.io/badge/Status-BRD_v2.0_%26_TDD_v2.0_Hardened-blue.svg)](#)
[![Scale](https://img.shields.io/badge/Scale-47%2C000%2B_Public_Schools_(Zero_Hardware_CapEx)-green.svg)](#)
[![AI Models](https://img.shields.io/badge/AI-Gemini_3.8_Flash_%26_Gemini_3.1_Pro-orange.svg)](#)

Decoupled, push-based national internet telemetry and autonomous ISP contract governance architecture for the **Department of Education (DepEd)** across **47,000+ public elementary and secondary schools** in the Philippines.

---

## 📌 Executive Overview

Attempting to centrally ping or speed-test 47,000 distributed schools from a single central server saturates central bandwidth, yields inaccurate latency metrics, and triggers ISP DDoS protections. Furthermore, procuring 47,000 dedicated hardware probes requires additional budget, while raw speed test rows alone cannot withstand telco SLA disputes or empower non-technical school principals.

This solution combines a **Zero-Hardware-CapEx Go static binary service on existing DepEd Computerization Program (DCP) Administrative PCs** and a **decoupled Google Cloud telemetry pipeline** (`API Gateway` $\rightarrow$ `Cloud Pub/Sub` $\rightarrow$ `Cloud Run 25MB In-Memory Enricher` $\rightarrow$ `Date-Partitioned BigQuery`) with **Gemini Enterprise (`Gemini 3.8 Flash` & `Gemini 3.1 Pro`)** to transform raw networking metrics into dispute-proof ISP SLA rebates, plain-language diagnostics, and bilingual conversational analytics.

---

## 📑 Documentation Index (`nw-speed-tracker`)

| Document | Description | Format |
| :--- | :--- | :--- |
| [**01_DEPED_NW_SPEED_TRACKER_BRD.md**](./01_DEPED_NW_SPEED_TRACKER_BRD.md) | **Business Requirements Document (`v2.0` Hardened Baseline):** Incorporates all 8 locked business & governance decisions: Zero-CapEx DCP Admin PC OS Service, `PC-Online / WAN-Offline` outage attribution during active school hours (`7 AM–5 PM`), local Wi-Fi RSSI vs. WAN disambiguation, Dual-Probe anti-gaming speed test anchors, Hybrid Tiered UI (`Looker + Gemini Enterprise` for Tier 1/2 + zero-license-cost `Cloud Run School Portal` for Tier 3), Split Governance (Zero-Touch Ticketing + HITL Financial Rebates), and Multi-Channel ITSM + Google Workspace dispatch. | Markdown |
| [**02_DEPED_NW_SPEED_TRACKER_TDD.md**](./02_DEPED_NW_SPEED_TRACKER_TDD.md) | **Technical Design Document (`v2.0` Hardened Baseline):** Incorporates all 7 locked engineering specifications: Zero-dependency **Go static binary** (`<10MB` RAM), **Per-Device DPAPI/Keystore enrollment & Ed25519 signed auto-updates**, **Serverless HTTPS/WSS Dual-Probe** (DepEd Cloud Run Anchor + M-Lab NDT7/Ookla), **25 MB In-Memory Cloud Run registry cache** ($0 Redis cost), **strict Date/Time-Partitioned BigQuery tables & materialized views**, **Cost-Guarded Tier 3 School Portal**, **Gemini 3.8 Flash & Gemini 3.1 Pro** agent workflows with **HITL Rebate State Machine**, and **Dual-Target 47k Locust Simulator** (Cloud Run Jobs + GKE Autopilot). | Markdown |
| [**Deped Network Speed Tracker.pdf**](./Deped%20Network%20Speed%20Tracker.pdf) | Foundational architecture and simulation strategy reference document. | PDF |

---

## 🚀 Key Architectural & Engineering Highlights (`BRD v2.0` & `TDD v2.0`)

1. **Zero-CapEx Go Static Agent on DCP Admin PCs:**
   - Single zero-dependency Go binary (`deped-netpulse-agent.exe`, `<10MB` RAM) running as a Windows Service (`.msi`) or Linux `systemd` daemon with per-device HMAC keys stored in **Windows DPAPI** and **Ed25519-signed** atomic binary updates via Cloud CDN.
2. **Dispute-Proof Outage & Local Wi-Fi Disambiguation:**
   - Runs strictly during **Active School Hours (`Mon–Fri, 7:00 AM – 5:00 PM PHT`)** with **3–4 staggered tests/day** ($1 - 900\text{s}$ jitter).
   - Probes **Local Hop Health** (`Ethernet` vs. `Wi-Fi RSSI`, local router gateway `192.168.x.1` reachability & ping) prior to every **Dual-Probe WAN Test** (DepEd Cloud Run Anchor + M-Lab NDT7 / Ookla over HTTPS/WSS).
3. **Zero-Idle-Cost Enrichment & Strictly Date-Partitioned BigQuery Warehouse:**
   - Caches the entire 47,000-school registry (`~25 MB`) in Cloud Run RAM (5-min TTL refresh) without paying for an always-on Redis cluster.
   - All BigQuery tables (`speedtest_measurements`, `sla_violation_ledger`, `agent_audit_trail`) and Materialized Views (`mv_school_daily_rollups`) enforce **Date/Time Partitioning (`require_partition_filter = TRUE`)** and hierarchical clustering (`region_id, division_id, isp_id, school_id`).
4. **Gemini 3.8 Flash & Gemini 3.1 Pro Operationalization:**
   - **`Gemini 3.8 Flash`:** Powers event-driven bilingual (English & Tagalog) Grounded Root-Cause Diagnostic cards, Tier 3 School Portal Q&A, and synthetic scenario generation.
   - **`Gemini 3.1 Pro`:** Powers the **Autonomous ISP SLA Auditor Agent** and COA-ready Rebate Dispute Memo generator, governed by **Zero-Touch Technical Ticketing** (ITSM + Google Workspace Gmail/Chat) and a **Human-in-the-Loop (HITL) Financial Rebate Approval State Machine**.
