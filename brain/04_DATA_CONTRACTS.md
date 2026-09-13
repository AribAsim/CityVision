# Data Contracts: SIH26124 MVP

This document specifies the exact schemas and data models exchanged between Edge, Backend, SQLite, and Frontend.

---

## 1. Edge Ingestion Payload (`POST /api/ingest`)

Sent as `multipart/form-data`:
- `event_data`: Stringified JSON matching `EdgeEventCreate`.
- `image_file`: Binary image file (`image/jpeg`).

*(Direct JSON without file upload is also accepted via `POST /api/ingest/json`).*

### `EdgeEventCreate` Schema (Pydantic / TypeScript)

#### Version 1 (MVP Baseline)
```json
{
  "edge_event_id": "c7a8b89e-25f0-43b6-9bb2-094bfca2e329",
  "bus_id": "BUS-01",
  "route_id": "ROUTE-RED",
  "timestamp": "2026-09-11T14:30:15.120Z",
  "latitude": 28.613939,
  "longitude": 77.209021,
  "speed_kmh": 32.5,
  "anomaly_type": "Pothole",
  "confidence": 0.88,
  "bbox": [210, 340, 390, 480],
  "severity": "High",
  "priority_score": 78
}
```

#### Version 2 (Multi-Perception Expansion)
```json
{
  "schema_version": 2,
  "edge_event_id": "EVT-TRK1-4B29DA",
  "message_id": "MSG-9A23E07BF812",
  "bus_id": "BUS-01",
  "route_id": "ROUTE-RED",
  "timestamp": "2026-09-14T04:30:15.120Z",
  "latitude": 28.613939,
  "longitude": 77.209021,
  "speed_kmh": 32.5,
  "anomaly_type": "Pothole",
  "confidence": 0.88,
  "bbox": [210, 340, 390, 480],
  "severity": "High",
  "priority_score": 78,
  "nearby_plates": [
    {
      "plate_text": "DL01AB1234",
      "plate_confidence": 0.92,
      "ocr_confidence": 0.89,
      "bbox": [100, 200, 220, 260]
    }
  ],
  "nearby_signs": [
    {
      "sign_type": "speed-100",
      "confidence": 0.84,
      "bbox": [500, 100, 560, 160]
    }
  ]
}
```

Allowed `anomaly_type` values:
- `"Pothole"`
- `"Crack"`
- `"Crack-Severe"`
- `"Speed-Bump"`

Allowed `severity` values:
- `"Low"`, `"Medium"`, `"High"`, `"Critical"`

---

## 2. Database Models (SQLAlchemy)

### Table: `incidents`
Represents a physical road defect detected in the field.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Internal identifier |
| `incident_id` | String | Unique, Index | Human-readable ID (`INC-XXXXXX`) |
| `anomaly_type` | String | Not Null, Index | `"Pothole"`, `"Crack"`, `"Crack-Severe"`, `"Speed-Bump"` |
| `severity` | String | Not Null, Index | `"Low"`, `"Medium"`, `"High"`, `"Critical"` |
| `priority_score` | Integer | Not Null, Default 50 | Calculated numeric priority (0 to 100) |
| `status` | String | Not Null, Default `"NEW"` | Workflow: `"NEW"`, `"VERIFIED"`, `"ASSIGNED"`, `"IN_PROGRESS"`, `"RESOLVED"` |
| `latitude` | Float | Not Null | Centroid latitude |
| `longitude` | Float | Not Null | Centroid longitude |
| `geom` | Geometry(Point, 4326) / String | Nullable | PostGIS spatial geometry when PostgreSQL is active |
| `first_detected_at` | DateTime | Not Null | Timestamp of first observation |
| `last_detected_at` | DateTime | Not Null | Timestamp of most recent observation |
| `confirmation_count`| Integer | Not Null, Default 1 | Total count of all observations |
| `unique_bus_count` | Integer | Not Null, Default 1 | Number of distinct buses that observed this defect |
| `primary_image_url` | String | Nullable | Snapshot image path for the clearest detection |

### Table: `observations`
Chronological log of every edge detection matching an incident.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Unique observation record |
| `incident_id` | Integer | FK (`incidents.id`), Not Null | Associated incident |
| `edge_event_id` | String | Not Null, Unique | UUID from the edge device |
| `message_id` | String | Nullable, Unique, Index | Idempotency key / MQTT message ID |
| `bus_id` | String | Not Null, Index | Bus identifier (e.g. `BUS-01`) |
| `route_id` | String | Not Null | Bus route code (e.g. `ROUTE-RED`) |
| `timestamp` | DateTime | Not Null | Observation timestamp |
| `latitude` | Float | Not Null | Instantaneous latitude |
| `longitude` | Float | Not Null | Instantaneous longitude |
| `geom` | Geometry(Point, 4326) / String | Nullable | PostGIS spatial point |
| `speed_kmh` | Float | Not Null, Default 0.0 | Bus speed at capture time |
| `confidence` | Float | Not Null | Model confidence (0.0 to 1.0) |
| `image_url` | String | Nullable | URL/path of stored snapshot |

### Table: `plate_reads`
Automatic Number Plate Recognition (ANPR) detection log.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Record ID |
| `incident_id` | Integer | FK (`incidents.id`), Nullable | Optional association with nearby road defect |
| `edge_event_id` | String | Nullable, Index | Edge event identifier |
| `bus_id` | String | Not Null, Index | Reporting bus identifier |
| `route_id` | String | Not Null | Transit route identifier |
| `timestamp` | DateTime | Not Null | Time of detection |
| `latitude` | Float | Not Null | GPS latitude |
| `longitude` | Float | Not Null | GPS longitude |
| `plate_text` | String | Not Null, Index | Extracted license plate characters |
| `plate_confidence` | Float | Not Null | Plate detector model confidence |
| `ocr_confidence` | Float | Not Null | EasyOCR text recognition confidence |
| `image_url` | String | Nullable | Snapshot URL |

### Table: `infra_observations`
Traffic sign and road infrastructure asset inventory observations.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Record ID |
| `sign_type` | String | Not Null, Index | Detected sign category (e.g. `speed-100`, `no-parking`) |
| `confidence` | Float | Not Null | Classifier confidence score |
| `bus_id` | String | Not Null, Index | Reporting bus identifier |
| `route_id` | String | Not Null | Transit route identifier |
| `timestamp` | DateTime | Not Null | Time of detection |
| `latitude` | Float | Not Null | GPS latitude |
| `longitude` | Float | Not Null | GPS longitude |
| `image_url` | String | Nullable | Snapshot URL |

### Table: `observations`
Chronological log of every edge detection matching an incident.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Unique observation record |
| `incident_id` | Integer | FK (`incidents.id`), Not Null | Associated incident |
| `edge_event_id` | String | Not Null, Unique | UUID from the edge device |
| `bus_id` | String | Not Null, Index | Bus identifier (e.g. `BUS-01`) |
| `route_id` | String | Not Null | Bus route code (e.g. `ROUTE-RED`) |
| `timestamp` | DateTime | Not Null | Observation timestamp |
| `latitude` | Float | Not Null | Instantaneous latitude |
| `longitude` | Float | Not Null | Instantaneous longitude |
| `speed_kmh` | Float | Not Null, Default 0.0 | Bus speed at capture time |
| `confidence` | Float | Not Null | Model confidence (0.0 to 1.0) |
| `image_url` | String | Nullable | URL/path of stored snapshot |

### Table: `status_history`
Audit log of all lifecycle status transitions for each incident.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Unique audit log ID |
| `incident_id` | Integer | FK (`incidents.id`), Not Null | Associated incident |
| `from_status` | String | Nullable | Previous status (None on initial creation) |
| `to_status` | String | Not Null | Target status |
| `changed_at` | DateTime | Not Null | Timestamp of change |
| `notes` | Text | Nullable | Reason / operational notes |

---

## 3. API Response Schemas

### `IncidentSummaryResponse`
```json
{
  "id": 1,
  "incident_id": "INC-7F39E21A",
  "anomaly_type": "Pothole",
  "severity": "High",
  "priority_score": 78,
  "status": "VERIFIED",
  "latitude": 28.613939,
  "longitude": 77.209021,
  "first_detected_at": "2026-09-11T14:30:15Z",
  "last_detected_at": "2026-09-11T14:35:10Z",
  "confirmation_count": 3,
  "unique_bus_count": 2,
  "primary_image_url": "/static/snapshots/c7a8b89e-25f0-43b6-9bb2-094bfca2e329.jpg"
}
```

### `IncidentDetailResponse`
Extends `IncidentSummaryResponse` with observations and audit history:
```json
{
  "id": 1,
  "incident_id": "INC-7F39E21A",
  "anomaly_type": "Pothole",
  "severity": "High",
  "priority_score": 78,
  "status": "IN_PROGRESS",
  "latitude": 28.613939,
  "longitude": 77.209021,
  "first_detected_at": "2026-09-11T14:30:15Z",
  "last_detected_at": "2026-09-11T14:35:10Z",
  "confirmation_count": 3,
  "unique_bus_count": 2,
  "primary_image_url": "/static/snapshots/c7a8b89e-25f0-43b6-9bb2-094bfca2e329.jpg",
  "observations": [
    {
      "id": 1,
      "edge_event_id": "c7a8b89e-25f0-43b6-9bb2-094bfca2e329",
      "bus_id": "BUS-01",
      "route_id": "ROUTE-RED",
      "timestamp": "2026-09-11T14:30:15Z",
      "latitude": 28.613939,
      "longitude": 77.209021,
      "confidence": 0.88,
      "speed_kmh": 32.5,
      "image_url": "/static/snapshots/c7a8b89e-25f0-43b6-9bb2-094bfca2e329.jpg"
    }
  ],
  "status_history": [
    {
      "id": 1,
      "from_status": null,
      "to_status": "NEW",
      "changed_at": "2026-09-11T14:30:15Z",
      "notes": "Initial defect detection logged by edge sensor"
    },
    {
      "id": 2,
      "from_status": "NEW",
      "to_status": "VERIFIED",
      "changed_at": "2026-09-11T14:35:10Z",
      "notes": "Auto-verified: confirmed by 2 unique buses"
    }
  ]
}
```

### `IncidentStatusUpdate`
```json
{
  "status": "IN_PROGRESS",
  "notes": "Contractor dispatched for asphalt patching"
}
```
*Valid values: `"NEW"`, `"VERIFIED"`, `"ASSIGNED"`, `"IN_PROGRESS"`, `"RESOLVED"`*

### `AnalyticsSummaryResponse`
```json
{
  "total_incidents": 42,
  "pending_count": 12,
  "verified_count": 8,
  "assigned_count": 7,
  "in_progress_count": 5,
  "resolved_count": 10,
  "multi_bus_verified_count": 12,
  "active_buses": 3,
  "by_anomaly_type": {
    "Pothole": 24,
    "Crack": 11,
    "Crack-Severe": 5,
    "Speed-Bump": 2
  },
  "by_severity": {
    "Critical": 6,
    "High": 18,
    "Medium": 12,
    "Low": 6
  }
}
```
