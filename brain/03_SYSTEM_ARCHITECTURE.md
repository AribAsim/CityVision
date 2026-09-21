# System Architecture: SIH26124 MVP

## 1. High-Level Architecture Overview

The SIH26124 MVP demonstrates a complete vertical slice of a mobile sensing public transport platform:
```
[ Video Feed ]
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. EDGE DETECTOR (YOLOv8m best.pt + Supervision)           │
│    - Target Classes: Pothole, Crack, Crack-Severe,          │
│      Speed-Bump                                             │
└─────────────────────────────────────────────────────────────┘
      │ Detections (boxes, classes, confidences)
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. BUS SIMULATOR & 3. GPS SIMULATOR                         │
│    - Vehicle metadata (bus_id, route_id, speed_kmh)         │
│    - Geo trajectory interpolation (lat, lon, heading)       │
└─────────────────────────────────────────────────────────────┘
      │ Telemetry & Detection Context
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. EVENT BUILDER & 5. DEDUPLICATION & 6. SEVERITY ENGINE    │
│    - Severity scoring (Low / Medium / High / Critical)      │
│    - Priority score calculation (0 - 100)                   │
│    - Spatio-temporal deduplication & cooldown throttling    │
│    - Cropped image snapshot generation                      │
└─────────────────────────────────────────────────────────────┘
      │ Filtered Structured Ingestion Event (HTTP POST multipart)
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. FASTAPI BACKEND (backend/main.py, routers/, services/)   │
│    - Ingestion endpoint: POST /api/ingest                   │
│    - Scan management: POST /api/scan/start, GET status      │
│    - Automated spatial correlation & incident grouping      │
│    - Tracks confirmation_count & unique_bus_count           │
│    - Multi-bus severity escalation (escalates 1 tier, max   │
│      Critical)                                              │
│    - REST endpoints for Dashboard & Lifecycle actions       │
└─────────────────────────────────────────────────────────────┘
      │ Read / Write (SQLAlchemy ORM)
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. SQLITE DATABASE (Embedded database: sih26124.db)        │
│    - Incidents table & Observations log                     │
└─────────────────────────────────────────────────────────────┘
      │ Near-Real-Time 4s Polling / REST API (JSON)
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. REACT FRONTEND (Vite + TypeScript)                       │
│    - Run Bus Scan panel (video upload → detection trigger)  │
│    - Incident triage list with priority scores              │
│    - "Verified by X Buses" badges                           │
│    - React Leaflet + OpenStreetMap GIS map                  │
│    - Recharts incident analytics                            │
│    - Status lifecycle management (Pending -> In Progress    │
│      -> Resolved)                                           │
└─────────────────────────────────────────────────────────────┘
```

### Video Upload → Detection → Logging Flow (Run Bus Scan)
```text
React Run Bus Scan
        ↓
FastAPI processing trigger
        ↓
Existing Edge Runner
        ↓
YOLOv8m
        ↓
Event Builder
        ↓
POST /api/ingest
        ↓
SQLite
        ↓
React polling
```

---

## 2. Directory Structure Convention

```text
d:\Al websites\sih2026-mvp\
├── brain/                   # Architecture & specifications (Ground truth)
├── edge/                    # Edge detector & vehicle simulator
│   ├── main.py              # Edge CLI runner
│   ├── detector.py          # YOLOv8 inference wrapper
│   ├── bus_sim.py           # Bus metadata & telemetry
│   ├── gps_sim.py           # Route waypoint GPS interpolation
│   ├── event_builder.py     # Payload & snapshot packaging
│   ├── deduplicator.py      # Spatial & temporal cooldown filter
│   └── severity_engine.py   # Anomaly scoring & priority logic
├── backend/                 # FastAPI REST API
│   ├── main.py              # Entrypoint (uvicorn backend.main:app)
│   ├── database.py          # SQLite engine & session setup
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── routers/             # API routes (ingest, incidents, analytics)
│   │   ├── ingest.py
│   │   ├── incidents.py
│   │   └── analytics.py
│   └── services/            # Incident correlation & escalation logic
│       └── incident_service.py
├── frontend/                # React + TypeScript + Vite dashboard
│   ├── src/
│   │   ├── api/             # Typed API client
│   │   ├── components/      # Map, Triage Feed, Analytics, Details Drawer
│   │   ├── types/           # TypeScript interfaces matching schemas
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── RoadDetectionModel/      # [UNTOUCHED] Original model weights
└── main.py                  # [UNTOUCHED] Original Streamlit application
```

---

## 3. Module Boundaries & Responsibilities

### Module 1: Edge Detector (`edge/detector.py`)
- **Responsibility**: Loads `RoadDetectionModel/RoadModel_yolov8m.pt_rounds120_b9/weights/best.pt` using `ultralytics.YOLO`.
- **Target Classes**: `Pothole`, `Crack`, `Crack-Severe`, `Speed-Bump`.
- **Inputs**: Video frame (`numpy.ndarray`).
- **Processing**: Runs inference using confidence threshold (default: 0.35). Uses `supervision.Detections` for bounding box and label parsing.
- **Outputs**:
  ```python
  class RawDetection:
      class_name: str       # "Pothole", "Crack", "Crack-Severe", "Speed-Bump"
      confidence: float     # 0.0 - 1.0
      bbox: list[int]       # [x1, y1, x2, y2]
  ```
- **Boundary Constraint**: Detector does not know about network, database, or GPS.

---

### Module 2: Bus Simulator (`edge/bus_sim.py`)
- **Responsibility**: Represents physical bus metadata.
- **State**: `bus_id` (e.g., `"DL-1PB-4501"`), `route_id` (e.g., `"ROUTE-42A"`), simulated instantaneous speed (`speed_kmh`).
- **Boundary Constraint**: Supplies vehicle identification and speed telemetry.

---

### Module 3: GPS Simulator (`edge/gps_sim.py`)
- **Responsibility**: Interpolates realistic coordinates along a predefined waypoint array.
- **Mechanism**: Calculates `latitude`, `longitude`, and `heading_deg` synchronized to video playback time or frame count.
- **Boundary Constraint**: Pure location generator (`get_current_location(frame_idx, fps) -> LocationData`).

---

### Module 4: Event Builder (`edge/event_builder.py`)
- **Responsibility**: Merges RawDetection, Bus telemetry, LocationData, and image snapshot into `EdgeEventCreate`.
- **Processing**:
  - Extracts/annotates frame snapshot around the anomaly.
  - Generates client-side `edge_event_id` (UUID4).
  - Encodes image bytes as JPEG for HTTP multipart upload.

---

### Module 5: Event Deduplication (`edge/deduplicator.py`)
- **Responsibility**: Prevents frame-by-frame network spam for the same physical road defect.
- **Mechanism**:
  - **Temporal Cooldown**: Suppresses duplicate network dispatches for the same class within $T_{\text{cooldown}}$ seconds (default: 2.5s).
  - **Spatial Radius**: Suppresses duplicate dispatches if within $R_{\text{distance}}$ (default: 12 meters).
  - **Visual Continuity**: Detections remain visibly outlined on the edge display window even while network events are throttled.

---

### Module 6: Severity Engine (`edge/severity_engine.py` & `backend/services/incident_service.py`)
- **Responsibility**: Computes baseline severity rating and numeric priority score (0–100).
- **Baseline Scoring**:
  - `Pothole`: base score = 70
  - `Crack-Severe`: base score = 55
  - `Crack`: base score = 30
  - `Speed-Bump`: base score = 20
  - Score scaled by confidence and bounding box area ($>4\%$ area adds $+15$).
- **Baseline Severity Mapping**:
  - Score $\ge 75$: **Critical**
  - Score $50 - 74$: **High**
  - Score $30 - 49$: **Medium**
  - Score $< 30$: **Low**
- **Multi-Bus Escalation Rule**:
  - When `unique_bus_count >= 2`: The incident escalates by **one tier** (e.g., Medium $\rightarrow$ High, High $\rightarrow$ Critical). Maximum tier is **Critical**.

---

### Module 7: Behavior Analyzer (`edge/behavior_analyzer.py`)
- **Responsibility**: Detects VRU proximity risks and hit-and-run candidates, gates ANPR inference.
- **VRU Proximity Risk**: Computes Euclidean distance between pedestrian/cyclist bounding boxes and moving vehicle boxes in pixel space (< 110px) or on zebra crossings.
- **Hit-and-Run Candidate**: Evaluates rolling 60-frame track history. Flags candidate if a pedestrian track vanishes post-proximity while a vehicle continues without decelerating.
- **ANPR Gating**: Activates ANPR inference only for `ANPR_TRIGGER_FRAMES = 45` frames post rash driving or hit-and-run candidate detection.

---

### Module 8: Density Accumulator (`edge/density_accumulator.py`)
- **Responsibility**: Buffers vehicle detection counts into discrete ~250m GPS spatial cells (`f"{route_id}:{int(lat*200)/200:.3f}:{int(lon*200)/200:.3f}"`).
- **Mechanism**: Computes peak concurrent vehicle counts per class across the segment window to avoid overcounting stationary objects across video frames.
- **Flushing**: Dispatches batched summaries to `POST /api/telemetry/density` upon entering new spatial cell or at end-of-stream.

---

### Module 9: Waterlogging Heuristic (`edge/waterlogging_heuristic.py`)
- **Responsibility**: Zero-model classical CV specular reflection detection.
- **Mechanism**: Inspects lower 40% of the frame (road surface zone). Analyzes HSV color space for low saturation ($S < 45$) and high brightness ($V > 195$). Flags `Waterlogging-Candidate` if specular reflection exceeds 8% of total frame area.

---

### Module 10: FastAPI Backend (`backend/`)
- **Responsibility**: Central REST API, ingestion gateway, analytics engine, and report generator.
- **Components**:
  - Entrypoint: `backend/main.py` (`uvicorn backend.app.main:app`).
  - `POST /api/ingest`: Accepts multipart `event_data` JSON and `image_file`.
  - `POST /api/telemetry/density`: Ingests batched vehicle density records and updates congestion indices.
  - `GET /api/telemetry/density/bottlenecks`: Ranked congestion chokepoints.
  - `GET /api/telemetry/density/delay`: Route travel time variance vs baseline.
  - `GET /api/telemetry/density/od`: Origin-Destination vehicle volume matrix.
  - `GET /api/reports/infrastructure-deficiency`: Audit summary of expected vs observed signage.
  - `GET /api/reports/infrastructure-deficiency.pdf`: ReportLab PDF export.
  - `GET /api/reports/route-performance.pdf`: ReportLab PDF export.
  - `POST /api/scan/start`: Accepts `.mp4` video upload, validates bus/route, and triggers `edge/runner.py`.
  - `GET /api/scan/status/{job_id}`: Returns real-time scan job status (`PROCESSING`, `COMPLETED`, `FAILED`).

---

### Module 11: SQLite Database (`backend/database.py`)
- **Responsibility**: Embedded, portable storage (`sih26124.db`).
- **Entities**:
  - `Incident`: Unique physical road anomaly entity.
  - `Observation`: Individual edge observation linked to parent `Incident`.
  - `StatusHistory`: Audit log of lifecycle transitions.
  - `Bus`: Fleet telemetry records.
  - `PlateRead`: Incident-linked or safety-triggered ANPR reads.
  - `InfraObservation`: Road sign and corridor infrastructure elements.
  - `TrafficDensity`: Segment-level vehicle counts, class breakdown, and congestion index.

---

### Module 12: React Frontend (`frontend/`)
- **Responsibility**: Command center and transport authority portals.
- **Tech Stack**: React 19, TypeScript, Vite, MapLibre GL JS, React Leaflet (OpenStreetMap), Recharts.
- **Key Features**:
  - **3-Button Role Switcher**: Command Center | Transport Authority | Field Official.
  - **Transport Authority View**:
    - MapLibre GL JS density heatmap with real-time intensity weights.
    - Corridor chokepoints and bottlenecks table.
    - Recharts route delay variance chart.
    - Infrastructure deficiency audit table with one-click PDF export.
    - Origin-Destination flow matrix table.
  - Interactive GIS map with severity-coded pins.
  - Priority triage feed showing severity pills, priority score (0–100), and "Verified by X Buses" badges.
  - Modal/drawer to inspect snapshots and historical observations.
  - One-click workflow transition (`Pending` $\rightarrow$ `In Progress` $\rightarrow$ `Resolved`).

