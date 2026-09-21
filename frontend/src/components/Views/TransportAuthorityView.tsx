import React, { useState, useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts'
import type { IncidentSummary, BusSummary } from '../../types'
import { BASE_URL } from '../../services/api'

interface TransportAuthorityViewProps {
  incidents?: IncidentSummary[]
  buses?: BusSummary[]
  onSelectIncident?: (incident: IncidentSummary) => void
}

interface DensityRecord {
  id: number
  segment_key: string
  route_id: string
  bus_id: string
  timestamp: string
  lat: number
  lon: number
  total_count: number
  congestion_index: number
  count_person: number
  count_car: number
  count_bus: number
  count_motorcycle: number
}

interface BottleneckRecord {
  segment_key: string
  route_id: string
  bus_id: string
  peak_count: number
  congestion_index: number
  latitude: number
  longitude: number
  timestamp: string
  status: string
}

interface InfraDeficiencyItem {
  route_id: string
  expected_assets: number
  observed_assets: number
  missing_assets: number
  deficiency_score: number
  status: string
  breakdown?: {
    expected: Record<string, number>
    observed: Record<string, number>
  }
}

interface ODFlowItem {
  route_id: string
  origin_segment: string
  destination_segment: string
  estimated_flow: number
  avg_congestion: number
}

interface RouteDelayData {
  route_id: string
  baseline_minutes: number
  actual_minutes: number
  delay_minutes: number
  status: string
  avg_congestion_index: number
  sample_count: number
}

export const TransportAuthorityView: React.FC<TransportAuthorityViewProps> = () => {
  const [selectedRoute, setSelectedRoute] = useState<string>('ROUTE-RED')
  const [densityList, setDensityList] = useState<DensityRecord[]>([])
  const [bottlenecks, setBottlenecks] = useState<BottleneckRecord[]>([])
  const [infraData, setInfraData] = useState<InfraDeficiencyItem[]>([])
  const [odFlows, setOdFlows] = useState<ODFlowItem[]>([])
  const [routeDelay, setRouteDelay] = useState<RouteDelayData | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)

  // Fetch telemetry & report APIs
  useEffect(() => {
    let isMounted = true
    setIsLoading(true)

    const fetchAllData = async () => {
      try {
        const [densRes, bneckRes, infraRes, odRes, delayRes] = await Promise.allSettled([
          fetch(`${BASE_URL}/api/telemetry/density?hours=24`),
          fetch(`${BASE_URL}/api/telemetry/density/bottlenecks?top_n=8`),
          fetch(`${BASE_URL}/api/reports/infrastructure-deficiency`),
          fetch(`${BASE_URL}/api/telemetry/density/od`),
          fetch(`${BASE_URL}/api/telemetry/density/delay?route_id=${selectedRoute}`),
        ])

        if (isMounted) {
          if (densRes.status === 'fulfilled' && densRes.value.ok) {
            const d = await densRes.value.json()
            setDensityList(d)
          }
          if (bneckRes.status === 'fulfilled' && bneckRes.value.ok) {
            const b = await bneckRes.value.json()
            setBottlenecks(b)
          }
          if (infraRes.status === 'fulfilled' && infraRes.value.ok) {
            const inf = await infraRes.value.json()
            setInfraData(inf)
          }
          if (odRes.status === 'fulfilled' && odRes.value.ok) {
            const od = await odRes.value.json()
            setOdFlows(od)
          }
          if (delayRes.status === 'fulfilled' && delayRes.value.ok) {
            const del = await delayRes.value.json()
            setRouteDelay(del)
          }
        }
      } catch (err) {
        console.error('Failed to load transport authority data:', err)
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    fetchAllData()
    return () => {
      isMounted = false
    }
  }, [selectedRoute])

  // Initialize MapLibre GL JS Heatmap
  useEffect(() => {
    if (!mapContainerRef.current) return

    if (!mapRef.current) {
      const map = new maplibregl.Map({
        container: mapContainerRef.current,
        style: {
          version: 8,
          sources: {
            osm: {
              type: 'raster',
              tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
              tileSize: 256,
              attribution: '&copy; OpenStreetMap Contributors',
            },
          },
          layers: [
            {
              id: 'osm-layer',
              type: 'raster',
              source: 'osm',
              minzoom: 0,
              maxzoom: 19,
            },
          ],
        },
        center: [77.209, 28.613],
        zoom: 11.5,
      })

      map.addControl(new maplibregl.NavigationControl(), 'top-right')

      map.on('load', () => {
        // Add GeoJSON points source for density heatmap
        map.addSource('density-points', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: [],
          },
        })

        // Heatmap layer
        map.addLayer({
          id: 'density-heat',
          type: 'heatmap',
          source: 'density-points',
          maxzoom: 16,
          paint: {
            'heatmap-weight': [
              'interpolate',
              ['linear'],
              ['get', 'congestion_index'],
              0, 0,
              0.5, 0.4,
              1.0, 0.8,
              2.0, 1.0,
            ],
            'heatmap-intensity': [
              'interpolate',
              ['linear'],
              ['zoom'],
              10, 1,
              15, 3,
            ],
            'heatmap-color': [
              'interpolate',
              ['linear'],
              ['heatmap-density'],
              0, 'rgba(33,102,172,0)',
              0.2, 'rgb(103,169,207)',
              0.4, 'rgb(209,229,240)',
              0.6, 'rgb(253,219,199)',
              0.8, 'rgb(239,138,98)',
              1, 'rgb(178,24,43)',
            ],
            'heatmap-radius': [
              'interpolate',
              ['linear'],
              ['zoom'],
              10, 15,
              15, 35,
            ],
            'heatmap-opacity': 0.85,
          },
        })

        // Circle layer for individual inspection at closer zoom
        map.addLayer({
          id: 'density-circle',
          type: 'circle',
          source: 'density-points',
          minzoom: 13,
          paint: {
            'circle-radius': 6,
            'circle-color': [
              'interpolate',
              ['linear'],
              ['get', 'congestion_index'],
              0, '#10b981',
              0.8, '#f59e0b',
              1.2, '#ef4444',
            ],
            'circle-stroke-color': 'white',
            'circle-stroke-width': 1.5,
          },
        })

        mapRef.current = map
      })
    }

    // Update map data whenever densityList changes
    if (mapRef.current && mapRef.current.isStyleLoaded()) {
      const src = mapRef.current.getSource('density-points') as maplibregl.GeoJSONSource
      if (src) {
        const geojson: GeoJSON.FeatureCollection = {
          type: 'FeatureCollection',
          features: densityList.map((d) => ({
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: [d.lon, d.lat],
            },
            properties: {
              congestion_index: d.congestion_index,
              total_count: d.total_count,
              segment_key: d.segment_key,
              route_id: d.route_id,
            },
          })),
        }
        src.setData(geojson)

        if (densityList.length > 0) {
          const first = densityList[0]
          mapRef.current.flyTo({ center: [first.lon, first.lat], zoom: 12 })
        }
      }
    }
  }, [densityList])

  // Download PDF helpers
  const handleDownloadInfraPdf = () => {
    window.open(`${BASE_URL}/api/reports/infrastructure-deficiency.pdf?route_id=${selectedRoute}`, '_blank')
  }

  const handleDownloadRoutePdf = () => {
    window.open(`${BASE_URL}/api/reports/route-performance.pdf?route_id=${selectedRoute}`, '_blank')
  }

  // Delay chart data
  const chartData = [
    {
      name: 'ROUTE-RED',
      Baseline: 22.0,
      Actual: selectedRoute === 'ROUTE-RED' && routeDelay ? routeDelay.actual_minutes : 24.5,
      Delay: selectedRoute === 'ROUTE-RED' && routeDelay ? routeDelay.delay_minutes : 2.5,
    },
    {
      name: 'ROUTE-BLUE',
      Baseline: 18.0,
      Actual: selectedRoute === 'ROUTE-BLUE' && routeDelay ? routeDelay.actual_minutes : 19.2,
      Delay: selectedRoute === 'ROUTE-BLUE' && routeDelay ? routeDelay.delay_minutes : 1.2,
    },
    {
      name: 'ROUTE-GREEN',
      Baseline: 15.0,
      Actual: selectedRoute === 'ROUTE-GREEN' && routeDelay ? routeDelay.actual_minutes : 15.8,
      Delay: selectedRoute === 'ROUTE-GREEN' && routeDelay ? routeDelay.delay_minutes : 0.8,
    },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', paddingBottom: '40px' }}>
      {/* Top Banner & Route Filter */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Transport Authority & Corridor Flow
            </h1>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                backgroundColor: '#e0e7ff',
                color: '#3730a3',
                padding: '3px 8px',
                borderRadius: '4px',
                fontFamily: 'JetBrains Mono, monospace',
                border: '1px solid #c7d2fe',
              }}
            >
              PS-COMPLIANT // MUNICIPAL GRID
            </span>
          </div>
          <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
            MapLibre GL corridor density heatmap, automated bottleneck identification, OD flows, and infrastructure audits.
          </p>
        </div>

        {/* Route Selector & PDF Actions */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            value={selectedRoute}
            onChange={(e) => setSelectedRoute(e.target.value)}
            style={{
              padding: '7px 12px',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              backgroundColor: '#ffffff',
              fontSize: '13px',
              fontWeight: 600,
              color: '#1e293b',
              cursor: 'pointer',
            }}
          >
            <option value="ROUTE-RED">Route Red (Central Arterial)</option>
            <option value="ROUTE-BLUE">Route Blue (Ring Corridor)</option>
            <option value="ROUTE-GREEN">Route Green (Suburban Spine)</option>
          </select>

          <button
            onClick={handleDownloadInfraPdf}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '7px 12px',
              borderRadius: '6px',
              backgroundColor: '#1e3a8a',
              color: '#ffffff',
              border: 'none',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>picture_as_pdf</span>
            Infra Audit PDF
          </button>

          <button
            onClick={handleDownloadRoutePdf}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '7px 12px',
              borderRadius: '6px',
              backgroundColor: '#0284c7',
              color: '#ffffff',
              border: 'none',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>download</span>
            Route Delay PDF
          </button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
        }}
      >
        <div style={{ backgroundColor: '#fff', borderRadius: '10px', padding: '16px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '12px', fontWeight: 600 }}>
            <span>TELEMETRY DENSITY CELLS</span>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#0284c7' }}>grid_view</span>
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#0f172a', marginTop: '8px' }}>
            {densityList.length} Cells
          </div>
          <div style={{ fontSize: '12px', color: '#16a34a', marginTop: '4px', fontWeight: 500 }}>
            ~250m discrete GPS buckets
          </div>
        </div>

        <div style={{ backgroundColor: '#fff', borderRadius: '10px', padding: '16px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '12px', fontWeight: 600 }}>
            <span>CRITICAL BOTTLENECKS</span>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#dc2626' }}>traffic</span>
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#dc2626', marginTop: '8px' }}>
            {bottlenecks.filter((b) => b.congestion_index >= 1.0).length} Segments
          </div>
          <div style={{ fontSize: '12px', color: '#ea580c', marginTop: '4px', fontWeight: 500 }}>
            Congestion Index &gt; 1.0 (Above capacity)
          </div>
        </div>

        <div style={{ backgroundColor: '#fff', borderRadius: '10px', padding: '16px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '12px', fontWeight: 600 }}>
            <span>ROUTE DELAY VARIANCE</span>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#ea580c' }}>schedule</span>
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#0f172a', marginTop: '8px' }}>
            +{routeDelay ? routeDelay.delay_minutes : 0.0} min
          </div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px', fontWeight: 500 }}>
            Baseline: {routeDelay ? routeDelay.baseline_minutes : 20}m | Observed: {routeDelay ? routeDelay.actual_minutes : 20}m
          </div>
        </div>

        <div style={{ backgroundColor: '#fff', borderRadius: '10px', padding: '16px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '12px', fontWeight: 600 }}>
            <span>ANPR SURVEILLANCE STATE</span>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#f59e0b' }}>badge</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px' }}>
            <span
              style={{
                backgroundColor: '#fef3c7',
                color: '#b45309',
                padding: '4px 10px',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 700,
                border: '1px solid #fde68a',
              }}
            >
              INCIDENT-TRIGGERED ONLY
            </span>
          </div>
          <div style={{ fontSize: '11px', color: '#78716c', marginTop: '6px' }}>
            Activates 45 frames post rash/hit-and-run
          </div>
        </div>
      </div>

      {/* 4-Panel Grid Architecture */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '16px' }}>
        {/* Panel 1: MapLibre GL Heatmap */}
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            border: '1px solid #e2e8f0',
            padding: '16px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div>
              <span style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
                Corridor Traffic Density Heatmap (MapLibre GL JS)
              </span>
              <div style={{ fontSize: '11px', color: '#64748b' }}>
                Real-time vehicle intensity aggregated across bus sensing routes
              </div>
            </div>
            {/* Heatmap Legend */}
            <div style={{ display: 'flex', gap: '6px', alignItems: 'center', fontSize: '10px', fontWeight: 600 }}>
              <span style={{ color: '#67a9cf' }}>Low</span>
              <div
                style={{
                  width: '60px',
                  height: '8px',
                  borderRadius: '4px',
                  background: 'linear-gradient(to right, #67a9cf, #fddbc7, #ef8a62, #b2182b)',
                }}
              />
              <span style={{ color: '#b2182b' }}>Critical</span>
            </div>
          </div>

          {/* Map Canvas with cold start handler */}
          <div style={{ position: 'relative', width: '100%', height: '360px', borderRadius: '8px', overflow: 'hidden' }}>
            <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />
            {densityList.length === 0 && !isLoading && (
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  backgroundColor: 'rgba(255, 255, 255, 0.92)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '20px',
                  textAlign: 'center',
                }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '36px', color: '#94a3b8' }}>
                  cloud_off
                </span>
                <span style={{ fontWeight: 700, color: '#1e293b', fontSize: '14px' }}>
                  No density data yet
                </span>
                <p style={{ fontSize: '12px', color: '#64748b', maxWidth: '300px', margin: 0 }}>
                  Run a bus scan or execute the seeded demo to populate corridor density readings.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Panel 2: Route Bottlenecks Table */}
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            border: '1px solid #e2e8f0',
            padding: '16px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            overflowY: 'auto',
            maxHeight: '430px',
          }}
        >
          <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a', marginBottom: '4px' }}>
            Corridor Chokepoints & Bottlenecks
          </div>
          <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '12px' }}>
            Ranked by congestion index (vehicles vs capacity baseline)
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b', textAlign: 'left' }}>
                <th style={{ padding: '6px' }}>Segment</th>
                <th style={{ padding: '6px' }}>Route</th>
                <th style={{ padding: '6px' }}>Peak Count</th>
                <th style={{ padding: '6px' }}>Index</th>
                <th style={{ padding: '6px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {bottlenecks.map((b, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '8px 6px', fontWeight: 600, color: '#1e293b', fontFamily: 'JetBrains Mono, monospace' }}>
                    {b.segment_key.split(':').slice(1).join(':')}
                  </td>
                  <td style={{ padding: '8px 6px', color: '#64748b' }}>{b.route_id}</td>
                  <td style={{ padding: '8px 6px', fontWeight: 700 }}>{b.peak_count} veh</td>
                  <td style={{ padding: '8px 6px', fontFamily: 'JetBrains Mono, monospace' }}>{b.congestion_index}</td>
                  <td style={{ padding: '8px 6px' }}>
                    <span
                      style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '10px',
                        fontWeight: 700,
                        backgroundColor:
                          b.congestion_index >= 1.2 ? '#fee2e2' : b.congestion_index >= 0.8 ? '#fef3c7' : '#ecfdf5',
                        color:
                          b.congestion_index >= 1.2 ? '#b91c1c' : b.congestion_index >= 0.8 ? '#b45309' : '#047857',
                      }}
                    >
                      {b.status}
                    </span>
                  </td>
                </tr>
              ))}
              {bottlenecks.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                    No bottlenecks flagged
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Row 2: Route Delay Recharts & Origin-Destination Flow & Infra Deficiency */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        {/* Panel 3: Transit Route Delay & Adherence */}
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            border: '1px solid #e2e8f0',
            padding: '16px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div>
              <span style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
                Route Transit Time Variance (Minutes)
              </span>
              <div style={{ fontSize: '11px', color: '#64748b' }}>
                Baseline free-flow travel time vs observed transit delay
              </div>
            </div>
          </div>

          <div style={{ width: '100%', height: '220px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Bar dataKey="Baseline" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Actual" fill="#0284c7" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Delay" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Panel 4: Infrastructure Deficiency Report Table */}
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            border: '1px solid #e2e8f0',
            padding: '16px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div>
              <span style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
                Infrastructure Deficiency Audit
              </span>
              <div style={{ fontSize: '11px', color: '#64748b' }}>
                Expected signage / crossings vs observed roadside assets
              </div>
            </div>
            <button
              onClick={handleDownloadInfraPdf}
              style={{
                fontSize: '11px',
                color: '#1e3a8a',
                backgroundColor: '#eff6ff',
                padding: '4px 8px',
                borderRadius: '4px',
                border: '1px solid #bfdbfe',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Export PDF
            </button>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b', textAlign: 'left' }}>
                <th style={{ padding: '6px' }}>Corridor</th>
                <th style={{ padding: '6px' }}>Expected</th>
                <th style={{ padding: '6px' }}>Observed</th>
                <th style={{ padding: '6px' }}>Deficiency</th>
                <th style={{ padding: '6px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {infraData.map((item, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '8px 6px', fontWeight: 600, color: '#1e293b' }}>{item.route_id}</td>
                  <td style={{ padding: '8px 6px' }}>{item.expected_assets} assets</td>
                  <td style={{ padding: '8px 6px' }}>{item.observed_assets} assets</td>
                  <td style={{ padding: '8px 6px', fontWeight: 700, color: item.deficiency_score > 40 ? '#b91c1c' : '#15803d' }}>
                    {item.deficiency_score}%
                  </td>
                  <td style={{ padding: '8px 6px' }}>
                    <span
                      style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '10px',
                        fontWeight: 700,
                        backgroundColor: item.deficiency_score > 40 ? '#fee2e2' : '#ecfdf5',
                        color: item.deficiency_score > 40 ? '#b91c1c' : '#047857',
                      }}
                    >
                      {item.status}
                    </span>
                  </td>
                </tr>
              ))}
              {infraData.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                    No audit records loaded
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Row 3: Origin-Destination Flow Table */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '10px',
          border: '1px solid #e2e8f0',
          padding: '16px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}
      >
        <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a', marginBottom: '4px' }}>
          Corridor Origin-Destination (OD) Flow Matrix
        </div>
        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '12px' }}>
          Inter-segment vehicle transitions and corridor load volume
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b', textAlign: 'left' }}>
              <th style={{ padding: '6px' }}>Route</th>
              <th style={{ padding: '6px' }}>Origin Segment</th>
              <th style={{ padding: '6px' }}>Destination Segment</th>
              <th style={{ padding: '6px' }}>Estimated Volume</th>
              <th style={{ padding: '6px' }}>Avg Congestion</th>
            </tr>
          </thead>
          <tbody>
            {odFlows.map((flow, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '8px 6px', fontWeight: 600, color: '#1e293b' }}>{flow.route_id}</td>
                <td style={{ padding: '8px 6px', fontFamily: 'JetBrains Mono, monospace' }}>{flow.origin_segment}</td>
                <td style={{ padding: '8px 6px', fontFamily: 'JetBrains Mono, monospace' }}>{flow.destination_segment}</td>
                <td style={{ padding: '8px 6px', fontWeight: 700 }}>{flow.estimated_flow} veh</td>
                <td style={{ padding: '8px 6px' }}>{flow.avg_congestion}</td>
              </tr>
            ))}
            {odFlows.length === 0 && (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                  No inter-segment flow transitions recorded yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
export default TransportAuthorityView
