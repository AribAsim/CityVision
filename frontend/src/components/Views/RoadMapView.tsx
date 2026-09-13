import React, { useState, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import L from 'leaflet'
import type { IncidentSummary, BusSummary } from '../../types'
import { MONITORED_ROUTES, SEED_RECENT_INCIDENTS } from '../../services/seedData'

interface RoadMapViewProps {
  incidents: IncidentSummary[]
  buses: BusSummary[]
  onSelectIncident: (inc: IncidentSummary) => void
  onUpdateStatus?: (id: string, status: string) => void
}

// Custom Leaflet DivIcons styled like Stitch
const createSeverityPin = (severity: string, isSelected: boolean) => {
  let color = '#3b82f6'
  let icon = 'report_problem'
  if (severity === 'Critical') {
    color = '#ba1a1a'
    icon = 'warning'
  } else if (severity === 'High') {
    color = '#ea580c'
    icon = 'crisis_alert'
  } else if (severity === 'Medium') {
    color = '#f59e0b'
    icon = 'report_problem'
  } else if (severity === 'Low' || severity === 'Resolved') {
    color = '#10b981'
    icon = 'check'
  }

  const html = `
    <div style="position: relative; display: flex; flex-direction: column; align-items: center; cursor: pointer;">
      ${isSelected ? `<span style="position: absolute; inset: -4px; border-radius: 50%; background-color: ${color}; opacity: 0.5; animation: radar-pulse 1.5s infinite;"></span>` : ''}
      <div style="
        width: ${isSelected ? '36px' : '30px'};
        height: ${isSelected ? '36px' : '30px'};
        border-radius: 50%;
        background-color: ${color};
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 3px 8px rgba(0,0,0,0.3);
        border: 2px solid #ffffff;
        transition: transform 0.2s;
      ">
        <span class="material-symbols-outlined" style="font-size: ${isSelected ? '20px' : '17px'};">${icon}</span>
      </div>
      <div style="width: 2px; height: 6px; background-color: ${color};"></div>
    </div>
  `

  return L.divIcon({
    html,
    className: 'custom-leaflet-pin',
    iconSize: [36, 42],
    iconAnchor: [18, 42],
    popupAnchor: [0, -42],
  })
}

const createBusPin = (busId: string) => {
  const html = `
    <div style="display: flex; flex-direction: column; align-items: center;">
      <div style="
        padding: 2px 6px;
        background-color: #00236f;
        color: #ffffff;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        font-weight: 700;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        gap: 3px;
      ">
        <span class="material-symbols-outlined" style="font-size: 12px; color: #60a5fa;">directions_bus</span>
        <span>${busId}</span>
      </div>
      <div style="width: 2px; height: 4px; background-color: #00236f;"></div>
    </div>
  `

  return L.divIcon({
    html,
    className: 'custom-bus-pin',
    iconSize: [60, 26],
    iconAnchor: [30, 26],
  })
}

export const RoadMapView: React.FC<RoadMapViewProps> = ({
  incidents,
  buses,
  onSelectIncident,
}) => {
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const effectiveIncidents = incidents.length > 0 ? incidents : SEED_RECENT_INCIDENTS

  // Filtered incidents
  const filteredIncidents = useMemo(() => {
    return effectiveIncidents.filter((inc) => {
      if (searchQuery && !inc.incident_id.toLowerCase().includes(searchQuery.toLowerCase()) && !inc.anomaly_type.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }
      if (typeFilter !== 'all' && inc.anomaly_type.toLowerCase() !== typeFilter.toLowerCase()) {
        return false
      }
      if (severityFilter !== 'all' && inc.severity.toLowerCase() !== severityFilter.toLowerCase()) {
        return false
      }
      if (statusFilter !== 'all' && inc.status.toLowerCase() !== statusFilter.toLowerCase()) {
        return false
      }
      return true
    })
  }, [effectiveIncidents, searchQuery, typeFilter, severityFilter, statusFilter])

  // Statistics
  const totalCount = effectiveIncidents.length
  const criticalCount = effectiveIncidents.filter((i) => i.severity === 'Critical' || i.severity === 'High').length
  const pendingCount = effectiveIncidents.filter((i) => i.status === 'NEW' || i.status === 'VERIFIED').length
  const resolvedCount = effectiveIncidents.filter((i) => i.status === 'RESOLVED').length
  const multiBusCount = effectiveIncidents.filter((i) => i.unique_bus_count >= 2).length
  const verifiedRate = totalCount > 0 ? Math.round((multiBusCount / totalCount) * 100) : 68

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Header Section */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="radar-ping" style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-secondary)' }} />
            <span className="font-label-sm" style={{ color: 'var(--color-secondary)', fontWeight: 700, letterSpacing: '0.05em' }}>
              GIS CADASTRAL LAYER // LIVE TELEMETRY
            </span>
          </div>
          <h1 className="font-headline-xl" style={{ color: 'var(--color-primary)', margin: 0 }}>
            GEOSPATIAL ROAD MAP
          </h1>
          <p className="font-body-md" style={{ color: 'var(--color-on-surface-variant)', margin: 0 }}>
            Visualize detected road issues and transit routes across monitored municipal bus corridors
          </p>
        </div>

        {/* Quick Status Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '5px 12px', backgroundColor: '#ffffff', borderRadius: 'var(--radius-full)', border: '1px solid #e2e8f0' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '16px', color: 'var(--color-primary)' }}>satellite_alt</span>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface)' }}>GNSS RTK: ±0.14m ACTIVE</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '5px 12px', backgroundColor: '#ffffff', borderRadius: 'var(--radius-full)', border: '1px solid #e2e8f0' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '16px', color: 'var(--color-secondary)' }}>layers</span>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface)' }}>MAP: HYBRID VECTOR V4</span>
          </div>
        </div>
      </div>

      {/* 2. Top Filter & Search Bar */}
      <div className="cv-card" style={{ padding: '14px 20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Search Corridor */}
          <div style={{ flex: '1 1 240px', position: 'relative' }}>
            <span className="material-symbols-outlined" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', fontSize: '18px', color: '#94a3b8' }}>
              search
            </span>
            <input
              id="map-filter-search"
              type="text"
              placeholder="Filter road name or corridor (e.g. NH-24)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px 8px 36px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid #cbd5e1',
                fontFamily: 'var(--font-body)',
                fontSize: '13px',
                backgroundColor: '#f8faff',
                outline: 'none',
              }}
            />
          </div>

          {/* Type Filter */}
          <select
            id="map-filter-type"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1', fontFamily: 'var(--font-mono)', fontSize: '12px', backgroundColor: '#f8faff' }}
          >
            <option value="all">Type: All</option>
            <option value="pothole">Pothole</option>
            <option value="crack">Crack</option>
            <option value="crack-severe">Crack-Severe</option>
            <option value="speed-bump">Speed Bump</option>
          </select>

          {/* Severity Filter */}
          <select
            id="map-filter-severity"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1', fontFamily: 'var(--font-mono)', fontSize: '12px', backgroundColor: '#f8faff' }}
          >
            <option value="all">Severity: All</option>
            <option value="critical">● Critical (Red)</option>
            <option value="high">● High (Orange)</option>
            <option value="medium">● Medium (Amber)</option>
            <option value="low">● Low (Green)</option>
          </select>

          {/* Status Filter */}
          <select
            id="map-filter-status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1', fontFamily: 'var(--font-mono)', fontSize: '12px', backgroundColor: '#f8faff' }}
          >
            <option value="all">Status: All</option>
            <option value="new">NEW</option>
            <option value="verified">VERIFIED</option>
            <option value="assigned">ASSIGNED</option>
            <option value="in_progress">IN_PROGRESS</option>
            <option value="resolved">RESOLVED</option>
          </select>

          {/* Reset button */}
          <button
            id="btn-reset-map-filters"
            className="btn-secondary"
            onClick={() => {
              setSearchQuery('')
              setTypeFilter('all')
              setSeverityFilter('all')
              setStatusFilter('all')
            }}
            style={{ padding: '8px 14px' }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>filter_alt_off</span>
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* 3. Interactive Leaflet Map Container with Floating Legend */}
      <div
        className="cv-card"
        style={{
          position: 'relative',
          width: '100%',
          height: '620px',
          borderRadius: 'var(--radius-xl)',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-level2)',
        }}
      >
        <MapContainer
          center={[28.6139, 77.2090]}
          zoom={12}
          style={{ width: '100%', height: '100%' }}
          scrollWheelZoom={true}
        >
          {/* Crisp CartoDB Positron / OSM tiles */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          />

          {/* Transit Route Polylines from seed/specification */}
          {MONITORED_ROUTES.map((rt) => (
            <Polyline
              key={rt.route_id}
              positions={rt.coordinates}
              pathOptions={{
                color: rt.color,
                weight: 5,
                opacity: 0.85,
                dashArray: rt.route_id === 'ROUTE-8' ? '8, 6' : undefined,
              }}
            />
          ))}

          {/* Bus fleet location pins */}
          {buses.map((bus) => (
            <Marker
              key={`bus-${bus.bus_id}`}
              position={[bus.latitude, bus.longitude]}
              icon={createBusPin(bus.bus_id)}
            >
              <Popup>
                <div style={{ padding: '12px', minWidth: '180px' }}>
                  <div style={{ fontWeight: 700, color: 'var(--color-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>directions_bus</span>
                    <span>Transit Vehicle {bus.bus_id}</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--color-on-surface-variant)', marginTop: '4px' }}>
                    Route: {bus.route_id} | Status: {bus.status}
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', marginTop: '2px' }}>
                    GPS: {bus.latitude.toFixed(4)}, {bus.longitude.toFixed(4)}
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Incident Pins with Rich Stitch-Styled Popups */}
          {filteredIncidents.map((inc) => (
            <Marker
              key={inc.incident_id}
              position={[inc.latitude, inc.longitude]}
              icon={createSeverityPin(inc.severity, false)}
            >
              <Popup>
                <div style={{ width: '280px', padding: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '6px' }}>
                    <span className="font-label-md" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
                      {inc.incident_id}
                    </span>
                    <span
                      style={{
                        padding: '2px 6px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: inc.severity === 'Critical' ? '#fee2e2' : '#eff4ff',
                        color: inc.severity === 'Critical' ? '#ba1a1a' : 'var(--color-secondary)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '10px',
                        fontWeight: 700,
                      }}
                    >
                      {inc.severity} (Score: {inc.priority_score})
                    </span>
                  </div>

                  <div>
                    <h4 style={{ margin: 0, fontSize: '14px', fontFamily: 'var(--font-display)', color: 'var(--color-on-surface)' }}>
                      {inc.anomaly_type}
                    </h4>
                    <p style={{ margin: '2px 0 0 0', fontSize: '11px', color: 'var(--color-on-surface-variant)', fontFamily: 'var(--font-mono)' }}>
                      GPS: {inc.latitude.toFixed(4)}° N, {inc.longitude.toFixed(4)}° E
                    </p>
                  </div>

                  {inc.unique_bus_count >= 2 && (
                    <div className="badge-multibus" style={{ alignSelf: 'flex-start' }}>
                      <span className="material-symbols-outlined" style={{ fontSize: '12px' }}>verified</span>
                      <span>Verified by {inc.unique_bus_count} Buses</span>
                    </div>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--color-on-surface-variant)', paddingTop: '4px' }}>
                    <span>Status: <strong style={{ color: 'var(--color-primary)' }}>{inc.status}</strong></span>
                    <span>{new Date(inc.last_detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>

                  <button
                    className="btn-primary"
                    onClick={() => onSelectIncident(inc)}
                    style={{ width: '100%', justifyContent: 'center', fontSize: '12px', padding: '6px 12px', marginTop: '4px' }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>visibility</span>
                    <span>View Incident Details</span>
                  </button>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {/* Map Legend (Bottom Left Floating Panel) */}
        <div
          style={{
            position: 'absolute',
            bottom: '16px',
            left: '16px',
            zIndex: 1000,
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(8px)',
            padding: '14px 16px',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-level2)',
            border: '1px solid #e2e8f0',
            maxWidth: '280px',
          }}
        >
          <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)', fontWeight: 700, letterSpacing: '0.04em', display: 'block', marginBottom: '8px' }}>
            GIS CLASSIFICATION & LEGEND
          </span>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#ba1a1a' }} />
              <span>Critical / High</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#f59e0b' }} />
              <span>Medium</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#10b981' }} />
              <span>Resolved / Low</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '14px', height: '3px', borderRadius: '2px', backgroundColor: '#0051d5' }} />
              <span>Route 12 Transit</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '14px', height: '3px', borderRadius: '2px', backgroundColor: '#7e22ce' }} />
              <span>Route 8 Transit</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '13px', color: 'var(--color-secondary)' }}>verified</span>
              <span>Multi-Bus Ingest</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Summary KPI Footer Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div className="cv-card" style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>TOTAL ISSUES</span>
            <div className="font-headline-lg" style={{ color: 'var(--color-primary)', lineHeight: 1, marginTop: '4px' }}>{totalCount}</div>
          </div>
          <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-lg)', backgroundColor: '#eff4ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary)' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>grid_goldenratio</span>
          </div>
        </div>

        <div className="cv-card" style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderLeft: '4px solid #ba1a1a' }}>
          <div>
            <span className="font-label-sm" style={{ color: '#ba1a1a' }}>HIGH PRIORITY</span>
            <div className="font-headline-lg" style={{ color: '#ba1a1a', lineHeight: 1, marginTop: '4px' }}>{criticalCount}</div>
          </div>
          <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-lg)', backgroundColor: '#ffdad6', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ba1a1a' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>warning</span>
          </div>
        </div>

        <div className="cv-card" style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>PENDING</span>
            <div className="font-headline-lg" style={{ color: 'var(--color-on-surface)', lineHeight: 1, marginTop: '4px' }}>{pendingCount}</div>
          </div>
          <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-lg)', backgroundColor: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-on-surface-variant)' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>pending_actions</span>
          </div>
        </div>

        <div className="cv-card" style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>RESOLVED</span>
            <div className="font-headline-lg" style={{ color: '#047857', lineHeight: 1, marginTop: '4px' }}>{resolvedCount}</div>
          </div>
          <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-lg)', backgroundColor: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#047857' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>task_alt</span>
          </div>
        </div>

        <div className="cv-card" style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>VERIFIED RATE</span>
            <div className="font-headline-lg" style={{ color: 'var(--color-secondary)', lineHeight: 1, marginTop: '4px' }}>{verifiedRate}%</div>
          </div>
          <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-lg)', backgroundColor: '#eff4ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-secondary)' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>verified</span>
          </div>
        </div>
      </div>
    </div>
  )
}
