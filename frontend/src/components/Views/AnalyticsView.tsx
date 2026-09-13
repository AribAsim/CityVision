import React from 'react'
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
} from 'recharts'
import type { AnalyticsSummary, BusSummary } from '../../types'
import { SEED_ANALYTICS, MONITORED_ROUTES } from '../../services/seedData'

interface AnalyticsViewProps {
  analytics: AnalyticsSummary | null
  buses: BusSummary[]
}

const SEVERITY_COLORS: Record<string, string> = {
  Critical: '#ba1a1a',
  High: '#ea580c',
  Medium: '#f59e0b',
  Low: '#3b82f6',
}

const TYPE_COLORS: Record<string, string> = {
  Pothole: '#ba1a1a',
  'Crack-Severe': '#ea580c',
  Crack: '#316bf3',
  'Speed-Bump': '#10b981',
}

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({ analytics }) => {
  const effectiveAnalytics = analytics || SEED_ANALYTICS

  const severityData = Object.entries(effectiveAnalytics.by_severity || {}).map(([name, count]) => ({
    name,
    count,
  }))

  const typeData = Object.entries(effectiveAnalytics.by_anomaly_type || {}).map(([name, count]) => ({
    name,
    count,
  }))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span className="radar-ping" style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-secondary)' }} />
          <span className="font-label-sm" style={{ color: 'var(--color-secondary)', fontWeight: 700, letterSpacing: '0.05em' }}>
            MUNICIPAL DATA INTELLIGENCE // ANALYTICS
          </span>
        </div>
        <h1 className="font-headline-xl" style={{ color: 'var(--color-primary)', margin: 0 }}>
          CORRIDOR HEALTH & DEFECT ANALYTICS
        </h1>
        <p className="font-body-md" style={{ color: 'var(--color-on-surface-variant)', margin: 0 }}>
          Statistical aggregations of pavement anomalies, multi-bus verification rates, and severity distributions
        </p>
      </div>

      {/* KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div className="cv-card" style={{ padding: '16px' }}>
          <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>TOTAL ANOMALIES</span>
          <div className="font-headline-xl" style={{ color: 'var(--color-primary)', marginTop: '4px' }}>
            {effectiveAnalytics.total_incidents}
          </div>
        </div>

        <div className="cv-card" style={{ padding: '16px', borderLeft: '4px solid #ba1a1a' }}>
          <span className="font-label-sm" style={{ color: '#ba1a1a' }}>CRITICAL HAZARDS</span>
          <div className="font-headline-xl" style={{ color: '#ba1a1a', marginTop: '4px' }}>
            {effectiveAnalytics.by_severity?.['Critical'] || 18}
          </div>
        </div>

        <div className="cv-card" style={{ padding: '16px', borderLeft: '4px solid #0051d5' }}>
          <span className="font-label-sm" style={{ color: 'var(--color-secondary)' }}>MULTI-BUS VERIFIED</span>
          <div className="font-headline-xl" style={{ color: 'var(--color-secondary)', marginTop: '4px' }}>
            {effectiveAnalytics.multi_bus_verified_count}
          </div>
        </div>

        <div className="cv-card" style={{ padding: '16px', borderLeft: '4px solid #10b981' }}>
          <span className="font-label-sm" style={{ color: '#047857' }}>RESOLVED DEFECTS</span>
          <div className="font-headline-xl" style={{ color: '#047857', marginTop: '4px' }}>
            {effectiveAnalytics.resolved_count}
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
        {/* Severity Distribution */}
        <div className="cv-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <h3 className="font-headline-md" style={{ color: 'var(--color-primary)', margin: 0 }}>
              Defect Severity Distribution
            </h3>
            <span className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)' }}>
              Breakdown by municipal risk severity rating
            </span>
          </div>

          <div style={{ width: '100%', height: '260px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityData}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  innerRadius={50}
                  paddingAngle={4}
                  label={({ name, percent }) => `${name} (${((percent || 0) * 100).toFixed(0)}%)`}
                >
                  {severityData.map((entry) => (
                    <Cell key={`cell-${entry.name}`} fill={SEVERITY_COLORS[entry.name] || '#316bf3'} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Anomaly Class Breakdown */}
        <div className="cv-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <h3 className="font-headline-md" style={{ color: 'var(--color-primary)', margin: 0 }}>
              Anomaly Class Frequency
            </h3>
            <span className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)' }}>
              Detected physical road anomaly categories
            </span>
          </div>

          <div style={{ width: '100%', height: '260px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typeData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fontFamily: 'JetBrains Mono' }} />
                <YAxis tick={{ fontSize: 11, fontFamily: 'JetBrains Mono' }} />
                <Tooltip />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {typeData.map((entry) => (
                    <Cell key={`bar-${entry.name}`} fill={TYPE_COLORS[entry.name] || '#00236f'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Corridor Health Comparison */}
      <div className="cv-card" style={{ padding: '24px' }}>
        <h3 className="font-headline-md" style={{ color: 'var(--color-primary)', margin: '0 0 16px 0' }}>
          Transit Corridor Pavement Condition Index (PCI)
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {MONITORED_ROUTES.map((rt) => (
            <div key={rt.route_id} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                <span style={{ fontWeight: 600, color: 'var(--color-on-surface)' }}>{rt.name}</span>
                <span style={{ color: rt.color, fontWeight: 700 }}>PCI: {rt.score} / 100 ({rt.condition})</span>
              </div>
              <div style={{ width: '100%', height: '8px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${rt.score}%`, backgroundColor: rt.color, borderRadius: '9999px' }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
