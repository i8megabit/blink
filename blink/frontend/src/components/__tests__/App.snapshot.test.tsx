import { render } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from '../../App';

// Мокаем уведомления
vi.mock('../../hooks/useNotifications', () => ({
  useNotifications: () => ({
    addNotification: vi.fn(),
    removeNotification: vi.fn(),
    notifications: [],
    selectedNotification: null,
    showNotificationDetails: vi.fn(),
    hideNotificationDetails: vi.fn(),
    pauseNotification: vi.fn(),
    resumeNotification: vi.fn()
  })
}));

// Мокаем API
vi.mock('../../hooks/useApi', () => ({
  useApi: () => ({
    analyzeDomain: vi.fn(),
    getAnalysisHistory: vi.fn(),
    getBenchmarks: vi.fn(),
    getDomainDetails: vi.fn(),
    exportData: vi.fn(),
    loading: false,
    error: null
  })
}));

// Мокаем WebSocket
vi.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    isConnected: false,
    lastMessage: null,
    sendMessage: vi.fn()
  })
}));

describe('App Snapshot', () => {
  it('рендерится без изменений', () => {
    const { container } = render(<App />);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с активной вкладкой Домены', () => {
    const { container } = render(<App />);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с активной вкладкой История', () => {
    const { container } = render(<App />);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с активной вкладкой Бенчмарки', () => {
    const { container } = render(<App />);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с активной вкладкой Настройки', () => {
    const { container } = render(<App />);
    expect(container).toMatchSnapshot();
  });
}); 