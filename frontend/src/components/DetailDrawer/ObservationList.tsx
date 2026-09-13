import React from 'react'
import type { Observation } from '../../types'
import { Bus, Gauge, CheckCircle } from 'lucide-react'

interface ObservationListProps {
  observations: Observation[]
}

export const ObservationList: React.FC<ObservationListProps> = ({ observations }) => {
  const formatTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    } catch {
      return iso
    }
  }

  return (
    <div className="observations-timeline">
      {observations.map((obs, idx) => (
        <div key={obs.id || idx} className="timeline-item">
          <div className="timeline-item-header">
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <Bus size={13} color="#3B82F6" />
              <strong className="timeline-bus-tag">{obs.bus_id}</strong>
              <span style={{ color: '#64748B', fontSize: '11px' }}>({obs.route_id})</span>
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '3px', color: '#10B981', fontSize: '11px' }}>
              <CheckCircle size={11} />
              {(obs.confidence * 100).toFixed(0)}% Conf
            </span>
          </div>

          <div className="timeline-item-meta">
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Gauge size={11} />
              {obs.speed_kmh.toFixed(1)} km/h
            </span>
            <span>{formatTime(obs.timestamp)}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
