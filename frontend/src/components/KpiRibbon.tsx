import React from 'react'
import type { AnalyticsSummary } from '../types'
import { AlertTriangle, CheckCircle2, ShieldCheck, Clock, Flame } from 'lucide-react'

interface KpiRibbonProps {
  analytics: AnalyticsSummary | null
}

export const KpiRibbon: React.FC<KpiRibbonProps> = ({ analytics }) => {
  const total = analytics?.total_incidents ?? 0
  const pending = analytics?.pending_count ?? 0
  const multiBus = analytics?.multi_bus_verified_count ?? 0
  const inProgress = (analytics?.assigned_count ?? 0) + (analytics?.in_progress_count ?? 0)
  const resolved = analytics?.resolved_count ?? 0
  const critical = (analytics?.by_severity?.Critical ?? 0) + (analytics?.by_severity?.High ?? 0)

  return (
    <section className="kpi-ribbon" aria-label="Incident Analytics Ribbon">
      <div className="kpi-card">
        <div>
          <div className="kpi-info-label">Total Detected</div>
          <div className="kpi-value">{total}</div>
        </div>
        <div className="kpi-icon-box" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA' }}>
          <AlertTriangle size={18} />
        </div>
      </div>

      <div className="kpi-card">
        <div>
          <div className="kpi-info-label">Multi-Bus Verified</div>
          <div className="kpi-value" style={{ color: '#C4B5FD' }}>{multiBus}</div>
        </div>
        <div className="kpi-icon-box" style={{ background: 'rgba(139, 92, 246, 0.18)', color: '#A78BFA' }}>
          <ShieldCheck size={18} />
        </div>
      </div>

      <div className="kpi-card">
        <div>
          <div className="kpi-info-label">High / Critical</div>
          <div className="kpi-value" style={{ color: '#F87171' }}>{critical}</div>
        </div>
        <div className="kpi-icon-box" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#F87171' }}>
          <Flame size={18} />
        </div>
      </div>

      <div className="kpi-card">
        <div>
          <div className="kpi-info-label">Triage Pending</div>
          <div className="kpi-value" style={{ color: '#FBBF24' }}>{pending}</div>
        </div>
        <div className="kpi-icon-box" style={{ background: 'rgba(234, 179, 8, 0.15)', color: '#FBBF24' }}>
          <Clock size={18} />
        </div>
      </div>

      <div className="kpi-card">
        <div>
          <div className="kpi-info-label">Action In-Flight</div>
          <div className="kpi-value" style={{ color: '#FB923C' }}>{inProgress}</div>
        </div>
        <div className="kpi-icon-box" style={{ background: 'rgba(249, 115, 22, 0.15)', color: '#FB923C' }}>
          <Clock size={18} />
        </div>
      </div>

      <div className="kpi-card">
        <div>
          <div className="kpi-info-label">Resolved</div>
          <div className="kpi-value" style={{ color: '#34D399' }}>{resolved}</div>
        </div>
        <div className="kpi-icon-box" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34D399' }}>
          <CheckCircle2 size={18} />
        </div>
      </div>
    </section>
  )
}
