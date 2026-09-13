import React from 'react'
import type { StatusHistoryEntry } from '../../types'

interface StatusHistoryProps {
  history: StatusHistoryEntry[]
}

export const StatusHistory: React.FC<StatusHistoryProps> = ({ history }) => {
  const formatTime = (iso: string) => {
    try {
      const d = new Date(iso)
      return `${d.toLocaleDateString([], { month: 'short', day: 'numeric' })} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
    } catch {
      return iso
    }
  }

  if (!history || history.length === 0) {
    return (
      <div style={{ fontSize: '11px', color: '#64748B', fontStyle: 'italic' }}>
        No lifecycle status transitions recorded yet.
      </div>
    )
  }

  return (
    <div className="audit-log-list">
      {history.map((entry, idx) => (
        <div key={entry.id || idx} className="audit-entry">
          <div className="audit-entry-top">
            <span className="audit-transition-text">
              {entry.from_status ? `${entry.from_status} → ` : 'INITIAL → '}
              <strong>{entry.to_status}</strong>
            </span>
            <span style={{ fontSize: '10px', color: '#64748B' }}>
              {formatTime(entry.changed_at)}
            </span>
          </div>
          {entry.notes && (
            <div className="audit-notes">
              "{entry.notes}"
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
