import React, { useEffect, useState } from 'react'
import type { IncidentDetail, IncidentSummary } from '../../types'
import { fetchIncidentDetail } from '../../services/api'
import { ObservationList } from './ObservationList'
import { StatusHistory } from './StatusHistory'
import { StatusUpdater } from './StatusUpdater'
import { X, MapPin, ShieldCheck, Camera, Layers, History, Loader2, Cpu, AlertTriangle } from 'lucide-react'

interface DetailDrawerProps {
  incidentSummary: IncidentSummary | null
  onClose: () => void
  onRefresh: () => void
}

const SEVERITY_COLOR: Record<string, string> = {
  Critical: '#EF4444',
  High: '#F97316',
  Medium: '#EAB308',
  Low: '#3B82F6',
}

const SEVERITY_LABEL: Record<string, string> = {
  Critical: '🔴 CRITICAL',
  High: '🟠 HIGH',
  Medium: '🟡 MEDIUM',
  Low: '🔵 LOW',
}

const STATUS_STEPS = ['NEW', 'VERIFIED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED']
const STATUS_LABEL: Record<string, string> = {
  NEW: 'Detected',
  VERIFIED: 'Verified',
  ASSIGNED: 'Assigned',
  IN_PROGRESS: 'In Progress',
  RESOLVED: 'Resolved',
}

export const DetailDrawer: React.FC<DetailDrawerProps> = ({
  incidentSummary,
  onClose,
  onRefresh,
}) => {
  const [incidentDetail, setIncidentDetail] = useState<IncidentDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadDetail = async (id: string) => {
    try {
      setLoading(true)
      const data = await fetchIncidentDetail(id)
      setIncidentDetail(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch incident details')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (incidentSummary) {
      loadDetail(incidentSummary.incident_id)
    } else {
      setIncidentDetail(null)
    }
  }, [incidentSummary])

  if (!incidentSummary) return null

  const data = incidentDetail || (incidentSummary as unknown as IncidentDetail)
  const sevColor = SEVERITY_COLOR[data.severity] || '#64748B'
  const currentStepIdx = STATUS_STEPS.indexOf(data.status)

  return (
    <div className="detail-drawer-overlay">
      {/* Header */}
      <div className="drawer-header" style={{ borderBottom: `2px solid ${sevColor}33` }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '16px', fontWeight: 800, color: '#F8FAFC' }}>
              {data.anomaly_type}
            </span>
            <span style={{
              fontSize: '11px', fontWeight: 700, padding: '2px 7px',
              borderRadius: '4px', textTransform: 'uppercase',
              background: 'rgba(255,255,255,0.1)', color: '#93C5FD'
            }}>
              {data.incident_id}
            </span>
            <span style={{
              fontSize: '11px', fontWeight: 700, padding: '2px 8px',
              borderRadius: '4px', background: `${sevColor}22`,
              color: sevColor, border: `1px solid ${sevColor}55`,
            }}>
              {SEVERITY_LABEL[data.severity] || data.severity}
            </span>
          </div>
          <div style={{ fontSize: '11px', color: '#64748B', marginTop: '3px' }}>
            Road defect detected by YOLOv8m on transit vehicle — awaiting resolution
          </div>
        </div>
        <button className="drawer-close-btn" onClick={onClose} aria-label="Close details">
          <X size={18} />
        </button>
      </div>

      <div className="drawer-content-scroll">
        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#60A5FA', fontSize: '12px' }}>
            <Loader2 className="animate-spin" size={14} />
            <span>Synchronizing incident data...</span>
          </div>
        )}
        {error && (
          <div style={{ fontSize: '12px', color: '#F87171' }}>{error}</div>
        )}

        {/* Lifecycle progress stepper */}
        <div style={{ marginBottom: '4px' }}>
          <div className="drawer-section-title" style={{ marginBottom: '8px' }}>
            <History size={13} />
            Resolution Pipeline
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
            {STATUS_STEPS.map((step, idx) => {
              const isDone = idx <= currentStepIdx
              const isCurrent = idx === currentStepIdx
              return (
                <React.Fragment key={step}>
                  <div style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px',
                    flex: 1,
                  }}>
                    <div style={{
                      width: 20, height: 20, borderRadius: '50%',
                      background: isCurrent ? sevColor : isDone ? '#10B981' : '#1E293B',
                      border: `2px solid ${isCurrent ? sevColor : isDone ? '#10B981' : '#334155'}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '10px', fontWeight: 700, color: '#fff',
                      transition: 'all 0.3s',
                    }}>
                      {isDone && !isCurrent ? '✓' : idx + 1}
                    </div>
                    <span style={{
                      fontSize: '9px', fontWeight: isCurrent ? 700 : 500,
                      color: isCurrent ? sevColor : isDone ? '#10B981' : '#475569',
                      textAlign: 'center', whiteSpace: 'nowrap',
                    }}>
                      {STATUS_LABEL[step]}
                    </span>
                  </div>
                  {idx < STATUS_STEPS.length - 1 && (
                    <div style={{
                      height: '2px', flex: 1, maxWidth: '20px',
                      background: idx < currentStepIdx ? '#10B981' : '#1E293B',
                      marginBottom: '12px',
                    }} />
                  )}
                </React.Fragment>
              )
            })}
          </div>
        </div>

        {/* Multi-bus verification banner */}
        {data.unique_bus_count >= 2 && (
          <div style={{
            background: 'rgba(139, 92, 246, 0.12)',
            border: '1px solid rgba(139, 92, 246, 0.35)',
            borderRadius: 'var(--radius-sm)',
            padding: '8px 12px',
            display: 'flex', alignItems: 'flex-start', gap: '8px',
          }}>
            <ShieldCheck size={18} color="#A78BFA" style={{ flexShrink: 0, marginTop: '1px' }} />
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#DDD6FE' }}>
                ⚡ Cross-Verified by {data.unique_bus_count} Independent Transit Vehicles
              </div>
              <div style={{ fontSize: '11px', color: '#7C3AED', marginTop: '2px' }}>
                Multiple buses detected the same defect independently at this GPS location.
                Severity escalated by one tier. High confidence.
              </div>
            </div>
          </div>
        )}

        {/* AI Detection Badge */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '8px', padding: '7px 10px',
          background: 'rgba(37, 99, 235, 0.1)', border: '1px solid rgba(37,99,235,0.25)',
          borderRadius: 'var(--radius-sm)',
        }}>
          <Cpu size={14} color="#60A5FA" />
          <span style={{ fontSize: '11px', color: '#93C5FD', fontWeight: 600 }}>
            AI MODEL: YOLOv8m Road Anomaly Detector
          </span>
          <span style={{
            marginLeft: 'auto', fontSize: '10px', color: '#64748B',
            fontFamily: 'monospace',
          }}>
            best.pt @ 120 epochs
          </span>
        </div>

        {/* Evidence Snapshot */}
        <div>
          <div className="drawer-section-title">
            <Camera size={13} />
            YOLOv8 Detection Snapshot
            {data.confirmation_count > 0 && (
              <span style={{
                marginLeft: 'auto', fontSize: '10px', color: '#64748B',
                background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '4px',
              }}>
                {data.confirmation_count} frame{data.confirmation_count > 1 ? 's' : ''} captured
              </span>
            )}
          </div>
          <div className="snapshot-container">
            {data.primary_image_url ? (
              <img
                src={data.primary_image_url}
                alt={`YOLOv8 detection snapshot for ${data.incident_id}`}
                className="snapshot-image"
                onError={(e) => {
                  e.currentTarget.style.display = 'none'
                  const fallback = e.currentTarget.parentElement?.querySelector('.snapshot-empty-fallback') as HTMLElement
                  if (fallback) fallback.style.display = 'flex'
                }}
              />
            ) : null}
            <div
              className="snapshot-empty snapshot-empty-fallback"
              style={{ display: data.primary_image_url ? 'none' : 'flex' }}
            >
              <AlertTriangle size={28} color="#F59E0B" />
              <span style={{ fontWeight: 600, color: '#F59E0B', marginTop: '4px' }}>Snapshot Pending</span>
              <span style={{ fontSize: '11px', color: '#64748B', textAlign: 'center', marginTop: '4px' }}>
                Edge pipeline has not yet uploaded evidence for this detection.
                Launch the edge runner with a video file to capture a snapshot.
              </span>
            </div>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr',
          gap: '8px', background: 'var(--color-surface-elevated)',
          padding: '12px', borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)'
        }}>
          <div>
            <div style={{ fontSize: '10px', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Centroid GPS</div>
            <div style={{ fontSize: '12px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
              <MapPin size={12} color="#3B82F6" />
              {data.latitude.toFixed(5)}, {data.longitude.toFixed(5)}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '10px', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Priority Index</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '3px' }}>
              <div style={{
                height: '6px', flex: 1, background: '#1E293B',
                borderRadius: '3px', overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%', width: `${data.priority_score}%`,
                  background: sevColor, borderRadius: '3px',
                  transition: 'width 0.5s',
                }} />
              </div>
              <span style={{ fontSize: '12px', fontWeight: 700, color: sevColor, minWidth: '36px', textAlign: 'right' }}>
                {data.priority_score}/100
              </span>
            </div>
          </div>

          <div>
            <div style={{ fontSize: '10px', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Observations</div>
            <div style={{ fontSize: '13px', fontWeight: 700, marginTop: '2px', color: '#F8FAFC' }}>
              {data.confirmation_count}
              <span style={{ fontSize: '11px', fontWeight: 400, color: '#64748B', marginLeft: '4px' }}>detections logged</span>
            </div>
          </div>

          <div>
            <div style={{ fontSize: '10px', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Detecting Buses</div>
            <div style={{ fontSize: '13px', fontWeight: 700, marginTop: '2px', color: data.unique_bus_count >= 2 ? '#A78BFA' : '#F8FAFC' }}>
              {data.unique_bus_count}
              <span style={{ fontSize: '11px', fontWeight: 400, color: '#64748B', marginLeft: '4px' }}>
                {data.unique_bus_count >= 2 ? 'cross-verified ✓' : 'unique vehicle'}
              </span>
            </div>
          </div>
        </div>

        {/* Lifecycle Status Updater */}
        <StatusUpdater
          incidentId={data.incident_id}
          currentStatus={data.status}
          onStatusUpdated={() => {
            loadDetail(data.incident_id)
            onRefresh()
          }}
        />

        {/* Multi-Bus Observation Timeline */}
        <div>
          <div className="drawer-section-title">
            <Layers size={13} />
            Bus Observation Log ({data.observations?.length || 0})
          </div>
          <ObservationList observations={data.observations || []} />
        </div>

        {/* Status Audit Trail */}
        <div>
          <div className="drawer-section-title">
            <History size={13} />
            Lifecycle Audit Trail
          </div>
          <StatusHistory history={data.status_history || []} />
        </div>
      </div>
    </div>
  )
}
