import React from 'react'
import type { IncidentFilters, IncidentSummary } from '../../types'
import { FilterBar } from './FilterBar'
import { IncidentCard } from './IncidentCard'
import { BusScanPanel } from '../BusScan/BusScanPanel'
import { ListFilter, AlertCircle, Loader2 } from 'lucide-react'

interface TriageFeedProps {
  incidents: IncidentSummary[]
  loading: boolean
  error: string | null
  filters: IncidentFilters
  onFilterChange: (filters: IncidentFilters) => void
  selectedIncidentId: string | null
  onSelectIncident: (incident: IncidentSummary) => void
  onScanComplete?: () => void
}

export const TriageFeed: React.FC<TriageFeedProps> = ({
  incidents,
  loading,
  error,
  filters,
  onFilterChange,
  selectedIncidentId,
  onSelectIncident,
  onScanComplete,
}) => {
  return (
    <aside className="triage-panel">
      <div className="triage-panel-header">
        <div className="triage-title-bar">
          <h2>
            <ListFilter size={16} />
            DEFECT TRIAGE FEED
          </h2>
          <span className="incident-count-tag">
            {incidents.length} Detected
          </span>
        </div>
        <FilterBar filters={filters} onFilterChange={onFilterChange} />
        <BusScanPanel onScanComplete={onScanComplete} />
      </div>

      <div className="incident-cards-scroll">
        {loading && incidents.length === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 20px', color: '#64748B', gap: '8px' }}>
            <Loader2 className="animate-spin" size={24} color="#3B82F6" />
            <span>Scanning for live detections...</span>
          </div>
        )}

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px', color: '#F87171', fontSize: '12px' }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {!loading && incidents.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748B', fontSize: '13px' }}>
            <p>No road defects match the current filter criteria.</p>
          </div>
        )}

        {incidents.map((incident) => (
          <IncidentCard
            key={incident.id}
            incident={incident}
            isSelected={selectedIncidentId === incident.incident_id}
            onSelect={onSelectIncident}
          />
        ))}
      </div>
    </aside>
  )
}
