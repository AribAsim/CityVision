# Agent Rules: SIH26124

The following rules are mandatory for all coding agents and contributors working on SIH26124.

---

## 1. Ground Truth & Architecture
1. **The `/brain` directory is the single source of truth**:
   Never assume or invent architecture. Always review `/brain` before proposing or making changes.
2. **Stable Module Boundaries**:
   Implement modular code within the designated boundaries:
   - `edge/`: Edge detector, bus simulator, GPS simulator, event builder, deduplicator, severity engine.
   - `backend/`: FastAPI application, database schemas, incident correlation, static file server.
   - `frontend/`: React + TypeScript + Vite dashboard with Leaflet and Recharts.

---

## 2. Model & AI Preservation
3. **Never retrain the existing YOLO model** unless explicitly directed by the user.
4. **Never replace the existing model** (`RoadDetectionModel/RoadModel_yolov8m.pt_rounds120_b9/weights/best.pt`) with another model without prior approval.
5. **Preserve existing repository files**:
   Do NOT touch or overwrite `main.py`, `run.py`, `run2model.py`, `train.ipynb`, or `.streamlit/`. All new functionality must reside in new modular directories (`edge/`, `backend/`, `frontend/`).

---

## 3. Technology & Framework Constraints
6. **Strictly follow the technology stack**:
   - Edge: Python, OpenCV, Ultralytics YOLOv8, Supervision.
   - Backend: Python, FastAPI, SQLite, SQLAlchemy/SQLModel, Pydantic.
   - Frontend: React, TypeScript, Vite, React Leaflet (OpenStreetMap), Recharts, TailwindCSS.
7. **Strictly prohibited technologies**:
   Do NOT introduce PostgreSQL/PostGIS, Redis, MQTT, microservices, Kubernetes, Docker Swarm, authentication systems, or cloud infrastructure.
8. **Never introduce a new framework** when an existing or specified framework can solve the problem.

---

## 4. Engineering & Hackathon Philosophy
9. **Optimize for a reliable hackathon demo**:
   Prioritize a robust end-to-end vertical slice over theoretical enterprise scalability or distributed system complexity.
10. **Do not implement future-scope features**:
    Features like ANPR, driver behavior analytics, rash driving detection, LLMs, or predictive degradation are strictly out of MVP scope.
11. **Do not hardcode backend data in the frontend**:
    All UI telemetry, map coordinates, incident lists, and metrics must be fetched dynamically from the FastAPI backend.
12. **Do not silently change API contracts**:
    If an endpoint schema changes, update `04_DATA_CONTRACTS.md` and `05_API_CONTRACT.md` in `/brain` first.
13. **Keep changes small and modular**:
    Write clean, readable code and verify after meaningful changes.
14. **Always update `11_IMPLEMENTATION_STATUS.md`** after completing any phase or milestone.
