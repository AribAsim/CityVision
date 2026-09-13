# CityVision — Mobile Urban Sensing & Road Anomaly Monitoring Platform

> *"Every Bus a Sensor. Every Road a Safer Path."*

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF.svg)](https://github.com/ultralytics/ultralytics)
[![Leaflet](https://img.shields.io/badge/Leaflet-GIS%20Mapping-199900.svg?logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![Tests](https://img.shields.io/badge/tests-78%20passing-brightgreen.svg)](#-automated-testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**CityVision** (Smart India Hackathon — Problem Statement SIH26124) transforms routine public transit buses into intelligent, mobile urban sensing units. Dashcam sensors mounted on public buses continuously detect road surface anomalies (potholes, cracks, speed bumps), vehicle license plates, and traffic infrastructure signs, then GPS-tag, cross-correlate, and escalate verified road hazards to a municipal command center — automatically.

---

## Table of Contents

- [What CityVision Does](#what-cityvision-does)
- [System Architecture](#system-architecture)
- [Key Features](#key-features)
- [Repository Structure](#repository-structure)
- [Machine Learning Models](#machine-learning-models)
- [Quick Start Guide](#quick-start-guide-for-beginners)
- [Edge CLI Runner](#edge-cli-runner)
- [Automated Testing](#automated-testing)
- [REST API Reference](#rest-api-reference)
- [Architecture and Governance Docs](#architecture-and-governance-docs)
- [License](#license)

---

## What CityVision Does

Traditional road maintenance relies on expensive physical surveys or slow citizen grievance queues. **CityVision replaces this reactive model** with continuous, automated, multi-vehicle sensing:

1. **Passive Edge Capture** — City buses traverse scheduled routes while AI models analyze dashcam footage in real time.
2. **Physical Anomaly Tracking** — Kalman filtering (ByteTrack) + a post-track trajectory stitcher collapse hundreds of frame detections into a single cohesive defect identity.
3. **ANPR and Traffic Infrastructure Detection** — Concurrently detects Indian license plates via EasyOCR + YOLOv8n, and traffic signs via YOLOv8s, persisting them alongside each road anomaly event.
4. **Multi-Bus Spatial Consensus** — Multiple buses passing the same GPS coordinate (<=15 m) automatically corroborate observations, escalating severity from NEW to VERIFIED.
5. **Command Center Operations** — Civil engineers prioritize repair backlogs via a dynamic risk-scoring dashboard, interactive Leaflet GIS maps, downloadable PDF work orders, and a fully audited lifecycle state machine.

---

## System Architecture

```
[ Public Bus Dashcam / MP4 Video ]
                |
                v
+--------------------------------------------------------------+
| 1. EDGE INTELLIGENCE PIPELINE  (edge/)                       |
|    +-- Road Anomaly Detector   YOLOv8m  (Pothole/Crack/Bump) |
|    +-- Vehicle Detector        YOLOv8n  (Car/Truck/VRU)      |
|    +-- ANPR Pipeline           YOLOv8n  + EasyOCR            |
|    +-- Infra Sign Detector     YOLOv8s  (Traffic Signs)      |
|    +-- ByteTrack + Stitcher    (Frame->Track->Physical Defect)|
|    +-- GPS & Bus Fleet Sims    (Delhi transit corridors)      |
|    +-- Event Builder           (Best-frame crop + JSON v2)   |
+--------------------------------------------------------------+
                | HTTP POST /api/ingest (multipart + JSON)
                v
+--------------------------------------------------------------+
| 2. CENTRAL BACKEND SERVICE  (backend/)                       |
|    +-- FastAPI Async App       (OpenAPI docs at /docs)       |
|    +-- 15m Haversine Cluster   (Spatial deduplication)       |
|    +-- Multi-Bus Escalation    (Auto NEW->VERIFIED->CRITICAL)|
|    +-- Persistence Layer       (Incident/PlateRead/InfraObs) |
|    +-- PDF Work Order Engine   (ReportLab, no GTK deps)      |
|    +-- Background Scan Jobs    (/api/scan)                   |
|    +-- SQLite -> PostgreSQL    (via Alembic migrations)      |
+--------------------------------------------------------------+
                | REST API / 4s polling (JSON)
                v
+--------------------------------------------------------------+
| 3. COMMAND CENTER DASHBOARD  (frontend/)                     |
|    +-- Command Center (Home)   KPIs, PCI gauge, live HUD     |
|    +-- Live Detection          Scan trigger, progress feed   |
|    +-- Geospatial Road Map     Leaflet GIS, severity pins    |
|    +-- Reports & Work Orders   Triage table, PDF download    |
|    +-- Bus Fleet Telemetry     Real-time routes & GPS        |
|    +-- Analytics & KPIs       Recharts defect breakdown      |
+--------------------------------------------------------------+
```

---

## Key Features

### Edge Intelligence Pipeline

| Feature | Detail |
|---|---|
| Road Anomaly Detection | Custom YOLOv8m — mAP@0.5: 0.745 on Indian roads |
| Indian ANPR | YOLOv8n plate detector + EasyOCR text recognition |
| Traffic Sign Detection | YOLOv8s infra model (demo; IS:1179 weights ready to swap in) |
| Vehicle Detection | YOLOv8n — 9.2 FPS on CPU |
| Physical Tracking | supervision.ByteTrack, 30-frame buffer, 2-frame gate |
| Post-Track Stitcher | Trajectory extrapolation across <=15 frame dropouts |
| Event Buffering | ANPR & sign detections buffered per frame, attached to event JSON v2 |
| Lineage Audit | scripts/audit_lineage.py — raw detections to incidents contact sheets |

### Central Platform

| Feature | Detail |
|---|---|
| Spatial Clustering | 15m Haversine — collapses successive bus passes into one incident |
| Spam Guard | 2.0s per-vehicle cooldown on duplicate frame events |
| Multi-Bus Escalation | unique_bus_count >= 2 triggers severity +1 tier, status -> VERIFIED |
| Priority Scoring | 0-100 formula (confidence + area + recurrence + bus count) |
| ANPR Persistence | PlateRead table — plate text, confidence, GPS, nullable incident link |
| Infra Persistence | InfraObservation table — class, confidence, GPS, route, message_id |
| PDF Work Orders | ReportLab-based PDF at GET /api/incidents/{id}/report.pdf |
| Idempotency | message_id dedup on Observation, PlateRead, InfraObservation |
| Optional Scale-Up | Alembic migrations to TimescaleDB/PostGIS, MinIO S3, Mosquitto MQTT |

### Command Center Frontend

| Feature | Detail |
|---|---|
| Design System | Municipal Sentinel Modern — Space Grotesk, Inter, JetBrains Mono |
| 6 Operational Views | Home, Live Detection, Road Map, Reports, Bus Fleet, Analytics |
| PCI Gauge | Radial SVG Pavement Condition Index (ASTM D6433 adaptation) |
| Scan Manager | Global persistent scan — survives tab switches, shows live events |
| ANPR Badge | Indian Plate subsystem status badge in Live Detection view |
| PDF Download | One-click work order PDF from Reports and Detail Drawer |
| GIS Map | Leaflet with Delhi route polylines, severity-coloured pins, popups |

---

## Repository Structure

```
sih2026-mvp/
+-- backend/                             FastAPI backend service
|   +-- app/
|   |   +-- routers/                     API endpoints (incidents, scan, buses, ingest, analytics)
|   |   +-- services/
|   |   |   +-- deduplication.py         Haversine + PostGIS spatial clustering
|   |   |   +-- event_fusion.py          Ingestion -> PlateRead / InfraObservation persistence
|   |   |   +-- severity.py              Rule-based severity & priority scoring
|   |   |   +-- analytics_engine.py      PCI (ASTM D6433) + near-miss telemetry
|   |   |   +-- minio_storage.py         MinIO S3 with local disk fallback
|   |   |   +-- pdf_report.py            ReportLab PDF work order generator
|   |   +-- database.py                  SQLAlchemy engine & session factory
|   |   +-- models.py                    Incident, Observation, PlateRead, InfraObservation, Bus
|   |   +-- schemas.py                   Pydantic v2 request/response schemas
|   |   +-- main.py                      FastAPI entrypoint + CORS + static mount
|   +-- static/snapshots/                Anomaly evidence crop storage
|   +-- requirements.txt
|
+-- edge/                                Edge detection & vehicle simulation
|   +-- detector.py                      YOLOv8m road anomaly inference wrapper
|   +-- vehicle_detector.py              YOLOv8n vehicle/VRU inference wrapper
|   +-- infra_detector.py                YOLOv8s traffic sign inference wrapper
|   +-- anpr/
|   |   +-- plate_detector.py            YOLOv8n plate region detector
|   |   +-- ocr_engine.py                EasyOCR text recognition engine
|   |   +-- anpr_pipeline.py             Combined plate detect + OCR pipeline
|   +-- anomaly_tracker.py               ByteTrack Kalman filter tracker
|   +-- track_stitcher.py                Post-track spatial/temporal stitcher
|   +-- bus_simulator.py                 Fleet vehicle simulator (BUS-01/02/03)
|   +-- gps_simulator.py                 Delhi GPS corridor interpolator
|   +-- event_builder.py                 Track->event packaging (JSON v2 schema)
|   +-- runner.py                        Edge CLI runner with --benchmark flags
|
+-- frontend/                            React 18 + Vite + TypeScript dashboard
|   +-- src/
|   |   +-- components/
|   |   |   +-- Navigation/              Sidebar & TopHeader
|   |   |   +-- Views/                   6 operational views
|   |   |   +-- DetailDrawer/            Incident details, observation feed, PDF button
|   |   |   +-- GisMap/                  Leaflet interactive map
|   |   |   +-- BusScan/                 Video scan modal & trigger
|   |   +-- hooks/                       useScanManager, useIncidents, useBuses, useAnalytics
|   |   +-- services/                    API client & seed data fallback
|   |   +-- types/                       TypeScript data contracts
|   +-- package.json
|   +-- vite.config.ts
|
+-- RoadDetectionModel/                  AI model weights
|   +-- RoadModel_yolov8m.pt_rounds120_b9/
|   |   +-- weights/best.pt              Road anomaly model (52 MB, mAP@0.5: 0.745)
|   +-- ANPRPlateDetector_yolov8n/
|   |   +-- weights/best.pt              Indian plate detector (6.2 MB)
|   +-- TrafficInfraModel_yolov8s/
|       +-- weights/best.pt              Traffic sign model (22.6 MB, demo fallback)
|
+-- alembic/                             Database migration scripts
|   +-- versions/001_initial_postgres.py Full DDL: all tables + PostGIS geometries
|
+-- brain/                               Architecture ground-truth docs
|   +-- 00_PROJECT_CONTEXT.md
|   +-- 03_SYSTEM_ARCHITECTURE.md
|   +-- 04_DATA_CONTRACTS.md
|   +-- 05_API_CONTRACT.md
|   +-- 07_EVENT_ENGINE.md
|   +-- 11_IMPLEMENTATION_STATUS.md      Comprehensive verification report
|
+-- demo/                                Live evaluator demo suite
|   +-- scenario.json                    Deterministic multi-bus incident timeline
|   +-- run_demo.py                      Interactive demo orchestrator
|
+-- scripts/                             Offline evaluation & verification
|   +-- audit_lineage.py                 Raw detection -> incident lineage audit
|   +-- download_models.py               Model weight download helper
|   +-- inspect_merges.py                Track stitcher trajectory analysis
|   +-- measure_stitching.py             Stitching performance benchmark
|
+-- tests/                               Automated test suite (78 tests, 100% pass)
|   +-- test_edge_pipeline.py            Edge tracker, stitcher, GPS, ANPR tests
|   +-- test_scan_router.py              Video scan job dispatch & status API
|   +-- test_integration_full.py         End-to-end pipeline & multi-bus fusion
|
+-- docker-compose.yml                   Optional: TimescaleDB, MinIO, Mosquitto
+-- .env.example                         Environment flags & feature toggles
+-- alembic.ini                          Alembic DB migration config
+-- README.md
```

---

## Machine Learning Models

CityVision runs **four** YOLOv8 models on the edge pipeline. All weights are stored in `RoadDetectionModel/` and loaded locally — **no internet connection required at runtime**.

### Model 1: Road Anomaly Detector (Primary)

Custom YOLOv8m trained on **30,685 annotated Indian road images** for 120 epochs.

| Attribute | Value |
|---|---|
| Architecture | YOLOv8m (25.9M params) |
| Training Hardware | NVIDIA RTX 3060 6GB |
| Training Duration | ~27.8 hours / 120 epochs |
| Weights | `RoadDetectionModel/RoadModel_yolov8m.pt_rounds120_b9/weights/best.pt` |
| CPU Inference Speed | ~1414 ms/frame (0.7 FPS) |

**Test Set Results:**

| Class | Precision | Recall | mAP@0.5 | mAP@0.5:.95 |
|:---|:---|:---|:---|:---|
| **Overall** | **0.736** | **0.740** | **0.745** | **0.448** |
| Heavy-Vehicle | 0.913 | 0.978 | 0.981 | 0.763 |
| Light-Vehicle | 0.892 | 0.951 | 0.961 | 0.649 |
| Pedestrian | 0.822 | 0.915 | 0.918 | 0.522 |
| **Crack** | 0.576 | 0.484 | **0.505** | 0.240 |
| **Crack-Severe** | 0.548 | 0.503 | **0.493** | 0.273 |
| **Pothole** | 0.597 | 0.440 | **0.468** | 0.198 |
| **Speed-Bump** | 0.804 | 0.908 | **0.885** | 0.487 |

### Model 2: Indian License Plate Detector

Pre-trained YOLOv8n sourced from `gursharn01/indian-license-plate-detector` on Hugging Face. Text is extracted using **EasyOCR** (no Tesseract dependency).

| Attribute | Value |
|---|---|
| Architecture | YOLOv8n |
| Weights | `RoadDetectionModel/ANPRPlateDetector_yolov8n/weights/best.pt` |
| CPU Inference Speed | ~92 ms/frame (10.9 FPS) |

### Model 3: Vehicle / VRU Detector

| Attribute | Value |
|---|---|
| Architecture | YOLOv8n |
| Weights | `yolov8n.pt` (root, loaded locally) |
| CPU Inference Speed | ~109 ms/frame (9.2 FPS) |

### Model 4: Traffic Sign / Infrastructure Detector (Demo Fallback)

Pre-trained YOLOv8s (`JakobJFL/yolov8-dk-Traffic-Signs`, 19 classes). Serves as a demonstration fallback; in production this slot is reserved for Indian IS:1179 road sign weights.

| Attribute | Value |
|---|---|
| Architecture | YOLOv8s |
| Weights | `RoadDetectionModel/TrafficInfraModel_yolov8s/weights/best.pt` |
| CPU Inference Speed | ~471 ms/frame (2.1 FPS) |

---

## Quick Start Guide (For Beginners)

This guide walks you through running CityVision locally from scratch. You will have the full system running in about 10 minutes.

### Step 0: Prerequisites

Make sure the following are installed before starting:

| Tool | Minimum Version | Download |
|---|---|---|
| **Python** | 3.10 | https://www.python.org/downloads/ |
| **Node.js** | 18 | https://nodejs.org/ |
| **Git** | Any | https://git-scm.com/ |

> **Windows users**: Use **PowerShell** (not Command Prompt) for all Python commands.

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/AribAsim/CityVision.git
cd CityVision
```

---

### Step 2: Set Up Python Environment

A **virtual environment** keeps CityVision's dependencies isolated from your other projects.

```bash
# Create the virtual environment (run once)
python -m venv venv
```

**Activate it every time you open a new terminal:**

```powershell
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux / macOS:
# source venv/bin/activate
```

> **Activation blocked on Windows?** Run this once in PowerShell as Administrator:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

Install all Python dependencies:

```bash
pip install -r backend/requirements.txt
pip install -r requirements.txt
```

> This installs PyTorch, Ultralytics YOLOv8, FastAPI, and EasyOCR. Allow 2-5 minutes on a normal connection.

**Optional — copy the environment config:**

```powershell
# Windows
copy .env.example .env

# Linux / macOS
# cp .env.example .env
```

The defaults in `.env.example` work out-of-the-box with SQLite. No database server required.

---

### Step 3: Start the Backend Server

With your virtual environment active:

```powershell
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

- **API Base URL**: http://localhost:8000
- **Swagger UI (interactive docs)**: http://localhost:8000/docs

Leave this terminal running and open a new one.

---

### Step 4: Start the Frontend Dashboard

In a **new terminal**:

```bash
cd frontend
npm install       # Install packages (run once)
npm run dev       # Start the dev server
```

Expected output:
```
  VITE ready in Xms
  Local:  http://localhost:5173/
```

Open **http://localhost:5173** in your browser to see the CityVision Command Center.

---

### Step 5: Run the Live Demo

The demo simulates a complete multi-bus detection cycle:
1. **BUS-01** detects a pothole and creates a NEW incident
2. **BUS-02** detects the same location — Multi-Bus Verification triggers
3. Severity auto-escalates: High to Critical
4. Lifecycle advances: NEW to VERIFIED

In a **third terminal** (venv active, from project root):

```powershell
# Interactive mode — pauses between steps for a presentation
python -m demo.run_demo

# Automated mode — runs the full scenario without pauses
python -m demo.run_demo --auto-advance
```

Watch the dashboard at http://localhost:5173 update in real time.

---

### Step 6: Process a Video Scan

#### Option A: Via Web UI (Recommended)
1. Go to the **Live Detection** tab in the dashboard
2. Click **"Run Bus Scan"**
3. Select a Bus (BUS-01, BUS-02, or BUS-03), choose a route, and upload any `.mp4` dashcam video
4. The scan runs in the background — navigate between tabs freely while it processes

#### Option B: Via Edge CLI

```powershell
# Full pipeline — road anomalies + ANPR + traffic signs
python -m edge.runner --bus BUS-01 --route ROUTE-RED --video "path/to/road_video.mp4"

# Road anomalies only (faster on CPU)
python -m edge.runner --bus BUS-01 --video "path/to/video.mp4" --no-anpr --no-infra

# Benchmark inference speed on your machine
python -m edge.runner --benchmark --video "path/to/video.mp4"
```

---

## Edge CLI Runner

```
python -m edge.runner [OPTIONS]

  --bus TEXT      Bus ID to simulate  (default: BUS-01)
  --route TEXT    Route ID            (default: ROUTE-RED)
  --video TEXT    Path to .mp4 file   (required for file mode)
  --no-vehicles   Disable vehicle/VRU detection
  --no-anpr       Disable Indian license plate detection
  --no-infra      Disable traffic sign detection
  --benchmark     Run speed benchmark and exit
```

---

## Automated Testing

```powershell
# Activate venv and set PYTHONPATH
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."

# Run all 78 tests
python -m pytest tests/ -v

# Run individual modules
python -m pytest tests/test_edge_pipeline.py -v      # Edge AI pipeline (29 tests)
python -m pytest tests/test_scan_router.py -v        # Video scan job API (5 tests)
python -m pytest tests/test_integration_full.py -v   # End-to-end fusion (44 tests)

# Useful flags
python -m pytest tests/ -x      # Stop on first failure
python -m pytest tests/ -s      # Show stdout/print output
python -m pytest tests/ --pdb   # Drop into debugger on failure
```

**Current status: 78/78 tests passing.**

Verify the frontend TypeScript compiles cleanly:

```bash
cd frontend && npm run build
```

---

## REST API Reference

All endpoints are available at `http://localhost:8000`. Full interactive documentation at `/docs`.

### Core Endpoints

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/health` | Service liveness check |
| `POST` | `/api/ingest` | Ingest event with evidence image (multipart) |
| `POST` | `/api/ingest/json` | Ingest event directly via JSON body |
| `GET` | `/api/incidents` | List incidents (filter by status, severity, anomaly_type) |
| `GET` | `/api/incidents/{id}` | Full incident detail + observation history + status audit |
| `PATCH` | `/api/incidents/{id}/status` | Transition lifecycle status |
| `GET` | `/api/incidents/{id}/report.pdf` | Download PDF work order |
| `GET` | `/api/buses` | Real-time fleet GPS telemetry |
| `GET` | `/api/analytics/summary` | KPI aggregates, PCI, severity distributions |

### Video Scan Endpoints

| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/scan/start` | Upload .mp4 and launch background edge scan |
| `GET` | `/api/scan/status/{job_id}` | Check scan status and event count |

### ANPR & Infrastructure Endpoints

| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/ingest/plates` | Directly ingest ANPR plate reads |
| `GET` | `/api/ingest/plates` | Query persisted plate reads (filter by bus, time) |
| `POST` | `/api/ingest/infra` | Directly ingest infrastructure observations |
| `GET` | `/api/ingest/infra` | Query persisted infra observations |

---

## Architecture and Governance Docs

The `brain/` directory is the single source of truth for all architectural and technical decisions:

| File | Contents |
|---|---|
| [00_PROJECT_CONTEXT.md](brain/00_PROJECT_CONTEXT.md) | Problem statement, MVP objectives and boundaries |
| [02_MVP_SCOPE.md](brain/02_MVP_SCOPE.md) | In-scope vs out-of-scope for SIH26124 |
| [03_SYSTEM_ARCHITECTURE.md](brain/03_SYSTEM_ARCHITECTURE.md) | Data flow, component boundaries, pipeline sequence |
| [04_DATA_CONTRACTS.md](brain/04_DATA_CONTRACTS.md) | Incident, PlateRead, InfraObservation, Bus schemas |
| [05_API_CONTRACT.md](brain/05_API_CONTRACT.md) | Full REST API contract with payloads |
| [07_EVENT_ENGINE.md](brain/07_EVENT_ENGINE.md) | ByteTrack, stitcher, Haversine clustering, escalation math |
| [11_IMPLEMENTATION_STATUS.md](brain/11_IMPLEMENTATION_STATUS.md) | Verification report, empirical benchmarks, test results |

---

## Optional: Docker Compose (Scale-Up)

For evaluators who want to test production-scale optional services:

```bash
# Start TimescaleDB/PostGIS, MinIO S3, and Mosquitto MQTT
docker compose up -d

# Run Alembic migrations (PostgreSQL DDL)
alembic upgrade head
```

Then enable feature flags in `.env`:

```env
TIMESCALE_ENABLED=true
MINIO_ENABLED=true
MQTT_ENABLED=true
```

> All services are optional. The system falls back to SQLite + local disk + HTTP polling if Docker is not available.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
