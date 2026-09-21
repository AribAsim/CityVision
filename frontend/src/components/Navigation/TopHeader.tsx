import React from 'react'
import type { ScanManager } from '../../hooks/useScanManager'
import type { NavTab } from './Sidebar'

export type UserRole = 'command_center' | 'transport_authority' | 'field_official'

interface TopHeaderProps {
  activeBusesCount: number
  lastUpdated: string
  onRefreshAll: () => void
  searchQuery: string
  onSearchChange: (q: string) => void
  scanManager?: ScanManager
  onNavigateTab?: (tab: NavTab) => void
  activeRole?: UserRole
  onRoleChange?: (role: UserRole) => void
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  activeBusesCount,
  lastUpdated,
  onRefreshAll,
  searchQuery,
  onSearchChange,
  scanManager,
  onNavigateTab,
  activeRole = 'command_center',
  onRoleChange,
}) => {
  return (
    <header
      style={{
        position: 'fixed',
        top: 0,
        left: '280px',
        right: 0,
        height: '64px',
        backgroundColor: 'rgba(255, 255, 255, 0.94)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid #e2e8f0',
        zIndex: 40,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 28px',
        boxShadow: '0 1px 4px rgba(0, 0, 0, 0.03)',
      }}
    >
      {/* Left side: System status & search */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* Status Pill */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '5px 14px',
            backgroundColor: '#eff4ff',
            borderRadius: 'var(--radius-full)',
            border: '1px solid #dce9ff',
          }}
        >
          <span
            className="radar-ping"
            style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              backgroundColor: 'var(--color-secondary)',
              display: 'inline-block',
            }}
          />
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              color: 'var(--color-primary)',
              fontWeight: 600,
              letterSpacing: '0.01em',
            }}
          >
            SYSTEM ONLINE | {activeBusesCount || 24} Active Buses | Municipal Transit Grid
          </span>
        </div>

        {/* Search Input */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: '#f8faff',
            border: '1px solid #e2e8f0',
            borderRadius: 'var(--radius-md)',
            padding: '5px 12px',
            width: '320px',
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{ fontSize: '18px', color: '#94a3b8' }}
          >
            search
          </span>
          <input
            id="global-search-input"
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search anomaly ID, road, corridor..."
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              fontFamily: 'var(--font-body)',
              fontSize: '12.5px',
              color: 'var(--color-on-surface)',
              width: '100%',
            }}
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: '#94a3b8',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>
                close
              </span>
            </button>
          )}
        </div>

        {/* 3-Button Role Switcher */}
        <div
          style={{
            display: 'inline-flex',
            backgroundColor: '#f1f5f9',
            padding: '3px',
            borderRadius: '8px',
            border: '1px solid #e2e8f0',
            gap: '2px',
          }}
        >
          <button
            id="role-btn-command-center"
            onClick={() => {
              onRoleChange?.('command_center')
              onNavigateTab?.('home')
            }}
            style={{
              padding: '4px 10px',
              borderRadius: '6px',
              border: 'none',
              fontSize: '11px',
              fontWeight: activeRole === 'command_center' ? 700 : 500,
              cursor: 'pointer',
              backgroundColor: activeRole === 'command_center' ? '#1e3a8a' : 'transparent',
              color: activeRole === 'command_center' ? '#ffffff' : '#64748b',
              transition: 'all 0.15s ease',
            }}
          >
            Command Center
          </button>
          <button
            id="role-btn-transport-authority"
            onClick={() => {
              onRoleChange?.('transport_authority')
              onNavigateTab?.('transport-authority')
            }}
            style={{
              padding: '4px 10px',
              borderRadius: '6px',
              border: 'none',
              fontSize: '11px',
              fontWeight: activeRole === 'transport_authority' ? 700 : 500,
              cursor: 'pointer',
              backgroundColor: activeRole === 'transport_authority' ? '#1e3a8a' : 'transparent',
              color: activeRole === 'transport_authority' ? '#ffffff' : '#64748b',
              transition: 'all 0.15s ease',
            }}
          >
            Transport Authority
          </button>
          <button
            id="role-btn-field-official"
            onClick={() => {
              onRoleChange?.('field_official')
              onNavigateTab?.('field-ops')
            }}
            style={{
              padding: '4px 10px',
              borderRadius: '6px',
              border: 'none',
              fontSize: '11px',
              fontWeight: activeRole === 'field_official' ? 700 : 500,
              cursor: 'pointer',
              backgroundColor: activeRole === 'field_official' ? '#1e3a8a' : 'transparent',
              color: activeRole === 'field_official' ? '#ffffff' : '#64748b',
              transition: 'all 0.15s ease',
            }}
          >
            Field Official
          </button>
        </div>
      </div>

      {/* Right side: Active Scan indicator, Demo badge, refresh, user */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Active Scan Indicator */}
        {scanManager && scanManager.scanStatus.status === 'PROCESSING' && (
          <button
            id="header-scan-indicator"
            onClick={() => onNavigateTab?.('live-detection')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '5px 14px',
              backgroundColor: '#fee2e2',
              border: '1px solid #fca5a5',
              color: '#991b1b',
              borderRadius: 'var(--radius-full)',
              cursor: 'pointer',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              fontWeight: 700,
              boxShadow: '0 2px 8px rgba(239, 68, 68, 0.25)',
              transition: 'all 0.15s ease',
            }}
            title="Click to view live detection feed"
          >
            <span className="radar-ping" style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: '#ef4444' }} />
            <span>
              SCANNING {scanManager.selectedBus}: {scanManager.scanStatus.events_dispatched} EVENTS
            </span>
          </button>
        )}

        {scanManager && scanManager.scanStatus.status === 'COMPLETED' && (
          <div
            id="header-scan-completed"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 12px',
              backgroundColor: '#ecfdf5',
              border: '1px solid #a7f3d0',
              color: '#047857',
              borderRadius: 'var(--radius-full)',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              fontWeight: 700,
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>check_circle</span>
            <span>SCAN COMPLETE: {scanManager.scanStatus.events_dispatched} EVENTS</span>
            <button
              onClick={() => scanManager.resetScan()}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: '#047857',
                padding: '0 4px',
                fontWeight: 800,
                fontSize: '12px',
              }}
              title="Dismiss"
            >
              ✕
            </button>
          </div>
        )}

        {/* Demo Mode Badge */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 12px',
            backgroundColor: '#eff6ff',
            border: '1px solid #bfdbfe',
            color: '#1e40af',
            borderRadius: 'var(--radius-full)',
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>
            smart_toy
          </span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '10.5px',
              fontWeight: 700,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            DEMO MODE: ON
          </span>
        </div>

        {/* Auto-sync & manual refresh */}
        <button
          id="btn-global-refresh"
          onClick={onRefreshAll}
          title="Refresh All Real-Time Data"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            backgroundColor: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-on-surface-variant)',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: '16px', color: 'var(--color-secondary)' }}>
            sync
          </span>
          <span>{lastUpdated}</span>
        </button>

        {/* User Profile */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', paddingLeft: '8px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'right' }}>
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '13px',
                fontWeight: 600,
                color: 'var(--color-on-surface)',
                lineHeight: 1.2,
              }}
            >
              Transit Ops
            </span>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '9.5px',
                color: 'var(--color-on-surface-variant)',
                textTransform: 'uppercase',
              }}
            >
              Municipal Admin
            </span>
          </div>
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '50%',
              backgroundColor: 'var(--color-primary-container)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>
              person
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
