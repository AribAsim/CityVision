import { useState, useEffect, useCallback, useRef } from 'react'
import type { ScanJobStatus, ScanStatus } from '../types'
import { startBusScan, fetchScanStatus } from '../services/api'

interface UseScanManagerOptions {
  onScanComplete?: () => void
}

export interface ScanManager {
  scanStatus: ScanStatus
  selectedBus: string
  setSelectedBus: (bus: string) => void
  selectedRoute: string
  setSelectedRoute: (route: string) => void
  startScan: (busId: string, routeId: string, file: File) => Promise<void>
  resetScan: () => void
}

export function useScanManager(options?: UseScanManagerOptions): ScanManager {
  const [selectedBus, setSelectedBus] = useState<string>('BUS-01')
  const [selectedRoute, setSelectedRoute] = useState<string>('ROUTE-12')
  const [scanStatus, setScanStatus] = useState<ScanStatus>(() => {
    // Try restoring from sessionStorage in case of quick page reload
    const saved = sessionStorage.getItem('cv_active_scan')
    if (saved) {
      try {
        return JSON.parse(saved)
      } catch {
        // ignore parse error
      }
    }
    return {
      job_id: '',
      status: 'READY',
      events_dispatched: 0,
      error: null,
    }
  })

  const onScanCompleteRef = useRef(options?.onScanComplete)
  onScanCompleteRef.current = options?.onScanComplete

  // Persist active scan status to sessionStorage
  useEffect(() => {
    if (scanStatus.job_id) {
      sessionStorage.setItem('cv_active_scan', JSON.stringify(scanStatus))
    } else {
      sessionStorage.removeItem('cv_active_scan')
    }
  }, [scanStatus])

  // Continuous background polling whenever status is PROCESSING
  useEffect(() => {
    if (!scanStatus.job_id || scanStatus.status !== 'PROCESSING') return

    const pollInterval = setInterval(async () => {
      try {
        const res = await fetchScanStatus(scanStatus.job_id)
        setScanStatus({
          job_id: res.job_id,
          status: res.status as ScanJobStatus,
          events_dispatched: res.events_dispatched,
          error: res.error,
        })

        if (res.status === 'COMPLETED' || res.status === 'FAILED') {
          clearInterval(pollInterval)
          if (res.status === 'COMPLETED' && onScanCompleteRef.current) {
            onScanCompleteRef.current()
          }
        }
      } catch (err) {
        console.error('Scan polling error in background:', err)
      }
    }, 1500)

    return () => clearInterval(pollInterval)
  }, [scanStatus.job_id, scanStatus.status])

  const startScan = useCallback(async (busId: string, routeId: string, file: File) => {
    setSelectedBus(busId)
    setSelectedRoute(routeId)
    setScanStatus({
      job_id: '',
      status: 'UPLOADING',
      events_dispatched: 0,
      error: null,
    })

    try {
      const res = await startBusScan(busId, routeId, file)
      setScanStatus({
        job_id: res.job_id,
        status: 'PROCESSING',
        events_dispatched: 0,
        error: null,
      })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to initiate video scan'
      setScanStatus((prev) => ({
        ...prev,
        status: 'FAILED',
        error: msg,
      }))
      throw err
    }
  }, [])

  const resetScan = useCallback(() => {
    sessionStorage.removeItem('cv_active_scan')
    setScanStatus({
      job_id: '',
      status: 'READY',
      events_dispatched: 0,
      error: null,
    })
  }, [])

  return {
    scanStatus,
    selectedBus,
    setSelectedBus,
    selectedRoute,
    setSelectedRoute,
    startScan,
    resetScan,
  }
}
