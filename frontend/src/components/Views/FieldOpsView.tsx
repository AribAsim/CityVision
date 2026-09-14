import React, { useState } from 'react'
import type { IncidentSummary } from '../../types'
import { patchIncidentStatus } from '../../services/api'

interface FieldOpsViewProps {
  incidents: IncidentSummary[]
  onSelectIncident: (incident: IncidentSummary) => void
  onRefresh: () => void
}

export const FieldOpsView: React.FC<FieldOpsViewProps> = ({
  incidents,
  onSelectIncident,
  onRefresh,
}) => {
  const [filter, setFilter] = useState<'ALL' | 'ASSIGNED' | 'IN_PROGRESS' | 'RESOLVED'>('ALL')
  const [submittingId, setSubmittingId] = useState<string | null>(null)
  const [resolutionNote, setResolutionNote] = useState<string>('')
  const [activeResolvingId, setActiveResolvingId] = useState<string | null>(null)

  // Filter incidents for field operations
  const fieldIncidents = incidents.filter((inc) => {
    if (filter === 'ALL') return inc.status !== 'NEW'
    return inc.status === filter
  })

  const handleResolve = async (incidentId: string) => {
    try {
      setSubmittingId(incidentId)
      await patchIncidentStatus(incidentId, 'RESOLVED', resolutionNote || 'Resolved by Field Ops Crew')
      setActiveResolvingId(null)
      setResolutionNote('')
      onRefresh()
    } catch (err: any) {
      alert(`Failed to resolve: ${err.message || err}`)
    } finally {
      setSubmittingId(null)
    }
  }

  const handleStartWork = async (incidentId: string) => {
    try {
      setSubmittingId(incidentId)
      await patchIncidentStatus(incidentId, 'IN_PROGRESS', 'Field crew dispatched on-site')
      onRefresh()
    } catch (err: any) {
      alert(`Failed to update status: ${err.message || err}`)
    } finally {
      setSubmittingId(null)
    }
  }

  const openGoogleMaps = (lat: number, lng: number) => {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', paddingBottom: '50px' }}>
      {/* Header Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Field Operations & Resolution Portal
            </h1>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                backgroundColor: '#dbeafe',
                color: '#1e40af',
                padding: '3px 8px',
                borderRadius: '4px',
                fontFamily: 'JetBrains Mono, monospace',
              }}
            >
              MOBILE OPTIMIZED
            </span>
          </div>
          <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
            Field official dispatch, on-site GPS navigation, evidence inspection, and work order closure.
          </p>
        </div>

        {/* Filter Pills */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {(['ALL', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
                border: '1px solid #cbd5e1',
                backgroundColor: filter === f ? '#0051d5' : '#ffffff',
                color: filter === f ? '#ffffff' : '#475569',
                cursor: 'pointer',
              }}
            >
              {f.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Incident List Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: '16px',
        }}
      >
        {fieldIncidents.length === 0 ? (
          <div
            style={{
              gridColumn: '1 / -1',
              backgroundColor: '#ffffff',
              borderRadius: '10px',
              padding: '40px',
              textAlign: 'center',
              border: '1px solid #e2e8f0',
              color: '#64748b',
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '48px', color: '#cbd5e1' }}>
              assignment_turned_in
            </span>
            <div style={{ fontSize: '16px', fontWeight: 700, marginTop: '8px' }}>
              No Work Orders in this Category
            </div>
            <div style={{ fontSize: '13px', marginTop: '4px' }}>
              Select "All" or check back when new road repairs are assigned to the field.
            </div>
          </div>
        ) : (
          fieldIncidents.map((inc) => (
            <div
              key={inc.incident_id}
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '10px',
                border: '1px solid #e2e8f0',
                padding: '16px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '12px',
              }}
            >
              <div>
                {/* Header: ID + Status + Severity */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '12px', fontWeight: 700, color: '#334155' }}>
                    {inc.incident_id}
                  </span>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: 700,
                        padding: '2px 6px',
                        borderRadius: '4px',
                        backgroundColor: inc.severity === 'Critical' ? '#fee2e2' : inc.severity === 'High' ? '#ffedd5' : '#fef3c7',
                        color: inc.severity === 'Critical' ? '#ba1a1a' : inc.severity === 'High' ? '#c2410c' : '#b45309',
                      }}
                    >
                      {inc.severity}
                    </span>
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: 700,
                        padding: '2px 6px',
                        borderRadius: '4px',
                        backgroundColor: inc.status === 'RESOLVED' ? '#dcfce7' : '#f1f5f9',
                        color: inc.status === 'RESOLVED' ? '#15803d' : '#475569',
                      }}
                    >
                      {inc.status}
                    </span>
                  </div>
                </div>

                {/* Anomaly Title */}
                <div style={{ fontSize: '16px', fontWeight: 800, color: '#0f172a', marginTop: '8px' }}>
                  {inc.anomaly_type}
                </div>

                {/* Location & Time Info */}
                <div style={{ fontSize: '12px', color: '#64748b', marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                  <div>📍 Lat: {inc.latitude.toFixed(5)}, Lon: {inc.longitude.toFixed(5)}</div>
                  <div>🕒 Reported: {new Date(inc.first_detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                  <div>🚌 Multi-Bus Confirmations: {inc.confirmation_count}</div>
                </div>

                {/* Snapshot preview if available */}
                {inc.primary_image_url && (
                  <div style={{ marginTop: '10px', height: '120px', borderRadius: '6px', overflow: 'hidden', backgroundColor: '#f1f5f9' }}>
                    <img
                      src={inc.primary_image_url}
                      alt="Hazard Evidence"
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => openGoogleMaps(inc.latitude, inc.longitude)}
                    style={{
                      flex: 1,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '4px',
                      padding: '8px',
                      borderRadius: '6px',
                      border: '1px solid #cbd5e1',
                      backgroundColor: '#f8fafc',
                      color: '#0284c7',
                      fontSize: '12px',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>navigation</span>
                    <span>Navigate</span>
                  </button>

                  <button
                    onClick={() => onSelectIncident(inc)}
                    style={{
                      padding: '8px 12px',
                      borderRadius: '6px',
                      border: '1px solid #cbd5e1',
                      backgroundColor: '#ffffff',
                      color: '#475569',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Details
                  </button>
                </div>

                {/* Status Advancement */}
                {inc.status === 'ASSIGNED' && (
                  <button
                    disabled={submittingId === inc.incident_id}
                    onClick={() => handleStartWork(inc.incident_id)}
                    style={{
                      width: '100%',
                      padding: '8px',
                      borderRadius: '6px',
                      border: 'none',
                      backgroundColor: '#ea580c',
                      color: '#ffffff',
                      fontSize: '12px',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    {submittingId === inc.incident_id ? 'Updating...' : 'Start Work (Mark In-Progress)'}
                  </button>
                )}

                {inc.status === 'IN_PROGRESS' && (
                  <div>
                    {activeResolvingId === inc.incident_id ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        <input
                          type="text"
                          placeholder="Resolution note (e.g. cold mix patched)"
                          value={resolutionNote}
                          onChange={(e) => setResolutionNote(e.target.value)}
                          style={{
                            padding: '6px 8px',
                            borderRadius: '4px',
                            border: '1px solid #cbd5e1',
                            fontSize: '12px',
                          }}
                        />
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <button
                            disabled={submittingId === inc.incident_id}
                            onClick={() => handleResolve(inc.incident_id)}
                            style={{
                              flex: 1,
                              padding: '6px',
                              borderRadius: '4px',
                              border: 'none',
                              backgroundColor: '#16a34a',
                              color: '#ffffff',
                              fontSize: '12px',
                              fontWeight: 700,
                              cursor: 'pointer',
                            }}
                          >
                            Confirm Resolved
                          </button>
                          <button
                            onClick={() => setActiveResolvingId(null)}
                            style={{
                              padding: '6px 10px',
                              borderRadius: '4px',
                              border: '1px solid #cbd5e1',
                              backgroundColor: '#ffffff',
                              fontSize: '12px',
                              cursor: 'pointer',
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => setActiveResolvingId(inc.incident_id)}
                        style={{
                          width: '100%',
                          padding: '8px',
                          borderRadius: '6px',
                          border: 'none',
                          backgroundColor: '#16a34a',
                          color: '#ffffff',
                          fontSize: '12px',
                          fontWeight: 700,
                          cursor: 'pointer',
                        }}
                      >
                        Complete & Mark Resolved
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
