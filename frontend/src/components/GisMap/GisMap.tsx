import React, { useEffect } from 'react'
import { MapContainer, TileLayer, CircleMarker, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import type { IncidentSummary, BusSummary } from '../../types'

interface GisMapProps {
  incidents: IncidentSummary[]
  buses: BusSummary[]
  selectedIncident: IncidentSummary | null
  onSelectIncident: (incident: IncidentSummary) => void
}

// Helper to center and zoom map when an incident is selected
const MapFlyTo: React.FC<{ target: [number, number] | null }> = ({ target }) => {
  const map = useMap()
  useEffect(() => {
    if (target) {
      map.flyTo(target, 16, { duration: 1.2 })
    }
  }, [target, map])
  return null
}

const getSeverityColor = (severity: string, status: string): string => {
  if (status === 'RESOLVED') return '#10B981'
  switch (severity.toLowerCase()) {
    case 'critical': return '#EF4444'
    case 'high': return '#F97316'
    case 'medium': return '#EAB308'
    case 'low': return '#3B82F6'
    default: return '#3B82F6'
  }
}

// Custom Bus HTML Marker
const createBusIcon = (busId: string, routeId: string) => {
  return L.divIcon({
    className: 'custom-bus-marker',
    html: `
      <div style="
        background: #2563EB;
        border: 2px solid #60A5FA;
        border-radius: 6px;
        padding: 2px 6px;
        color: #ffffff;
        font-weight: 700;
        font-size: 10px;
        white-space: nowrap;
        display: flex;
        align-items: center;
        gap: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.6);
        transform: translate(-50%, -50%);
      " title="Transit Bus: ${busId} (${routeId})">
        <span>🚌</span>
        <span>${busId}</span>
      </div>
    `,
    iconSize: [60, 24],
    iconAnchor: [30, 12],
  })
}

export const GisMap: React.FC<GisMapProps> = ({
  incidents,
  buses,
  selectedIncident,
  onSelectIncident,
}) => {
  // Center on New Delhi coordinates as defined in edge simulator and system specs
  const defaultCenter: [number, number] = [28.6139, 77.2090]

  const incidentCounts = {
    total: incidents.length,
    active: incidents.filter(i => i.status !== 'RESOLVED').length,
    multiBus: incidents.filter(i => i.unique_bus_count >= 2).length,
  }

  return (
    <div className="map-workspace-panel" style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* Map title overlay */}
      <div style={{
        position: 'absolute', top: 10, left: '50%', transform: 'translateX(-50%)',
        zIndex: 800, background: 'rgba(15,23,42,0.88)', border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '8px', padding: '6px 14px', backdropFilter: 'blur(8px)',
        display: 'flex', alignItems: 'center', gap: '10px', pointerEvents: 'none',
      }}>
        <span style={{ fontSize: '12px', fontWeight: 700, color: '#E2E8F0', letterSpacing: '0.5px' }}>🗺️ GIS ROAD INTELLIGENCE</span>
        <span style={{ width: '1px', height: '14px', background: 'rgba(255,255,255,0.15)' }} />
        <span style={{ fontSize: '11px', color: '#60A5FA' }}>{incidentCounts.active} Active Incidents</span>
        {incidentCounts.multiBus > 0 && (
          <>
            <span style={{ width: '1px', height: '14px', background: 'rgba(255,255,255,0.15)' }} />
            <span style={{ fontSize: '11px', color: '#A78BFA' }}>⚡ {incidentCounts.multiBus} Multi-Bus Verified</span>
          </>
        )}
        <span style={{ width: '1px', height: '14px', background: 'rgba(255,255,255,0.15)' }} />
        <span style={{ fontSize: '11px', color: '#34D399' }}>{buses.length} Buses Transmitting</span>
      </div>
      <MapContainer
        center={defaultCenter}
        zoom={13}
        style={{ width: '100%', height: '100%' }}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {selectedIncident && (
          <MapFlyTo target={[selectedIncident.latitude, selectedIncident.longitude]} />
        )}

        {/* Bus Fleet Markers */}
        {buses.map((bus) => (
          <Marker
            key={`bus-${bus.bus_id}`}
            position={[bus.latitude, bus.longitude]}
            icon={createBusIcon(bus.bus_id, bus.route_id)}
          >
            <Popup>
              <div style={{ padding: '4px', color: '#1E293B' }}>
                <strong style={{ fontSize: '13px', color: '#1D4ED8' }}>Transit Bus {bus.bus_id}</strong>
                <div style={{ fontSize: '11px', marginTop: '4px' }}>Route: <strong>{bus.route_id}</strong></div>
                <div style={{ fontSize: '11px' }}>Status: <strong>{bus.status}</strong></div>
                <div style={{ fontSize: '11px', color: '#64748B' }}>
                  GPS: {bus.latitude.toFixed(4)}, {bus.longitude.toFixed(4)}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Road Defect Incident Markers */}
        {incidents.map((incident) => {
          const isSelected = selectedIncident?.incident_id === incident.incident_id
          const color = getSeverityColor(incident.severity, incident.status)

          return (
            <CircleMarker
              key={`inc-${incident.incident_id}`}
              center={[incident.latitude, incident.longitude]}
              radius={isSelected ? 11 : 8}
              pathOptions={{
                color: isSelected ? '#FFFFFF' : color,
                fillColor: color,
                fillOpacity: isSelected ? 0.95 : 0.8,
                weight: isSelected ? 3 : 2,
              }}
              eventHandlers={{
                click: () => onSelectIncident(incident),
              }}
            >
              <Popup>
                <div style={{ padding: '4px', color: '#1E293B' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                    <strong style={{ fontSize: '13px' }}>{incident.anomaly_type}</strong>
                    <span style={{
                      fontSize: '10px',
                      fontWeight: 700,
                      padding: '1px 5px',
                      borderRadius: '4px',
                      background: color,
                      color: '#FFFFFF'
                    }}>
                      {incident.severity}
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', marginTop: '4px', color: '#475569' }}>
                    ID: <strong>{incident.incident_id}</strong>
                  </div>
                  <div style={{ fontSize: '11px', color: '#475569' }}>
                    Priority: <strong>{incident.priority_score}/100</strong>
                  </div>
                  <div style={{ fontSize: '11px', color: '#475569' }}>
                    Status: <strong>{incident.status}</strong>
                  </div>
                  {incident.unique_bus_count >= 2 && (
                    <div style={{ fontSize: '11px', color: '#7C3AED', fontWeight: 600, marginTop: '2px' }}>
                      ★ Confirmed by {incident.unique_bus_count} Buses
                    </div>
                  )}
                  <button
                    onClick={() => onSelectIncident(incident)}
                    style={{
                      marginTop: '6px',
                      width: '100%',
                      padding: '4px 8px',
                      background: '#1D4ED8',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '11px',
                      cursor: 'pointer',
                      fontWeight: 600,
                    }}
                  >
                    View Details & Workflow
                  </button>
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
      </MapContainer>

      {/* Map Legend */}
      <div className="map-legend">
        <strong style={{ fontSize: '11px', color: '#E2E8F0', marginBottom: '4px', display: 'block', letterSpacing: '0.5px' }}>MAP LEGEND</strong>
        <div className="legend-row">
          <span className="legend-marker-dot" style={{ background: '#EF4444' }}></span>
          <span style={{ color: '#F87171' }}>Critical</span>
        </div>
        <div className="legend-row">
          <span className="legend-marker-dot" style={{ background: '#F97316' }}></span>
          <span style={{ color: '#FB923C' }}>High</span>
        </div>
        <div className="legend-row">
          <span className="legend-marker-dot" style={{ background: '#EAB308' }}></span>
          <span style={{ color: '#FBBF24' }}>Medium</span>
        </div>
        <div className="legend-row">
          <span className="legend-marker-dot" style={{ background: '#3B82F6' }}></span>
          <span style={{ color: '#60A5FA' }}>Low</span>
        </div>
        <div className="legend-row">
          <span className="legend-marker-dot" style={{ background: '#10B981' }}></span>
          <span style={{ color: '#34D399' }}>Resolved</span>
        </div>
        <div className="legend-row" style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '4px', marginTop: '4px' }}>
          <span style={{ fontSize: '12px' }}>🚌</span>
          <span style={{ color: '#93C5FD' }}>Bus Sensor</span>
        </div>
        <div className="legend-row">
          <span style={{ fontSize: '12px' }}>⚡</span>
          <span style={{ color: '#A78BFA' }}>Multi-Bus Verified</span>
        </div>
      </div>
    </div>
  )
}
