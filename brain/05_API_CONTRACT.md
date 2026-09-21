# API Contract: SIH26124 MVP

Base URL: `http://localhost:8000`

This document details the implemented REST API endpoints for the SIH26124 backend.

---

## 1. System Health

### `GET /api/health`
- **Description**: Verifies backend availability.
- **Response**: `200 OK`
  ```json
  {
    "status": "ok",
    "service": "SIH26124 Road Anomaly Platform"
  }
  ```

---

## 2. Ingestion & Event Intelligence

### `POST /api/ingest`
- **Description**: Multipart ingestion endpoint for edge devices. Accepts structured detection JSON and an optional snapshot evidence image. Runs spatial clustering (15m radius), multi-bus verification, and dynamic severity escalation.
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `event_data`: Stringified JSON matching `EdgeEventCreate`.
  - `image_file`: Binary JPEG image upload (optional).
- **Response**: `201 Created`
  ```json
  {
    "id": 1,
    "incident_id": "INC-7F39E21A",
    "anomaly_type": "Pothole",
    "severity": "High",
    "priority_score": 78,
    "status": "NEW",
    "latitude": 28.613939,
    "longitude": 77.209021,
    "first_detected_at": "2026-09-11T14:30:15Z",
    "last_detected_at": "2026-09-11T14:30:15Z",
    "confirmation_count": 1,
    "unique_bus_count": 1,
    "primary_image_url": "/static/snapshots/EVT-01.jpg"
  }
  ```

### `POST /api/ingest/json`
- **Description**: Direct JSON ingestion endpoint for edge devices without image file attachment.
- **Content-Type**: `application/json`
- **Request Body**: `EdgeEventCreate` schema.
- **Response**: `201 Created` (same schema as above).

---

## 3. Traffic Density & Corridor Telemetry

### `POST /api/telemetry/density`
- **Description**: Ingests batched segment density observations (~250m GPS cells) from the edge pipeline. Automatically computes congestion index based on corridor baseline capacity.
- **Request Body**: `VehicleDensityCreate`
- **Response**: `201 Created` (`VehicleDensityResponse`)

### `GET /api/telemetry/density`
- **Query Params**: `route_id` (optional), `hours` (default: 24), `limit` (default: 200)
- **Response**: `200 OK` (list of `VehicleDensityResponse`)

### `GET /api/telemetry/density/bottlenecks`
- **Query Params**: `route_id` (optional), `top_n` (default: 5)
- **Response**: `200 OK` (list of ranked congestion chokepoints with congestion index, coordinates, and status)

### `GET /api/telemetry/density/delay`
- **Query Params**: `route_id` (default: "ROUTE-RED")
- **Response**: `200 OK` (`baseline_minutes`, `actual_minutes`, `delay_minutes`, `status`, `avg_congestion_index`)

### `GET /api/telemetry/density/od`
- **Query Params**: `route_id` (optional)
- **Response**: `200 OK` (list of origin-destination transitions with estimated volume and average congestion)

---

## 4. Infrastructure Audits & Reports

### `GET /api/reports/infrastructure-deficiency`
- **Query Params**: `route_id` (optional)
- **Response**: `200 OK` (audit comparison of expected vs observed signs/assets with deficiency score)

### `GET /api/reports/infrastructure-deficiency.pdf`
- **Response**: `200 OK` (`application/pdf` binary download)

### `GET /api/reports/route-performance`
- **Query Params**: `route_id`
- **Response**: `200 OK` (route travel time variance and delay metrics)

### `GET /api/reports/route-performance.pdf`
- **Response**: `200 OK` (`application/pdf` binary download)

---

## 5. Road Defect Incidents

### `GET /api/incidents`
- **Description**: Retrieves road defect incidents sorted by most recent observation timestamp (`last_detected_at` descending).
- **Query Parameters**:
  - `status`: Filter by `"NEW"`, `"VERIFIED"`, `"ASSIGNED"`, `"IN_PROGRESS"`, `"RESOLVED"`.
  - `severity`: Filter by `"Low"`, `"Medium"`, `"High"`, `"Critical"`.
  - `anomaly_type`: Filter by `"Pothole"`, `"Crack"`, `"Crack-Severe"`, `"Speed-Bump"`.
- **Response**: `200 OK` (Array of `IncidentSummaryResponse` objects).

### `GET /api/incidents/{incident_id}`
- **Description**: Retrieves complete incident details by `incident_id` (e.g. `INC-7F39E21A` or primary key integer), including chronological observations and audit history.
- **Response**: `200 OK` (`IncidentDetailResponse`) or `404 Not Found`.

### `PATCH /api/incidents/{incident_id}/status`
- **Description**: Updates the operational resolution lifecycle status. Strictly validates allowed state transitions (`NEW -> VERIFIED -> ASSIGNED -> IN_PROGRESS -> RESOLVED`).
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "status": "ASSIGNED",
    "notes": "Work order dispatched to Central PWD Depot"
  }
  ```
- **Response**: `200 OK` (Updated `IncidentDetailResponse`) or `400 Bad Request` (Invalid transition).

---

## 4. Bus Fleet Telemetry

### `GET /api/buses`
- **Description**: Retrieves all tracked public transport buses with latest GPS position, status, and last seen timestamp.
- **Response**: `200 OK`
  ```json
  [
    {
      "id": 1,
      "bus_id": "BUS-01",
      "route_id": "ROUTE-RED",
      "status": "Active",
      "latitude": 28.6329,
      "longitude": 77.2195,
      "last_seen": "2026-09-11T14:51:53.791683"
    }
  ]
  ```

---

## 5. Analytics & KPIs

### `GET /api/analytics/summary`
- **Description**: Delivers aggregate KPI metrics for dashboard visualizations.
- **Response**: `200 OK`
  ```json
  {
    "total_incidents": 12,
    "pending_count": 4,
    "verified_count": 3,
    "assigned_count": 2,
    "in_progress_count": 2,
    "resolved_count": 1,
    "multi_bus_verified_count": 3,
    "active_buses": 3,
    "by_anomaly_type": {
      "Pothole": 6,
      "Crack-Severe": 3,
      "Crack": 2,
      "Speed-Bump": 1
    },
    "by_severity": {
      "Critical": 3,
      "High": 5,
      "Medium": 3,
      "Low": 1
    }
  }
  ```

---

## 6. Static Snapshot Media

### `GET /static/snapshots/{filename}`
- **Description**: Serves snapshot evidence images stored on the backend.
- **Response**: Binary image stream (`image/jpeg`, `image/png`).

---

## 7. Video Scan Management (Run Bus Scan)

### `POST /api/scan/start`
- **Description**: Triggers the edge YOLO detection pipeline (`edge/runner.py`) as an asynchronous background subprocess for an uploaded `.mp4` video.
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `bus_id`: Required string (`"BUS-01"`, `"BUS-02"`, `"BUS-03"`).
  - `route_id`: Optional string (`"ROUTE-RED"`, `"ROUTE-BLUE"`, `"ROUTE-GREEN"`).
  - `video_file`: Required `.mp4` binary video upload.
- **Response**: `200 OK`
  ```json
  {
    "job_id": "9f323a67-0c2b-4e6a-bc01-e2e1a3bc42df",
    "status": "PROCESSING",
    "message": "BUS-01 scan initiated for sample.mp4"
  }
  ```

### `GET /api/scan/status/{job_id}`
- **Description**: Retrieves real-time status and live event dispatch count for an active or completed bus scan.
- **Response**: `200 OK`
  ```json
  {
    "job_id": "9f323a67-0c2b-4e6a-bc01-e2e1a3bc42df",
    "status": "PROCESSING",
    "events_dispatched": 4,
    "error": null
  }
  ```
- **Status values**: `"READY"`, `"UPLOADING"`, `"PROCESSING"`, `"COMPLETED"`, `"FAILED"`.
