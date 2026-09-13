# SIH26124 Demo Orchestrator

This directory contains the automated demonstration script for the SIH26124 MVP evaluation.

It orchestrates the full vertical slice:
1. `BUS-01` Edge Detection
2. UI Triage Update
3. `BUS-02` Independent Multi-Bus Verification
4. Incident Resolution Lifecycle

## Prerequisites
Ensure the backend and frontend are running before starting the demo.

**Terminal 1 (Backend):**
```bash
python -m uvicorn backend.app.main:app --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

## Running the Demo

Run this from the repository root:
```bash
python -m demo.run_demo
```

This will run the interactive demo, pausing for the presenter to explain the dashboard and allowing them to manually click through the resolution stages.

### Unattended / Auto-Advance Mode
If you want the script to automatically step through the resolution lifecycle (`VERIFIED -> ASSIGNED -> IN_PROGRESS -> RESOLVED`), run:
```bash
python -m demo.run_demo --auto-advance
```

## Configuration
All parameters for the demo (coordinates, anomaly type, severity, bus IDs, and pause durations) are located in `scenario.json`. Edit this file to tweak the presentation without modifying code.
