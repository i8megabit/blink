import { useState, useCallback } from 'react';
import { ApiResponse, LoadingState } from '../types';

interface UseApiOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: string) => void;
  onFinally?: () => void;
}

interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  state: LoadingState;
  execute: (...args: any[]) => Promise<T | null>;
  reset: () => void;
}

export function useApi<T = any>(
  apiFunction: (...args: any[]) => Promise<ApiResponse<T>>,
  options: UseApiOptions<T> = {}
): UseApiReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [state, setState] = useState<LoadingState>('idle');

  const execute = useCallback(async (...args: any[]): Promise<T | null> => {
    try {
      setLoading(true);
      setError(null);
      setState('loading');

      const response = await apiFunction(...args);

      if (response.success && response.data) {
        setData(response.data);
        setState('success');
        
        if (options.onSuccess) {
          options.onSuccess(response.data);
        }
        
        return response.data;
      } else {
        const errorMessage = response.error || response.message || 'Неизвестная ошибка';
        setError(errorMessage);
        setState('error');
        
        if (options.onError) {
          options.onError(errorMessage);
        }
        
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Ошибка сети';
      setError(errorMessage);
      setState('error');
      
      if (options.onError) {
        options.onError(errorMessage);
      }
      
      return null;
    } finally {
      setLoading(false);
      
      if (options.onFinally) {
        options.onFinally();
      }
    }
  }, [apiFunction, options]);

  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
    setState('idle');
  }, []);

  return {
    data,
    loading,
    error,
    state,
    execute,
    reset
  };
}

// Специализированные хуки для конкретных API
export function useDomains() {
  return useApi(async () => {
    const response = await fetch('/api/v1/domains');
    const data = await response.json();
    return {
      success: response.ok,
      data: response.ok ? data.domains : undefined,
      error: response.ok ? undefined : data.error || 'Ошибка загрузки доменов'
    };
  });
}

export function useOllamaStatus() {
  return useApi(async () => {
    const response = await fetch('/api/v1/ollama_status');
    const data = await response.json();
    return {
      success: response.ok,
      data: response.ok ? data : undefined,
      error: response.ok ? undefined : data.error || 'Ошибка проверки статуса Ollama'
    };
  });
}

export function useAnalysisHistory(domain?: string) {
  return useApi(async () => {
    const url = domain 
      ? `/api/v1/analysis_history?domain=${encodeURIComponent(domain)}`
      : '/api/v1/analysis_history';
    
    const response = await fetch(url);
    const data = await response.json();
    return {
      success: response.ok,
      data: response.ok ? data.history : undefined,
      error: response.ok ? undefined : data.error || 'Ошибка загрузки истории'
    };
  });
}

export function useBenchmarkHistory() {
  return useApi(async () => {
    const response = await fetch('/api/v1/benchmark_history');
    const data = await response.json();
    return {
      success: response.ok,
      data: response.ok ? data.benchmarks : undefined,
      error: response.ok ? undefined : data.error || 'Ошибка загрузки истории бенчмарков'
    };
  });
} 