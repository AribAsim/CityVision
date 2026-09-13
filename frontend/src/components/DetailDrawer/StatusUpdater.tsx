import React, { useState } from 'react'
import type { IncidentStatus } from '../../types'
import { patchIncidentStatus } from '../../services/api'
import { ArrowRight, Check, AlertCircle, Loader2 } from 'lucide-react'

interface StatusUpdaterProps {
  incidentId: string
  currentStatus: IncidentStatus
  onStatusUpdated: () => void
}

const STATUS_CONFIG: Record<IncidentStatus, {
  label: string; color: string; bg: string; icon: string; hint: string
}> = {
  NEW:         { label: 'Detected',    color: '#60A5FA', bg: 'rgba(59,130,246,0.15)',  icon: '📡', hint: 'Awaiting triage by road authority' },
  VERIFIED:    { label: 'Verified',    color: '#A78BFA', bg: 'rgba(139,92,246,0.15)', icon: '✅', hint: 'Defect confirmed, pending assignment' },
  ASSIGNED:    { label: 'Assigned',    color: '#FB923C', bg: 'rgba(249,115,22,0.15)',  icon: '📋', hint: 'Maintenance team has been notified' },
  IN_PROGRESS: { label: 'In Progress', color: '#FBBF24', bg: 'rgba(234,179,8,0.15)',   icon: '🔧', hint: 'Repair crew actively working on site' },
  RESOLVED:    { label: 'Resolved',    color: '#34D399', bg: 'rgba(16,185,129,0.15)',  icon: '🏁', hint: 'Road defect repaired and closed' },
}

const NEXT_STATUS: Partial<Record<IncidentStatus, IncidentStatus[]>> = {
  NEW:         ['VERIFIED', 'ASSIGNED'],
  VERIFIED:    ['ASSIGNED'],
  ASSIGNED:    ['IN_PROGRESS'],
  IN_PROGRESS: ['RESOLVED'],
  RESOLVED:    [],
}

const TRANSITION_LABELS: Partial<Record<IncidentStatus, string>> = {
  VERIFIED:    'Mark Verified',
  ASSIGNED:    'Assign to Crew',
  IN_PROGRESS: 'Start Repair',
  RESOLVED:    'Mark Resolved',
}

export const StatusUpdater: React.FC<StatusUpdaterProps> = ({
  incidentId,
  currentStatus,
  onStatusUpdated,
}) => {
  const [updating, setUpdating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notes, setNotes] = useState('')

  const nextStatuses = NEXT_STATUS[currentStatus] || []
  const cfg = STATUS_CONFIG[currentStatus] || STATUS_CONFIG.NEW

  const handleTransition = async (targetStatus: IncidentStatus) => {
    try {
      setUpdating(true)
      setError(null)
      await patchIncidentStatus(
        incidentId,
        targetStatus,
        notes.trim() ? notes.trim() : `Operator action: transition to ${targetStatus}`
      )
      setNotes('')
      onStatusUpdated()
    } catch (err: any) {
      setError(err.message || 'Status transition failed')
    } finally {
      setUpdating(false)
    }
  }

  if (currentStatus === 'RESOLVED') {
    return (
      <div className="status-updater-bar" style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#10B981' }}>
          <Check size={18} />
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700 }}>Incident Resolved — Lifecycle Complete</div>
            <div style={{ fontSize: '11px', color: '#064E3B', marginTop: '2px' }}>
              Road defect marked as repaired. Status recorded in audit trail.
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="status-updater-bar">
      {/* Current status context */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '8px',
        padding: '8px 10px', borderRadius: 'var(--radius-sm)',
        background: cfg.bg, border: `1px solid ${cfg.color}44`,
        marginBottom: '8px',
      }}>
        <span style={{ fontSize: '18px' }}>{cfg.icon}</span>
        <div>
          <div style={{ fontSize: '11px', fontWeight: 700, color: cfg.color, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Current: {cfg.label}
          </div>
          <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '2px' }}>
            {cfg.hint}
          </div>
        </div>
      </div>

      <div style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>
        Operator Actions
      </div>

      <input
        type="text"
        placeholder="Add operational notes (optional)..."
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        style={{
          background: 'rgba(0,0,0,0.25)', border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-sm)', color: '#F8FAFC',
          padding: '6px 10px', fontSize: '12px', outline: 'none', width: '100%',
          boxSizing: 'border-box',
        }}
      />

      <div className="status-actions-group" style={{ marginTop: '8px' }}>
        {nextStatuses.map((stat) => (
          <button
            key={stat}
            type="button"
            className="action-transition-btn"
            disabled={updating}
            onClick={() => handleTransition(stat)}
            style={{ minWidth: '140px' }}
          >
            {updating ? <Loader2 size={13} className="animate-spin" /> : <ArrowRight size={13} />}
            <span>{TRANSITION_LABELS[stat] || `Mark ${stat.replace('_', ' ')}`}</span>
          </button>
        ))}
      </div>

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#F87171', fontSize: '11px', marginTop: '6px' }}>
          <AlertCircle size={13} />
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}
