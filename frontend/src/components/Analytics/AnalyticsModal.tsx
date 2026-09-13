import React from 'react'
import type { AnalyticsSummary, BusSummary } from '../../types'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import { X, BarChart3, PieChart as PieIcon, Bus } from 'lucide-react'

interface AnalyticsModalProps {
  analytics: AnalyticsSummary | null
  buses: BusSummary[]
  isOpen: boolean
  onClose: () => void
}

const SEVERITY_COLORS: Record<string, string> = {
  Critical: '#EF4444',
  High: '#F97316',
  Medium: '#EAB308',
  Low: '#3B82F6',
}

const TYPE_COLORS: string[] = ['#3B82F6', '#8B5CF6', '#EC4899', '#10B981']

export const AnalyticsModal: React.FC<AnalyticsModalProps> = ({
  analytics,
  buses,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !analytics) return null

  // Format anomaly types for Recharts
  const anomalyData = Object.entries(analytics.by_anomaly_type || {}).map(([type, count]) => ({
    name: type,
    count,
  }))

  // Format severities for Recharts
  const severityData = Object.entries(analytics.by_severity || {}).map(([sev, count]) => ({
    name: sev,
    value: count,
  }))

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000,
      padding: '20px',
    }}>
      <div style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-lg)',
        width: '840px',
        maxWidth: '100%',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        {/* Modal Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--color-surface-elevated)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(59, 130, 246, 0.15)',
              color: '#3B82F6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <BarChart3 size={18} />
            </div>
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC' }}>
                FLEET TELEMETRY & DEFECT ANALYTICS
              </h2>
              <div style={{ fontSize: '11px', color: '#94A3B8' }}>
                Aggregated Statistical Distribution Across Municipal Transit Corridors
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94A3B8',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Fleet Status Summary Cards */}
          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: '#94A3B8', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Bus size={14} color="#3B82F6" />
              Active Mobile Transit Fleet ({buses.length} Vehicles)
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px' }}>
              {buses.map((b) => (
                <div key={b.bus_id} style={{
                  background: 'var(--color-surface-elevated)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '10px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: '#93C5FD' }}>
                      🚌 {b.bus_id}
                    </div>
                    <div style={{ fontSize: '11px', color: '#94A3B8' }}>
                      Route: <strong style={{ color: '#F8FAFC' }}>{b.route_id}</strong>
                    </div>
                    <div style={{ fontSize: '10px', color: '#64748B' }}>
                      GPS: {b.latitude.toFixed(3)}, {b.longitude.toFixed(3)}
                    </div>
                  </div>
                  <div style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '12px',
                    background: 'rgba(16, 185, 129, 0.15)',
                    color: '#34D399',
                    border: '1px solid rgba(16, 185, 129, 0.3)'
                  }}>
                    {b.status}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Charts Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Defect Breakdown by Type */}
            <div style={{
              background: 'var(--color-surface-elevated)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: '16px',
            }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#F8FAFC', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BarChart3 size={15} color="#60A5FA" />
                Defects by Anomaly Type
              </div>
              <div style={{ width: '100%', height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={anomalyData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                    <XAxis dataKey="name" stroke="#64748B" fontSize={11} interval={0} angle={-15} textAnchor="end" />
                    <YAxis stroke="#64748B" fontSize={11} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: '6px', fontSize: '12px' }}
                    />
                    <Bar dataKey="count" fill="#3B82F6" radius={[4, 4, 0, 0]}>
                      {anomalyData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={TYPE_COLORS[index % TYPE_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Defect Breakdown by Severity */}
            <div style={{
              background: 'var(--color-surface-elevated)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: '16px',
            }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#F8FAFC', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <PieIcon size={15} color="#F87171" />
                Distribution by Severity
              </div>
              <div style={{ width: '100%', height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={severityData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={75}
                      innerRadius={40}
                      paddingAngle={3}
                    >
                      {severityData.map((entry) => (
                        <Cell key={`sev-${entry.name}`} fill={SEVERITY_COLORS[entry.name] || '#3B82F6'} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: '6px', fontSize: '12px' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', color: '#94A3B8' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
