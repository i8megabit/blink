import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useApi } from '../useApi';

describe('useApi Hook', () => {
  const mockApiFunction = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('инициализируется с правильными значениями по умолчанию', () => {
    const { result } = renderHook(() => useApi(mockApiFunction));

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.state).toBe('idle');
    expect(typeof result.current.execute).toBe('function');
    expect(typeof result.current.reset).toBe('function');
  });

  it('выполняет API запрос успешно', async () => {
    const mockData = { id: 1, name: 'test' };
    const mockResponse = { success: true, data: mockData };
    mockApiFunction.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useApi(mockApiFunction));

    await act(async () => {
      const response = await result.current.execute('test-arg');
      expect(response).toEqual(mockData);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.state).toBe('success');
    expect(mockApiFunction).toHaveBeenCalledWith('test-arg');
  });

  it('обрабатывает ошибки API', async () => {
    const mockError = 'API Error';
    const mockResponse = { success: false, error: mockError };
    mockApiFunction.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useApi(mockApiFunction));

    await act(async () => {
      const response = await result.current.execute();
      expect(response).toBeNull();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(mockError);
    expect(result.current.state).toBe('error');
  });

  it('обрабатывает исключения', async () => {
    const mockError = new Error('Network error');
    mockApiFunction.mockRejectedValue(mockError);

    const { result } = renderHook(() => useApi(mockApiFunction));

    await act(async () => {
      const response = await result.current.execute();
      expect(response).toBeNull();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe('Network error');
    expect(result.current.state).toBe('error');
  });

  it('вызывает onSuccess callback при успехе', async () => {
    const mockData = { id: 1, name: 'test' };
    const mockResponse = { success: true, data: mockData };
    const onSuccess = vi.fn();
    
    mockApiFunction.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => 
      useApi(mockApiFunction, { onSuccess })
    );

    await act(async () => {
      await result.current.execute();
    });

    expect(onSuccess).toHaveBeenCalledWith(mockData);
  });

  it('вызывает onError callback при ошибке', async () => {
    const mockError = 'API Error';
    const mockResponse = { success: false, error: mockError };
    const onError = vi.fn();
    
    mockApiFunction.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => 
      useApi(mockApiFunction, { onError })
    );

    await act(async () => {
      await result.current.execute();
    });

    expect(onError).toHaveBeenCalledWith(mockError);
  });

  it('вызывает onFinally callback', async () => {
    const mockData = { id: 1, name: 'test' };
    const mockResponse = { success: true, data: mockData };
    const onFinally = vi.fn();
    
    mockApiFunction.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => 
      useApi(mockApiFunction, { onFinally })
    );

    await act(async () => {
      await result.current.execute();
    });

    expect(onFinally).toHaveBeenCalled();
  });

  it('сбрасывает состояние при вызове reset', async () => {
    const mockData = { id: 1, name: 'test' };
    const mockResponse = { success: true, data: mockData };
    mockApiFunction.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useApi(mockApiFunction));

    // Сначала выполняем запрос
    await act(async () => {
      await result.current.execute();
    });

    // Проверяем, что данные загружены
    expect(result.current.data).toEqual(mockData);
    expect(result.current.state).toBe('success');

    // Сбрасываем состояние
    act(() => {
      result.current.reset();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.state).toBe('idle');
  });

  it('устанавливает loading состояние во время выполнения', async () => {
    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    
    mockApiFunction.mockReturnValue(promise);

    const { result } = renderHook(() => useApi(mockApiFunction));

    // Запускаем запрос
    act(() => {
      result.current.execute();
    });

    // Проверяем, что loading установлен
    expect(result.current.loading).toBe(true);
    expect(result.current.state).toBe('loading');

    // Завершаем запрос
    await act(async () => {
      resolvePromise!({ success: true, data: { test: 'data' } });
      await promise;
    });

    expect(result.current.loading).toBe(false);
  });
}); 