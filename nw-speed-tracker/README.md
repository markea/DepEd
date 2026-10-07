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
| [**03_DEPED_NW_SPEED_TRACKER_PROTOTYPE_DEMO_TDD.md**](./03_DEPED_NW_SPEED_TRACKER_PROTOTYPE_DEMO_TDD.md) | **Interactive Full-Stack Prototype & Demo TDD (`v1.0`):** Engineering blueprint for the self-contained FastAPI + 5-Tab Web Showcase (Localhost & Google Cloud Run) featuring the 17-Region Philippines Heatmap, Dual-Probe Anti-Gaming Leaderboard, Tier 3 Principal Portal with QR-verifiable PDF Speed Certificates, Bilingual `Gemini 3.8 Flash` Conversational Analytics, `Gemini 3.1 Pro` HITL Rebate Queue, and live 47k Chaos Simulator. | Markdown |
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

---

## 🌐 Live Prototype Demo & Cloud Run Deployment

An interactive, full-stack demonstration prototype is deployed and running on Google Cloud Platform:

| Property | Details |
| :--- | :--- |
| **GCP Project** | `deped-demos-01` |
| **GCP Region** | `asia-southeast1` (Singapore) |
| **Cloud Run Service** | `deped-netpulse-demo` |
| **Live Service URL** | [`https://deped-netpulse-demo-948357328216.asia-southeast1.run.app`](https://deped-netpulse-demo-948357328216.asia-southeast1.run.app) |
| **Source Directory** | [`demo-app/`](./demo-app/) |
| **AI Models Active** | `gemini-3.8-flash` (Conversational Analytics & Diagnostics) + `gemini-3.1-pro` (ISP SLA Auditor) |
| **Geospatial Analytics** | Native **Google Maps Platform** (`maps.googleapis.com` JavaScript API + Visualization Library `google.maps.visualization.HeatmapLayer` with custom dark theme) featuring dual-layer modes (Heat Density Cloud vs. Individual Outage Pins & CIR Circles), 18 seeded showcase schools with precise coordinates, and 1-click School Portal drilldown. |
| **Pre-Seeded Data** | **47,000 public schools** across **17 Philippine administrative regions**, 5 major ISPs (PLDT, Globe, Converge, SpeedNet, Starlink), and 5 days of hourly school-hours telemetry. |

### How to Access the Live Demo

Because the Cloud Run service is secured within the Google Cloud organization policy of `deped-demos-01`, access the live web application using either of the following methods:

#### Option A: Direct Web Browser Access (Authorized Google Account)
Open [`https://deped-netpulse-demo-948357328216.asia-southeast1.run.app`](https://deped-netpulse-demo-948357328216.asia-southeast1.run.app) in your browser while signed into your authorized Google account (`admin@markea.altostrat.com` or authorized domain member).

#### Option B: Cloud Run Services Proxy (Local Port-Forwarding)
Run the `gcloud run services proxy` command in your terminal to create an authenticated local tunnel:
```bash
gcloud run services proxy deped-netpulse-demo \
  --region=asia-southeast1 \
  --project=deped-demos-01 \
  --port=8080
```
Then navigate to:
```
http://localhost:8080
```

#### Option C: Run Locally (Standalone Container / Python Script)
You can also launch the full prototype locally in one command:
```bash
cd demo-app
./run_demo.sh
```
Or with Docker:
```bash
cd demo-app
docker build -t deped-netpulse-demo .
docker run -p 8080:8080 -e DEMO_ENV=LOCAL deped-netpulse-demo
```

