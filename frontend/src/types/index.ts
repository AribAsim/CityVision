export type AnomalyType = 'Pothole' | 'Crack' | 'Crack-Severe' | 'Speed-Bump'

export type Severity = 'Low' | 'Medium' | 'High' | 'Critical'

export type IncidentStatus = 'NEW' | 'VERIFIED' | 'ASSIGNED' | 'IN_PROGRESS' | 'RESOLVED'

export interface Observation {
  id: number
  edge_event_id: string
  bus_id: string
  route_id: string
  timestamp: string
  latitude: number
  longitude: number
  confidence: number
  speed_kmh: number
  image_url: string | null
}

export interface StatusHistoryEntry {
  id: number
  from_status: string | null
  to_status: IncidentStatus
  changed_at: string
  notes: string | null
}

export interface IncidentSummary {
  id: number
  incident_id: string
  anomaly_type: AnomalyType
  severity: Severity
  priority_score: number
  status: IncidentStatus
  latitude: number
  longitude: number
  first_detected_at: string
  last_detected_at: string
  confirmation_count: number
  unique_bus_count: number
  primary_image_url: string | null
}

export interface IncidentDetail extends IncidentSummary {
  observations: Observation[]
  status_history: StatusHistoryEntry[]
}

export interface BusSummary {
  id: number
  bus_id: string
  route_id: string
  status: string
  latitude: number
  longitude: number
  last_seen: string
}

export interface AnalyticsSummary {
  total_incidents: number
  pending_count: number
  verified_count: number
  assigned_count: number
  in_progress_count: number
  resolved_count: number
  multi_bus_verified_count: number
  active_buses: number
  by_anomaly_type: Record<string, number>
  by_severity: Record<string, number>
}

export interface IncidentFilters {
  status?: string
  severity?: string
  anomaly_type?: string
}

export type ScanJobStatus = 'READY' | 'UPLOADING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'

export interface ScanStartResponse {
  job_id: string
  status: string
  message: string
}

export interface ScanStatus {
  job_id: string
  status: ScanJobStatus
  events_dispatched: number
  error: string | null
}
