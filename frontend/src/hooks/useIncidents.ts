import { useState, useEffect, useCallback, useRef } from 'react'
import type { IncidentSummary, IncidentFilters } from '../types'
import { fetchIncidents } from '../services/api'

export function useIncidents(filters: IncidentFilters) {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const filtersRef = useRef(filters)
  filtersRef.current = filters

  const loadIncidents = useCallback(async (isInitial = false) => {
    try {
      if (isInitial) setLoading(true)
      const data = await fetchIncidents(filtersRef.current)
      setIncidents(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load incidents')
    } finally {
      if (isInitial) setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadIncidents(true)
    const timer = setInterval(() => {
      loadIncidents(false)
    }, 4000)

    return () => clearInterval(timer)
  }, [filters.status, filters.severity, filters.anomaly_type, loadIncidents])

  return { incidents, loading, error, refetch: () => loadIncidents(false) }
}
