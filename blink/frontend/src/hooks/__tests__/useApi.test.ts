import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useDomains, useOllamaStatus, useAnalysisHistory, useBenchmarkHistory } from '../useApi';

// Мокаем fetch
global.fetch = vi.fn();

describe('API Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useDomains', () => {
    it('успешно загружает домены', async () => {
      const mockResponse = {
        domains: [
          { id: 1, name: 'example.com', status: 'analyzed' }
        ]
      };

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const { result } = renderHook(() => useDomains());
      
      await result.current.execute();
      
      await waitFor(() => {
        expect(result.current.data).toEqual(mockResponse.domains);
        expect(result.current.loading).toBe(false);
        expect(result.current.error).toBeNull();
      });
    });

    it('обрабатывает ошибки загрузки доменов', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: false,
        json: async () => ({ error: 'Ошибка сервера' })
      });

      const { result } = renderHook(() => useDomains());
      
      await result.current.execute();
      
      await waitFor(() => {
        expect(result.current.error).toBe('Ошибка сервера');
        expect(result.current.loading).toBe(false);
      });
    });
  });

  describe('useOllamaStatus', () => {
    it('успешно получает статус Ollama', async () => {
      const mockResponse = {
        status: 'available',
        models: ['qwen2.5:7b-instruct'],
        version: '0.1.0'
      };

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const { result } = renderHook(() => useOllamaStatus());
      
      await result.current.execute();
      
      await waitFor(() => {
        expect(result.current.data).toEqual(mockResponse);
        expect(result.current.loading).toBe(false);
        expect(result.current.error).toBeNull();
      });
    });

    it('обрабатывает ошибки статуса Ollama', async () => {
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useOllamaStatus());
      
      await result.current.execute();
      
      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
        expect(result.current.loading).toBe(false);
      });
    });
  });

  describe('useAnalysisHistory', () => {
    it('успешно загружает историю анализов', async () => {
      const mockResponse = {
        history: [
          { id: 1, domain: 'example.com', date: '2024-01-01' }
        ]
      };

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const { result } = renderHook(() => useAnalysisHistory());
      
      await result.current.execute();
      
      await waitFor(() => {
        expect(result.current.data).toEqual(mockResponse.history);
        expect(result.current.loading).toBe(false);
        expect(result.current.error).toBeNull();
      });
    });

    it('загружает историю для конкретного домена', async () => {
      const mockResponse = {
        history: [
          { id: 1, domain: 'example.com', date: '2024-01-01' }
        ]
      };

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const { result } = renderHook(() => useAnalysisHistory('example.com'));
      
      await result.current.execute();
      
      await waitFor(() => {
        expect(result.current.data).toEqual(mockResponse.history);
        expect(global.fetch).toHaveBeenCalledWith('/api/v1/analysis_history?domain=example.com');
      });
    });
  });

  describe('useBenchmarkHistory', () => {
    it('успешно загружает историю бенчмарков', async () => {
      const mockResponse = {
        benchmarks: [
          { id: 1, name: 'SEO Benchmark', score: 90 }
        ]
      };

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const { result } = renderHook(() => useBenchmarkHistory());
      
      await result.current.execute();
      
      await waitFor(() => {
        expect(result.current.data).toEqual(mockResponse.benchmarks);
        expect(result.current.loading).toBe(false);
        expect(result.current.error).toBeNull();
      });
    });
  });

  describe('Общие функции хуков', () => {
    it('показывает состояние загрузки', async () => {
      (global.fetch as any).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: async () => ({ domains: [] })
        }), 100))
      );

      const { result } = renderHook(() => useDomains());
      
      result.current.execute();
      
      expect(result.current.loading).toBe(true);
      expect(result.current.state).toBe('loading');
    });

    it('сбрасывает состояние', async () => {
      const mockResponse = { domains: [] };

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const { result } = renderHook(() => useDomains());
      
      await result.current.execute();
      
      result.current.reset();
      
      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.state).toBe('idle');
    });
  });
}); 