import React from 'react'

export type NavTab = 'home' | 'live-detection' | 'road-map' | 'transport-authority' | 'field-ops' | 'reports' | 'bus-fleet' | 'analytics'

interface SidebarProps {
  activeTab: NavTab
  onSelectTab: (tab: NavTab) => void
  activeBusesCount: number
  isScanProcessing?: boolean
  scanEventsCount?: number
}

interface NavItem {
  id: NavTab
  label: string
  icon: string
  badge?: string
}

const NAV_ITEMS: NavItem[] = [
  { id: 'home', label: 'Command Center', icon: 'grid_view' },
  { id: 'live-detection', label: 'Live Detection', icon: 'videocam', badge: 'LIVE' },
  { id: 'road-map', label: 'Geospatial Road Map', icon: 'map' },
  { id: 'transport-authority', label: 'Transport Corridor', icon: 'traffic', badge: 'OD' },
  { id: 'field-ops', label: 'Field Ops Portal', icon: 'handyman' },
  { id: 'reports', label: 'Reports & Work Orders', icon: 'assignment_late' },
  { id: 'bus-fleet', label: 'Bus Fleet Telemetry', icon: 'directions_bus' },
  { id: 'analytics', label: 'Analytics & KPIs', icon: 'insights' },
]

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  activeBusesCount,
  isScanProcessing,
  scanEventsCount = 0,
}) => {
  return (
    <aside
      style={{
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        width: '280px',
        backgroundColor: '#ffffff',
        borderRight: '1px solid #e2e8f0',
        zIndex: 50,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        boxShadow: '0 1px 8px rgba(0, 0, 0, 0.04)',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {/* Logo & Brand Identity */}
        <div
          style={{
            height: '72px',
            padding: '0 20px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            borderBottom: '1px solid #f1f5f9',
            backgroundColor: '#ffffff',
          }}
        >
          {/* Custom City Vision SVG Icon */}
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 44 44" width="38" height="38" fill="none">
            <rect x="2" y="2" width="40" height="40" rx="10" fill="#1E3A8A" />
            <path d="M12 30L22 14L32 30" stroke="#60A5FA" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="22" cy="22" r="3.5" fill="#38BDF8" />
            <path d="M16 32H28" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" />
            <circle cx="22" cy="14" r="2.5" fill="#EF4444" />
          </svg>
          <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '17px',
                fontWeight: 700,
                color: 'var(--color-primary)',
                letterSpacing: '-0.02em',
                lineHeight: 1.1,
              }}
            >
              CITY VISION
            </span>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '9.5px',
                fontWeight: 600,
                color: 'var(--color-secondary)',
                letterSpacing: '0.08em',
                marginTop: '2px',
              }}
            >
              AI ROAD MONITORING
            </span>
          </div>
        </div>

        {/* Motto Banner */}
        <div style={{ padding: '10px 20px', backgroundColor: '#f8faff', borderBottom: '1px solid #f1f5f9' }}>
          <p
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '11px',
              fontStyle: 'italic',
              color: 'var(--color-on-surface-variant)',
              lineHeight: 1.4,
              margin: 0,
            }}
          >
            Every Bus a Sensor. Every Road a Safer Path.
          </p>
        </div>

        {/* Section Label */}
        <div style={{ padding: '18px 20px 8px 20px' }}>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '10px',
              fontWeight: 600,
              color: '#64748b',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
            }}
          >
            Operations Command
          </span>
        </div>

        {/* Navigation List */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px', padding: '0 12px' }}>
          {NAV_ITEMS.map((item) => {
            const isActive = activeTab === item.id
            return (
              <button
                key={item.id}
                id={`nav-tab-${item.id}`}
                onClick={() => onSelectTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-lg)',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: isActive ? 'var(--color-primary-container)' : 'transparent',
                  color: isActive ? '#ffffff' : 'var(--color-on-surface-variant)',
                  fontWeight: isActive ? 600 : 500,
                  fontFamily: 'var(--font-body)',
                  fontSize: '13.5px',
                  boxShadow: isActive ? '0 2px 6px rgba(30, 58, 138, 0.25)' : 'none',
                  transition: 'all 0.15s ease',
                  textAlign: 'left',
                  width: '100%',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = '#eff4ff'
                    e.currentTarget.style.color = 'var(--color-on-surface)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = 'transparent'
                    e.currentTarget.style.color = 'var(--color-on-surface-variant)'
                  }
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span
                    className="material-symbols-outlined"
                    style={{
                      fontSize: '19px',
                      color: isActive ? '#ffffff' : 'var(--color-secondary)',
                    }}
                  >
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </div>

                {item.id === 'live-detection' && isScanProcessing ? (
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '9px',
                      fontWeight: 700,
                      backgroundColor: '#ef4444',
                      color: '#ffffff',
                      padding: '2px 6px',
                      borderRadius: 'var(--radius-full)',
                      letterSpacing: '0.04em',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      boxShadow: '0 0 8px rgba(239, 68, 68, 0.4)',
                    }}
                  >
                    <span style={{ width: '5px', height: '5px', borderRadius: '50%', backgroundColor: '#ffffff' }} />
                    <span>{scanEventsCount} EVTS</span>
                  </span>
                ) : item.badge ? (
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '9px',
                      fontWeight: 700,
                      backgroundColor: isActive ? 'rgba(255, 255, 255, 0.2)' : '#fee2e2',
                      color: isActive ? '#ffffff' : '#ba1a1a',
                      padding: '2px 6px',
                      borderRadius: 'var(--radius-full)',
                      letterSpacing: '0.04em',
                    }}
                  >
                    {item.badge}
                  </span>
                ) : null}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Telemetry Widget Footer */}
      <div
        style={{
          margin: '14px',
          padding: '14px',
          backgroundColor: '#eff4ff',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid #dce9ff',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '10px',
              fontWeight: 600,
              color: 'var(--color-on-surface-variant)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Telemetry Feed
          </span>
          <span
            className="radar-ping"
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: 'var(--color-secondary)',
              display: 'inline-block',
            }}
          />
        </div>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            fontWeight: 600,
            color: 'var(--color-primary)',
            letterSpacing: '0.02em',
          }}
        >
          RT-STREAM // ACTIVE
        </div>
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '11px',
            color: 'var(--color-on-surface-variant)',
            marginTop: '4px',
            lineHeight: 1.35,
            margin: 0,
          }}
        >
          {activeBusesCount || 24} vehicles syncing GIS and road health payloads in real-time.
        </p>
      </div>
    </aside>
  )
}
