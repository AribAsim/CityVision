import { useState, useEffect, useCallback } from 'react'
import type { BusSummary } from '../types'
import { fetchBuses } from '../services/api'

export function useBuses() {
  const [buses, setBuses] = useState<BusSummary[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const loadBuses = useCallback(async (isInitial = false) => {
    try {
      if (isInitial) setLoading(true)
      const data = await fetchBuses()
      setBuses(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load buses')
    } finally {
      if (isInitial) setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadBuses(true)
    const timer = setInterval(() => {
      loadBuses(false)
    }, 4000)

    return () => clearInterval(timer)
  }, [loadBuses])

  return { buses, loading, error, refetch: () => loadBuses(false) }
}
