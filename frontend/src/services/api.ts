import type {
  AnalyticsSummary,
  BusSummary,
  IncidentDetail,
  IncidentFilters,
  IncidentStatus,
  IncidentSummary,
} from '../types'
const rawBase = (import.meta.env.VITE_API_BASE_URL || '').trim()
export const BASE_URL = rawBase
  ? (rawBase.startsWith('http://') || rawBase.startsWith('https://') ? rawBase : `https://${rawBase}`).replace(/\/$/, '')
  : ''
export async function fetchIncidents(filters?: IncidentFilters): Promise<IncidentSummary[]> {
  const params = new URLSearchParams()
  if (filters?.status) params.append('status', filters.status)
  if (filters?.severity) params.append('severity', filters.severity)
  if (filters?.anomaly_type) params.append('anomaly_type', filters.anomaly_type)

  const query = params.toString() ? `?${params.toString()}` : ''
  const res = await fetch(`${BASE_URL}/api/incidents${query}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch incidents: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchIncidentDetail(incidentId: string | number): Promise<IncidentDetail> {
  const res = await fetch(`${BASE_URL}/api/incidents/${incidentId}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch incident ${incidentId}: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchAnalytics(): Promise<AnalyticsSummary> {
  const res = await fetch(`${BASE_URL}/api/analytics/summary`)
  if (!res.ok) {
    throw new Error(`Failed to fetch analytics: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchBuses(): Promise<BusSummary[]> {
  const res = await fetch(`${BASE_URL}/api/buses`)
  if (!res.ok) {
    throw new Error(`Failed to fetch buses: ${res.statusText}`)
  }
  return res.json()
}

export async function patchIncidentStatus(
  incidentId: string | number,
  status: IncidentStatus,
  notes?: string
): Promise<IncidentDetail> {
  const res = await fetch(`${BASE_URL}/api/incidents/${incidentId}/status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ status, notes }),
  })
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}))
    throw new Error(errData.detail || `Failed to update status: ${res.statusText}`)
  }
  return res.json()
}

export async function startBusScan(
  busId: string,
  routeId: string,
  videoFile: File
): Promise<{ job_id: string; status: string; message: string }> {
  const formData = new FormData()
  formData.append('bus_id', busId)
  formData.append('route_id', routeId)
  formData.append('video_file', videoFile)

  const res = await fetch(`${BASE_URL}/api/scan/start`, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}))
    throw new Error(errData.detail || `Failed to start scan: ${res.statusText}`)
  }

  return res.json()
}

export async function fetchScanStatus(jobId: string): Promise<{
  job_id: string
  status: 'READY' | 'UPLOADING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  events_dispatched: number
  error: string | null
}> {
  const res = await fetch(`${BASE_URL}/api/scan/status/${jobId}`)
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}))
    throw new Error(errData.detail || `Failed to fetch scan status: ${res.statusText}`)
  }
  return res.json()
}
