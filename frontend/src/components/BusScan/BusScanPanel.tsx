import React, { useState, useEffect, useRef } from 'react'
import { Video, Play, Loader2, CheckCircle2, AlertTriangle, UploadCloud } from 'lucide-react'
import { startBusScan, fetchScanStatus } from '../../services/api'
import type { ScanJobStatus } from '../../types'

interface BusScanPanelProps {
  onScanComplete?: () => void
}

const BUS_ROUTES: Record<string, string> = {
  'BUS-01': 'ROUTE-RED',
  'BUS-02': 'ROUTE-BLUE',
  'BUS-03': 'ROUTE-GREEN',
}

export const BusScanPanel: React.FC<BusScanPanelProps> = ({ onScanComplete }) => {
  const [selectedBus, setSelectedBus] = useState<string>('BUS-01')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [status, setStatus] = useState<ScanJobStatus>('READY')
  const [jobId, setJobId] = useState<string | null>(null)
  const [eventsDetected, setEventsDetected] = useState<number>(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const pollIntervalRef = useRef<number | null>(null)

  const currentRoute = BUS_ROUTES[selectedBus] || 'ROUTE-RED'

  // Clean up polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [])

  // Poll status when job is in PROCESSING
  useEffect(() => {
    if (status !== 'PROCESSING' || !jobId) {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
      return
    }

    pollIntervalRef.current = window.setInterval(async () => {
      try {
        const data = await fetchScanStatus(jobId)
        setEventsDetected(data.events_dispatched)

        if (data.status === 'COMPLETED') {
          setStatus('COMPLETED')
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
          onScanComplete?.()
        } else if (data.status === 'FAILED') {
          setStatus('FAILED')
          setErrorMessage(data.error || 'Scan process failed')
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
        }
      } catch (err: any) {
        // Keep retrying if temporary network blip, but if persistent error show it
        console.error('Error polling scan status:', err)
      }
    }, 2000)

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [status, jobId, onScanComplete])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      if (!file.name.toLowerCase().endsWith('.mp4')) {
        setErrorMessage('Please select a valid .mp4 video file')
        setSelectedFile(null)
        return
      }
      setSelectedFile(file)
      setErrorMessage(null)
      if (status === 'COMPLETED' || status === 'FAILED') {
        setStatus('READY')
        setEventsDetected(0)
      }
    }
  }

  const handleStartScan = async () => {
    if (!selectedFile) {
      setErrorMessage('Please select a .mp4 video file first')
      return
    }

    try {
      setStatus('UPLOADING')
      setErrorMessage(null)
      setEventsDetected(0)

      const res = await startBusScan(selectedBus, currentRoute, selectedFile)
      setJobId(res.job_id)
      setStatus('PROCESSING')
    } catch (err: any) {
      setStatus('FAILED')
      setErrorMessage(err.message || 'Failed to start bus scan')
    }
  }

  return (
    <div
      style={{
        background: 'linear-gradient(145deg, rgba(26, 35, 50, 0.9), rgba(19, 26, 38, 0.95))',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-sm)',
        padding: '12px 14px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
          <div
            style={{
              background: 'rgba(59, 130, 246, 0.15)',
              padding: '4px 6px',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <Video size={14} color="#60A5FA" />
          </div>
          <span style={{ fontSize: '12px', fontWeight: 700, letterSpacing: '0.04em', color: '#F1F5F9' }}>
            RUN BUS SCAN
          </span>
        </div>
        <span
          style={{
            fontSize: '10px',
            color: '#94A3B8',
            background: 'rgba(255, 255, 255, 0.05)',
            padding: '2px 6px',
            borderRadius: '4px',
          }}
        >
          EDGE AI PIPELINE
        </span>
      </div>

      {/* Selectors Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
        {/* Bus Selector */}
        <div>
          <label style={{ fontSize: '11px', color: '#94A3B8', display: 'block', marginBottom: '3px' }}>
            Bus Unit
          </label>
          <select
            id="scan-bus-select"
            value={selectedBus}
            disabled={status === 'PROCESSING' || status === 'UPLOADING'}
            onChange={(e) => setSelectedBus(e.target.value)}
            style={{
              width: '100%',
              background: 'var(--color-surface-elevated)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-xs)',
              color: '#F8FAFC',
              fontSize: '12px',
              padding: '5px 8px',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="BUS-01">BUS-01</option>
            <option value="BUS-02">BUS-02</option>
            <option value="BUS-03">BUS-03</option>
          </select>
        </div>

        {/* Route Info */}
        <div>
          <label style={{ fontSize: '11px', color: '#94A3B8', display: 'block', marginBottom: '3px' }}>
            Assigned Route
          </label>
          <div
            style={{
              width: '100%',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: 'var(--radius-xs)',
              color: '#38BDF8',
              fontSize: '12px',
              fontWeight: 600,
              padding: '5px 8px',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {currentRoute}
          </div>
        </div>
      </div>

      {/* Video Selection */}
      <div>
        <input
          id="scan-video-input"
          type="file"
          ref={fileInputRef}
          accept="video/mp4"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <div
          onClick={() => {
            if (status !== 'PROCESSING' && status !== 'UPLOADING') {
              fileInputRef.current?.click()
            }
          }}
          style={{
            border: '1px dashed var(--color-border-focus)',
            borderRadius: 'var(--radius-xs)',
            padding: '8px 10px',
            background: selectedFile ? 'rgba(59, 130, 246, 0.06)' : 'rgba(255, 255, 255, 0.02)',
            cursor: status === 'PROCESSING' || status === 'UPLOADING' ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '8px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflow: 'hidden' }}>
            <UploadCloud size={14} color="#94A3B8" style={{ flexShrink: 0 }} />
            <span
              style={{
                fontSize: '11px',
                color: selectedFile ? '#F8FAFC' : '#94A3B8',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {selectedFile ? selectedFile.name : 'Select recorded bus feed (.mp4)'}
            </span>
          </div>
          <span
            style={{
              fontSize: '10px',
              color: '#38BDF8',
              background: 'rgba(56, 189, 248, 0.1)',
              padding: '2px 6px',
              borderRadius: '3px',
              flexShrink: 0,
            }}
          >
            {selectedFile ? 'Change' : 'Browse'}
          </span>
        </div>
      </div>

      {/* Action Button */}
      <button
        id="btn-start-detection"
        onClick={handleStartScan}
        disabled={!selectedFile || status === 'UPLOADING' || status === 'PROCESSING'}
        style={{
          width: '100%',
          background:
            !selectedFile || status === 'UPLOADING' || status === 'PROCESSING'
              ? 'rgba(71, 85, 105, 0.4)'
              : 'linear-gradient(135deg, #2563EB, #1D4ED8)',
          color: '#FFFFFF',
          border: 'none',
          borderRadius: 'var(--radius-xs)',
          padding: '7px 12px',
          fontSize: '12px',
          fontWeight: 700,
          cursor: !selectedFile || status === 'UPLOADING' || status === 'PROCESSING' ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '6px',
          transition: 'background 0.2s ease',
        }}
      >
        {status === 'UPLOADING' ? (
          <>
            <Loader2 size={13} className="animate-spin" />
            <span>Uploading Video...</span>
          </>
        ) : status === 'PROCESSING' ? (
          <>
            <Loader2 size={13} className="animate-spin" />
            <span>Detecting Road Anomalies...</span>
          </>
        ) : (
          <>
            <Play size={13} fill="#FFFFFF" />
            <span>START DETECTION</span>
          </>
        )}
      </button>

      {/* Live Status & Progress Feedback */}
      {status === 'PROCESSING' && (
        <div
          style={{
            background: 'rgba(59, 130, 246, 0.12)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: 'var(--radius-xs)',
            padding: '7px 10px',
            fontSize: '11px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            color: '#93C5FD',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: '#3B82F6',
                display: 'inline-block',
                boxShadow: '0 0 6px #3B82F6',
              }}
            />
            <span>{selectedBus} scanning road footage...</span>
          </div>
          <span style={{ fontWeight: 600, color: '#F8FAFC' }}>
            Events: {eventsDetected}
          </span>
        </div>
      )}

      {status === 'COMPLETED' && (
        <div
          style={{
            background: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: 'var(--radius-xs)',
            padding: '7px 10px',
            fontSize: '11px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            color: '#6EE7B7',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <CheckCircle2 size={13} color="#10B981" />
            <span>Scan Complete ({selectedBus})</span>
          </div>
          <span style={{ fontWeight: 700, color: '#F8FAFC' }}>
            {eventsDetected} {eventsDetected === 1 ? 'Event' : 'Events'} logged
          </span>
        </div>
      )}

      {status === 'FAILED' && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-xs)',
            padding: '7px 10px',
            fontSize: '11px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            color: '#F87171',
          }}
        >
          <AlertTriangle size={13} color="#EF4444" style={{ flexShrink: 0 }} />
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {errorMessage || 'Scan failed'}
          </span>
        </div>
      )}
    </div>
  )
}
