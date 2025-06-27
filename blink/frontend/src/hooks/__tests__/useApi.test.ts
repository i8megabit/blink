import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useApi } from '../useApi';

// Мокаем fetch
global.fetch = vi.fn();

describe('useApi Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('возвращает функции API', () => {
    const { result } = renderHook(() => useApi());
    
    expect(result.current.getOllamaStatus).toBeDefined();
    expect(result.current.getDomains).toBeDefined();
    expect(result.current.getAnalysisHistory).toBeDefined();
    expect(result.current.getBenchmarks).toBeDefined();
    expect(result.current.analyzeDomain).toBeDefined();
    expect(result.current.exportResults).toBeDefined();
  });

  describe('getOllamaStatus', () => {
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

      const { result } = renderHook(() => useApi());
      
      const response = await result.current.getOllamaStatus();
      
      expect(response).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith('/api/ollama/status');
    });

    it('обрабатывает ошибки API', async () => {
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useApi());
      
      await expect(result.current.getOllamaStatus()).rejects.toThrow('Network error');
    });

    it('обрабатывает HTTP ошибки', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      const { result } = renderHook(() => useApi());
      
      await expect(result.current.getOllamaStatus()).rejects.toThrow('HTTP error! status: 500');
    });
  });

  describe('getDomains', () => {
    it('успешно получает список доменов', async () => {
      const mockResponse = [
        { id: 1, name: 'example.com', status: 'analyzed' }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const { result } = renderHook(() => useApi());
      
      const response = await result.current.getDomains();
      
      expect(response).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith('/api/domains');
    });
  });

  describe('getAnalysisHistory', () => {
    it('успешно получает историю анализов', async () => {
      const mockResponse = [
        { id: 1, domain: 'example.com', date: '2024-01-01' }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const { result } = renderHook(() => useApi());
      
      const response = await result.current.getAnalysisHistory();
      
      expect(response).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith('/api/analysis/history');
    });
  });

  describe('getBenchmarks', () => {
    it('успешно получает бенчмарки', async () => {
      const mockResponse = [
        { id: 1, name: 'SEO Benchmark', score: 90 }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const { result } = renderHook(() => useApi());
      
      const response = await result.current.getBenchmarks();
      
      expect(response).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith('/api/benchmarks');
    });
  });

  describe('analyzeDomain', () => {
    it('успешно анализирует домен', async () => {
      const mockResponse = {
        success: true,
        domain: 'example.com',
        posts_found: 10
      };

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const { result } = renderHook(() => useApi());
      
      const response = await result.current.analyzeDomain('example.com');
      
      expect(response).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ domain: 'example.com' })
      });
    });

    it('отправляет comprehensive параметр', async () => {
      const mockResponse = { success: true };

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const { result } = renderHook(() => useApi());
      
      await result.current.analyzeDomain('example.com', true);
      
      expect(global.fetch).toHaveBeenCalledWith('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ domain: 'example.com', comprehensive: true })
      });
    });
  });

  describe('exportResults', () => {
    it('успешно экспортирует результаты', async () => {
      const mockResponse = {
        success: true,
        download_url: '/api/export/123'
      };

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const { result } = renderHook(() => useApi());
      
      const response = await result.current.exportResults('example.com');
      
      expect(response).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith('/api/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ domain: 'example.com' })
      });
    });
  });

  describe('Обработка ошибок', () => {
    it('обрабатывает JSON ошибки', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        }
      });

      const { result } = renderHook(() => useApi());
      
      await expect(result.current.getOllamaStatus()).rejects.toThrow('Invalid JSON');
    });

    it('обрабатывает таймауты', async () => {
      (global.fetch as any).mockImplementation(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Timeout')), 100)
        )
      );

      const { result } = renderHook(() => useApi());
      
      await expect(result.current.getOllamaStatus()).rejects.toThrow('Timeout');
    });
  });
}); 