# Department of Education (DepEd) — Google Cloud & Gemini Enterprise Solutions Repository

[![Agency](https://img.shields.io/badge/Agency-Department_of_Education_(DepEd)-blue.svg)](#)
[![Structure](https://img.shields.io/badge/Repo_Structure-Per_Use--Case_Directory-green.svg)](#)
[![Platform](https://img.shields.io/badge/Platform-Google_Cloud_%7C_Gemini_Enterprise-orange.svg)](#)

Welcome to the central **Department of Education (DepEd)** solutions repository. 

This repository is structured on a **per-use-case basis**, where each top-level folder contains the self-contained Business Requirements Documents (BRDs), Technical Design Documents (TDDs), architectural blueprints, and reference implementations for a specific DepEd digital transformation initiative.

---

## 📂 Active Use-Case Directories

| Use-Case Folder | Initiative / Solution Name | Overview | Documentation |
| :--- | :--- | :--- | :--- |
| [**`nw-speed-tracker/`**](./nw-speed-tracker/) | **National Network Speed Tracker & Autonomous ISP SLA Governance Platform** | Decoupled, push-based internet telemetry and autonomous ISP contract SLA auditing across **47,000+ public schools** using Google Cloud (`Pub/Sub`, `Cloud Run`, `BigQuery`, `Looker`) and **Gemini Enterprise** (Conversational Analytics, ISP SLA Auditor Agent, Grounded Diagnostics, and 47k Locust Simulation). | • [Overview (`README.md`)](./nw-speed-tracker/README.md)<br/>• [BRD (`v2.0`)](./nw-speed-tracker/01_DEPED_NW_SPEED_TRACKER_BRD.md)<br/>• [Production TDD (`v2.0`)](./nw-speed-tracker/02_DEPED_NW_SPEED_TRACKER_TDD.md)<br/>• [Prototype & Demo TDD (`v1.0`)](./nw-speed-tracker/03_DEPED_NW_SPEED_TRACKER_PROTOTYPE_DEMO_TDD.md) |

---

## 🧭 Repository Conventions

Each use-case directory follows a standardized structure:
1. **`README.md`** — Executive overview and quick index for the specific use case.
2. **`01_*_BRD.md`** — Business Requirements Document (statutory alignment, functional/non-functional requirements, stakeholder RBAC personas, and KPIs).
3. **`02_*_TDD.md`** — Technical Design Document (system architecture, data schemas, Gemini Enterprise agent specifications, and deployable code/scripts).
4. **Reference Documents & Prototypes** — Foundational PDFs, simulation scripts, and proof-of-concept application code.
