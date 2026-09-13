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

## 5. Architectural Non-Goals & Strict Exclusions

- **No Microservices**: Edge, Backend, and Frontend are modular within a single repo structure.
- **No Heavy Message Queues**: No Kafka, RabbitMQ, or Celery. Ingestion is handled directly in FastAPI.
- **No Cloud Services**: Runs 100% locally on localhost without AWS, Azure, or GCP requirements.
- **No Auth / RBAC Complexity**: Direct access to command center for demo clarity.
