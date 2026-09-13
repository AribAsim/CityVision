import React, { useState } from 'react'
import type { AnalyticsSummary, IncidentSummary, BusSummary } from '../../types'
import { MONITORED_ROUTES, SEED_ANALYTICS, SEED_RECENT_INCIDENTS } from '../../services/seedData'
import type { NavTab } from '../Navigation/Sidebar'

interface HomeViewProps {
  analytics: AnalyticsSummary | null
  incidents: IncidentSummary[]
  buses: BusSummary[]
  onNavigateTab: (tab: NavTab) => void
  onSelectIncident: (incident: IncidentSummary) => void
}

export const HomeView: React.FC<HomeViewProps> = ({
  analytics,
  incidents,
  buses,
  onNavigateTab,
  onSelectIncident,
}) => {
  const [selectedCam, setSelectedCam] = useState<string>('CAM-04')

  // Use real backend data with smart fallback
  const totalCount = analytics?.total_incidents || incidents.length || SEED_ANALYTICS.total_incidents
  const highPriorityCount = (analytics?.by_severity?.['Critical'] || 0) + (analytics?.by_severity?.['High'] || 0) || 18
  const resolvedCount = analytics?.resolved_count || SEED_ANALYTICS.resolved_count
  const activeBusesCount = buses.length || analytics?.active_buses || SEED_ANALYTICS.active_buses
  const displayIncidents = incidents.length > 0 ? incidents.slice(0, 4) : SEED_RECENT_INCIDENTS

  // City Health Score calculation (Pavement Condition Index 0-100)
  const healthScore = Math.max(30, Math.min(95, Math.round(100 - (highPriorityCount * 1.5 + (totalCount - resolvedCount) * 0.4))))

  const getSeverityBadgeClass = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return 'badge-critical'
      case 'high':
        return 'badge-high'
      case 'medium':
        return 'badge-medium'
      default:
        return 'badge-low'
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. Dynamic Operational Hero Banner */}
      <section
        className="cv-card"
        style={{
          position: 'relative',
          overflow: 'hidden',
          padding: '24px 32px',
          background: 'linear-gradient(135deg, #ffffff 0%, #f0f6ff 100%)',
          border: '1px solid #dce9ff',
        }}
      >
        <div
          style={{
            position: 'absolute',
            right: '-60px',
            top: '-80px',
            width: '360px',
            height: '360px',
            background: 'radial-gradient(circle, rgba(0, 81, 213, 0.08) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '20px', position: 'relative', zIndex: 1 }}>
          <div style={{ maxWidth: '750px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '3px 10px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: '#eff4ff',
                  border: '1px solid #bfdbfe',
                  color: 'var(--color-primary)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  fontWeight: 600,
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                }}
              >
                <span className="radar-ping" style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-secondary)' }} />
                SYSTEM ONLINE
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--color-on-surface-variant)' }}>
                TELEMETRY SYNC: 100% RELIABLE
              </span>
            </div>

            <h1 className="font-headline-xl" style={{ color: 'var(--color-primary)', margin: '0 0 6px 0' }}>
              CITY VISION — AI-Powered Road Monitoring
            </h1>
            <p className="font-body-lg" style={{ color: 'var(--color-on-surface-variant)', fontStyle: 'italic', margin: 0 }}>
              Every Bus a Sensor. Every Road a Safer Path.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              id="btn-hero-start-patrol"
              className="btn-primary"
              onClick={() => onNavigateTab('live-detection')}
              style={{ padding: '10px 20px', fontSize: '14px' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>
                play_circle
              </span>
              <span>Start Live Patrol</span>
            </button>
            <button
              id="btn-hero-export-gis"
              className="btn-secondary"
              onClick={() => onNavigateTab('reports')}
              style={{ padding: '10px 18px', fontSize: '14px' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '18px', color: 'var(--color-primary)' }}>
                file_download
              </span>
              <span>Export GIS Dossier</span>
            </button>
          </div>
        </div>
      </section>

      {/* 2. Key Operational Metric Indicators (5 Cards) */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '16px' }}>
        {/* Metric 1: Active Buses */}
        <div className="cv-card" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)', letterSpacing: '0.06em' }}>
              ACTIVE BUSES
            </span>
            <div style={{ width: '32px', height: '32px', borderRadius: 'var(--radius-md)', backgroundColor: '#eff4ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-secondary)' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>directions_bus</span>
            </div>
          </div>
          <div>
            <div className="font-headline-xl" style={{ color: 'var(--color-primary)', lineHeight: 1 }}>{activeBusesCount}</div>
            <div className="font-body-sm" style={{ color: 'var(--color-secondary)', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px', fontWeight: 500 }}>
              <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>trending_up</span>
              <span>Continuous Fleet Ingest</span>
            </div>
          </div>
          <div style={{ width: '100%', height: '6px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: '88%', backgroundColor: 'var(--color-secondary)', borderRadius: '9999px' }} />
          </div>
        </div>

        {/* Metric 2: Roads Monitored */}
        <div className="cv-card" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)', letterSpacing: '0.06em' }}>
              ROADS MONITORED
            </span>
            <div style={{ width: '32px', height: '32px', borderRadius: 'var(--radius-md)', backgroundColor: '#eff4ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary)' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>alt_route</span>
            </div>
          </div>
          <div>
            <div className="font-headline-xl" style={{ color: 'var(--color-primary)', lineHeight: 1 }}>128 km</div>
            <div className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)', marginTop: '4px' }}>
              Coverage 94.2% municipal corridors
            </div>
          </div>
          <div style={{ width: '100%', height: '6px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: '94.2%', backgroundColor: 'var(--color-primary)', borderRadius: '9999px' }} />
          </div>
        </div>

        {/* Metric 3: Issues Detected */}
        <div className="cv-card" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)', letterSpacing: '0.06em' }}>
              ISSUES DETECTED
            </span>
            <div style={{ width: '32px', height: '32px', borderRadius: 'var(--radius-md)', backgroundColor: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-tertiary)' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>travel_explore</span>
            </div>
          </div>
          <div>
            <div className="font-headline-xl" style={{ color: 'var(--color-on-surface)', lineHeight: 1 }}>{totalCount}</div>
            <div className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)', marginTop: '4px' }}>
              Deduplicated road defects recorded
            </div>
          </div>
          <div style={{ width: '100%', height: '6px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: '68%', backgroundColor: 'var(--color-tertiary-container)', borderRadius: '9999px' }} />
          </div>
        </div>

        {/* Metric 4: High Priority */}
        <div
          className="cv-card"
          style={{
            padding: '18px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            backgroundColor: '#fff5f5',
            border: '1px solid #fecaca',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="font-label-sm" style={{ color: '#ba1a1a', letterSpacing: '0.06em' }}>
              HIGH PRIORITY
            </span>
            <div style={{ width: '32px', height: '32px', borderRadius: 'var(--radius-md)', backgroundColor: '#ffdad6', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ba1a1a' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>warning</span>
            </div>
          </div>
          <div>
            <div className="font-headline-xl" style={{ color: '#ba1a1a', lineHeight: 1 }}>{highPriorityCount}</div>
            <div className="font-body-sm" style={{ color: '#991b1b', marginTop: '4px', fontWeight: 500 }}>
              Requires immediate work order
            </div>
          </div>
          <div style={{ width: '100%', height: '6px', backgroundColor: '#fee2e2', borderRadius: '9999px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: '35%', backgroundColor: '#ef4444', borderRadius: '9999px' }} />
          </div>
        </div>

        {/* Metric 5: Resolved */}
        <div className="cv-card" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)', letterSpacing: '0.06em' }}>
              RESOLVED
            </span>
            <div style={{ width: '32px', height: '32px', borderRadius: 'var(--radius-md)', backgroundColor: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#047857' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>task_alt</span>
            </div>
          </div>
          <div>
            <div className="font-headline-xl" style={{ color: '#047857', lineHeight: 1 }}>{resolvedCount}</div>
            <div className="font-body-sm" style={{ color: '#047857', marginTop: '4px', fontWeight: 500 }}>
              59.3% resolution velocity
            </div>
          </div>
          <div style={{ width: '100%', height: '6px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: '59.3%', backgroundColor: '#10b981', borderRadius: '9999px' }} />
          </div>
        </div>
      </section>

      {/* 3. Distributed Ingestion Architecture Pipeline (6 steps) */}
      <section className="cv-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '18px' }}>
          <div>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)', letterSpacing: '0.06em' }}>
              DISTRIBUTED INGESTION ARCHITECTURE
            </span>
            <h2 className="font-headline-md" style={{ color: 'var(--color-primary)', margin: '4px 0 0 0' }}>
              End-to-End Computational Pipeline
            </h2>
          </div>
          <p className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)', fontStyle: 'italic', margin: 0 }}>
            Every routine bus journey converts public transit into a distributed road-sensing network.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '12px' }}>
          {[
            { step: '01 // EDGE', title: 'Public Bus Camera', desc: '1080p windshield video ingestion', icon: 'photo_camera', color: 'var(--color-primary)' },
            { step: '02 // GEO', title: 'GPS & Telemetry', desc: 'Sub-meter coordinates & velocity', icon: 'pin_drop', color: 'var(--color-secondary)' },
            { step: '03 // VISION', title: 'Edge / YOLO Vision', desc: 'Real-time object bounding & detection', icon: 'memory', color: 'var(--color-primary-container)' },
            { step: '04 // FUSION', title: 'Deduplication', desc: 'Multi-bus spatio-temporal cluster', icon: 'hub', color: 'var(--color-secondary)' },
            { step: '05 // TRIAGE', title: 'Severity Engine', desc: 'PCI structural degradation scoring', icon: 'speed', color: 'var(--color-tertiary)' },
            { step: '06 // ACTION', title: 'Municipal Command', desc: 'Automated repair crew work orders', icon: 'domain', color: '#ffffff', bg: 'var(--color-primary)', isAction: true },
          ].map((item) => (
            <div
              key={item.step}
              style={{
                backgroundColor: item.bg || 'var(--color-surface-container-low)',
                color: item.isAction ? '#ffffff' : 'var(--color-on-surface)',
                padding: '16px',
                borderRadius: 'var(--radius-lg)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                border: item.isAction ? 'none' : '1px solid #dce9ff',
                boxShadow: item.isAction ? '0 2px 6px rgba(0, 35, 111, 0.2)' : 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span className="font-label-sm" style={{ color: item.isAction ? '#b6c4ff' : 'var(--color-on-surface-variant)' }}>
                  {item.step}
                </span>
                <span className="material-symbols-outlined" style={{ fontSize: '20px', color: item.color }}>
                  {item.icon}
                </span>
              </div>
              <div>
                <h3 className="font-headline-sm" style={{ color: item.isAction ? '#ffffff' : 'var(--color-on-surface)', margin: 0 }}>
                  {item.title}
                </h3>
                <p className="font-body-sm" style={{ color: item.isAction ? 'rgba(255, 255, 255, 0.8)' : 'var(--color-on-surface-variant)', margin: '4px 0 0 0', lineHeight: 1.3 }}>
                  {item.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 4. Two-Column Operational Split: Live Monitoring & Recent Events */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '24px' }}>
        {/* Left Column (7 cols): Live Monitoring Card */}
        <div className="cv-card" style={{ gridColumn: 'span 7', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '14px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#f8faff', borderBottom: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span className="font-headline-sm" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
                LIVE MONITORING
              </span>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: '#eff4ff',
                  color: 'var(--color-primary)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  fontWeight: 600,
                }}
              >
                <span className="radar-ping" style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-secondary)' }} />
                FEED #04
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <select
                id="cam-feed-select"
                value={selectedCam}
                onChange={(e) => setSelectedCam(e.target.value)}
                style={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: 'var(--radius-md)',
                  padding: '4px 8px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '12px',
                  color: 'var(--color-on-surface)',
                  outline: 'none',
                  cursor: 'pointer',
                }}
              >
                <option value="CAM-04">Bus CAM-04 (Route 12)</option>
                <option value="CAM-02">Bus CAM-02 (Route 8)</option>
                <option value="CAM-08">Bus CAM-08 (Sector 62)</option>
                <option value="CAM-01">Bus CAM-01 (Route 5)</option>
              </select>
            </div>
          </div>

          {/* Video Viewport with HUD */}
          <div
            style={{
              position: 'relative',
              width: '100%',
              aspectRatio: '16 / 9',
              backgroundColor: '#131b2e',
              overflow: 'hidden',
            }}
          >
            {/* Modern Asphalt Dashboard Video Stream */}
            <video
              src="/patrol_route12.mp4"
              autoPlay
              loop
              muted
              playsInline
              style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.9, display: 'block' }}
            />

            {/* Top Left HUD: Bus info & GPS */}
            <div
              style={{
                position: 'absolute',
                top: '16px',
                left: '16px',
                backgroundColor: 'rgba(15, 23, 42, 0.88)',
                backdropFilter: 'blur(8px)',
                borderRadius: 'var(--radius-md)',
                padding: '8px 12px',
                color: '#ffffff',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                display: 'flex',
                flexDirection: 'column',
                gap: '2px',
                boxShadow: 'var(--shadow-level2)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: '#10b981' }} />
                <span style={{ fontWeight: 700 }}>Bus {selectedCam} | Route 12 | Status: LIVE</span>
              </div>
              <div style={{ color: '#94a3b8', fontSize: '10px' }}>
                <span>GPS: 28.6139° N, 77.2090° E</span> | <span>Speed: 32 km/h</span>
              </div>
              <div style={{ color: '#60a5fa', fontSize: '9.5px' }}>
                INFERENCE: YOLOv8m-RoadAnomaly @ 30 FPS
              </div>
            </div>

            {/* Top Right HUD: Latency */}
            <div
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                backgroundColor: 'rgba(15, 23, 42, 0.88)',
                backdropFilter: 'blur(8px)',
                borderRadius: 'var(--radius-md)',
                padding: '5px 10px',
                fontFamily: 'var(--font-mono)',
                fontSize: '10px',
                display: 'flex',
                gap: '8px',
              }}
            >
              <span style={{ color: '#60a5fa', fontWeight: 700 }}>LATENCY: 42ms</span>
              <span style={{ color: '#94a3b8' }}>HD 1080P</span>
            </div>

            {/* Bounding Box 1: Pothole */}
            <div
              style={{
                position: 'absolute',
                top: '52%',
                left: '35%',
                width: '180px',
                height: '110px',
                border: '2px solid #ba1a1a',
                backgroundColor: 'rgba(186, 26, 26, 0.18)',
                boxShadow: '0 0 15px rgba(186, 26, 26, 0.4)',
                borderRadius: 'var(--radius-xs)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                padding: '4px',
                transform: 'rotate(-2deg)',
                pointerEvents: 'none',
              }}
            >
              <div
                style={{
                  backgroundColor: '#ba1a1a',
                  color: '#ffffff',
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-xs)',
                  fontSize: '10px',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 700,
                  alignSelf: 'flex-start',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '11px' }}>warning</span>
                <span>Pothole (92%)</span>
              </div>
              <div
                style={{
                  fontSize: '9px',
                  fontFamily: 'var(--font-mono)',
                  color: '#ffffff',
                  backgroundColor: 'rgba(15, 23, 42, 0.85)',
                  padding: '2px 5px',
                  borderRadius: 'var(--radius-xs)',
                  alignSelf: 'flex-end',
                }}
              >
                Vol: 0.04m³ | Depth: 6.2cm
              </div>
            </div>

            {/* Bounding Box 2: Surface Crack */}
            <div
              style={{
                position: 'absolute',
                bottom: '22%',
                right: '25%',
                width: '130px',
                height: '70px',
                border: '1.5px solid #2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.15)',
                borderRadius: 'var(--radius-xs)',
                display: 'flex',
                padding: '4px',
                pointerEvents: 'none',
              }}
            >
              <div
                style={{
                  backgroundColor: '#2563eb',
                  color: '#ffffff',
                  padding: '1px 5px',
                  borderRadius: 'var(--radius-xs)',
                  fontSize: '9px',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 600,
                  alignSelf: 'flex-start',
                }}
              >
                Surface Crack (78%)
              </div>
            </div>
          </div>

          {/* Telemetry Control Strip */}
          <div style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#f8faff', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div>
                <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>STREAM HEALTH</span>
                <div className="font-headline-sm" style={{ color: '#047857', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981' }} />
                  99.8% Nominal
                </div>
              </div>
              <div style={{ height: '24px', width: '1px', backgroundColor: '#e2e8f0' }} />
              <div>
                <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>SECTOR</span>
                <div className="font-headline-sm" style={{ color: 'var(--color-on-surface)' }}>
                  Central Arterial Corridors
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                className="btn-primary"
                onClick={() => onNavigateTab('live-detection')}
                style={{ fontSize: '12px', padding: '6px 14px' }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>sensors</span>
                <span>OPEN FULL PATROL</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Column (5 cols): Recent Road Issues */}
        <div className="cv-card" style={{ gridColumn: 'span 5', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ padding: '16px 20px', backgroundColor: '#f8faff', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <span className="font-headline-sm" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
                RECENT ROAD ISSUES
              </span>
              <p className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)', margin: 0 }}>
                Real-time alerts queued for municipal remediation
              </p>
            </div>
            <span className="font-label-sm" style={{ color: 'var(--color-secondary)', fontWeight: 700 }}>
              LIVE FEED
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {displayIncidents.map((item, idx) => (
              <div
                key={item.incident_id || idx}
                onClick={() => onSelectIncident(item)}
                style={{
                  padding: '14px 20px',
                  borderBottom: idx < displayIncidents.length - 1 ? '1px solid #f1f5f9' : 'none',
                  cursor: 'pointer',
                  transition: 'background-color 0.15s ease',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#f8faff' }}
                onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="font-label-md" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
                      {item.incident_id}
                    </span>
                    <span className={getSeverityBadgeClass(item.severity)}>
                      {item.severity}
                    </span>
                  </div>
                  <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>
                    {new Date(item.last_detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <div className="font-headline-sm" style={{ color: 'var(--color-on-surface)', fontWeight: 600 }}>
                      {item.anomaly_type}
                    </div>
                    <p className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)', margin: 0 }}>
                      GPS: {item.latitude.toFixed(4)}° N, {item.longitude.toFixed(4)}° E
                    </p>
                  </div>
                  <span
                    style={{
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: item.status === 'RESOLVED' ? '#ecfdf5' : '#eff4ff',
                      color: item.status === 'RESOLVED' ? '#047857' : 'var(--color-secondary)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '11px',
                      fontWeight: 600,
                    }}
                  >
                    {item.status}
                  </span>
                </div>

                {item.unique_bus_count >= 2 && (
                  <div
                    className="badge-multibus"
                    style={{ marginTop: '8px' }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>verified</span>
                    <span>Multi-Bus Verified: {item.unique_bus_count} Buses</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div style={{ padding: '14px 20px', backgroundColor: '#f8faff', borderTop: '1px solid #e2e8f0', display: 'flex', gap: '10px' }}>
            <button
              className="btn-secondary"
              onClick={() => onNavigateTab('reports')}
              style={{ width: '100%', justifyContent: 'center', fontSize: '12px' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>visibility</span>
              <span>View All Reports ({totalCount})</span>
            </button>
          </div>
        </div>
      </section>

      {/* 5. Bottom Section: Municipal Road Condition & Corridor Health */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '24px' }}>
        {/* City Health Score Card (4 cols) */}
        <div className="cv-card" style={{ gridColumn: 'span 4', padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)', letterSpacing: '0.06em' }}>
                MUNICIPAL ROAD CONDITION
              </span>
              <span className="font-label-sm" style={{ color: 'var(--color-secondary)', fontWeight: 700 }}>
                METRIC: PCI
              </span>
            </div>
            <h3 className="font-headline-md" style={{ color: 'var(--color-primary)', margin: 0 }}>
              City Health Score
            </h3>
            <p className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)', margin: '4px 0 0 0' }}>
              Aggregated Pavement Condition Index calculated from continuous fleet passes.
            </p>
          </div>

          {/* Radial Health Gauge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px', padding: '16px', backgroundColor: '#eff4ff', borderRadius: 'var(--radius-xl)' }}>
            <div style={{ position: 'relative', width: '84px', height: '84px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <svg style={{ width: '84px', height: '84px', transform: 'rotate(-90deg)' }} viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.9155" fill="none" stroke="#dce9ff" strokeWidth="3.5" />
                <circle
                  cx="18"
                  cy="18"
                  r="15.9155"
                  fill="none"
                  stroke="var(--color-secondary)"
                  strokeWidth="3.5"
                  strokeDasharray={`${healthScore}, 100`}
                  strokeLinecap="round"
                />
              </svg>
              <div style={{ position: 'absolute', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <span className="font-headline-lg" style={{ color: 'var(--color-primary)', lineHeight: 1 }}>{healthScore}</span>
                <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)', fontSize: '9px' }}>/ 100</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span className="font-headline-sm" style={{ color: 'var(--color-secondary)', fontWeight: 700 }}>
                {healthScore >= 75 ? 'NOMINAL HEALTH' : healthScore >= 55 ? 'MODERATE HEALTH' : 'CRITICAL ATTENTION'}
              </span>
              <p className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)', margin: 0, fontSize: '11px', lineHeight: 1.35 }}>
                Continuous inspection validates maintenance crew readiness within scheduled window.
              </p>
            </div>
          </div>

          {/* Segmented Ratio Bar */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
              <span style={{ color: 'var(--color-on-surface-variant)' }}>Distribution Ratio</span>
              <span style={{ color: 'var(--color-on-surface)', fontWeight: 600 }}>65% Good | 25% Mod | 10% Poor</span>
            </div>
            <div style={{ height: '8px', width: '100%', display: 'flex', borderRadius: '9999px', overflow: 'hidden', backgroundColor: '#e2e8f0' }}>
              <div style={{ width: '65%', backgroundColor: '#10b981' }} title="Good: 65%" />
              <div style={{ width: '25%', backgroundColor: '#f59e0b' }} title="Moderate: 25%" />
              <div style={{ width: '10%', backgroundColor: '#ef4444' }} title="Poor: 10%" />
            </div>
          </div>
        </div>

        {/* Active Fleet Route Health Breakdown (8 cols) */}
        <div className="cv-card" style={{ gridColumn: 'span 8', padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)', letterSpacing: '0.06em' }}>
                CORRIDOR PERFORMANCE
              </span>
              <h3 className="font-headline-md" style={{ color: 'var(--color-primary)', margin: '4px 0 0 0' }}>
                Active Fleet Route Health Breakdown
              </h3>
            </div>
            <button
              className="btn-secondary"
              onClick={() => onNavigateTab('road-map')}
              style={{ fontSize: '12px', padding: '6px 12px' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>map</span>
              <span>Open on GIS Map</span>
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
            {MONITORED_ROUTES.map((rt) => (
              <div
                key={rt.route_id}
                style={{
                  padding: '16px',
                  backgroundColor: '#f8faff',
                  border: '1px solid #e2e8f0',
                  borderRadius: 'var(--radius-lg)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span className="font-headline-sm" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
                    {rt.name.split(' ')[0]} {rt.name.split(' ')[1]}
                  </span>
                  <span
                    style={{
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: '#eff4ff',
                      color: rt.color,
                      fontFamily: 'var(--font-mono)',
                      fontSize: '11px',
                      fontWeight: 700,
                    }}
                  >
                    PCI: {rt.score}
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-on-surface-variant)' }}>Condition:</span>
                    <span style={{ fontWeight: 600, color: rt.score >= 70 ? '#047857' : '#b45309' }}>{rt.condition}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-on-surface-variant)' }}>Active Buses:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{rt.active_buses} Buses</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-on-surface-variant)' }}>Degraded Zones:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: '#ba1a1a', fontWeight: 600 }}>{rt.degraded_zones} Areas</span>
                  </div>
                </div>

                <div style={{ width: '100%', height: '6px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${rt.score}%`, backgroundColor: rt.color, borderRadius: '9999px' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
