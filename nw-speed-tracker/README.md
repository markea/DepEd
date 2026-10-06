# DepEd National Network Speed Tracker & Autonomous ISP SLA Governance Platform

[![Status](https://img.shields.io/badge/Status-Architecture_%26_Solution_Design-blue.svg)](#)
[![Scale](https://img.shields.io/badge/Scale-47%2C000%2B_Public_Schools-green.svg)](#)
[![Platform](https://img.shields.io/badge/Platform-Google_Cloud_%7C_Gemini_Enterprise-orange.svg)](#)

Decoupled, push-based national internet telemetry and autonomous ISP contract governance architecture for the **Department of Education (DepEd)** across **47,000+ public elementary and secondary schools** in the Philippines.

---

## 📌 Executive Overview

Attempting to centrally ping or speed-test 47,000 distributed schools from a single central server saturates central bandwidth, yields inaccurate latency metrics, and triggers ISP DDoS protections. Furthermore, collecting millions of daily telemetry rows is only valuable if non-technical school principals, division superintendents, and central office administrators can translate that data into immediate repairs and enforceable **ISP Service Level Agreement (SLA) rebates**.

This solution combines a **decoupled Google Cloud telemetry pipeline** (`Edge Agents with Jitter` $\rightarrow$ `API Gateway` $\rightarrow$ `Cloud Pub/Sub` $\rightarrow$ `Cloud Run Serverless Enrichment` $\rightarrow$ `BigQuery` $\rightarrow$ `Looker`) with **Gemini Enterprise** to transform raw networking metrics into conversational intelligence and autonomous contract enforcement.

---

## 📑 Documentation Index (`nw-speed-tracker`)

| Document | Description | Format |
| :--- | :--- | :--- |
| [**01_DEPED_NW_SPEED_TRACKER_BRD.md**](./01_DEPED_NW_SPEED_TRACKER_BRD.md) | **Business Requirements Document (BRD):** Statutory mandate (DCP, RA 10929, RA 12009, RA 10173), problem analysis, 5 Gemini Enterprise acceleration pillars, 3-Tier RBAC personas, SLA rebate calculation matrix, and functional/non-functional requirements. | Markdown |
| [**02_DEPED_NW_SPEED_TRACKER_TDD.md**](./02_DEPED_NW_SPEED_TRACKER_TDD.md) | **Technical Design Document (TDD):** End-to-end architecture, signed JSON payload schema, Python & MikroTik RouterOS edge scripts with jitter & offline SQLite spooling, Cloud Run enricher, BigQuery partitioned/clustered DDLs & RLS policies, LookML bilingual semantic model, Gemini Enterprise **ISP SLA Auditor Agent**, Vertex AI anomaly detection, and 47,000-node Locust + Gemini synthetic simulator. | Markdown |
| [**Deped Network Speed Tracker.pdf**](./Deped%20Network%20Speed%20Tracker.pdf) | Foundational architecture and simulation strategy reference document. | PDF |

---

## 🚀 Key Architectural & Gemini Enterprise Capabilities

### 1. Decoupled Push-Based Edge Telemetry with Jitter
- **Lightweight Edge Agents:** Runs on existing school MikroTik routers, Raspberry Pis, or administrative PCs using `Ookla Speedtest CLI` or `iperf3`.
- **Staggered Execution (Jitter):** Applies a randomized $1 - 900\text{s}$ ($15\text{–}30\text{ min}$) delay window before testing to prevent 47,000 schools from artificially congesting national routing at the top of the hour.
- **Offline Spooling & Backoff:** Queues failed/offline tests locally during outages and flushes historical payloads with preserved `measured_at` timestamps upon reconnection.

### 2. High-Concurrency Cloud Ingestion & Time-Series Warehouse
- **API Gateway & Cloud Pub/Sub:** Absorbs simultaneous post-outage reconnect bursts from thousands of schools without data loss.
- **Serverless Enrichment (Cloud Run):** Verifies HMAC-SHA256 anti-spoofing signatures and enriches payloads with Region, Division, ISP, and Contracted Bandwidth metadata.
- **BigQuery Time-Series Warehouse:** Partitioned by `DATE(measured_at)` and clustered by `region_id, division_id, isp_id, school_id` (optimized with **Gemini in BigQuery**).

### 3. Hierarchical 3-Tier Dashboard & Conversational Analytics
- **National View (Central Office):** Philippines GIS heatmap, total offline schools, national actual vs. contracted bandwidth, and ISP SLA compliance scorecards.
- **Division / Regional View (Superintendents):** Provincial cluster outage detection (e.g., cut regional fiber backbone) and underperforming district watchlists.
- **School Level View (Principals & School IT):** Daily/hourly performance curves proving school-hour bandwidth drops ($10\text{ AM} - 2\text{ PM}$) to ISPs.
- **Conversational Analytics (Gemini in Looker):** Enables non-technical staff to ask questions in plain **English or Tagalog/Taglish** and receive instant charts.

### 4. Autonomous Operationalization & Grounded Diagnostics (Gemini Enterprise)
- **ISP SLA Auditor Agent (Agent Designer):** Continuously monitors BigQuery for schools reporting $<50\%$ contracted bandwidth for 3 consecutive days (or total offline status), calculates statutory PHP rebate penalties, and drafts formal ISP dispute notices.
- **Support Desk Connector:** Automatically opens and tracks trouble tickets in ServiceNow, Jira, or the DepEd ICTS Helpdesk.
- **Grounded Root Cause Diagnostics & Vertex AI Anomaly Detection:** Translates raw packet loss, jitter, and ping anomalies into plain-language guidance for school principals while distinguishing local router faults from regional fiber cuts.
- **Enterprise RBAC, Sovereignty & Audit Trails:** Enforces BigQuery Row-Level Security (RLS) down to the individual school level and logs a distinct `agent_identity` audit trail for every autonomous action.
