# Technical Decisions: SIH26124 MVP

This document records the architectural and technology decisions for SIH26124.

---

## 1. Edge / AI Layer

| Decision | Selection | Rationale | Alternatives Rejected |
| :--- | :--- | :--- | :--- |
| **Model Reused** | Custom YOLOv8m (`RoadModel_yolov8m.pt_rounds120_b9/weights/best.pt`) | Already trained and validated in this repository (mAP@0.5 = 0.745). Directly detects `Pothole`, `Crack`, `Crack-Severe`, and `Speed-Bump`. | Replacing with YOLOv9/v11 or retraining (violates agent rule #3 & #4). |
| **Edge Environment** | Python 3.10+ / OpenCV / Supervision | Native environment for Ultralytics YOLO; matches existing repo scripts (`main.py`, `run.py`, `run2model.py`). | ONNX Web / TensorFlow.js (unnecessary conversion overhead, potential precision loss). |
| **Simulation Strategy** | Decoupled Video Driver + Synthetic GPS | Enables deterministic testing and predictable hackathon demos without requiring live vehicle hardware. | Real-time Android / Raspberry Pi hardware integration (out of scope for MVP). |

---

## 2. Ingestion & Communication Protocol

| Decision | Selection | Rationale | Alternatives Rejected |
| :--- | :--- | :--- | :--- |
| **Protocol** | HTTP / REST (`POST /api/ingest` multipart) | Simple, stateless, universally debuggable, and perfectly suitable for throttled anomaly events. | MQTT / WebSockets for edge (excessive complexity and broker setup for a hackathon MVP). |
| **Deduplication** | Dual-Tier (Client-side cooldown + Server-side spatial clustering) | Prevents network saturation while also aggregating reports when multiple simulated buses report the same pothole. | Unthrottled raw transmission (would flood the database with 30-60 events per second per pothole). |

---

## 3. Backend Tier

| Decision | Selection | Rationale | Alternatives Rejected |
| :--- | :--- | :--- | :--- |
| **Framework** | FastAPI (Python) | High performance, async support, native Pydantic integration, and automatic Swagger docs. | Django (too heavy), Flask (synchronous, manual validation). |
| **ORM / Data Access**| SQLAlchemy 2.0 (or SQLModel) | Mature typing, seamless schema migrations, and clean separation between models and schemas. | Raw SQL cursor queries (fragile), full enterprise micro-ORMs. |
| **Database** | SQLite (`sih26124.db`) | Zero configuration, zero external service dependency, single-file portability for hackathon judging. | PostgreSQL / PostGIS (violates MVP constraints; unnecessary operational overhead). |

---

## 4. Frontend Tier

| Decision | Selection | Rationale | Alternatives Rejected |
| :--- | :--- | :--- | :--- |
| **Build & Language** | Vite + React + TypeScript | Fast HMR, strict type-safety aligned with Pydantic contracts, and lightweight build output. | Next.js (SSR unnecessary for an internal command dashboard), CRA (deprecated). |
| **GIS Mapping** | React Leaflet + OpenStreetMap | Free, zero API key required, reliable tile loading, easy custom markers for severity coloring. | Google Maps API (requires billing and API keys), Mapbox (token friction). |
| **Charts** | Recharts | Declarative React SVG charting library, ideal for defect breakdown and resolution stats. | D3.js (too low-level for hackathon pace), Chart.js (canvas-based). |
| **UI Updates** | Periodic Polling (e.g. 3-5s interval) | Extremely robust for demo environments; eliminates socket reconnection failure modes. | WebSockets / SSE (can be added later; polling guarantees rock-solid hackathon demo reliability). |

---

## 5. Architectural Non-Goals & Strict Exclusions (Phase 0 / MVP)

- **No Microservices**: Edge, Backend, and Frontend are modular within a single repo structure.
- **No Heavy Message Queues**: No Kafka, RabbitMQ, or Celery. Ingestion is handled directly in FastAPI.
- **No Cloud Services**: Runs 100% locally on localhost without AWS, Azure, or GCP requirements.
- **No Auth / RBAC Complexity**: Direct access to command center for demo clarity.

---

---

# Phase 1–8 Full-Scope Stack Decisions
> **Version:** v2 — Post-MVP expansion. All decisions below supersede or extend the Phase 0 MVP decisions above.
> Feature flags preserve full backward compatibility with the Phase 0 demo mode.

---

## 6. Infrastructure Layer (Phase 1)

| Decision | Selection | Rationale | Alternatives Rejected |
| :--- | :--- | :--- | :--- |
| **Relational + Spatial DB** | PostgreSQL 16 + PostGIS 3 (Docker: `timescale/timescaledb-ha`) | Unlocks accurate spatial fusion via `ST_DWithin`, GeoJSON endpoints, and heatmap data. Single container replaces SQLite for production path. | MySQL + spatial extensions (weaker PostGIS ecosystem); separate Postgres + PostGIS + TimescaleDB containers (unnecessary operational split). |
| **Time-Series DB** | TimescaleDB extension (same container as PostGIS) | One database, three capabilities: relational + spatial + time-series. Avoids running 3 separate DB engines. `time_bucket` enables per-segment traffic density queries. | InfluxDB (separate engine, separate client library, additional operational overhead). |
| **Schema Migrations** | Alembic | Mature, SQLAlchemy-native migration tool. Revision history provides auditable rollback path. | Manual `CREATE TABLE` statements (fragile, no rollback); Flyway (Java-native, mismatched ecosystem). |
| **Object Storage** | MinIO (Docker, S3-compatible) | Replaces local `/static/snapshots` folder with S3-API-compatible evidence storage. Same API shape as AWS S3 — zero code change needed if moving to real cloud later. Local disk fallback preserves demo reliability when MinIO is down. | AWS S3 (requires cloud account + billing); local disk only (not scalable, can't serve from multiple nodes). |
| **Feature Flag Protocol** | Environment variables (`DATABASE_URL`, `TIMESCALE_ENABLED`, `MINIO_ENABLED`, `MQTT_ENABLED`, `AUTH_ENABLED`) | Zero-dependency, universally supported. SQLite fallback active by default — MVP demo mode is always one env-var away. | Runtime config tables (too heavy); build-time flags (inflexible). |

---

## 7. Edge Layer Extensions (Phases 2–3)

| Decision | Selection | Rationale | Alternatives Rejected |
| :--- | :--- | :--- | :--- |
| **Infrastructure Model** | New YOLOv8s fine-tuned on DriveIndia, saved to `RoadDetectionModel/TrafficInfraModel_yolov8s/` | Separate model file and detector class (`edge/infra_detector.py`) ensures zero risk of corrupting the existing road anomaly model. DriveIndia covers 24 Indian traffic classes in one dataset — high leverage. | Extending the existing YOLOv8m (violates agent rule #6); Roboflow Indian Roads set (smaller, faster but less class coverage). |
| **ANPR Pipeline** | Two-stage: YOLOv8n plate detector → EasyOCR | YOLOv8n is fast enough for edge; EasyOCR handles degraded Indian plates reasonably. Plate reads are informational only (not enforcement). | End-to-end OCR models (lower accuracy on Indian plates); commercial ANPR APIs (require keys, violate $0 constraint). |
| **Behavior Analysis** | Rule-based heuristic layer on top of ByteTrack output | No new model required. Standard ITS technique: TTC, speed thresholds, track-disappearance proximity. Clearly marked `candidate_only=True` in all outputs. | ML-based behavior classification (requires labeled behavior dataset; excessive for non-enforcement heuristic). |
| **Secure Transmission** | Eclipse Mosquitto MQTT broker (Docker) + paho-mqtt on edge | Adds the poster's literal "HTTPS/MQTT" label as a genuinely working path. TLS via self-signed cert for demo. Same `message_id` on both HTTP and MQTT paths prevents double-ingestion. | Kafka (excessive for 3-bus demo scale); NATS (less familiar, fewer examples). |

---

## 8. Backend Extensions (Phases 4–6)

| Decision | Selection | Rationale | Alternatives Rejected |
| :--- | :--- | :--- | :--- |
| **Auth / RBAC** | FastAPI-Users (JWT strategy) | Native FastAPI integration, 4 roles (`COMMAND_CENTER`, `TRANSPORT_AUTHORITY`, `FIELD_OFFICIAL`, `CITIZEN`). `AUTH_ENABLED=false` default means the demo remains open-access. | Auth0 / Firebase Auth (cloud dependency, API keys); DIY JWT (reinventing the wheel). |
| **GIS Endpoints** | PostGIS `ST_AsGeoJSON` + optional `pg_tileserv` | Serves road segment polygons and incident points as GeoJSON directly from the database. Eliminates manual coordinate serialization. | Geoserver (Java, too heavy); raw coordinate arrays in JSON (no spatial indexing). |
| **Forecasting** | Prophet (Meta, open-source) | Handles weekly/daily seasonality, requires minimal data preparation, runs locally. Outputs are ranges, not point predictions. Clearly labelled experimental. | ARIMA (harder to tune for irregular incident data); LSTM (requires more data and GPU). |
| **PDF Reports** | WeasyPrint | Python-native, HTML/CSS → PDF. No external service. Note: requires GTK/Cairo on Windows — Docker-based alternative acceptable if native install is blocked. | ReportLab (lower-level, more verbose); wkhtmltopdf (less actively maintained). |
| **Webhook Adapter** | Generic outbound webhook dispatcher in `backend/app/routers/webhooks.py` | Pattern-based: any municipal system with an HTTP endpoint can receive events. `POST /api/webhooks/mock-receiver` provides a demoable target. | Zapier/Make (cloud dependency); direct SAP/Maximo API calls (no real target system exists). |

---

## 9. Frontend Extensions (Phases 6–7)

| Decision | Selection | Rationale | Alternatives Rejected |
| :--- | :--- | :--- | :--- |
| **Heatmap Layer** | MapLibre GL JS heatmap layer | WebGL-accelerated, handles large point datasets. Open-source, no API key. Fed by Phase 4 TimescaleDB density data. | Leaflet.heat (canvas-based, performance degrades at scale); Mapbox (token required). |
| **Role Switching (Demo)** | Role Badge in top header + `/field` route | No login required in demo mode. Role is toggled via demo-mode selector. Field Official view auto-applies mobile-responsive narrow layout at `/field`. | Full login screen (adds friction for judges); separate apps per role (excessive complexity). |
| **Citizen Portal** | Same React app, new `/citizen` route | Public read-only map + `CitizenReportForm`. Submission returns `report_id` + status page. No new tech stack. | Separate static HTML page (no shared component reuse); third-party form service (cloud dependency). |
