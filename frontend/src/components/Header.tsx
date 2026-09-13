import React from 'react'
import { ShieldAlert, Bus, Cpu } from 'lucide-react'

interface HeaderProps {
  activeBusesCount: number
  lastUpdated: string
}

// System Flow steps to display in header bar
const FLOW_STEPS = [
  { label: 'DETECT', icon: '📷', desc: 'YOLOv8 on Bus Camera' },
  { label: 'LOG', icon: '📡', desc: 'Edge → FastAPI' },
  { label: 'VERIFY', icon: '🔁', desc: 'Multi-Bus Clustering' },
  { label: 'PRIORITIZE', icon: '🎯', desc: 'Severity Engine' },
  { label: 'ESCALATE', icon: '⚠️', desc: 'Auto-Escalation' },
  { label: 'RESOLVE', icon: '✅', desc: 'Operator Closes' },
]

export const Header: React.FC<HeaderProps> = ({ activeBusesCount, lastUpdated }) => {
  return (
    <header className="app-header" style={{ flexDirection: 'column', gap: 0, padding: 0 }}>

      {/* Top brand bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 20px',
        borderBottom: '1px solid var(--color-border)',
        width: '100%',
      }}>
        <div className="header-brand">
          <div className="header-badge-icon">
            <ShieldAlert size={20} />
          </div>
          <div className="header-title-wrap">
            <h1>SIH26124 — Mobile Urban Intelligence Platform</h1>
            <div className="header-subtitle">
              Turning public transport fleets into distributed urban sensing units.
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#94A3B8' }}>
            <Bus size={15} color="#3B82F6" />
            <span>Fleet: <strong style={{ color: '#F8FAFC' }}>{activeBusesCount} Buses Active</strong></span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', color: '#94A3B8' }}>
            <Cpu size={14} color="#8B5CF6" />
            <span>AI: <strong style={{ color: '#A78BFA' }}>YOLOv8m Road Anomaly</strong></span>
          </div>
          <div className="header-status-indicator">
            <span className="pulsing-dot"></span>
            <span>LIVE • 4s AUTO-SYNC</span>
            <span style={{ fontSize: '10px', color: '#64748B', marginLeft: '4px' }}>
              ({lastUpdated})
            </span>
          </div>
        </div>
      </div>

      {/* System Flow Ribbon */}
      <div className="system-flow-ribbon">
        {FLOW_STEPS.map((step, idx) => (
          <React.Fragment key={step.label}>
            <div className="flow-step">
              <span className="flow-step-icon">{step.icon}</span>
              <div className="flow-step-text">
                <span className="flow-step-label">{step.label}</span>
                <span className="flow-step-desc">{step.desc}</span>
              </div>
            </div>
            {idx < FLOW_STEPS.length - 1 && (
              <div className="flow-arrow">→</div>
            )}
          </React.Fragment>
        ))}
      </div>
    </header>
  )
}
