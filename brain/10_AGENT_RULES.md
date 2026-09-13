# Agent Rules: SIH26124

The following rules are mandatory for all coding agents and contributors working on SIH26124.

> **Version:** v2 — Updated for Full-Scope Post-MVP Expansion (Phases 1–8).
> Phase 0 (MVP) rules that were correct for the hackathon are superseded where noted below.
> See `09_TECH_DECISIONS.md` v2 for the authoritative stack decisions.

---

## 1. Ground Truth & Architecture
1. **The `/brain` directory is the single source of truth**:
   Never assume or invent architecture. Always review `/brain` before proposing or making changes.
2. **Stable Module Boundaries**:
   Implement modular code within the designated boundaries:
   - `edge/`: Edge detector, infra detector, ANPR pipeline, bus simulator, GPS simulator, event builder, behavior analyzer, MQTT publisher, deduplicator, severity engine.
   - `backend/`: FastAPI application, database schemas (Postgres + PostGIS + TimescaleDB), incident correlation, auth, GIS endpoints, analytics engine, webhook adapter.
   - `frontend/`: React + TypeScript + Vite dashboard with Leaflet/MapLibre, Recharts, and role-specific views.
   - `alembic/`: Database migration scripts — all schema changes go through Alembic revisions.

---

## 2. Model & AI Preservation
3. **Never retrain the existing YOLO model** unless explicitly directed by the user.
4. **Never replace the existing model** (`RoadDetectionModel/RoadModel_yolov8m.pt_rounds120_b9/weights/best.pt`) with another model without prior approval.
5. **Preserve existing repository files**:
   Do NOT touch or overwrite `main.py`, `run.py`, `run2model.py`, `train.ipynb`, or `.streamlit/`. All new functionality must reside in new modular directories.
6. **New models get new directories**:
   Fine-tuned or new models (e.g., `TrafficInfraModel_yolov8s`, ANPR plate detector) must be saved to their own subdirectory under `RoadDetectionModel/` and loaded by a new, separate detector class. Never share a weights file between detector classes.

---

## 3. Technology & Framework Constraints
7. **Current approved technology stack** (supersedes MVP v1 exclusions):
   - Edge: Python, OpenCV, Ultralytics YOLOv8, Supervision, EasyOCR, paho-mqtt.
   - Backend: Python, FastAPI, PostgreSQL + PostGIS + TimescaleDB (Docker), SQLAlchemy 2.0, Alembic, MinIO (boto3/minio-py), FastAPI-Users, Prophet, WeasyPrint.
   - Frontend: React, TypeScript, Vite, React Leaflet + MapLibre GL, Recharts, TailwindCSS.
   - Infrastructure: Docker Compose (self-hosted, $0), Eclipse Mosquitto MQTT broker.
8. **Never introduce a new framework** when an existing or specified framework can solve the problem.
9. **Feature flags govern stack activation** — new infrastructure components must be gated:
   - `DATABASE_URL` — defaults to SQLite if unset (preserves MVP fallback).
   - `TIMESCALE_ENABLED=false` — TimescaleDB analytics endpoints return seeded fallback data when false.
   - `MINIO_ENABLED=false` — evidence storage falls back to local `/data/evidence/` disk path.
   - `MQTT_ENABLED=false` — MQTT publish is skipped; HTTP POST remains the only transport.
   - `AUTH_ENABLED=false` — FastAPI-Users guards are bypassed; all endpoints remain publicly accessible for demo mode.

---

## 4. Data Integrity & API Contracts
10. **Do not silently change API contracts**:
    If an endpoint schema changes, update `04_DATA_CONTRACTS.md` and `05_API_CONTRACT.md` in `/brain` first.
11. **Schema versioning over mutation**:
    New fields added to `EdgeEventCreate` or any shared payload must use `schema_version: 2` (or higher) tagging. Existing v1 consumers must continue to receive v1-compatible shapes without modification.
12. **Assign `message_id` (UUID4) to every edge event** at creation time in `edge/event_builder.py`. The backend must check `message_id` uniqueness before the spatial dedup step to prevent double-ingestion from dual HTTP+MQTT transport.
13. **Do not hardcode backend data in the frontend**:
    All UI telemetry, map coordinates, incident lists, and metrics must be fetched dynamically from the FastAPI backend. Seed data in `frontend/src/services/seedData.ts` is only used as an offline fallback when the backend is unreachable.

---

## 5. Regression & Migration Safety
14. **Phase 1 regression gate is mandatory**:
    All 60 automated tests (`python -m pytest tests/ -v`) must pass against the Postgres backend before Phase 2 begins. Do not advance phases with a broken test suite.
15. **Alembic for all schema changes**:
    Never modify the database schema by hand or by dropping/recreating tables. All schema changes must go through `alembic revision --autogenerate` + `alembic upgrade head`.
16. **Keep `sih26124.db` (SQLite) intact** during Phase 1 migration. It serves as a read-only fallback and reference during the migration window.
17. **Keep changes small and modular**:
    Write clean, readable code and verify after meaningful changes.
18. **Always update `11_IMPLEMENTATION_STATUS.md`** after completing any phase or milestone.

---

## 6. Behavior Analysis & ANPR — Scope & Honesty Rules
19. **Behavior analysis events are heuristic-only**:
    Rash driving, VRU proximity risk, and hit-and-run detections must always be flagged as `candidate_only=True` and display `"⚠️ CANDIDATE — Requires Human Review"` in the UI. Never auto-escalate a behavior flag to a legal or enforcement action.
20. **ANPR plate reads are informational**:
    Plate text extracted by EasyOCR must include `plate_confidence` and must not be used for enforcement decisions within this system.
21. **Predictive insights (Prophet) are experimental**:
    Any predictive panel in the UI must carry a persistent `"⚠️ EXPERIMENTAL — Research Mode"` badge. Outputs must be presented as ranges, not point predictions.

---

## 7. Integration Honesty
22. **External integrations are demonstrated against mock receivers**:
    No live municipal, emergency, or government system exists to integrate with. Webhook dispatch and MQTT publishing must be demoed against `POST /api/webhooks/mock-receiver` and document this clearly in `docs/INTEGRATION_CONTRACT.md`.

