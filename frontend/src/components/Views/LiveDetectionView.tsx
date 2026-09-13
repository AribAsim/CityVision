import React, { useState, useEffect, useRef } from 'react'
import type { IncidentSummary } from '../../types'
import type { ScanManager } from '../../hooks/useScanManager'

interface LiveDetectionViewProps {
  scanManager: ScanManager
  onSelectIncident: (inc: IncidentSummary) => void
}

interface TelemetryRow {
  timestamp: string
  frame: string
  entity: string
  severity: string
  gps: string
  confidence: number
  status: string
}

export const LiveDetectionView: React.FC<LiveDetectionViewProps> = ({ scanManager }) => {
  const [selectedCam, setSelectedCam] = useState<string>('CAM-04')
  const [isPaused, setIsPaused] = useState<boolean>(false)
  const [frameCount, setFrameCount] = useState<number>(1240)
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)

  const {
    scanStatus,
    selectedBus,
    setSelectedBus,
    selectedRoute,
    setSelectedRoute,
    startScan,
    resetScan,
  } = scanManager

  // Sync play/pause with HTML5 video element
  useEffect(() => {
    if (videoRef.current) {
      if (isPaused) {
        videoRef.current.pause()
      } else {
        videoRef.current.play().catch(() => {})
      }
    }
  }, [isPaused])

  // If user picks a local file, preview it in the live video viewport
  useEffect(() => {
    if (videoFile) {
      const url = URL.createObjectURL(videoFile)
      setVideoPreviewUrl(url)
      return () => URL.revokeObjectURL(url)
    } else {
      setVideoPreviewUrl(null)
    }
  }, [videoFile])

  // Camera feed source mapping
  const currentVideoSrc = videoPreviewUrl || (selectedCam === 'CAM-01' ? '/demo_bus_video.mp4' : '/patrol_route12.mp4')

  // Live frame ticker animation
  useEffect(() => {
    if (isPaused) return
    const interval = setInterval(() => {
      setFrameCount((prev) => prev + 1)
    }, 120)
    return () => clearInterval(interval)
  }, [isPaused])

  const handleStartScan = async () => {
    if (!videoFile) {
      alert('Please choose a .mp4 video file to run detection on.')
      return
    }

    try {
      await startScan(selectedBus, selectedRoute, videoFile)
    } catch (err: unknown) {
      console.error('Scan initiation error:', err)
    }
  }

  const telemetryLog: TelemetryRow[] = [
    { timestamp: '14:28:49.812', frame: '#001240', entity: 'POTHOLE', severity: 'Critical', gps: '28.6139°N, 77.2090°E', confidence: 0.92, status: 'ACTIVE_LOCK' },
    { timestamp: '14:28:48.420', frame: '#001218', entity: 'CRACK', severity: 'High', gps: '28.6142°N, 77.2094°E', confidence: 0.84, status: 'TRACKING' },
    { timestamp: '14:28:46.105', frame: '#001185', entity: 'SPEED_BUMP', severity: 'Low', gps: '28.6150°N, 77.2105°E', confidence: 0.88, status: 'VERIFIED' },
    { timestamp: '14:28:44.750', frame: '#001150', entity: 'POTHOLE', severity: 'High', gps: '28.6158°N, 77.2115°E', confidence: 0.79, status: 'RESOLVED' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. Operational Sub-Header */}
      <div
        className="cv-card"
        style={{
          padding: '16px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <h1 className="font-headline-lg" style={{ color: 'var(--color-primary)', margin: 0 }}>
              LIVE DETECTION & INFERENCE PIPELINE
            </h1>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '3px 10px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: '#fef2f2',
                border: '1px solid #fecaca',
                color: '#ba1a1a',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                fontWeight: 600,
              }}
            >
              <span className="radar-ping" style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#ef4444' }} />
              <span>BUS {selectedCam} | Route 12 | LIVE FEED</span>
            </span>
          </div>
          <p className="font-body-md" style={{ color: 'var(--color-on-surface-variant)', margin: 0 }}>
            Real-time edge neural inference stream from onboard public transit camera array
          </p>
        </div>

        {/* Edge Engine Telemetry Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <div style={{ padding: '6px 12px', backgroundColor: '#eff4ff', borderRadius: 'var(--radius-md)', border: '1px solid #dce9ff' }}>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)', display: 'block' }}>STREAM RATE</span>
            <span className="font-label-md" style={{ color: 'var(--color-secondary)', fontWeight: 700 }}>28.4 FPS</span>
          </div>
          <div style={{ padding: '6px 12px', backgroundColor: '#eff4ff', borderRadius: 'var(--radius-md)', border: '1px solid #dce9ff' }}>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)', display: 'block' }}>ACTIVE MODEL</span>
            <span className="font-label-md" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>YOLOv8m-RoadAnomaly</span>
          </div>
          <div style={{ padding: '6px 12px', backgroundColor: '#eff4ff', borderRadius: 'var(--radius-md)', border: '1px solid #dce9ff' }}>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)', display: 'block' }}>INFERENCE LATENCY</span>
            <span className="font-label-md" style={{ color: '#047857', fontWeight: 700 }}>18.2 ms</span>
          </div>
          <div style={{ padding: '6px 12px', backgroundColor: '#f1f5f9', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0' }}>
            <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)', display: 'block' }}>SENSOR ACCEL</span>
            <span className="font-label-md" style={{ color: 'var(--color-tertiary)', fontWeight: 700 }}>EDGE_ACCEL_NPU</span>
          </div>
          <div style={{ padding: '6px 12px', backgroundColor: '#fef3c7', borderRadius: 'var(--radius-md)', border: '1px solid #fde68a' }}>
            <span className="font-label-sm" style={{ color: '#92400e', display: 'block' }}>ANPR SUBSYSTEM</span>
            <span className="font-label-md" style={{ color: '#b45309', fontWeight: 700 }}>Indian Plate YOLO + EasyOCR (Demo)</span>
          </div>
        </div>
      </div>

      {/* 2. Main Split: Viewport (7 cols) & Triage Panel (5 cols) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '24px' }}>
        {/* Left Side: Video Canvas & Run Scan Controller */}
        <div style={{ gridColumn: 'span 7', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Video Viewport Container with High-Tech HUD */}
          <div
            className="cv-card"
            style={{
              position: 'relative',
              width: '100%',
              aspectRatio: '16 / 10',
              backgroundColor: '#0b1c30',
              overflow: 'hidden',
              boxShadow: 'var(--shadow-level3)',
            }}
          >
            {/* Live Dashcam Feed Video Element */}
            <video
              ref={videoRef}
              key={currentVideoSrc}
              src={currentVideoSrc}
              autoPlay
              loop
              muted
              playsInline
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                display: 'block',
              }}
            />

            {/* High-Tech Grid Lines Scan Overlay */}
            <div
              style={{
                position: 'absolute',
                inset: 0,
                backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px)',
                backgroundSize: '32px 32px',
                pointerEvents: 'none',
              }}
            />

            {/* HUD Top Left: Status & Rec */}
            <div
              style={{
                position: 'absolute',
                top: '16px',
                left: '16px',
                backgroundColor: 'rgba(11, 28, 48, 0.9)',
                backdropFilter: 'blur(8px)',
                padding: '6px 12px',
                borderRadius: 'var(--radius-md)',
                color: '#ffffff',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span className="radar-ping" style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: '#ba1a1a' }} />
              <span style={{ fontWeight: 700 }}>REC ● 1080p @ 30fps</span>
            </div>

            {/* HUD Top Right: Serial & Lock */}
            <div
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                backgroundColor: 'rgba(11, 28, 48, 0.9)',
                backdropFilter: 'blur(8px)',
                padding: '6px 12px',
                borderRadius: 'var(--radius-md)',
                color: '#90a8ff',
                fontFamily: 'var(--font-mono)',
                fontSize: '10.5px',
              }}
            >
              INGEST_BUS_04 | SYNC_LOCK: OK
            </div>

            {/* BOUNDING BOX 1: Pothole */}
            <div
              style={{
                position: 'absolute',
                left: '38%',
                top: '54%',
                width: '28%',
                height: '24%',
                border: '2px solid #ba1a1a',
                backgroundColor: 'rgba(186, 26, 26, 0.2)',
                boxShadow: '0 0 15px rgba(186, 26, 26, 0.4)',
                borderRadius: '2px',
                pointerEvents: 'none',
              }}
            >
              {/* Corner brackets */}
              <div style={{ position: 'absolute', top: '-2px', left: '-2px', width: '8px', height: '8px', borderTop: '3px solid #ffffff', borderLeft: '3px solid #ffffff' }} />
              <div style={{ position: 'absolute', top: '-2px', right: '-2px', width: '8px', height: '8px', borderTop: '3px solid #ffffff', borderRight: '3px solid #ffffff' }} />
              <div style={{ position: 'absolute', bottom: '-2px', left: '-2px', width: '8px', height: '8px', borderBottom: '3px solid #ffffff', borderLeft: '3px solid #ffffff' }} />
              <div style={{ position: 'absolute', bottom: '-2px', right: '-2px', width: '8px', height: '8px', borderBottom: '3px solid #ffffff', borderRight: '3px solid #ffffff' }} />

              <div
                style={{
                  position: 'absolute',
                  top: '-24px',
                  left: 0,
                  backgroundColor: '#ba1a1a',
                  color: '#ffffff',
                  padding: '2px 6px',
                  fontSize: '9.5px',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 700,
                  borderRadius: '2px',
                  whiteSpace: 'nowrap',
                }}
              >
                Pothole | Conf: 0.92 | Size: 1.4m² | High
              </div>
            </div>

            {/* BOUNDING BOX 2: Surface Crack */}
            <div
              style={{
                position: 'absolute',
                left: '16%',
                top: '44%',
                width: '18%',
                height: '16%',
                border: '1.5px solid #316bf3',
                backgroundColor: 'rgba(49, 107, 243, 0.15)',
                borderRadius: '2px',
                pointerEvents: 'none',
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  top: '-20px',
                  left: 0,
                  backgroundColor: '#316bf3',
                  color: '#ffffff',
                  padding: '1px 5px',
                  fontSize: '9px',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 600,
                  borderRadius: '2px',
                  whiteSpace: 'nowrap',
                }}
              >
                Surface Crack | Conf: 0.78
              </div>
            </div>

            {/* HUD Bottom Overlays */}
            <div
              style={{
                position: 'absolute',
                bottom: '16px',
                left: '16px',
                right: '16px',
                display: 'flex',
                justifyContent: 'space-between',
                backgroundColor: 'rgba(11, 28, 48, 0.9)',
                backdropFilter: 'blur(8px)',
                padding: '8px 14px',
                borderRadius: 'var(--radius-md)',
                color: '#ffffff',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
              }}
            >
              <div>
                <span>GPS: 28.6139° N, 77.2090° E</span> | <span>Speed: 32 km/h</span> | <strong style={{ color: '#90a8ff' }}>Bus {selectedCam}</strong>
              </div>
              <div>
                <span>Frame: <strong style={{ color: '#60a5fa' }}>#{frameCount}</strong></span> | <span>Detections: <strong>2</strong></span> | <span>Track: #TRK-89</span>
              </div>
            </div>
          </div>

          {/* Stream & Camera Controls Strip */}
          <div
            className="cv-card"
            style={{
              padding: '12px 18px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '10px',
              backgroundColor: '#f8faff',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                id="btn-live-pause"
                className="btn-secondary"
                onClick={() => setIsPaused(!isPaused)}
                style={{ padding: '6px 14px', fontSize: '12px' }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>
                  {isPaused ? 'play_arrow' : 'pause'}
                </span>
                <span>{isPaused ? 'Resume Feed' : 'Pause Stream'}</span>
              </button>
              <button
                className="btn-secondary"
                onClick={() => alert('Snapshot captured and staged for evidence audit.')}
                style={{ padding: '6px 14px', fontSize: '12px' }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>photo_camera</span>
                <span>Capture Frame</span>
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>ACTIVE FEED:</span>
              <select
                id="live-camera-feed-select"
                value={selectedCam}
                onChange={(e) => setSelectedCam(e.target.value)}
                style={{
                  padding: '6px 10px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid #cbd5e1',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '12px',
                  backgroundColor: '#ffffff',
                  outline: 'none',
                }}
              >
                <option value="CAM-04">BUS CAM-04 (Route 12 Express)</option>
                <option value="CAM-01">BUS CAM-01 (Route 5 Downtown)</option>
                <option value="CAM-02">BUS CAM-02 (Route 8 Bypass)</option>
                <option value="CAM-08">BUS CAM-08 (Outer Ring Sector)</option>
              </select>
            </div>
          </div>

          {/* Integrated Run Bus Scan Panel (Real Video Detection Subprocess) */}
          <div
            className="cv-card"
            style={{
              padding: '20px',
              backgroundColor: '#ffffff',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="material-symbols-outlined" style={{ color: 'var(--color-primary)' }}>
                  videocam
                </span>
                <span className="font-headline-sm" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
                  RUN REAL BUS VIDEO PATROL
                </span>
              </div>
              <span className="badge-low">EDGE PIPELINE RUNNER</span>
            </div>

            <p className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)', margin: 0 }}>
              Upload recorded dashcam footage (.mp4) to run YOLO detection, Kalman ByteTrack tracking, and live incident dispatch.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 2fr auto', gap: '10px', alignItems: 'center' }}>
              {/* Bus Selector */}
              <div>
                <label className="font-label-sm" style={{ display: 'block', marginBottom: '4px', color: 'var(--color-on-surface-variant)' }}>
                  Bus Unit:
                </label>
                <select
                  id="scan-bus-select"
                  value={selectedBus}
                  onChange={(e) => setSelectedBus(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid #cbd5e1',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    backgroundColor: '#f8faff',
                  }}
                >
                  <option value="BUS-01">BUS-01 (Corridor Red)</option>
                  <option value="BUS-02">BUS-02 (Corridor Blue)</option>
                  <option value="BUS-03">BUS-03 (Corridor Green)</option>
                </select>
              </div>

              {/* Route Selector */}
              <div>
                <label className="font-label-sm" style={{ display: 'block', marginBottom: '4px', color: 'var(--color-on-surface-variant)' }}>
                  Assigned Route:
                </label>
                <select
                  id="scan-route-select"
                  value={selectedRoute}
                  onChange={(e) => setSelectedRoute(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid #cbd5e1',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    backgroundColor: '#f8faff',
                  }}
                >
                  <option value="ROUTE-12">ROUTE-12 (NH-24)</option>
                  <option value="ROUTE-8">ROUTE-8 (Ring Road)</option>
                  <option value="ROUTE-5">ROUTE-5 (Sector 62)</option>
                </select>
              </div>

              {/* Video File Picker */}
              <div>
                <label className="font-label-sm" style={{ display: 'block', marginBottom: '4px', color: 'var(--color-on-surface-variant)' }}>
                  Road Video (.mp4):
                </label>
                <input
                  id="scan-video-input"
                  ref={fileInputRef}
                  type="file"
                  accept="video/mp4"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setVideoFile(e.target.files[0])
                    }
                  }}
                  style={{
                    width: '100%',
                    padding: '6px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid #cbd5e1',
                    fontSize: '12px',
                    backgroundColor: '#f8faff',
                  }}
                />
              </div>

              {/* Start Trigger Button */}
              <div style={{ paddingTop: '18px' }}>
                <button
                  id="btn-start-video-scan"
                  className="btn-primary"
                  onClick={handleStartScan}
                  disabled={scanStatus.status === 'UPLOADING' || scanStatus.status === 'PROCESSING'}
                  style={{
                    padding: '10px 18px',
                    opacity: scanStatus.status === 'PROCESSING' ? 0.7 : 1,
                  }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>
                    play_arrow
                  </span>
                  <span>
                    {scanStatus.status === 'UPLOADING'
                      ? 'Uploading...'
                      : scanStatus.status === 'PROCESSING'
                      ? 'Detecting...'
                      : 'Start Detection'}
                  </span>
                </button>
              </div>
            </div>

            {/* Scan Status Banner */}
            {scanStatus.status === 'PROCESSING' && (
              <div
                style={{
                  padding: '10px 14px',
                  backgroundColor: '#eff4ff',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid #bfdbfe',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="radar-ping" style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#2563eb' }} />
                  <span className="font-body-sm" style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
                    Running edge detection pipeline for {selectedBus}...
                  </span>
                </div>
                <span className="font-label-sm" style={{ color: 'var(--color-secondary)', fontWeight: 700 }}>
                  Dispatched: {scanStatus.events_dispatched} Events
                </span>
              </div>
            )}

            {scanStatus.status === 'COMPLETED' && (
              <div
                style={{
                  padding: '10px 14px',
                  backgroundColor: '#ecfdf5',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid #a7f3d0',
                  color: '#047857',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>check_circle</span>
                  <span className="font-body-sm" style={{ fontWeight: 600 }}>
                    Scan complete! Successfully dispatched {scanStatus.events_dispatched} road anomaly events to database.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={resetScan}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: '#047857',
                    fontWeight: 600,
                    fontSize: '12px',
                    textDecoration: 'underline',
                  }}
                >
                  Dismiss
                </button>
              </div>
            )}

            {scanStatus.status === 'FAILED' && (
              <div
                style={{
                  padding: '10px 14px',
                  backgroundColor: '#fef2f2',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid #fecaca',
                  color: '#ba1a1a',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>error</span>
                  <span className="font-body-sm">
                    Detection failed: {scanStatus.error}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={resetScan}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: '#ba1a1a',
                    fontWeight: 600,
                    fontSize: '12px',
                    textDecoration: 'underline',
                  }}
                >
                  Dismiss
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Side: AI Detection Panel & Live Event Trigger */}
        <div style={{ gridColumn: 'span 5', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Live Detected Anomaly Triage Card */}
          <div className="cv-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '3px 10px',
                  backgroundColor: '#fee2e2',
                  borderRadius: 'var(--radius-full)',
                  color: '#ba1a1a',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  fontWeight: 700,
                }}
              >
                <span className="radar-ping" style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#ef4444' }} />
                NEW ROAD ANOMALY DETECTED
              </span>
              <span className="font-label-md" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
                #CV-000128
              </span>
            </div>

            {/* Primary Anomaly Identifier */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px', backgroundColor: '#eff4ff', borderRadius: 'var(--radius-lg)' }}>
              <div>
                <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>CLASS IDENTIFIED</span>
                <div className="font-headline-lg" style={{ color: 'var(--color-on-surface)', lineHeight: 1.1 }}>Pothole</div>
                <span className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)', fontSize: '11.5px' }}>
                  Volumetric Footprint: ~1.42 m²
                </span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>CONFIDENCE</span>
                <div className="font-headline-lg" style={{ color: 'var(--color-primary)', fontFamily: 'var(--font-mono)', lineHeight: 1.1 }}>92%</div>
                <span className="font-label-sm" style={{ color: 'var(--color-secondary)', fontWeight: 600 }}>High Certainty</span>
              </div>
            </div>

            {/* Rule-Based Severity Engine Breakdown */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span className="font-headline-sm" style={{ color: 'var(--color-on-surface)', fontWeight: 700 }}>
                  Rule-Based Severity Engine
                </span>
                <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>WEIGHTED SCORER V3</span>
              </div>
              <p className="font-body-sm" style={{ color: 'var(--color-on-surface-variant)', margin: '0 0 10px 0', fontSize: '11.5px' }}>
                Multi-parametric risk evaluation incorporating transit frequency and geometric severity
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', padding: '14px', backgroundColor: '#f8faff', borderRadius: 'var(--radius-lg)', border: '1px solid #e2e8f0' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11.5px', marginBottom: '3px' }}>
                    <span style={{ color: 'var(--color-on-surface-variant)' }}>Confidence Weight (0.25)</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>23.0 pts</span>
                  </div>
                  <div style={{ width: '100%', height: '5px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div style={{ width: '92%', height: '100%', backgroundColor: 'var(--color-secondary)' }} />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11.5px', marginBottom: '3px' }}>
                    <span style={{ color: 'var(--color-on-surface-variant)' }}>Bounding Box Area (0.20)</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>18.5 pts</span>
                  </div>
                  <div style={{ width: '100%', height: '5px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div style={{ width: '74%', height: '100%', backgroundColor: 'var(--color-secondary)' }} />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11.5px', marginBottom: '3px' }}>
                    <span style={{ color: 'var(--color-on-surface-variant)' }}>Recurrence Multiplier (0.15)</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>15.0 pts</span>
                  </div>
                  <div style={{ width: '100%', height: '5px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div style={{ width: '100%', height: '100%', backgroundColor: 'var(--color-secondary)' }} />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11.5px', marginBottom: '3px' }}>
                    <span style={{ color: 'var(--color-on-surface-variant)' }}>Road Transit Importance (0.40)</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>36.0 pts</span>
                  </div>
                  <div style={{ width: '100%', height: '5px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div style={{ width: '90%', height: '100%', backgroundColor: 'var(--color-secondary)' }} />
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '6px', borderTop: '1px solid #e2e8f0' }}>
                  <div>
                    <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>PRIORITY SCORE</span>
                    <div className="font-headline-md" style={{ color: 'var(--color-primary)', fontFamily: 'var(--font-mono)' }}>92.5 / 100</div>
                  </div>
                  <span className="badge-critical" style={{ fontSize: '11px', padding: '4px 10px' }}>
                    CRITICAL PRIORITY
                  </span>
                </div>
              </div>
            </div>

            {/* Multi-Bus Consensus Well */}
            <div style={{ padding: '14px', backgroundColor: '#eff4ff', borderRadius: 'var(--radius-lg)', border: '1px solid #dce9ff', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-primary)' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '18px', color: 'var(--color-secondary)' }}>verified_user</span>
                <span className="font-headline-sm" style={{ fontWeight: 700 }}>Multi-Bus Consensus Engine</span>
              </div>
              <p className="font-body-sm" style={{ color: 'var(--color-on-surface)', margin: 0, fontSize: '12px', lineHeight: 1.4 }}>
                <strong>Multi-Bus Verified:</strong> Detected by <strong>CAM-04</strong>, <strong>CAM-07</strong>, and <strong>CAM-12</strong> at identical GPS cluster within &lt; 5m radius.
              </p>
              <div className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>
                104 frames tracked across fleet → Deduplicated to 1 Persistent Road Event
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <button
                className="btn-primary"
                style={{ width: '100%', justifyContent: 'center', padding: '10px' }}
                onClick={() => alert('Anomaly CV-000128 submitted to Municipal Work Order Dispatch')}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>send_and_archive</span>
                <span>Submit to Municipal Dashboard</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Bottom Activity Log & Telemetry Ingestion */}
      <div className="cv-card" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="material-symbols-outlined" style={{ color: 'var(--color-primary)' }}>dvr</span>
            <span className="font-headline-sm" style={{ color: 'var(--color-on-surface)', fontWeight: 700 }}>
              Telemetry Stream & Detection Ingest Log
            </span>
          </div>
          <span className="font-label-sm" style={{ color: 'var(--color-on-surface-variant)' }}>
            AUTO-REFRESH: 100ms
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f1f5f9', color: 'var(--color-on-surface-variant)', textAlign: 'left' }}>
                <th style={{ padding: '8px 12px' }}>Timestamp</th>
                <th style={{ padding: '8px 12px' }}>Frame</th>
                <th style={{ padding: '8px 12px' }}>Entity Class</th>
                <th style={{ padding: '8px 12px' }}>GPS Location</th>
                <th style={{ padding: '8px 12px' }}>Confidence</th>
                <th style={{ padding: '8px 12px', textAlign: 'right' }}>Event Status</th>
              </tr>
            </thead>
            <tbody>
              {telemetryLog.map((row, idx) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: '1px solid #f1f5f9',
                    backgroundColor: idx % 2 === 0 ? '#ffffff' : '#f8faff',
                  }}
                >
                  <td style={{ padding: '8px 12px', color: 'var(--color-on-surface-variant)' }}>{row.timestamp}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--color-primary)' }}>{row.frame}</td>
                  <td style={{ padding: '8px 12px', fontWeight: 700, color: row.entity === 'POTHOLE' ? '#ba1a1a' : '#0051d5' }}>
                    {row.entity}
                  </td>
                  <td style={{ padding: '8px 12px', color: 'var(--color-on-surface-variant)' }}>{row.gps}</td>
                  <td style={{ padding: '8px 12px', fontWeight: 600 }}>{row.confidence}</td>
                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                    <span
                      style={{
                        padding: '2px 6px',
                        borderRadius: 'var(--radius-xs)',
                        backgroundColor: row.status === 'ACTIVE_LOCK' ? '#fee2e2' : '#eff4ff',
                        color: row.status === 'ACTIVE_LOCK' ? '#ba1a1a' : 'var(--color-secondary)',
                        fontSize: '10px',
                        fontWeight: 700,
                      }}
                    >
                      {row.status}
                    </span>
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
