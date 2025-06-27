import { useState, useEffect, useCallback } from 'react'
import { AnalysisHistory, ApiResponse } from '../types'

interface UseAnalysisHistoryOptions {
  domainId?: number
  limit?: number
  autoRefresh?: boolean
  refreshInterval?: number
}

interface UseAnalysisHistoryReturn {
  data: AnalysisHistory[]
  loading: boolean
  error: string | null
  execute: (domainId?: number) => Promise<void>
  refresh: () => Promise<void>
}

export function useAnalysisHistory({
  domainId,
  limit = 10,
  autoRefresh = false,
  refreshInterval = 30000
}: UseAnalysisHistoryOptions = {}): UseAnalysisHistoryReturn {
  const [data, setData] = useState<AnalysisHistory[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchHistory = useCallback(async (targetDomainId?: number) => {
    const id = targetDomainId || domainId
    if (!id) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/v1/analysis-history?domain_id=${id}&limit=${limit}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result: ApiResponse<AnalysisHistory[]> = await response.json()

      if (result.status === 'success' && result.data) {
        setData(result.data)
      } else {
        throw new Error(result.error || 'Неизвестная ошибка')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Ошибка загрузки истории'
      setError(errorMessage)
      console.error('Ошибка загрузки истории анализов:', err)
    } finally {
      setLoading(false)
    }
  }, [domainId, limit])

  const execute = useCallback(async (targetDomainId?: number) => {
    await fetchHistory(targetDomainId)
  }, [fetchHistory])

  const refresh = useCallback(async () => {
    await fetchHistory()
  }, [fetchHistory])

  // Автоматическое обновление
  useEffect(() => {
    if (!autoRefresh || !domainId) return

    const interval = setInterval(() => {
      fetchHistory()
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [autoRefresh, domainId, refreshInterval, fetchHistory])

  // Загрузка при изменении domainId
  useEffect(() => {
    if (domainId) {
      fetchHistory()
    }
  }, [domainId, fetchHistory])

  return {
    data,
    loading,
    error,
    execute,
    refresh
  }
} 