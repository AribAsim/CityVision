# Demo Scenario: SIH26124 Presentation Script

This document details the exact sequence of events used during the hackathon evaluation and demo presentation.

---

## 1. Pre-Demo Setup
1. **Backend Running**:
   - `python -m uvicorn backend.app.main:app --port 8000`
   - SQLite database initialized (`sih26124.db`).
2. **Frontend Running**:
   - `npm run dev` in `frontend/` (accessible at `http://localhost:5173`).
   - Browser opened to the Command Center dashboard.

---

## 2. Live Demo Script (Step-by-Step)

### Step 1: Establish the Problem & Architecture (30 seconds)
- Point to the command center map: "Municipalities currently lack automated, real-time visibility into road surface degradation. We turn existing public transit buses into mobile sensing units."

### Step 2: Launch Demo Orchestrator
- Command:
  ```bash
  python -m demo.run_demo
  ```
- **Action**: The orchestrator simulates `BUS-01` approaching a pothole and logging it.

### Step 3: Near-Real-Time Dashboard Live Update (Within 4 seconds)
- On the React dashboard, a new card immediately appears in the Triage Feed.
- A red pin drops onto the Leaflet map at the exact GPS coordinate.
- The user clicks the card:
  - Anomaly snapshot image shows the captured pothole with bounding box and "SIH26124 DEMO" watermark.
  - Telemetry displays: Bus `BUS-01`, Route `ROUTE-RED`, Confirmations: `1`.
  - Severity: **High**. Status: **NEW**.

### Step 4: Multi-Bus Confirmation & Severity Escalation
- The orchestrator simulates `BUS-02` on a second run over the same route.
- When the second bus detects the same pothole location ($\le 15$ meters), FastAPI correlates the coordinates.
- On the React dashboard:
  - Incident updates its badge to **"Verified by 2 Buses"**.
  - `unique_bus_count` becomes 2.
  - Severity auto-escalates.
  - Priority score increases on the dashboard meter.
  - Status automatically transitions from `NEW` to `VERIFIED`.

### Step 5: Triage & Resolution Workflow
- The presenter acts as the municipal road authority:
  - Navigates to the Incident Details drawer.
  - Types optional notes and clicks the transition buttons:
  - `Mark ASSIGNED`
  - `Mark IN PROGRESS`
  - `Mark RESOLVED`
- Demonstrates the complete vertical slice from edge detection to city resolution.

*(Optional: Use `--auto-advance` flag for the orchestrator to automatically click through the resolution lifecycle for a hands-free demo.)*
