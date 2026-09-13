import React from 'react'
import type { BusSummary } from '../../types'
import { SEED_BUSES, MONITORED_ROUTES } from '../../services/seedData'
import type { NavTab } from '../Navigation/Sidebar'

interface BusFleetViewProps {
  buses: BusSummary[]
  onNavigateTab: (tab: NavTab) => void
}

export const BusFleetView: React.FC<BusFleetViewProps> = ({ buses, onNavigateTab }) => {
  const effectiveBuses = buses.length > 0 ? buses : SEED_BUSES

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="radar-ping" style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-secondary)' }} />
            <span className="font-label-sm" style={{ color: 'var(--color-secondary)', fontWeight: 700, letterSpacing: '0.05em' }}>
              DISTRIBUTED MOBILE SENSING FLEET
            </span>
          </div>
          <h1 className="font-headline-xl" style={{ color: 'var(--color-primary)', margin: 0 }}>
            BUS FLEET TELEMETRY & EDGE SENSORS
          </h1>
          <p className="font-body-md" style={{ color: 'var(--color-on-surface-variant)', margin: 0 }}>
            Real-time status of public transit buses streaming road defect intelligence and GNSS telemetry
          </p>
        </div>

        <button className="btn-primary" onClick={() => onNavigateTab('live-detection')}>
          <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>videocam</span>
          <span>Open Live Patrol Feed</span>
        </button>
      </div>

      {/* Fleet Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
        {effectiveBuses.map((bus) => {
          const route = MONITORED_ROUTES.find((r) => r.route_id === bus.route_id) || MONITORED_ROUTES[0]
          return (
            <div
              key={bus.bus_id}
              className="cv-card"
              style={{
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '14px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div
                    style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: 'var(--radius-lg)',
                      backgroundColor: '#eff4ff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--color-primary)',
                    }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>directions_bus</span>
                  </div>
                  <div>
                    <h3 className="font-headline-md" style={{ color: 'var(--color-primary)', margin: 0 }}>
                      Vehicle {bus.bus_id}
                    </h3>
                    <span className="font-label-sm" style={{ color: route.color, fontWeight: 700 }}>
                      {route.name}
                    </span>
                  </div>
                </div>

                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: '#ecfdf5',
                    color: '#047857',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    fontWeight: 700,
                  }}
                >
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981' }} />
                  {bus.status}
                </span>
              </div>

              {/* Telemetry metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', padding: '12px', backgroundColor: '#f8faff', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0', fontFamily: 'var(--font-mono)', fontSize: '11.5px' }}>
                <div>
                  <span style={{ color: 'var(--color-on-surface-variant)', display: 'block', fontSize: '10px' }}>GPS COORDINATES</span>
                  <span style={{ fontWeight: 600, color: 'var(--color-on-surface)' }}>
                    {bus.latitude.toFixed(4)}, {bus.longitude.toFixed(4)}
                  </span>
                </div>
                <div>
                  <span style={{ color: 'var(--color-on-surface-variant)', display: 'block', fontSize: '10px' }}>EDGE ACCELERATOR</span>
                  <span style={{ fontWeight: 600, color: 'var(--color-secondary)' }}>
                    NPU (18.2ms)
                  </span>
                </div>
                <div>
                  <span style={{ color: 'var(--color-on-surface-variant)', display: 'block', fontSize: '10px' }}>CAMERA ARRAY</span>
                  <span style={{ fontWeight: 600, color: 'var(--color-on-surface)' }}>
                    1080p @ 30 FPS
                  </span>
                </div>
                <div>
                  <span style={{ color: 'var(--color-on-surface-variant)', display: 'block', fontSize: '10px' }}>LAST PING</span>
                  <span style={{ fontWeight: 600, color: 'var(--color-on-surface)' }}>
                    {new Date(bus.last_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </span>
                </div>
              </div>

              {/* Action buttons */}
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  className="btn-primary"
                  onClick={() => onNavigateTab('live-detection')}
                  style={{ width: '100%', justifyContent: 'center', fontSize: '12px', padding: '8px' }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>sensors</span>
                  <span>Inspect Live Sensor Stream</span>
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
