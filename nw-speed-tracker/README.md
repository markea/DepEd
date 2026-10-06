# DepEd National Network Speed Tracker & Autonomous ISP SLA Governance Platform

[![Status](https://img.shields.io/badge/Status-BRD_v2.0_Hardened_%26_TDD_v1.0-blue.svg)](#)
[![Scale](https://img.shields.io/badge/Scale-47%2C000%2B_Public_Schools_(Zero_Hardware_CapEx)-green.svg)](#)
[![Platform](https://img.shields.io/badge/Platform-Google_Cloud_%7C_Gemini_Enterprise-orange.svg)](#)

Decoupled, push-based national internet telemetry and autonomous ISP contract governance architecture for the **Department of Education (DepEd)** across **47,000+ public elementary and secondary schools** in the Philippines.

---

## 📌 Executive Overview

Attempting to centrally ping or speed-test 47,000 distributed schools from a single central server saturates central bandwidth, yields inaccurate latency metrics, and triggers ISP DDoS protections. Furthermore, procuring 47,000 dedicated hardware probes requires additional budget, while raw speed test rows alone cannot withstand telco SLA disputes or empower non-technical school principals.

This solution combines a **Zero-Hardware-CapEx software agent on existing DepEd Computerization Program (DCP) Administrative PCs** and a **decoupled Google Cloud telemetry pipeline** (`API Gateway` $\rightarrow$ `Cloud Pub/Sub` $\rightarrow$ `Cloud Run Serverless Enrichment` $\rightarrow$ `BigQuery`) with **Gemini Enterprise** to transform raw networking metrics into dispute-proof ISP SLA rebates, plain-language diagnostics, and bilingual conversational analytics.

---

## 📑 Documentation Index (`nw-speed-tracker`)

| Document | Description | Format |
| :--- | :--- | :--- |
| [**01_DEPED_NW_SPEED_TRACKER_BRD.md**](./01_DEPED_NW_SPEED_TRACKER_BRD.md) | **Business Requirements Document (`v2.0` Hardened Baseline):** Incorporates all 8 locked architectural & governance decisions: Zero-CapEx DCP Admin PC OS Service, `PC-Online / WAN-Offline` outage attribution during active school hours (`7 AM–5 PM`), local Wi-Fi RSSI vs. WAN disambiguation, Dual-Probe anti-gaming speed test anchors, Hybrid Tiered UI (`Looker + Gemini Enterprise` for Tier 1/2 + zero-license-cost `Cloud Run School Portal` for Tier 3), Split Governance (Zero-Touch Ticketing + HITL Financial Rebates), and Multi-Channel ITSM + Google Workspace dispatch. | Markdown |
| [**02_DEPED_NW_SPEED_TRACKER_TDD.md**](./02_DEPED_NW_SPEED_TRACKER_TDD.md) | **Technical Design Document (TDD):** End-to-end architecture, signed JSON payload schema, edge agent reference scripts with jitter & offline SQLite spooling, Cloud Run enricher, BigQuery partitioned/clustered DDLs & RLS policies, LookML bilingual semantic model, Gemini Enterprise **ISP SLA Auditor Agent**, Vertex AI anomaly detection, and 47,000-node Locust + Gemini synthetic simulator. | Markdown |
| [**Deped Network Speed Tracker.pdf**](./Deped%20Network%20Speed%20Tracker.pdf) | Foundational architecture and simulation strategy reference document. | PDF |

---

## 🚀 Key Architectural & Governance Decisions (`BRD v2.0`)

1. **Zero-Hardware-CapEx Edge Footprint (DCP Admin PCs):**
   - Packaged as a tamper-resistant background **OS Service** (Windows `.msi` service + Linux `systemd` daemon) deployed via Microsoft Intune/GPO or a 1-click Division Enrollment Installer—requiring **$0 in new router or Raspberry Pi hardware**.
2. **Dispute-Proof Outage & Wi-Fi Attribution:**
   - Restricted strictly to **Active School Hours (`Mon–Fri, 7:00 AM – 5:00 PM PHT`)** with **3–4 staggered tests/day** ($1 - 900\text{s}$ jitter) and payload caps for metered LTE/Satellite links.
   - Captures **Local Hop Diagnostics** (`Ethernet` vs. `Wi-Fi RSSI`, local gateway ping/loss) before every WAN test. Outages are attributed to the ISP only when **`PC-Online / WAN-Offline`** is verified (`local_gateway_reachable = TRUE` while WAN is down), spooling signed records locally for post-outage delivery.
3. **Dual-Probe Anti-Gaming Speed Test Architecture:**
   - Tests primary throughput against **DepEd-Hosted Cloud Anchors** (real educational cloud traffic) alongside secondary checks against public reference servers (`Ookla CLI` / `M-Lab`) to expose ISP speedtest whitelisting and selective traffic shaping.
4. **Hybrid 3-Tier UI & Licensing Optimization:**
   - **Tier 1 (Central Office) & Tier 2 (17 Regions / 220+ Divisions):** Full **Looker + Gemini Enterprise** (Bilingual English/Tagalog Conversational Analytics & Agent Workspace).
   - **Tier 3 (47,000 School Principals):** Lightweight **Cloud Run School Web Portal** via `@deped.gov.ph` Google Workspace SSO at **$0 per-seat BI license cost**, featuring school charts, plain-English/Tagalog Gemini diagnostic cards, and downloadable PDF Speed Test Certificates.
5. **Split Autonomous Governance & Multi-Channel Dispatch:**
   - **Zero-Touch Autonomous Execution** for technical trouble tickets via **DepEd ICTS Helpdesk / ITSM + Automated Google Workspace (Gmail & Google Chat)** alerts to the ISP NOC, DITO, and Principal.
   - **Mandatory Human-in-the-Loop (HITL) Sign-Off** for financial **ISP SLA Rebate Deductions** (Agent computes PHP rebates and drafts COA-ready memos; ICTS / Division Officer approves before billing deduction).
