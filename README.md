# CityVision — Mobile Urban Sensing & Road Anomaly Monitoring Platform

> *"Every Bus a Sensor. Every Road a Safer Path."*

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF.svg)](https://github.com/ultralytics/ultralytics)
[![Leaflet](https://img.shields.io/badge/Leaflet-GIS%20Mapping-199900.svg?logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**CityVision** (Smart India Hackathon SIH26124) transforms routine public municipal transit buses into intelligent, mobile urban sensing units. By mounting dashcam sensors on public bus fleets, CityVision continuously detects road surface anomalies (potholes, severe cracks, speed bumps), tags them with live GPS and telemetry, cross-correlates multi-bus observations to eliminate false positives, and escalates verified road hazards directly to municipal public works command centers.

---

## 📑 Table of Contents

- [Executive Summary](#-executive-summary)
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Repository Structure](#-repository-structure)
- [Machine Learning & Model Evaluation](#-machine-learning--model-evaluation)
- [Quick Start Guide](#-quick-start-guide)
  - [1. Backend Setup](#1-backend-setup)
  - [2. Frontend Setup](#2-frontend-setup)
  - [3. Running the Live Demo](#3-running-the-live-demo)
  - [4. Processing a Video Scan](#4-processing-a-video-scan)
- [Automated Testing](#-automated-testing)
- [REST API Reference](#-rest-api-reference)
- [Architecture & Governance Docs (`/brain`)](#-architecture--governance-docs-brain)
- [License](#-license)

---

## 🏙️ Executive Summary

Traditional road maintenance relies on sporadic, expensive physical road surveys or slow-moving citizen grievance queues. **CityVision** replaces this reactive model with **continuous, passive, multi-vehicle verified sensing**:

1. **Passive Edge Capture**: City buses traverse regular scheduled routes while edge intelligence models analyze live dashcam footage in real time.
2. **Physical Anomaly Tracking**: Uses Kalman filtering (`supervision.ByteTrack`) coupled with a post-track trajectory stitcher to collapse hundreds of frame detections into a single, cohesive defect identity.
3. **Multi-Bus Spatial Consensus**: Multiple buses passing the same geographic coordinate ($\le 15\text{ m}$) automatically corroborate observations, elevating incident confidence and escalating severity from `NEW` to `VERIFIED`.
4. **Command Center Operations**: Municipal civil engineers prioritize repair backlogs via dynamic risk-scoring algorithms, interactive Leaflet GIS maps, and audited lifecycle state machines (`NEW` $\to$ `VERIFIED` $\to$ `ASSIGNED` $\to$ `IN_PROGRESS` $\to$ `RESOLVED`).

---

## 🏗️ System Architecture

```
[ Public Bus Dashcam / Video Stream ]
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. EDGE INTELLIGENCE PIPELINE (`edge/`)                     │
│    ├── Custom YOLOv8m Inference (Pothole, Crack, Bump)      │
│    ├── ByteTrack Kalman Filter (Frame-to-Frame Association) │
│    ├── Trajectory Stitcher (Dropout & Gap Bridging)         │
│    ├── Bus Fleet & GPS Simulators (Delhi Transit Corridors) │
│    └── Event Builder (Best-Frame Crop & JSON Telemetry)     │
└─────────────────────────────────────────────────────────────┘
                │ HTTP POST multipart/form-data (/api/ingest)
                ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. CENTRAL BACKEND SERVICE (`backend/`)                     │
│    ├── FastAPI Asynchronous Application Engine              │
│    ├── 15-meter Haversine Spatial Clustering Engine         │
│    ├── Multi-Bus Consensus & Auto-Escalation Engine         │
│    ├── Dynamic Priority Scoring (0 - 100)                   │
│    ├── Background Video Scan Job Dispatcher (/api/scan)     │
│    └── SQLite Canonical Data Store (`sih26124.db`)          │
└─────────────────────────────────────────────────────────────┘
                │ REST API / Live Polling (JSON)
                ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. COMMAND CENTER WEB DASHBOARD (`frontend/`)               │
│    ├── Command Center (Home): KPIs, Live HUD, PCI Gauges    │
│    ├── Live Detection: Real-time inference feed & scanner   │
│    ├── Geospatial Road Map: Interactive Leaflet GIS         │
│    ├── Reports & Work Orders: Exportable triage management  │
│    ├── Bus Fleet Telemetry: Active routes & vehicle status  │
│    └── Analytics & KPIs: Trend analytics & defect breakdown │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 1. Edge Intelligence Pipeline (`edge/`)
- **Custom Trained YOLOv8m**: Native custom weights trained over 30,000+ Indian road images achieving **0.745 mAP@0.5** and ~12ms inference latency.
- **Physical Anomaly Tracking**: Uses `supervision.ByteTrack` with a 30-frame persistence buffer, `minimum_matching_threshold=0.80`, and 2-frame confirmation gate to ensure distinct physical defects receive unique identities.
- **Motion-Compensated Post-Track Stitcher (`edge/track_stitcher.py`)**: Extrapolates spatial trajectories across detection dropouts up to 15 frames ($0 < \text{gap} \le 15$), enforcing directional alignment ($\cos \ge 0.40$) and strict spatial proximity ($\le 25.0\text{ px}$) while guaranteeing concurrent tracks remain distinct.
- **Lineage Audit Suite (`scripts/audit_lineage.py`)**: End-to-end audit tracing from raw YOLO detections $\to$ ByteTrack track identities $\to$ Stitched physical defects $\to$ Dispatched edge events $\to$ Backend incidents, with contact sheet generation.

### 2. Central Platform & Fusion Engine (`backend/`)
- **15m Haversine Clustering**: Correlates successive passes over the same road segment into one canonical incident while maintaining a running centroid.
- **Rapid Observation Spam Guard**: Throttles duplicate frame detections from the same vehicle within a 2.0-second cooldown window.
- **Dynamic Multi-Bus Escalation**: When `unique_bus_count >= 2`, severity escalates by one tier (e.g. `High` $\to$ `Critical`) and automatically transitions status from `NEW` to `VERIFIED`.
- **Background Scan Processing**: Asynchronously processes uploaded `.mp4` videos via background worker threads (`POST /api/scan/start` and `GET /api/scan/status/{job_id}`).

### 3. Municipal Sentinel Modern Frontend (`frontend/`)
- **Design System**: Crafted using the *Municipal Sentinel Modern* aesthetic: deep maritime blue palettes, high-contrast severity badges, and engineered typography (`Space Grotesk`, `Inter`, `JetBrains Mono`).
- **6 Dedicated Operational Views**:
  - **Command Center (Home)**: High-level metrics ribbon, 6-stage pipeline breadcrumb, live dashcam HUD, radial Pavement Condition Index (PCI) gauge, and corridor performance cards.
  - **Live Detection**: Optical crosshair canvas, live GPS stream, detection parameters, and persistent background scan manager.
  - **Geospatial Road Map**: Leaflet GIS map with polyline transit corridors (Route 12, Route 8, Route 5), clustered pins, and interactive status action popups.
  - **Reports & Work Orders**: Tabular incident management with filtering, search, and CSV export.
  - **Bus Fleet Telemetry**: Real-time vehicle location, speed, route assignment, and health metrics.
  - **Analytics & KPIs**: Severity distribution, defect type breakdowns, and resolution velocity charts.
- **Cross-View Persistent Scan Manager**: Video upload scans continue polling and processing in the background even when switching across tabs or views.

---

## 📂 Repository Structure

```text
├── backend/                             # FastAPI backend service
│   ├── app/
│   │   ├── routers/                     # API routers (incidents, scan, buses, ingest, analytics)
│   │   ├── services/                    # Spatial deduplication, event fusion, severity scoring
│   │   ├── database.py                  # SQLite engine & session management
│   │   ├── models.py                    # SQLAlchemy models (Incident, Observation, StatusHistory, Bus)
│   │   ├── schemas.py                   # Pydantic validation schemas
│   │   └── main.py                      # FastAPI entrypoint
│   ├── static/snapshots/                # Stored anomaly evidence crops
│   └── requirements.txt                 # Backend Python dependencies
│
├── edge/                                # Edge detection and vehicle simulation
│   ├── detector.py                      # YOLOv8m inference wrapper
│   ├── anomaly_tracker.py               # ByteTrack Kalman filter tracking
│   ├── track_stitcher.py                # Post-track spatial/temporal trajectory stitcher
│   ├── bus_simulator.py                 # Transit fleet vehicle simulator
│   ├── gps_simulator.py                 # Delhi transit corridor GPS interpolator
│   ├── event_builder.py                 # Track-to-event packaging and evidence crop builder
│   └── runner.py                        # Edge video processing CLI runner
│
├── frontend/                            # React 18 + Vite + TypeScript Command Center
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navigation/              # Sidebar and TopHeader navigation bars
│   │   │   ├── Views/                   # 6 Dedicated Operational Views
│   │   │   ├── DetailDrawer/            # Incident inspection, observation feed & status updater
│   │   │   ├── GisMap/                  # Leaflet interactive map with corridor polylines
│   │   │   └── BusScan/                 # Video scan modal and trigger panel
│   │   ├── hooks/                       # React hooks (useScanManager, useIncidents, useBuses, useAnalytics)
│   │   ├── services/                    # API client and seed fallback data
│   │   └── types/                       # TypeScript data contracts
│   ├── package.json
│   └── vite.config.ts
│
├── RoadDetectionModel/                  # Custom trained YOLOv8m model
│   └── RoadModel_yolov8m.pt_rounds120_b9/
│       ├── weights/best.pt              # Custom weights (mAP@0.5: 0.745, 52MB)
│       ├── args.yaml                    # Training hyperparameters
│       └── confusion_matrix.png         # Model performance charts
│
├── brain/                               # Architecture ground-truth & documentation
│   ├── 00_PROJECT_CONTEXT.md            # Vision, MVP scope, and boundaries
│   ├── 03_SYSTEM_ARCHITECTURE.md        # Technical architecture specifications
│   ├── 04_DATA_CONTRACTS.md             # Canonical schemas & database contracts
│   ├── 05_API_CONTRACT.md               # OpenAPI / REST endpoint specifications
│   ├── 07_EVENT_ENGINE.md               # Tracking, deduplication & escalation logic
│   └── 11_IMPLEMENTATION_STATUS.md      # Comprehensive audit and verification status
│
├── demo/                                # Live evaluators demonstration suite
│   ├── scenario.json                    # Deterministic multi-bus incident timeline
│   └── run_demo.py                      # Interactive demo orchestration script
│
├── scripts/                             # Offline evaluation & lineage verification
│   ├── audit_lineage.py                 # Full raw-detection to incident lineage audit
│   ├── inspect_merges.py                # Track stitcher trajectory analysis
│   └── measure_stitching.py             # Performance measurement script
│
├── tests/                               # Automated test suite (pytest)
│   ├── test_edge_pipeline.py            # Edge detector, tracker, stitcher, GPS tests
│   ├── test_scan_router.py              # Video scan job dispatch & status tests
│   └── test_integration_full.py        # End-to-end pipeline & multi-bus fusion tests
│
├── .gitignore                           # Excludes heavy videos, node_modules, venvs, DBs
└── README.md
```

---

## 📊 Machine Learning & Model Evaluation

The core detection engine uses **Model 1: Custom YOLOv8m** trained specifically on Indian roadway conditions across 30,685 annotated images.

* **Architecture**: YOLOv8m (25.9M parameters)
* **Training Hardware**: NVIDIA GeForce RTX 3060 (6GB)
* **Training Epochs**: 120 rounds (~27.8 hours)
* **Weights Location**: [`RoadDetectionModel/RoadModel_yolov8m.pt_rounds120_b9/weights/best.pt`](RoadDetectionModel/RoadModel_yolov8m.pt_rounds120_b9/weights/best.pt)
* **Average Inference Speed**: ~12.0 ms per frame

### Test Set Performance Evaluation (Final Benchmark)

| Class | Precision | Recall | mAP@0.5 | mAP@0.5:.95 |
| :--- | :--- | :--- | :--- | :--- |
| **Overall** | **0.736** | **0.740** | **0.745** | **0.448** |
| Heavy-Vehicle | 0.913 | 0.978 | 0.981 | 0.763 |
| Light-Vehicle | 0.892 | 0.951 | 0.961 | 0.649 |
| Pedestrian | 0.822 | 0.915 | 0.918 | 0.522 |
| **Crack** | 0.576 | 0.484 | **0.505** | 0.240 |
| **Crack-Severe** | 0.548 | 0.503 | **0.493** | 0.273 |
| **Pothole** | 0.597 | 0.440 | **0.468** | 0.198 |
| **Speed-Bump** | 0.804 | 0.908 | **0.885** | 0.487 |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+** (Python 3.10 – 3.12 recommended)
- **Node.js 18+** and `npm`
- **Git**

---

### 1. Backend Setup

```bash
# 1. Create and activate a Python virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
# source venv/bin/activate

# 2. Install backend & edge dependencies
pip install -r backend/requirements.txt
pip install -r requirements.txt

# 3. Start the FastAPI server
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
> The API will be live at `http://localhost:8000`. Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

---

### 2. Frontend Setup

In a new terminal:

```bash
# 1. Navigate to the frontend folder
cd frontend

# 2. Install dependencies
npm install

# 3. Start the Vite development server
npm run dev
```
> Open your browser and navigate to `http://localhost:5173`.

---

### 3. Running the Live Demo

To run the automated multi-bus simulation demonstrating:
1. `BUS-01` detecting an anomaly and creating a `NEW` incident,
2. `BUS-02` re-detecting the same coordinate and triggering **Multi-Bus Verification**,
3. Auto-escalation of severity (`High` $\to$ `Critical`),
4. Interactive lifecycle status transitions (`NEW` $\to$ `VERIFIED` $\to$ `ASSIGNED` $\to$ `RESOLVED`):

```bash
# With the backend running, execute the demo script:
python -m demo.run_demo
```

---

### 4. Processing a Video Scan

#### Option A: Via Web UI
1. Navigate to the **Live Detection** tab in the web interface.
2. Click **"Run Bus Scan"**.
3. Select an assigned Bus (`BUS-01`, `BUS-02`, `BUS-03`), choose a transit corridor, and upload any `.mp4` road dashcam video.
4. The background scan manager will track processing progress in real time without blocking the UI.

#### Option B: Via Edge CLI Runner
```bash
python -m edge.runner --bus BUS-01 --route ROUTE-RED --video "path/to/road_video.mp4"
```

---

## 🧪 Automated Testing

The codebase includes an extensive suite of automated tests covering edge tracking, Kalman motion compensation, spatial clustering, API contracts, and scan background workers:

```bash
# Run all automated tests:
python -m pytest tests/ -v

# Run edge pipeline tests (29 tests):
python -m pytest tests/test_edge_pipeline.py -v

# Run scan job dispatch tests (5 tests):
python -m pytest tests/test_scan_router.py -v

# Run end-to-end integration & lineage tests (26 tests):
python -m pytest tests/test_integration_full.py -v
```

All 60 tests pass with 100% success rate. The frontend TypeScript codebase compiles cleanly:
```bash
cd frontend && npm run build
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/scan/start` | Upload `.mp4` video and launch unbuffered background edge scan |
| `GET` | `/api/scan/status/{job_id}` | Check status and dispatched event count of a video scan job |
| `POST` | `/api/ingest` | Ingest structured detection event with evidence snapshot image |
| `POST` | `/api/ingest/json` | Ingest structured detection event directly via JSON |
| `GET` | `/api/incidents` | List road incidents (supports filtering by `status`, `severity`, `anomaly_type`) |
| `GET` | `/api/incidents/{id}` | Get full incident detail, observation history, and status audit log |
| `PATCH` | `/api/incidents/{id}/status` | Transition incident lifecycle status (`NEW`, `VERIFIED`, `ASSIGNED`, `IN_PROGRESS`, `RESOLVED`) |
| `GET` | `/api/buses` | Real-time transit fleet GPS telemetry and active bus status |
| `GET` | `/api/analytics/summary` | Aggregated KPIs, severity distributions, and municipal health indexes |
| `GET` | `/api/health` | Service liveness health check |

---

## 🧠 Architecture & Governance Docs (`/brain`)

The [`brain/`](brain/) directory serves as the **single source of truth** for all architectural and technical decisions:

- [`00_PROJECT_CONTEXT.md`](brain/00_PROJECT_CONTEXT.md): Core problem statement, MVP objectives, and boundaries.
- [`01_REPOSITORY_AUDIT.md`](brain/01_REPOSITORY_AUDIT.md): Inventory of legacy code reuse and trained weights evaluation.
- [`02_MVP_SCOPE.md`](brain/02_MVP_SCOPE.md): Defined scope: In-Scope vs Out-of-Scope capabilities.
- [`03_SYSTEM_ARCHITECTURE.md`](brain/03_SYSTEM_ARCHITECTURE.md): Complete data flow, component boundaries, and pipeline sequence.
- [`04_DATA_CONTRACTS.md`](brain/04_DATA_CONTRACTS.md): Incident, Observation, Bus, and StatusHistory schemas.
- [`05_API_CONTRACT.md`](brain/05_API_CONTRACT.md): Comprehensive REST API contract with request/response payloads.
- [`06_FRONTEND_SPEC.md`](brain/06_FRONTEND_SPEC.md): Design system tokens, operational views, and component hierarchy.
- [`07_EVENT_ENGINE.md`](brain/07_EVENT_ENGINE.md): Tracking, trajectory stitching, Haversine clustering, and escalation mathematics.
- [`08_DEMO_SCENARIO.md`](brain/08_DEMO_SCENARIO.md): Scripted timeline for hackathon jury evaluations.
- [`09_TECH_DECISIONS.md`](brain/09_TECH_DECISIONS.md): Architectural decisions and trade-off rationales.
- [`10_AGENT_RULES.md`](brain/10_AGENT_RULES.md): Engineering rules and constraints.
- [`11_IMPLEMENTATION_STATUS.md`](brain/11_IMPLEMENTATION_STATUS.md): Verification report, empirical metrics, and test results.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
