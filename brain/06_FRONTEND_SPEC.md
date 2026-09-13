# Frontend Specification: City Vision AI Road Monitoring Command Center

## 1. Overview
The Frontend is an enterprise municipal road authority platform built with **React 18+, TypeScript, Vite, and the Municipal Sentinel Modern design system**.
Embodying the motto *"Every Bus a Sensor. Every Road a Safer Path."*, it provides municipal dispatchers and civil engineers with high-contrast, real-time situational awareness of roadway hazards detected by public transit bus cameras across city corridors.

---

## 2. Technology Stack & Design Foundations
- **Framework**: React 18+
- **Build Tool**: Vite
- **Language**: TypeScript
- **Styling Architecture**: Municipal Sentinel Modern design tokens (`Space Grotesk`, `Inter`, `JetBrains Mono`) with maritime deep navy (`#00236f`, `#1e3a8a`), crisp surface layers (`#f8f9ff`, `#ffffff`), and high-contrast severity accents.
- **Mapping**: React Leaflet (`react-leaflet`, `leaflet`) with OpenStreetMap/CartoDB voyager tile layers, animated SVG pulses, and route transit polylines.
- **Charts**: Recharts (`PieChart`, `BarChart` for severity and anomaly class distributions).
- **Icons**: Material Symbols Outlined + Lucide React (`lucide-react`).
- **HTTP Client**: Typed async API wrapper with continuous 4-second polling and background scan status monitoring.

---

## 3. UI Layout & View Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ Pinned Left Rail (280px)      │ Top Header: SYSTEM ONLINE • 24 Active Buses • Transit Ops│
├───────────────────────────────┼─────────────────────────────────────────────────────────┤
│ [Logo] CITY VISION            │ Active View Canvas:                                     │
│ AI ROAD MONITORING            │                                                         │
│ "Every Bus a Sensor..."       │ 1. Home (Command Center):                               │
│                               │    - Operational Hero Banner & Quick Patrol Trigger     │
│ Navigation:                   │    - 5 Real-Time KPI Cards (Buses, Coverage, Hazards)   │
│ - Command Center (Home)       │    - 6-Stage Ingestion Pipeline Ribbon                  │
│ - Live Detection (Patrol)     │    - Live Dashcam Monitoring HUD & Recent Issues Feed   │
│ - Geospatial Road Map (GIS)   │    - City Health Score Gauge (PCI 0-100) & Route Health │
│ - Reports & Work Orders       │                                                         │
│ - Bus Fleet Telemetry         │ 2. Live Detection:                                      │
│ - Analytics & KPIs            │    - 16:9 Video Canvas with YOLO Bounding Reticles      │
│                               │    - Working Bus Video Scan Runner (.mp4 upload)        │
│ Bottom Telemetry Widget:      │    - Rule-Based Severity & Priority Index Engine        │
│ [RT-STREAM // ACTIVE]         │    - Multi-Bus Consensus Card & Live Telemetry Table    │
│ 24 vehicles syncing GIS...    │                                                         │
│                               │ 3. Geospatial Road Map:                                 │
│                               │    - Leaflet Map with Route 12/8/5 Polylines & Pins     │
│                               │    - Folium-Styled Interactive Popups & Detail Drawer   │
│                               │                                                         │
│                               │ 4. Reports & Work Orders:                               │
│                               │    - Cadastral Infrastructure Log Table                 │
│                               │    - CSV Dossier Export & Status Progression Actions    │
│                               │                                                         │
│                               │ 5. Bus Fleet Telemetry:                                 │
│                               │    - Active Public Transit Sensing Units & GNSS Telemetry│
└───────────────────────────────┴─────────────────────────────────────────────────────────┘
```

---

## 4. Key UI Behaviors & State Machine
1. **Multi-View Seamless Routing**: Side rail tabs allow zero-lag instant switching across Command Center, Live Detection, Geospatial Road Map, Reports & Work Orders, Bus Fleet Telemetry, and Analytics.
2. **Near-Real-Time Synchronization**: Polls `GET /api/incidents`, `GET /api/analytics/summary`, and `GET /api/buses` every 4 seconds to reflect edge detection events automatically.
3. **Real Video Scan Trigger (Live Patrol)**: Allows uploading `.mp4` dashcam footage with selected bus unit (`BUS-01`, `BUS-02`, `BUS-03`) and assigned corridor (`ROUTE-12`, `ROUTE-8`, `ROUTE-5`), launching the edge YOLOv8 detection subprocess in the background and polling `/api/scan/status/{job_id}`.
4. **Multi-Bus Verification Consensus**: Highlights persistent defects confirmed by $\ge 2$ independent vehicles with glowing blue/purple `⚡ Multi-Bus Verified` badges.
5. **Operational Lifecycle Stepper**: Full status progression support:
   $$\text{NEW} \longrightarrow \text{VERIFIED} \longrightarrow \text{ASSIGNED} \longrightarrow \text{IN\_PROGRESS} \longrightarrow \text{RESOLVED}$$
   Supported via quick row actions and the interactive slide-over detail drawer.
6. **Graceful Seeding & Offline Resilience**: In addition to binding directly to active database records (166 incidents and buses), provides rich municipal corridor fallback schemas ensuring zero broken screens or empty state flashes in live demonstrations.
