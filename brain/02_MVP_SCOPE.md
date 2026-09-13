# MVP Scope: SIH26124

## Included (In-Scope)

1. **Anomaly Classes Detected & Processed**
   - `Pothole`
   - `Crack`
   - `Crack-Severe`
   - `Speed-Bump`

2. **Simulated Edge Node (Python)**
   - Modular edge pipeline in `edge/` reusing the custom YOLOv8m weights (`best.pt`).
   - Processing test route video feeds.
   - Synthetic GPS telemetry interpolation (lat, lon, heading, speed).
   - Bus identification (`bus_id`, `route_id`).
   - Dual-tier deduplication (spatial radius + temporal cooldown).
   - Local bounding-box visualization window with real-time detection telemetry.
   - Dispatching structured multipart events (`EdgeEventCreate` JSON + JPEG snapshot) to FastAPI.

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
   - Automated spatial clustering to correlate observations into distinct `Incident` records.
   - Tracking `confirmation_count` and `unique_bus_count`.
   - Multi-bus severity escalation logic (escalates one tier upon multi-bus verification, capped at `Critical`).
   - Calculation and persistence of `priority_score` (0–100).
   - REST endpoints: `GET /api/incidents`, `GET /api/incidents/{id}`, `PATCH /api/incidents/{id}/status`, `GET /api/analytics/summary`.
   - Static snapshot image server at `/static/snapshots/{filename}`.
   - Status workflow strictly enforced: **Pending $\rightarrow$ In Progress $\rightarrow$ Resolved**.

4. **Authority Command Center (React + TypeScript + Vite)**
   - Near-real-time synchronization (4-second polling).
   - OpenStreetMap via React Leaflet with custom severity-colored markers.
   - Triage feed with status pills, priority scores, and "Verified by X Buses" badges.
   - High-resolution snapshot inspection drawer with observation timeline.
   - Interactive status update workflow (Pending $\rightarrow$ In Progress $\rightarrow$ Resolved).
   - Recharts visual analytics for incident breakdown and resolution tracking.

---

## Excluded (Out-of-Scope)
- Retraining or fine-tuning existing YOLOv8 models.
- Real physical hardware integration (Raspberry Pi / Jetson).
- Complex authentication / RBAC / JWT systems.
- PostgreSQL / PostGIS / Redis / MQTT / Cloud infrastructure.
- ANPR, hit-and-run detection, rash driving, driver behavior analysis.
- Live video streaming to the web dashboard (only snapshots and JSON events are transferred).
