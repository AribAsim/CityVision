import { useState, useEffect, useCallback } from 'react'
import type { AnalyticsSummary } from '../types'
import { fetchAnalytics } from '../services/api'

export function useAnalytics() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const loadAnalytics = useCallback(async (isInitial = false) => {
    try {
      if (isInitial) setLoading(true)
      const data = await fetchAnalytics()
      setAnalytics(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics')
    } finally {
      if (isInitial) setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAnalytics(true)
    const timer = setInterval(() => {
      loadAnalytics(false)
    }, 4000)

    return () => clearInterval(timer)
  }, [loadAnalytics])

  return { analytics, loading, error, refetch: () => loadAnalytics(false) }
}
