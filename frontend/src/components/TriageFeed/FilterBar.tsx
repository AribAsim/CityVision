import React from 'react'
import type { IncidentFilters } from '../../types'

interface FilterBarProps {
  filters: IncidentFilters
  onFilterChange: (filters: IncidentFilters) => void
}

export const FilterBar: React.FC<FilterBarProps> = ({ filters, onFilterChange }) => {
  return (
    <div className="filter-bar">
      <select
        className="filter-select"
        value={filters.severity || ''}
        onChange={(e) => onFilterChange({ ...filters, severity: e.target.value || undefined })}
        aria-label="Filter by Severity"
      >
        <option value="">All Severities</option>
        <option value="Critical">Critical</option>
        <option value="High">High</option>
        <option value="Medium">Medium</option>
        <option value="Low">Low</option>
      </select>

      <select
        className="filter-select"
        value={filters.status || ''}
        onChange={(e) => onFilterChange({ ...filters, status: e.target.value || undefined })}
        aria-label="Filter by Status"
      >
        <option value="">All Statuses</option>
        <option value="NEW">New</option>
        <option value="VERIFIED">Verified</option>
        <option value="ASSIGNED">Assigned</option>
        <option value="IN_PROGRESS">In Progress</option>
        <option value="RESOLVED">Resolved</option>
      </select>

      <select
        className="filter-select"
        value={filters.anomaly_type || ''}
        onChange={(e) => onFilterChange({ ...filters, anomaly_type: e.target.value || undefined })}
        aria-label="Filter by Defect Type"
      >
        <option value="">All Types</option>
        <option value="Pothole">Pothole</option>
        <option value="Crack">Crack</option>
        <option value="Crack-Severe">Crack-Severe</option>
        <option value="Speed-Bump">Speed-Bump</option>
      </select>
    </div>
  )
}
