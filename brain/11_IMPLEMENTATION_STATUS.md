# Implementation Status: SIH26124 MVP

## Current Status: Video Upload → Edge Detection → Ingestion Flow Verified — 100% Demo-Ready

The SIH26124 Mobile Urban Sensing Platform MVP is fully implemented, audited, and verified across all architectural tiers: Edge, Backend, Frontend, Integration, and Demo Orchestration.

All 60 backend/edge/integration automated tests pass cleanly (29 edge pipeline, 26 full integration & lineage verification, 5 scan router), and the React + TypeScript frontend compiles with zero warnings or errors (`tsc -b && vite build`).

---

## 1. Completed Features

### Backend Tier (`backend/`)
- **FastAPI REST Application**: High-performance asynchronous API service (`backend/app/main.py`) with Swagger/OpenAPI docs at `/docs`.
- **Database Architecture (SQLite)**: Canonical entities defined in `backend/app/models.py`:
  - `Incident`: Physical road defect with centroid GPS, severity, priority score, confirmation count, unique bus count, and lifecycle status.
  - `Observation`: Chronological detection log per reporting vehicle with raw telemetry, speed, confidence, and snapshot URL.
  - `StatusHistory`: Full audit trail tracking operational transitions and notes.
  - `Bus`: Public transit vehicle fleet telemetry (`bus_id`, `route_id`, `latitude`, `longitude`, `status`, `last_seen`).
- **Video Scan Trigger Router (`backend/app/routers/scan.py`)**:
  - `POST /api/scan/start`: Accepts `.mp4` video uploads with bus/route selection (`BUS-01`, `BUS-02`, `BUS-03`), stages the video to `data/uploads/`, and launches the existing `edge/runner.py` pipeline in a background daemon thread with unbuffered subprocess execution (`subprocess.Popen` with `-u`) without blocking the server or failing on Windows event loops.
  - `GET /api/scan/status/{job_id}`: Delivers live scan status (`PROCESSING`, `COMPLETED`, `FAILED`) and real-time count of dispatched events.
  - Auto-cleanup of uploaded temporary video upon process completion.
- **15m Haversine Spatial Clustering**: `find_matching_incident` in `backend/app/services/deduplication.py` correlates nearby observations ($\le 15$ m) to the same physical defect and maintains a running centroid.
- **Rapid Observation Spam Guard**: Throttles duplicate frame detections from the same vehicle within 2.0 seconds while refreshing the latest timestamp.
- **Rule-Based Severity & Priority Engine**: Transparent scoring in `backend/app/services/severity.py`:
  - Baseline severity: High ($\ge 0.85$), Medium ($\ge 0.65$), Low ($< 0.65$).
  - Dynamic multi-bus escalation: When `unique_bus_count >= 2`, severity escalates by one tier (capped at `Critical`).
  - Priority score formula (0–100): Combines base class weight, confidence factor, observation bonuses, and multi-bus verification bonuses.
- **Strict Lifecycle State Machine**: Enforces operational workflow:
  $$\text{NEW} \longrightarrow \text{VERIFIED} \longrightarrow \text{ASSIGNED} \longrightarrow \text{IN\_PROGRESS} \longrightarrow \text{RESOLVED}$$
  (Multi-bus confirmation automatically advances `NEW` to `VERIFIED`; `RESOLVED` is terminal).
- **REST Endpoints**:
  - `POST /api/scan/start` (video upload and edge detection trigger)
  - `GET /api/scan/status/{job_id}` (real-time scan monitoring)
  - `POST /api/ingest` (multipart JSON + evidence image upload)
  - `POST /api/ingest/json` (direct JSON ingestion)
  - `GET /api/incidents` (filtered by status, severity, anomaly_type; sorted by recency)
  - `GET /api/incidents/{id}` (full detail with nested observations and status history)
  - `PATCH /api/incidents/{id}/status` (status transition guard with audit trail)
  - `GET /api/buses` (fleet tracking telemetry)
  - `GET /api/analytics/summary` (aggregate KPIs for dashboard)
  - `GET /api/health` (system liveness check)
- **Static Evidence Server**: Snapshot images served directly at `/static/snapshots/{filename}`.
- **CORS & Middleware**: Configured for local development (`localhost:5173`, `3000`, and wildcards).

### Edge Intelligence Pipeline (`edge/`)
- **YOLOv8m Model Integration**: `edge/detector.py` loads existing custom weights (`RoadDetectionModel/RoadModel_yolov8m.pt_rounds120_b9/weights/best.pt`, mAP@0.5 = 0.745) without modification or retraining.
- **Target Anomaly Classes**: Filters and processes `Pothole`, `Crack`, `Crack-Severe`, and `Speed-Bump`.
- **Bus Fleet Simulator**: `edge/bus_simulator.py` simulates vehicles `BUS-01`, `BUS-02`, and `BUS-03` along routes `RED`, `BLUE`, and `GREEN` with realistic speeds.
- **GPS Waypoint Simulator**: `edge/gps_simulator.py` interpolates coordinates along Delhi transit corridors and calculates instantaneous compass heading.
- **Physical Anomaly Tracking Engine**: `edge/anomaly_tracker.py` wraps `supervision.ByteTrack` per anomaly class with Kalman motion estimation, 30-frame persistence buffer, `minimum_matching_threshold=0.80`, and 2-frame minimum observation gate. Ensures repeated detections of the same defect collapse into 1 event while distinct defects receive distinct tracks.
- **Motion-Compensated Post-Track Stitcher (`edge/track_stitcher.py`)**: Post-ByteTrack evidence-based stitcher targeting gap-based fragmentation without disturbing frame-to-frame association. Extrapolates spatial trajectories across detection dropouts up to 15 frames ($0 < \text{gap} \le 15$), enforcing strict spatial alignment ($\le 25.0\text{ px}$), directional alignment ($\cos \ge 0.40$), and chain validation. Concurrent tracks are strictly excluded.
- **Track-to-Event Builder**: `edge/event_builder.py` selects the highest-confidence frame observation, bbox, and GPS coordinates from each completed track, calculates severity/priority scores, saves evidence crops, and dispatches HTTP POST events to `/api/ingest`.
- **Edge CLI Runner**: `edge/runner.py` executes inference, physical tracking, real-time event dispatch, and logs a comprehensive diagnostic metrics block (`frames_processed`, `raw_yolo_detections`, `anomaly_detections`, `active_tracks`, `completed_tracks`, `events_created`, `events_dispatched`). Fully integrated with `backend/app/routers/scan.py`.
- **Physical Lineage Audit Suite (`scripts/audit_lineage.py`)**:
  - Full lineage tracing from YOLO raw detections $\to$ ByteTrack track identities $\to$ TrackStitcher $\to$ CompletedTracks $\to$ EdgeEvents $\to$ Backend Incidents.
  - Multi-frame contact sheet generation (`data/audit/track_{id}_{class}_sheet.jpg`) showing up to 8 timestamped observations per track with bounding boxes and confidence scores.
  - Full audit output exported to `data/audit/lineage.csv` and `data/audit/frame_observations.csv`.
  - **Empirical Validation (821 frames / 27s video)**:
    - Reduced 1,153 raw YOLO detections $\to$ 31 ByteTrack tracks $\to$ **28 stitched physical tracks**.
    - Target gap-separated fragmentation pairs (`4->6`, `14->16`, and `30->31`) are correctly and safely merged.
    - Spatially distinct concurrent defects (e.g. Track 3 vs 4, Track 16 vs 18, Track 21 vs 22, Track 35 vs 36) remain strictly distinct.

### Frontend Command Center (`frontend/`)
- **Design System & Aesthetics**: Implemented the **Municipal Sentinel Modern** design system from `stitch_city_vision_road_monitor`:
  - Deep maritime blue palettes (`#00236f`, `#1e3a8a`), crisp surface layers (`#f8f9ff`, `#ffffff`), and high-contrast severity accents.
  - Engineered typography pairing: `Space Grotesk` (headers), `Inter` (body/controls), and `JetBrains Mono` (technical telemetry, coordinates, timestamps).
  - Authentic City Vision vector SVG logo with motto: *"Every Bus a Sensor. Every Road a Safer Path."*
- **Pinned Operations Navigation Rail (280px)**:
  - Six dedicated operational views: **Command Center (Home)**, **Live Detection**, **Geospatial Road Map**, **Reports & Work Orders**, **Bus Fleet Telemetry**, and **Analytics & KPIs**.
  - Persistent real-time telemetry feed widget (`RT-STREAM // ACTIVE`) with radar ping animation.
- **Top Header Bar**:
  - Pinned bar with real-time status: `SYSTEM ONLINE | X Active Buses | Municipal Transit Grid`.
  - Global Search input, `DEMO MODE: ON` badge, and Transit Ops Municipal Admin profile chip.
- **Command Center Dashboard (`HomeView.tsx`)**:
  - Operational Hero Banner with direct "Start Live Patrol" trigger.
  - 5 Operational Metric Cards: Active Buses, Monitored Kilometers (128km), Issues Detected, High Priority (Critical), and Resolved.
  - 6-Stage Distributed Ingestion Architecture Pipeline ribbon (`01 EDGE -> 02 GEO -> 03 VISION -> 04 FUSION -> 05 TRIAGE -> 06 ACTION`).
  - Live Dashcam Monitoring HUD with camera feed switcher (`CAM-04`, `CAM-01`, `CAM-02`, `CAM-08`) and AI bounding box overlays.
  - Municipal Road Condition Card with radial SVG Pavement Condition Index (PCI 0–100) gauge and segmented health distribution.
  - Corridor Performance breakdown cards for Route 12, Route 8, and Route 5.
- **Live Detection & Edge Scan Controller (`LiveDetectionView.tsx` & `useScanManager.ts`)**:
  - Operational sub-header with FPS (28.4 FPS), active model (`YOLOv8m-RoadAnomaly`), and inference latency (18.2ms).
  - 16:9 Video Canvas with simulated AI bounding reticles, optical crosshairs, and live GPS overlay.
  - Camera stream controls (Pause/Resume, Capture Snapshot, Feed Switcher).
  - **Persistent Root-Level Video Scan Trigger (`useScanManager.ts`)**:
    - Lifted scan state management to application root (`App.tsx`) with `sessionStorage` persistence.
    - Resolves tab-switch discrepancies: background polling (`/api/scan/status/{job_id}`) and progress indicators remain active across all pages even when navigating between Command Center, Geospatial Road Map, Reports, or Analytics.
    - Global Top Header and Sidebar display live scanning banners (`SCANNING BUS-XX: N EVENTS`) and radar pings with click-through navigation back to Live Detection.
    - Supports dismissal and auto-refresh of incidents, analytics, and fleet upon scan completion.
  - Rule-Based Severity Engine Breakdown (Confidence, Bbox Area, Recurrence, Transit Importance) and Multi-Bus Consensus card.
  - Tabular live telemetry stream and detection ingest log.
- **Geospatial Road Map (`RoadMapView.tsx`)**:
  - React Leaflet map centered on Delhi coordinates (`28.6139, 77.2090`).
  - Colored transit line polylines for Route 12 (Blue Trunk), Route 8 (Purple Ring), and Route 5 (Commercial Express).
  - Custom severity markers (Critical Red with animated pulse, High Orange, Medium Amber, Low Green) and active bus vehicle pins.
  - Folium-styled interactive popups with full incident details, multi-bus verified badges, and quick status actions.
  - Multi-attribute filter ribbon (search road corridor, type, severity, status).
  - Summary KPI footer bar with radial verification rate gauge.
- **Reports & Work Orders (`ReportsView.tsx`)**:
  - Cadastral Infrastructure Records table with search filter and status tabs (`ALL`, `PENDING`, `IN_PROGRESS`, `RESOLVED`).
  - Export CSV Dossier functionality and Print Work Orders trigger.
  - Operational lifecycle transition buttons (`NEW -> VERIFIED -> ASSIGNED -> IN_PROGRESS -> RESOLVED`).
- **Bus Fleet Telemetry (`BusFleetView.tsx`)**:
  - Vehicle cards showing route assignments, real-time GPS coordinates, edge accelerator latency, and last ping timestamps.
- **Analytics & Defect Distributions (`AnalyticsView.tsx`)**:
  - Recharts visual representations for Defect Severity Distribution (PieChart) and Anomaly Class Frequency (BarChart).
- **Incident Detail Slide-Over Drawer (`DetailDrawer.tsx`)**:
  - High-resolution YOLOv8 evidence snapshot crop preview.
  - Interactive Resolution Progress Stepper and Status History audit trail.
  - Multi-bus observation timeline with per-bus timestamps, coordinates, and speed.
- **Real Data Seeding & Offline Resilience**:
  - Seamlessly bound to the 166 real incidents and buses in `sih26124.db` via 4-second background polling.
  - Intelligent fallback schemas ensure zero blank screens, zero NaN values, and 100% demo-readiness in any environment.

### Demo Orchestration (`demo/`)
- **Automated Demo Script**: `demo/run_demo.py` provides a deterministic demonstration of the entire vertical slice (`BUS-01` detection $\rightarrow$ `BUS-02` cross-verification $\rightarrow$ severity escalation $\rightarrow$ resolution).
- **Synthetic Evidence Generator**: `demo/generate_evidence.py` generates labeled road defect snapshots with bounding boxes and hackathon watermarks.
- **Declarative Configuration**: `demo/scenario.json` controls coordinates, route IDs, pause timings, and speeds.

---

## 2. Known Limitations (MVP Scope)

1. **Localhost Deployment**: The MVP runs locally on `localhost` (ports 8000 and 5173). Cloud deployment (AWS/GCP/Azure) and TLS certificates are out of hackathon scope.
2. **Polling vs. WebSockets**: Near-real-time updates use 4-second HTTP polling rather than WebSockets/MQTT. This ensures extreme reliability in hackathon network conditions.
3. **Simulated GPS Telemetry**: Coordinates are interpolated along simulated route waypoints rather than connected to physical NMEA GPS serial hardware.
4. **Synthetic/File-based Video Feeds**: Video input is ingested from recorded MP4 files or webcams rather than physical bus camera hardware streams.
5. **Single-Node SQLite Storage**: Uses SQLite (`sih26124.db`) for zero-configuration hackathon evaluation. Production multi-tenant database scaling is reserved for future phases.
6. **No Auth/RBAC**: Direct access to the authority command center without login screens to optimize evaluation speed for judges.

---

## 3. Exact CLI Commands

### Command 1: Start Backend Server
From the repository root (PowerShell / Command Prompt):
```powershell
.\venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --port 8000
```
*The backend API will be available at `http://localhost:8000` with Swagger docs at `http://localhost:8000/docs`.*

### Command 2: Start Frontend Dashboard
From the repository root in a separate terminal:
```bash
cd frontend
npm run dev
```
*The Command Center dashboard will be accessible at `http://localhost:5173`.*

### Command 3: Run the Live Demo
From the repository root in a third terminal:

**Interactive Presenter Mode (Pauses for explanation):**
```powershell
.\venv\Scripts\Activate.ps1
python -m demo.run_demo
```

**Unattended / Automated Mode (Auto-advances through full resolution):**
```powershell
.\venv\Scripts\Activate.ps1
python -m demo.run_demo --auto-advance
```

### Command 4: Run Automated Test Suite
From the repository root (PowerShell):
```powershell
# Activate environment & set PYTHONPATH to repo root:
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."

# Run all 60 automated tests:
python -m pytest tests/ -v

# Run individual test modules:
python -m pytest tests/test_integration_full.py -v   # Full 28-event lineage, dedup & dashboard tests (26 tests)
python -m pytest tests/test_edge_pipeline.py -v      # Edge tracking, stitching, GPS, severity tests (29 tests)
python -m pytest tests/test_scan_router.py -v        # Video scan job dispatch & status API tests (5 tests)

# Run a specific single test by name:
python -m pytest -k "test_all_28_events_ingest_and_return_required_fields" -v

# Debug flags:
python -m pytest tests/ -s          # Show live print / stdout logs
python -m pytest tests/ -x          # Stop on first failure
python -m pytest tests/ --pdb       # Drop into interactive Python debugger on failure
```

### Command 5: Run Edge Pipeline with a Video File
```powershell
.\venv\Scripts\Activate.ps1
python -m edge.runner --bus BUS-01 --video "WhatsApp Video 2026-09-11 at 10.40.32 PM.mp4"
```

---

## 4. Step-by-Step Demo Instructions for Evaluators

1. **Open the Command Center**:
   - Open Chrome or any modern browser to `http://localhost:5173`.
   - Point out the title: *"SIH26124 • Mobile Urban Sensing Command Center"*.
   - Point out the 6-step lifecycle banner: *Detect $\rightarrow$ Log $\rightarrow$ Verify $\rightarrow$ Prioritize $\rightarrow$ Escalate $\rightarrow$ Resolve*.
   - Show the live Leaflet map and active transit buses.

2. **Trigger Initial Detection (BUS-01)**:
   - Run `python -m demo.run_demo`.
   - Within 4 seconds, a new High-Severity Pothole card appears in the Triage Feed and a red pin drops onto the map.
   - Click the incident card to open the Detail Drawer:
     - Review the YOLOv8 bounding-box snapshot.
     - Review the initial telemetry: Bus `BUS-01`, Route `ROUTE-RED`, Confirmations: `1`, Unique Buses: `1`.

3. **Demonstrate Multi-Bus Confirmation & Auto-Escalation (BUS-02)**:
   - As the script progresses, `BUS-02` drives over the same road segment and detects the same anomaly.
   - The backend correlates coordinates ($\le 15$ m) to the existing incident.
   - On the React dashboard:
     - The card updates with the purple badge: **"⚡ Verified by 2 Buses"**.
     - Severity auto-escalates from **High $\rightarrow$ Critical**.
     - Priority score increases on the gauge meter.
     - Incident status automatically advances from **NEW $\rightarrow$ VERIFIED**.
     - Observation timeline now lists detections from both `BUS-01` and `BUS-02`.

4. **Demonstrate Operational Resolution**:
   - In the Detail Drawer, click **Mark ASSIGNED** (dispatches work order).
   - Click **Mark IN PROGRESS** (crew begins repair).
   - Click **Mark RESOLVED** (repair verified).
   - The map pin turns **Green**, the incident counts update in the KPI ribbon, and the status history logs every step with timestamps.

---

## 5. Repository Publication & Git Hygiene

- **Remote Target**: `https://github.com/AribAsim/CityVision` (branch `main`).
- **History Cleaned**: Initialized fresh repository history with no prior clone history or corrupted packfile references.
- **Git Exclusions Configured (`.gitignore`)**:
  - Excluded all heavy video media (`*.mp4`, `demovideo.mp4`, `WhatsApp Video*.mp4`).
  - Excluded compressed archives (`stitch_city_vision_road_monitor.zip`).
  - Excluded temporary clones (`temp_clone/`), scratch scripts (`scratch/`), and test logs (`tests.txt`).
  - Excluded runtime databases (`*.db`, `*.sqlite`, `backend/road_anomalies.db`, `sih26124.db`).
  - Excluded generated runtime evidence, uploads, audit crops, and static snapshot images while maintaining directory stubs with `.gitkeep`.
  - Excluded virtual environments (`venv/`), `node_modules/`, and frontend build distributions (`dist/`).
  - Preserved canonical YOLOv8 weights (`RoadDetectionModel/.../weights/best.pt`) and all source modules across edge, backend, and frontend.
- **Documentation Overhaul (`README.md`)**: Replaced legacy single-script documentation with a comprehensive, professional README aligned with open-source and hackathon evaluation best practices:
  - Added architectural overview, system flow diagrams, and feature breakdowns across edge, backend, and frontend tiers.
  - Documented the custom YOLOv8m test benchmarks (mAP@0.5: 0.745), Kalman tracking, and post-track trajectory stitcher.
  - Added copy-pasteable local setup guides, demo instructions, and edge CLI runner examples.
  - Documented the 60-test automated verification suite and complete REST API reference table.
  - Linked all architecture governance specifications in `/brain`.

---


## 6. Future Scope (Post-MVP Roadmap)

1. **Edge Hardware Integration**: Deploy the edge runner as an optimized ONNX/TensorRT container on Raspberry Pi 5 or NVIDIA Jetson Orin Nano with physical USB cameras and GPS/IMU modules.
2. **MQTT Telemetry Broker**: Implement lightweight MQTT pub/sub messaging for low-bandwidth cellular transmission from buses to city servers.
3. **PostGIS & OpenLayers Migration**: Scale spatial clustering to enterprise PostgreSQL/PostGIS with road network topology snapping and historical heatmaps.
4. **Automated Work-Order Routing**: Connect the resolution lifecycle to municipal PWD depot ticketing systems (SAP, IBM Maximo, or municipal civic complaint portals).
5. **Citizen Crowdsourcing Fusion**: Correlate mobile sensing transit detections with citizen mobile app complaint reports to cross-validate citizen grievances automatically.
6. **Predictive Degradation AI**: Use time-series observation depth to model road surface deterioration rates before catastrophic pothole formation.

