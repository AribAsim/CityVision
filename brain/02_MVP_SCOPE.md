# MVP Scope: SIH26124

## Included (In-Scope)

1. **Anomaly Classes Detected & Processed**
   - `Pothole`
   - `Crack`
   - `Crack-Severe`
   - `Speed-Bump`
   - `Waterlogging-Candidate` (classical CV heuristic on road surface zone)

2. **Simulated Edge Node (Python)**
   - Modular edge pipeline in `edge/` reusing the custom YOLOv8m weights (`best.pt`).
   - Vehicle & pedestrian detection (`edge/vehicle_detector.py`) with density accumulation.
   - Traffic sign & infrastructure detection (`edge/infra_detector.py`).
   - Incident-triggered Indian license plate ANPR pipeline (`edge/anpr/`).
   - Behavior analysis (`edge/behavior_analyzer.py`): VRU proximity risk and hit-and-run candidate heuristics.
   - Density accumulator (`edge/density_accumulator.py`): aggregates vehicle counts per ~250m GPS cell.
   - Processing test route video feeds.
   - Synthetic GPS telemetry interpolation (lat, lon, heading, speed).
   - Bus identification (`bus_id`, `route_id`).
   - Dual-tier deduplication (spatial radius + temporal cooldown).
   - Local bounding-box visualization window with real-time detection telemetry.
   - Dispatching structured multipart events (`EdgeEventCreate` JSON + JPEG snapshot) to FastAPI.
   - Telemetry flushing to `POST /api/telemetry/density`.

3. **Central Backend (FastAPI + SQLite)**
   - Clean, standardized layout:
     ```text
     backend/
       main.py
       database.py
       models.py
       schemas.py
       routers/
       services/
     ```
   - Ingestion endpoint: `POST /api/ingest`.
   - Telemetry endpoints: `POST /api/telemetry/density`, `GET /api/telemetry/density`, bottlenecks, OD flows, delay analysis.
   - Corridor infrastructure deficiency audit endpoints: `GET /api/reports/infrastructure-deficiency` (.pdf and JSON).
   - Route performance delay endpoints: `GET /api/reports/route-performance` (.pdf and JSON).
   - Automated spatial clustering to correlate observations into distinct `Incident` records.
   - Tracking `confirmation_count` and `unique_bus_count`.
   - Multi-bus severity escalation logic (escalates one tier upon multi-bus verification, capped at `Critical`).
   - Calculation and persistence of `priority_score` (0–100).
   - Static snapshot image server at `/static/snapshots/{filename}`.
   - Status workflow strictly enforced: **Pending $\rightarrow$ In Progress $\rightarrow$ Resolved**.

4. **Authority Command Center & Transport Authority (React + TypeScript + Vite)**
   - 3-Button Role Switcher: Command Center | Transport Authority | Field Official.
   - Near-real-time synchronization (4-second polling).
   - OpenStreetMap via React Leaflet with custom severity-colored markers.
   - Transport Authority View with MapLibre GL JS density heatmap, bottlenecks table, route transit delay variance chart, infrastructure deficiency audit, and OD flow matrix.
   - Instant PDF generation & downloads for Municipal Work Orders, Infra Deficiency Audits, and Route Performance reports.
   - Triage feed with status pills, priority scores, and "Verified by X Buses" badges.
   - High-resolution snapshot inspection drawer with observation timeline.

---

## Excluded (Out-of-Scope)
- Retraining or fine-tuning existing YOLOv8 models.
- Real physical hardware integration (Raspberry Pi / Jetson).
- Complex authentication / RBAC / JWT systems.
- Production PostgreSQL / TimescaleDB / PostGIS migration (SQLite retained for zero-dependency portability).
- Live video streaming to the web dashboard (only snapshots and JSON events are transferred).
- MQTT message broker (Mosquitto/TLS deferred to post-MVP production deployment).

