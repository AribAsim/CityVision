import React, { useState, useMemo } from 'react'
import type { IncidentSummary, IncidentStatus } from '../../types'
import { patchIncidentStatus } from '../../services/api'
import { SEED_RECENT_INCIDENTS } from '../../services/seedData'

interface ReportsViewProps {
  incidents: IncidentSummary[]
  onSelectIncident: (inc: IncidentSummary) => void
  onRefresh: () => void
}

export const ReportsView: React.FC<ReportsViewProps> = ({
  incidents,
  onSelectIncident,
  onRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [statusTab, setStatusTab] = useState<'ALL' | 'PENDING' | 'IN_PROGRESS' | 'RESOLVED'>('ALL')
  const [updatingId, setUpdatingId] = useState<string | null>(null)

  const effectiveIncidents = incidents.length > 0 ? incidents : SEED_RECENT_INCIDENTS

  // Counts
  const totalCount = effectiveIncidents.length
  const pendingCount = effectiveIncidents.filter((i) => i.status === 'NEW' || i.status === 'VERIFIED').length
  const inProgressCount = effectiveIncidents.filter((i) => i.status === 'ASSIGNED' || i.status === 'IN_PROGRESS').length
  const resolvedCount = effectiveIncidents.filter((i) => i.status === 'RESOLVED').length
  const multiBusCount = effectiveIncidents.filter((i) => i.unique_bus_count >= 2).length

  // Filtered
  const filtered = useMemo(() => {
    return effectiveIncidents.filter((inc) => {
      if (searchTerm) {
        const q = searchTerm.toLowerCase()
        const matchId = inc.incident_id.toLowerCase().includes(q)
        const matchType = inc.anomaly_type.toLowerCase().includes(q)
        if (!matchId && !matchType) return false
      }

      if (statusTab === 'PENDING') {
        return inc.status === 'NEW' || inc.status === 'VERIFIED'
      }
      if (statusTab === 'IN_PROGRESS') {
        return inc.status === 'ASSIGNED' || inc.status === 'IN_PROGRESS'
      }
      if (statusTab === 'RESOLVED') {
        return inc.status === 'RESOLVED'
      }
      return true
    })
  }, [effectiveIncidents, searchTerm, statusTab])

  // Advance status lifecycle
  const handleAdvanceStatus = async (e: React.MouseEvent, inc: IncidentSummary) => {
    e.stopPropagation()
    let nextStatus: IncidentStatus = 'VERIFIED'
    if (inc.status === 'NEW') nextStatus = 'VERIFIED'
    else if (inc.status === 'VERIFIED') nextStatus = 'ASSIGNED'
    else if (inc.status === 'ASSIGNED') nextStatus = 'IN_PROGRESS'
    else if (inc.status === 'IN_PROGRESS') nextStatus = 'RESOLVED'
    else return // Already resolved

    try {
      setUpdatingId(inc.incident_id)
      await patchIncidentStatus(inc.incident_id, nextStatus, 'Updated via Municipal Command Center Work Order Dispatch')
      onRefresh()
    } catch (err) {
      console.error('Failed to update status:', err)
      alert(`Could not update status: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setUpdatingId(null)
    }
  }

  // Export CSV functionality
  const handleExportCSV = () => {
    const headers = ['IncidentID', 'Type', 'Severity', 'PriorityScore', 'Status', 'Latitude', 'Longitude', 'UniqueBuses', 'LastDetected']
    const rows = filtered.map((i) => [
      i.incident_id,
      i.anomaly_type,
      i.severity,
      i.priority_score,
      i.status,
      i.latitude,
      i.longitude,
      i.unique_bus_count,
      i.last_detected_at,
    ])

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n')
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement('a')
    link.setAttribute('href', encodedUri)
    link.setAttribute('download', `city_vision_dossier_${new Date().toISOString().slice(0, 10)}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Header & Global Actions */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="radar-ping" style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-secondary)' }} />
            <span className="font-label-sm" style={{ color: 'var(--color-secondary)', fontWeight: 700, letterSpacing: '0.05em' }}>
              MUNICIPAL AUDIT LOG // CADASTRAL INFRASTRUCTURE RECORDS
            </span>
          </div>
          <h1 className="font-headline-xl" style={{ color: 'var(--color-primary)', margin: 0 }}>
            REPORTS & WORK ORDER DISPATCH
          </h1>
          <p className="font-body-md" style={{ color: 'var(--color-on-surface-variant)', margin: 0 }}>
            Official municipal triage log of AI-detected road anomalies across public transit corridors
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <button id="btn-export-csv" className="btn-secondary" onClick={handleExportCSV}>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: 'var(--color-secondary)' }}>sim_card_download</span>
            <span>Export CSV Dossier</span>
          </button>
          <button id="btn-print-pdf" className="btn-secondary" onClick={() => window.print()}>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: 'var(--color-primary)' }}>picture_as_pdf</span>
            <span>Print Work Orders</span>
          </button>
        </div>
      </div>

      {/* 2. 5 KPI Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div className="cv-card" style={{ padding: '16px' }}>
          <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>TOTAL LOGGED</span>
          <div className="font-headline-xl" style={{ color: 'var(--color-primary)', marginTop: '4px', lineHeight: 1 }}>{totalCount}</div>
          <span className="font-body-sm" style={{ color: 'var(--color-secondary)', marginTop: '4px', display: 'block' }}>
            Gross corridor payload stream
          </span>
        </div>

        <div className="cv-card" style={{ padding: '16px', borderLeft: '4px solid #f59e0b' }}>
          <span className="font-label-sm" style={{ color: '#b45309' }}>PENDING TRIAGE</span>
          <div className="font-headline-xl" style={{ color: '#b45309', marginTop: '4px', lineHeight: 1 }}>{pendingCount}</div>
          <span className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)', marginTop: '4px', display: 'block' }}>
            Awaiting civil supervisor sign-off
          </span>
        </div>

        <div className="cv-card" style={{ padding: '16px', borderLeft: '4px solid #0051d5' }}>
          <span className="font-label-sm" style={{ color: 'var(--color-secondary)' }}>ACTIVE DISPATCH</span>
          <div className="font-headline-xl" style={{ color: 'var(--color-secondary)', marginTop: '4px', lineHeight: 1 }}>{inProgressCount}</div>
          <span className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)', marginTop: '4px', display: 'block' }}>
            Field repair crews mobilized
          </span>
        </div>

        <div className="cv-card" style={{ padding: '16px', borderLeft: '4px solid #10b981' }}>
          <span className="font-label-sm" style={{ color: '#047857' }}>RESOLVED / PATCHED</span>
          <div className="font-headline-xl" style={{ color: '#047857', marginTop: '4px', lineHeight: 1 }}>{resolvedCount}</div>
          <span className="font-body-sm" style={{ color: '#047857', marginTop: '4px', display: 'block', fontWeight: 600 }}>
            Closed post-resurfacing audit
          </span>
        </div>

        <div className="cv-card" style={{ padding: '16px', borderLeft: '4px solid #7e22ce' }}>
          <span className="font-label-sm" style={{ color: '#7e22ce' }}>CROSS-BUS VERIFIED</span>
          <div className="font-headline-xl" style={{ color: 'var(--color-primary)', marginTop: '4px', lineHeight: 1 }}>{multiBusCount}</div>
          <span className="font-body-sm" style={{ color: 'var(--color-secondary)', marginTop: '4px', display: 'block', fontFamily: 'var(--font-mono)' }}>
            Clustered by ≥2 buses
          </span>
        </div>
      </div>

      {/* 3. Search & Status Tabs Filter */}
      <div className="cv-card" style={{ padding: '14px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: '1 1 300px', backgroundColor: '#f8faff', padding: '6px 14px', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}>
          <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#94a3b8' }}>search</span>
          <input
            id="report-search-filter"
            type="text"
            placeholder="Search by Issue ID, defect type, or coordinates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ border: 'none', background: 'transparent', outline: 'none', width: '100%', fontFamily: 'var(--font-body)', fontSize: '13px' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: '#f1f5f9', padding: '4px', borderRadius: 'var(--radius-md)' }}>
          {(['ALL', 'PENDING', 'IN_PROGRESS', 'RESOLVED'] as const).map((tab) => {
            const isTabActive = statusTab === tab
            return (
              <button
                key={tab}
                id={`tab-filter-${tab.toLowerCase()}`}
                onClick={() => setStatusTab(tab)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 'var(--radius-sm)',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: isTabActive ? '#ffffff' : 'transparent',
                  color: isTabActive ? 'var(--color-primary)' : 'var(--color-on-surface-variant)',
                  fontWeight: isTabActive ? 700 : 500,
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11.5px',
                  boxShadow: isTabActive ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                  transition: 'all 0.15s ease',
                }}
              >
                {tab === 'ALL' && `All (${totalCount})`}
                {tab === 'PENDING' && `Pending (${pendingCount})`}
                {tab === 'IN_PROGRESS' && `In Progress (${inProgressCount})`}
                {tab === 'RESOLVED' && `Resolved (${resolvedCount})`}
              </button>
            )
          })}
        </div>
      </div>

      {/* 4. Comprehensive Cadastral Data Table */}
      <div className="cv-card" style={{ overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8faff', borderBottom: '1px solid #e2e8f0', color: 'var(--color-on-surface-variant)', fontFamily: 'var(--font-mono)', fontSize: '11px', textTransform: 'uppercase' }}>
                <th style={{ padding: '12px 16px' }}>Incident ID</th>
                <th style={{ padding: '12px 16px' }}>Anomaly Type</th>
                <th style={{ padding: '12px 16px' }}>Severity & Score</th>
                <th style={{ padding: '12px 16px' }}>Coordinates</th>
                <th style={{ padding: '12px 16px' }}>Consensus</th>
                <th style={{ padding: '12px 16px' }}>Status</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((inc, idx) => (
                <tr
                  key={inc.incident_id}
                  onClick={() => onSelectIncident(inc)}
                  style={{
                    borderBottom: '1px solid #f1f5f9',
                    backgroundColor: idx % 2 === 0 ? '#ffffff' : '#fcfdff',
                    cursor: 'pointer',
                    transition: 'background-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#eff4ff' }}
                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = idx % 2 === 0 ? '#ffffff' : '#fcfdff' }}
                >
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--color-primary)' }}>
                    {inc.incident_id}
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="material-symbols-outlined" style={{ fontSize: '18px', color: inc.anomaly_type === 'Pothole' ? '#ba1a1a' : '#0051d5' }}>
                        {inc.anomaly_type === 'Pothole' ? 'report_problem' : 'alt_route'}
                      </span>
                      <span>{inc.anomaly_type}</span>
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: 'var(--radius-full)',
                          fontSize: '10px',
                          fontFamily: 'var(--font-mono)',
                          fontWeight: 700,
                          backgroundColor: inc.severity === 'Critical' ? '#fee2e2' : inc.severity === 'High' ? '#fff7ed' : '#eff4ff',
                          color: inc.severity === 'Critical' ? '#ba1a1a' : inc.severity === 'High' ? '#c2410c' : '#1d4ed8',
                        }}
                      >
                        {inc.severity}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--color-on-surface-variant)' }}>
                        {inc.priority_score}/100
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: '11.5px', color: 'var(--color-on-surface-variant)' }}>
                    {inc.latitude.toFixed(4)}°N, {inc.longitude.toFixed(4)}°E
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {inc.unique_bus_count >= 2 ? (
                      <span className="badge-multibus">
                        <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>verified</span>
                        <span>{inc.unique_bus_count} Buses</span>
                      </span>
                    ) : (
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#64748b' }}>
                        Single Bus
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span
                      style={{
                        padding: '3px 10px',
                        borderRadius: 'var(--radius-sm)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: inc.status === 'RESOLVED' ? '#ecfdf5' : inc.status === 'IN_PROGRESS' ? '#eff4ff' : '#fef3c7',
                        color: inc.status === 'RESOLVED' ? '#047857' : inc.status === 'IN_PROGRESS' ? '#0051d5' : '#b45309',
                      }}
                    >
                      {inc.status}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                      <button
                        className="btn-secondary"
                        onClick={(e) => {
                          e.stopPropagation()
                          onSelectIncident(inc)
                        }}
                        style={{ padding: '4px 10px', fontSize: '11.5px' }}
                      >
                        Details
                      </button>

                      {inc.status !== 'RESOLVED' && (
                        <button
                          className="btn-primary"
                          disabled={updatingId === inc.incident_id}
                          onClick={(e) => handleAdvanceStatus(e, inc)}
                          style={{ padding: '4px 10px', fontSize: '11.5px' }}
                        >
                          {updatingId === inc.incident_id
                            ? '...'
                            : inc.status === 'NEW'
                            ? 'Verify'
                            : inc.status === 'VERIFIED'
                            ? 'Assign'
                            : inc.status === 'ASSIGNED'
                            ? 'Start'
                            : 'Resolve'}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
