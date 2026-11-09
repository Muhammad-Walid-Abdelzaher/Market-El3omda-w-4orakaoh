import { useState, useEffect, useCallback } from 'react'

const API_BASE = '/api/dashboard'

/**
 * Custom hook to fetch dashboard data from all endpoints.
 * Returns { data, loading, error, refetch }.
 */
export function useDashboardData() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const endpoints = [
        'summary',
        'sales-chart',
        'category-breakdown',
        'top-products',
        'inventory-status',
        'recent-alerts',
        'restocking-tasks',
        'stock-movements',
      ]

      const responses = await Promise.all(
        endpoints.map(async (endpoint) => {
          const response = await fetch(`${API_BASE}/${endpoint}`)
          if (!response.ok) {
            throw new Error(`Dashboard request failed (${response.status}): ${endpoint}`)
          }
          return response.json()
        })
      )

      setData({
        summary: responses[0],
        salesChart: responses[1],
        categories: responses[2],
        topProducts: responses[3],
        inventoryStatus: responses[4],
        alerts: responses[5],
        restockingTasks: responses[6],
        stockMovements: responses[7],
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  return { data, loading, error, refetch: fetchAll }
}
