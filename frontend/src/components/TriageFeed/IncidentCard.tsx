import React from 'react'
import type { IncidentSummary } from '../../types'
import { MapPin, Clock, ShieldCheck, Bus } from 'lucide-react'

interface IncidentCardProps {
  incident: IncidentSummary
  isSelected: boolean
  onSelect: (incident: IncidentSummary) => void
}

const SEVERITY_COLOR: Record<string, string> = {
  critical: '#EF4444',
  high: '#F97316',
  medium: '#EAB308',
  low: '#3B82F6',
}

const ANOMALY_ICON: Record<string, string> = {
  Pothole: '🕳️',
  Crack: '〰️',
  'Crack-Severe': '⚡',
  'Speed-Bump': '🔰',
}

const STATUS_BADGE_COLOR: Record<string, { bg: string; color: string; label: string }> = {
  NEW:         { bg: 'rgba(59,130,246,0.15)', color: '#60A5FA',  label: 'NEW' },
  VERIFIED:    { bg: 'rgba(139,92,246,0.15)', color: '#A78BFA',  label: 'VERIFIED' },
  ASSIGNED:    { bg: 'rgba(249,115,22,0.15)', color: '#FB923C',  label: 'ASSIGNED' },
  IN_PROGRESS: { bg: 'rgba(234,179,8,0.15)',  color: '#FBBF24',  label: 'IN PROGRESS' },
  RESOLVED:    { bg: 'rgba(16,185,129,0.15)', color: '#34D399',  label: 'RESOLVED' },
}

export const IncidentCard: React.FC<IncidentCardProps> = ({
  incident,
  isSelected,
  onSelect,
}) => {
  const sevKey = incident.severity.toLowerCase()
  const sevColor = SEVERITY_COLOR[sevKey] || '#64748B'
  const statusStyle = STATUS_BADGE_COLOR[incident.status] || STATUS_BADGE_COLOR.NEW

  const formatTime = (isoString: string) => {
    try {
      const d = new Date(isoString)
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    } catch {
      return isoString
    }
  }

  return (
    <article
      id={`incident-card-${incident.incident_id}`}
      data-testid="incident-card"
      className={`incident-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect(incident)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect(incident)
        }
      }}
      aria-label={`Incident ${incident.incident_id} ${incident.anomaly_type}`}
      style={{ borderLeft: `3px solid ${sevColor}` }}
    >
      {/* Top row: anomaly icon + type + severity + status */}
      <div className="card-top-row">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '16px' }}>{ANOMALY_ICON[incident.anomaly_type] || '⚠️'}</span>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#F8FAFC', lineHeight: 1.2 }}>
              {incident.anomaly_type}
            </div>
            <div style={{ fontSize: '10px', color: '#64748B', fontFamily: 'monospace' }}>
              {incident.incident_id}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '3px' }}>
          <span className={`severity-pill ${sevKey}`}>{incident.severity}</span>
          <span style={{
            fontSize: '9px', fontWeight: 700, padding: '1px 5px',
            borderRadius: '3px', background: statusStyle.bg,
            color: statusStyle.color, letterSpacing: '0.4px',
          }}>
            {statusStyle.label}
          </span>
        </div>
      </div>

      {/* Multi-bus verification badge — prominent */}
      {incident.unique_bus_count >= 2 && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '5px',
          background: 'rgba(139,92,246,0.12)', border: '1px solid rgba(139,92,246,0.3)',
          borderRadius: '4px', padding: '4px 8px', marginTop: '4px',
        }}>
          <ShieldCheck size={12} color="#A78BFA" />
          <span style={{ fontSize: '11px', fontWeight: 700, color: '#DDD6FE' }}>
            ⚡ Verified by {incident.unique_bus_count} independent buses
          </span>
        </div>
      )}

      {/* Priority bar */}
      <div style={{ marginTop: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#64748B', marginBottom: '3px' }}>
          <span>AI Priority Score</span>
          <span style={{ color: sevColor, fontWeight: 700 }}>{incident.priority_score}/100</span>
        </div>
        <div style={{ height: '4px', background: '#1E293B', borderRadius: '2px', overflow: 'hidden' }}>
          <div style={{
            height: '100%',
            width: `${Math.min(incident.priority_score, 100)}%`,
            background: `linear-gradient(90deg, ${sevColor}88, ${sevColor})`,
            borderRadius: '2px',
            transition: 'width 0.5s ease',
          }} />
        </div>
      </div>

      {/* Metadata row: GPS + time */}
      <div className="card-meta-row" style={{ marginTop: '8px' }}>
        <div className="card-meta-geo">
          <MapPin size={11} color="#3B82F6" />
          <span>{incident.latitude.toFixed(4)}°, {incident.longitude.toFixed(4)}°</span>
        </div>
        <div className="card-meta-time">
          <Clock size={11} />
          <span>{formatTime(incident.last_detected_at)}</span>
        </div>
      </div>

      {/* Footer: observations + bus count + CTA */}
      <div className="card-footer-row" style={{ marginTop: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#64748B' }}>
          <Bus size={11} />
          <span>{incident.unique_bus_count} bus{incident.unique_bus_count > 1 ? 'es' : ''}</span>
          <span style={{ margin: '0 2px' }}>·</span>
          <span>{incident.confirmation_count} detection{incident.confirmation_count > 1 ? 's' : ''}</span>
        </div>
        <span style={{ fontSize: '10px', color: '#334155', fontWeight: 600 }}>
          INSPECT →
        </span>
      </div>
    </article>
  )
}
