// @ts-nocheck
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useNotifications } from '../useNotifications.js';

describe('useNotifications Hook', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('инициализируется с пустым массивом уведомлений', () => {
    const { result } = renderHook(() => useNotifications());
    expect(result.current.notifications).toEqual([]);
    expect(typeof result.current.addNotification).toBe('function');
    expect(typeof result.current.removeNotification).toBe('function');
    expect(typeof result.current.clearAllNotifications).toBe('function');
    expect(typeof result.current.pauseNotification).toBe('function');
    expect(typeof result.current.resumeNotification).toBe('function');
  });

  it('добавляет уведомление', () => {
    const { result } = renderHook(() => useNotifications());
    act(() => {
      result.current.addNotification('success', 'Операция выполнена успешно');
    });
    expect(result.current.notifications).toHaveLength(1);
    expect(result.current.notifications[0]).toMatchObject({
      type: 'success',
      message: 'Операция выполнена успешно'
    });
    expect(typeof result.current.notifications[0]?.id).toBe('number');
    expect(result.current.notifications[0]?.timestamp).toBeInstanceOf(Date);
  });

  it('удаляет уведомление по ID', () => {
    const { result } = renderHook(() => useNotifications());
    let notificationId: number = 0;
    act(() => {
      result.current.addNotification('info', 'Тестовое сообщение');
      notificationId = result.current.notifications[0]?.id || 0;
    });
    expect(result.current.notifications).toHaveLength(1);
    act(() => {
      result.current.removeNotification(notificationId);
    });
    expect(result.current.notifications).toHaveLength(0);
  });

  it('очищает все уведомления', () => {
    const { result } = renderHook(() => useNotifications());
    act(() => {
      result.current.addNotification('success', 'Сообщение 1');
      result.current.addNotification('error', 'Сообщение 2');
    });
    expect(result.current.notifications).toHaveLength(2);
    act(() => {
      result.current.clearAllNotifications();
    });
    expect(result.current.notifications).toHaveLength(0);
  });

  it('автоматически удаляет уведомления через 15 секунд', () => {
    const { result } = renderHook(() => useNotifications());
    act(() => {
      result.current.addNotification('success', 'Временное уведомление');
    });
    expect(result.current.notifications).toHaveLength(1);
    act(() => {
      vi.advanceTimersByTime(15000);
    });
    expect(result.current.notifications).toHaveLength(0);
  });

  it('приостанавливает автоудаление уведомления', () => {
    const { result } = renderHook(() => useNotifications());
    let notificationId: number = 0;
    act(() => {
      result.current.addNotification('warning', 'Уведомление');
      notificationId = result.current.notifications[0]?.id || 0;
    });
    expect(result.current.notifications).toHaveLength(1);
    act(() => {
      result.current.pauseNotification(notificationId);
    });
    act(() => {
      vi.advanceTimersByTime(20000);
    });
    expect(result.current.notifications).toHaveLength(1);
  });

  it('возобновляет автоудаление уведомления', () => {
    const { result } = renderHook(() => useNotifications());
    let notificationId: number = 0;
    act(() => {
      result.current.addNotification('info', 'Уведомление');
      notificationId = result.current.notifications[0]?.id || 0;
    });
    act(() => {
      result.current.pauseNotification(notificationId);
      result.current.resumeNotification(notificationId);
    });
    act(() => {
      vi.advanceTimersByTime(10000);
    });
    expect(result.current.notifications).toHaveLength(0);
  });

  it('показывает детали уведомления', () => {
    const { result } = renderHook(() => useNotifications());
    act(() => {
      result.current.addNotification('error', 'Ошибка', 'Детали ошибки');
    });
    const notification = result.current.notifications[0];
    expect(notification).toBeDefined();
    act(() => {
      result.current.showNotificationDetails(notification);
    });
    expect(result.current.selectedNotification).toEqual(notification);
  });

  it('скрывает детали уведомления', () => {
    const { result } = renderHook(() => useNotifications());
    act(() => {
      result.current.addNotification('info', 'Информация');
      result.current.showNotificationDetails(result.current.notifications[0]);
    });
    expect(result.current.selectedNotification).toBeDefined();
    act(() => {
      result.current.hideNotificationDetails();
    });
    expect(result.current.selectedNotification).toBeNull();
  });

  it('фильтрует уведомления по типу', () => {
    const { result } = renderHook(() => useNotifications());
    act(() => {
      result.current.addNotification('success', 'Успех');
      result.current.addNotification('error', 'Ошибка');
      result.current.addNotification('success', 'Еще успех');
    });
    const successNotifications = result.current.getNotificationsByType('success');
    expect(successNotifications).toHaveLength(2);
    const errorNotifications = result.current.getNotificationsByType('error');
    expect(errorNotifications).toHaveLength(1);
  });

  it('показывает количество уведомлений', () => {
    const { result } = renderHook(() => useNotifications());
    expect(result.current.notificationsCount).toBe(0);
    expect(result.current.hasNotifications).toBe(false);
    act(() => {
      result.current.addNotification('info', 'Уведомление 1');
      result.current.addNotification('warning', 'Уведомление 2');
    });
    expect(result.current.notificationsCount).toBe(2);
    expect(result.current.hasNotifications).toBe(true);
  });
  
  it('генерирует уникальные ID для уведомлений', () => {
    const { result } = renderHook(() => useNotifications());
    act(() => {
      result.current.addNotification('info', 'Уведомление 1');
      result.current.addNotification('info', 'Уведомление 2');
    });
    const ids = result.current.notifications.map((n: any) => n.id);
    expect(ids[0]).not.toBe(ids[1]);
    expect(typeof ids[0]).toBe('number');
    expect(typeof ids[1]).toBe('number');
  });
  
  it('очищает все timeouts при clearAllNotifications', () => {
    const { result } = renderHook(() => useNotifications());
    act(() => {
      result.current.addNotification('success', 'Уведомление 1');
      result.current.addNotification('error', 'Уведомление 2');
    });
    expect(result.current.notifications).toHaveLength(2);
    act(() => {
      result.current.clearAllNotifications();
    });
    expect(result.current.notifications).toHaveLength(0);
    act(() => {
      vi.advanceTimersByTime(20000);
    });
    expect(result.current.notifications).toHaveLength(0);
  });
}); 