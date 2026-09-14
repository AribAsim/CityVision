import React, { useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline } from 'react-leaflet'
import {
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line,
} from 'recharts'
import type { IncidentSummary, BusSummary } from '../../types'
import { MONITORED_ROUTES } from '../../services/seedData'

interface TransportAuthorityViewProps {
  incidents: IncidentSummary[]
  buses: BusSummary[]
  onSelectIncident: (incident: IncidentSummary) => void
}

// Simulated corridor congestion hotspots with coordinates & severity
const CONGESTION_POINTS: { id: string; name: string; lat: number; lng: number; delayMin: number; level: 'High' | 'Medium' | 'Low' }[] = [
  { id: 'C1', name: 'Ashram Flyover Bottleneck', lat: 28.5708, lng: 77.2562, delayMin: 18, level: 'High' },
  { id: 'C2', name: 'ITO Intersection Transit Node', lat: 28.6289, lng: 77.2405, delayMin: 14, level: 'High' },
  { id: 'C3', name: 'Sector 62 Transit Corridor', lat: 28.6250, lng: 77.3680, delayMin: 8, level: 'Medium' },
  { id: 'C4', name: 'AIIMS Circle Inflow', lat: 28.5672, lng: 77.2100, delayMin: 12, level: 'Medium' },
  { id: 'C5', name: 'Dhaula Kuan Arterial Interlink', lat: 28.5921, lng: 77.1610, delayMin: 5, level: 'Low' },
]

// Origin-Destination (OD) Matrix Traffic Flow Data
const OD_FLOW_DATA = [
  { pair: 'Sec 62 → Connaught Pl', flow: 4200, avgSpeed: '24 km/h', reliability: '72%' },
  { pair: 'Outer Ring → AIIMS', flow: 3850, avgSpeed: '18 km/h', reliability: '61%' },
  { pair: 'NH-24 → Anand Vihar', flow: 5100, avgSpeed: '31 km/h', reliability: '84%' },
  { pair: 'Dwarka → Dhaula Kuan', flow: 2900, avgSpeed: '38 km/h', reliability: '89%' },
  { pair: 'Noida Mod → ITO', flow: 4600, avgSpeed: '16 km/h', reliability: '54%' },
]

// Hourly Delay Profile
const HOURLY_DELAY_DATA = [
  { time: '06:00', delayMin: 3 },
  { time: '08:00', delayMin: 14 },
  { time: '09:30', delayMin: 22 },
  { time: '11:00', delayMin: 9 },
  { time: '13:00', delayMin: 6 },
  { time: '15:00', delayMin: 8 },
  { time: '17:30', delayMin: 26 },
  { time: '19:00', delayMin: 19 },
  { time: '21:00', delayMin: 7 },
]

export const TransportAuthorityView: React.FC<TransportAuthorityViewProps> = ({
  incidents,
  buses,
}) => {
  const [selectedRoute, setSelectedRoute] = useState<string>('ALL')

  const activeDefectCount = incidents.filter((i) => i.status !== 'RESOLVED').length
  const potholeCount = incidents.filter((i) => i.anomaly_type === 'Pothole').length

  const getHeatmapColor = (level: string) => {
    switch (level) {
      case 'High':
        return '#dc2626'
      case 'Medium':
        return '#f59e0b'
      default:
        return '#10b981'
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', paddingBottom: '40px' }}>
      {/* Top Banner / Heading & Mode Disclaimers */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Transport Authority & Corridor Flow
            </h1>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                backgroundColor: '#e0e7ff',
                color: '#3730a3',
                padding: '3px 8px',
                borderRadius: '4px',
                fontFamily: 'JetBrains Mono, monospace',
                border: '1px solid #c7d2fe',
              }}
            >
              SIMULATED / DERIVED DATA
            </span>
          </div>
          <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
            Multi-modal corridor congestion analytics, route schedule adherence, and origin-destination flow matrices.
          </p>
        </div>

        {/* Data Qualification Badges */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: '#f1f5f9',
              padding: '6px 10px',
              borderRadius: '6px',
              fontSize: '12px',
              color: '#334155',
            }}
          >
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981' }}></span>
            <span>Edge Perception: <strong>LIVE</strong></span>
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: '#fef3c7',
              padding: '6px 10px',
              borderRadius: '6px',
              fontSize: '12px',
              color: '#92400e',
            }}
          >
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#f59e0b' }}></span>
            <span>Corridor Congestion: <strong>SIMULATED</strong></span>
          </div>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
        }}
      >
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            padding: '16px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '12px', fontWeight: 600 }}>
            <span>AVG NETWORK DELAY</span>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#ea580c' }}>schedule</span>
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#0f172a', marginTop: '8px' }}>
            +11.4 min
          </div>
          <div style={{ fontSize: '12px', color: '#ea580c', marginTop: '4px', fontWeight: 500 }}>
            Peak congestion window active (ITO / Ashram)
          </div>
        </div>

        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            padding: '16px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '12px', fontWeight: 600 }}>
            <span>TRANSIT ON-TIME RATE</span>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#0284c7' }}>directions_bus</span>
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#0f172a', marginTop: '8px' }}>
            83.6%
          </div>
          <div style={{ fontSize: '12px', color: '#16a34a', marginTop: '4px', fontWeight: 500 }}>
            Across {buses.length || 3} telemetry streams
          </div>
        </div>

        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            padding: '16px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '12px', fontWeight: 600 }}>
            <span>ROAD HAZARD BOTTLENECK</span>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#dc2626' }}>warning</span>
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#dc2626', marginTop: '8px' }}>
            {activeDefectCount} Hazards
          </div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px', fontWeight: 500 }}>
            {potholeCount} potholes impacting bus lane speeds
          </div>
        </div>

        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            padding: '16px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '12px', fontWeight: 600 }}>
            <span>CORRIDOR FLOW EFFICIENCY</span>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#10b981' }}>trending_up</span>
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#0f172a', marginTop: '8px' }}>
            76.2 / 100
          </div>
          <div style={{ fontSize: '12px', color: '#16a34a', marginTop: '4px', fontWeight: 500 }}>
            +4.1% post arterial resurfacing
          </div>
        </div>
      </div>

      {/* Main Map & Congestion Section */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.8fr 1fr',
          gap: '16px',
          alignItems: 'start',
        }}
      >
        {/* Map Container */}
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            border: '1px solid #e2e8f0',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div
            style={{
              padding: '12px 16px',
              borderBottom: '1px solid #f1f5f9',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <span style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
                Corridor Congestion & Hotspot Map
              </span>
              <span style={{ marginLeft: '8px', fontSize: '11px', color: '#64748b' }}>
                (Simulated Traffic Chokepoints)
              </span>
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                onClick={() => setSelectedRoute('ALL')}
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  padding: '4px 8px',
                  borderRadius: '4px',
                  border: '1px solid #cbd5e1',
                  backgroundColor: selectedRoute === 'ALL' ? '#0051d5' : '#ffffff',
                  color: selectedRoute === 'ALL' ? '#ffffff' : '#475569',
                  cursor: 'pointer',
                }}
              >
                All Routes
              </button>
              {MONITORED_ROUTES.map((r) => (
                <button
                  key={r.route_id}
                  onClick={() => setSelectedRoute(r.route_id)}
                  style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    padding: '4px 8px',
                    borderRadius: '4px',
                    border: '1px solid #cbd5e1',
                    backgroundColor: selectedRoute === r.route_id ? r.color : '#ffffff',
                    color: selectedRoute === r.route_id ? '#ffffff' : '#475569',
                    cursor: 'pointer',
                  }}
                >
                  {r.route_id}
                </button>
              ))}
            </div>
          </div>

          <div style={{ height: '420px', position: 'relative' }}>
            <MapContainer
              center={[28.6139, 77.2280]}
              zoom={12}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {/* Monitored Routes */}
              {MONITORED_ROUTES.filter((r) => selectedRoute === 'ALL' || selectedRoute === r.route_id).map((r) => (
                <Polyline
                  key={r.route_id}
                  positions={r.coordinates}
                  pathOptions={{ color: r.color, weight: 5, opacity: 0.8 }}
                />
              ))}

              {/* Congestion Hotspot Nodes */}
              {CONGESTION_POINTS.map((pt) => (
                <CircleMarker
                  key={pt.id}
                  center={[pt.lat, pt.lng]}
                  radius={pt.delayMin > 10 ? 18 : 12}
                  pathOptions={{
                    fillColor: getHeatmapColor(pt.level),
                    fillOpacity: 0.65,
                    color: '#ffffff',
                    weight: 2,
                  }}
                >
                  <Popup>
                    <div style={{ padding: '4px' }}>
                      <div style={{ fontWeight: 700, fontSize: '13px' }}>{pt.name}</div>
                      <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                        Delay: <strong>+{pt.delayMin} mins</strong>
                      </div>
                      <div style={{ fontSize: '11px', color: getHeatmapColor(pt.level), fontWeight: 600 }}>
                        Severity: {pt.level}
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>
        </div>

        {/* Hourly Delay Trend & Bottleneck List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '10px',
              border: '1px solid #e2e8f0',
              padding: '16px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            }}
          >
            <div style={{ fontWeight: 700, fontSize: '13px', color: '#0f172a', marginBottom: '12px' }}>
              Corridor Delay Profile (Mins / Hour)
            </div>
            <div style={{ height: '170px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={HOURLY_DELAY_DATA} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="time" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="delayMin" stroke="#ea580c" strokeWidth={2.5} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '10px',
              border: '1px solid #e2e8f0',
              padding: '16px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            }}
          >
            <div style={{ fontWeight: 700, fontSize: '13px', color: '#0f172a', marginBottom: '8px' }}>
              Critical Congestion Chokepoints
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {CONGESTION_POINTS.map((pt) => (
                <div
                  key={pt.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '6px 8px',
                    borderRadius: '6px',
                    backgroundColor: '#f8fafc',
                    fontSize: '12px',
                  }}
                >
                  <span style={{ fontWeight: 600, color: '#1e293b' }}>{pt.name}</span>
                  <span
                    style={{
                      fontWeight: 700,
                      color: getHeatmapColor(pt.level),
                      backgroundColor: '#ffffff',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      border: '1px solid #e2e8f0',
                    }}
                  >
                    +{pt.delayMin}m
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Origin-Destination (OD) Matrix Section */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '10px',
          border: '1px solid #e2e8f0',
          padding: '16px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div>
            <span style={{ fontWeight: 700, fontSize: '15px', color: '#0f172a' }}>
              Origin-Destination (OD) Traffic Flow Matrix
            </span>
            <span
              style={{
                marginLeft: '8px',
                fontSize: '11px',
                color: '#64748b',
                backgroundColor: '#f1f5f9',
                padding: '2px 6px',
                borderRadius: '4px',
              }}
            >
              Simulated Aggregated Public Transit Corridors
            </span>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b', textAlign: 'left' }}>
                <th style={{ padding: '8px' }}>Corridor Route Pair</th>
                <th style={{ padding: '8px' }}>Passenger Flow / Hr</th>
                <th style={{ padding: '8px' }}>Avg Corridor Speed</th>
                <th style={{ padding: '8px' }}>Schedule Reliability</th>
                <th style={{ padding: '8px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {OD_FLOW_DATA.map((row, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '10px 8px', fontWeight: 600, color: '#1e293b' }}>{row.pair}</td>
                  <td style={{ padding: '10px 8px', fontFamily: 'JetBrains Mono, monospace' }}>{row.flow} pax</td>
                  <td style={{ padding: '10px 8px', fontWeight: 600, color: '#0284c7' }}>{row.avgSpeed}</td>
                  <td style={{ padding: '10px 8px' }}>{row.reliability}</td>
                  <td style={{ padding: '10px 8px' }}>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: parseInt(row.reliability) > 75 ? '#dcfce7' : '#fee2e2',
                        color: parseInt(row.reliability) > 75 ? '#15803d' : '#b91c1c',
                      }}
                    >
                      {parseInt(row.reliability) > 75 ? 'OPTIMAL' : 'DELAY RISK'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
