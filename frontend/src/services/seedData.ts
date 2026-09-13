import type { IncidentSummary, BusSummary, AnalyticsSummary } from '../types'

export interface RouteInfo {
  route_id: string
  name: string
  color: string
  score: number
  condition: 'Good' | 'Moderate' | 'Poor'
  active_buses: number
  degraded_zones: number
  coordinates: [number, number][]
}

export const MONITORED_ROUTES: RouteInfo[] = [
  {
    route_id: 'ROUTE-12',
    name: 'Route 12 (NH-24 Arterial Trunk)',
    color: '#0051d5',
    score: 64,
    condition: 'Moderate',
    active_buses: 8,
    degraded_zones: 6,
    coordinates: [
      [28.6139, 77.2090],
      [28.6190, 77.2180],
      [28.6250, 77.2280],
      [28.6310, 77.2400],
      [28.6380, 77.2550],
    ],
  },
  {
    route_id: 'ROUTE-8',
    name: 'Route 8 (Outer Ring Road South-West)',
    color: '#7e22ce',
    score: 78,
    condition: 'Good',
    active_buses: 6,
    degraded_zones: 3,
    coordinates: [
      [28.5500, 77.1800],
      [28.5600, 77.1950],
      [28.5750, 77.2100],
      [28.5900, 77.2250],
      [28.6050, 77.2400],
    ],
  },
  {
    route_id: 'ROUTE-5',
    name: 'Route 5 (Sector 62 Commercial Express)',
    color: '#047857',
    score: 82,
    condition: 'Good',
    active_buses: 5,
    degraded_zones: 2,
    coordinates: [
      [28.6200, 77.3600],
      [28.6280, 77.3680],
      [28.6350, 77.3750],
    ],
  },
]

export const SEED_BUSES: BusSummary[] = [
  {
    id: 1,
    bus_id: 'BUS-01',
    route_id: 'ROUTE-12',
    status: 'Active',
    latitude: 28.6185,
    longitude: 77.2140,
    last_seen: new Date().toISOString(),
  },
  {
    id: 2,
    bus_id: 'BUS-02',
    route_id: 'ROUTE-8',
    status: 'Active',
    latitude: 28.5680,
    longitude: 77.2050,
    last_seen: new Date().toISOString(),
  },
  {
    id: 3,
    bus_id: 'BUS-03',
    route_id: 'ROUTE-5',
    status: 'Active',
    latitude: 28.6270,
    longitude: 77.3650,
    last_seen: new Date().toISOString(),
  },
]

export const SEED_ANALYTICS: AnalyticsSummary = {
  total_incidents: 128,
  pending_count: 52,
  verified_count: 24,
  assigned_count: 10,
  in_progress_count: 18,
  resolved_count: 76,
  multi_bus_verified_count: 41,
  active_buses: 24,
  by_anomaly_type: {
    'Pothole': 62,
    'Crack-Severe': 34,
    'Crack': 22,
    'Speed-Bump': 10,
  },
  by_severity: {
    'Critical': 18,
    'High': 42,
    'Medium': 48,
    'Low': 20,
  },
}

export const SEED_RECENT_INCIDENTS: IncidentSummary[] = [
  {
    id: 128,
    incident_id: 'CV-000128',
    anomaly_type: 'Pothole',
    severity: 'Critical',
    priority_score: 93,
    status: 'NEW',
    latitude: 28.6139,
    longitude: 77.2090,
    first_detected_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    last_detected_at: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
    confirmation_count: 6,
    unique_bus_count: 3,
    primary_image_url: null,
  },
  {
    id: 125,
    incident_id: 'CV-000125',
    anomaly_type: 'Crack-Severe',
    severity: 'High',
    priority_score: 84,
    status: 'IN_PROGRESS',
    latitude: 28.5720,
    longitude: 77.2100,
    first_detected_at: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    last_detected_at: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
    confirmation_count: 3,
    unique_bus_count: 2,
    primary_image_url: null,
  },
  {
    id: 119,
    incident_id: 'CV-000119',
    anomaly_type: 'Speed-Bump',
    severity: 'Low',
    priority_score: 38,
    status: 'RESOLVED',
    latitude: 28.6290,
    longitude: 77.3680,
    first_detected_at: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
    last_detected_at: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
    confirmation_count: 1,
    unique_bus_count: 1,
    primary_image_url: null,
  },
  {
    id: 114,
    incident_id: 'CV-000114',
    anomaly_type: 'Crack',
    severity: 'Medium',
    priority_score: 62,
    status: 'IN_PROGRESS',
    latitude: 28.6240,
    longitude: 77.2280,
    first_detected_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    last_detected_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    confirmation_count: 2,
    unique_bus_count: 1,
    primary_image_url: null,
  },
]
