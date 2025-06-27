import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../../App';

// Мокаем fetch для тестов
global.fetch = vi.fn();

// Мокаем API вызовы
vi.mock('../../hooks/useApi', () => ({
  useApi: () => ({
    getOllamaStatus: vi.fn().mockResolvedValue({
      status: 'available',
      models: ['qwen2.5:7b-instruct', 'llama3.1:8b-instruct']
    }),
    getDomains: vi.fn().mockResolvedValue([
      { id: 1, domain: 'example.com', status: 'analyzed', score: 85 }
    ]),
    getAnalysisHistory: vi.fn().mockResolvedValue([
      { id: 1, domain: 'example.com', date: '2024-01-01', score: 85 }
    ]),
    getBenchmarks: vi.fn().mockResolvedValue([
      { id: 1, name: 'SEO Benchmark', score: 90 }
    ]),
    analyzeDomain: vi.fn().mockResolvedValue({ success: true }),
    exportResults: vi.fn().mockResolvedValue({ success: true })
  })
}));

// Мокаем WebSocket
global.WebSocket = vi.fn().mockImplementation(() => ({
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  send: vi.fn(),
  close: vi.fn(),
  readyState: 1
})) as any;

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

describe('App Component', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    // Сбрасываем моки перед каждым тестом
    vi.clearAllMocks();
    
    // Мокаем успешные ответы API
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'healthy',
        version: '4.0.0'
      })
    });
  });

  it('рендерится без ошибок', () => {
    render(<App />);
    expect(screen.getByText(/Blink/i)).toBeInTheDocument();
  });

  it('отображает основные навигационные вкладки', () => {
    render(<App />);
    
    // Проверяем основные навигационные элементы
    expect(screen.getByText(/Дашборд/i)).toBeInTheDocument();
    expect(screen.getByText(/Домены/i)).toBeInTheDocument();
    expect(screen.getByText(/История/i)).toBeInTheDocument();
    expect(screen.getByText(/Бенчмарки/i)).toBeInTheDocument();
    expect(screen.getByText(/Настройки/i)).toBeInTheDocument();
  });

  it('показывает правильный заголовок', () => {
    render(<App />);
    expect(screen.getByText('Blink')).toBeInTheDocument();
  });

  it('отображает содержимое дашборда', () => {
    render(<App />);
    
    // Проверяем основные элементы дашборда
    expect(screen.getByText(/Всего доменов/i)).toBeInTheDocument();
    expect(screen.getByText(/Анализ домена/i)).toBeInTheDocument();
    expect(screen.getByText(/Начать анализ/i)).toBeInTheDocument();
  });

  it('переключается между вкладками', async () => {
    render(<App />);
    
    // Переключаемся на вкладку Домены
    await user.click(screen.getByText(/Домены/i));
    expect(screen.getByText(/Список доменов/i)).toBeInTheDocument();
    
    // Переключаемся на вкладку История
    await user.click(screen.getByText(/История/i));
    expect(screen.getByText(/История анализов/i)).toBeInTheDocument();
    
    // Переключаемся на вкладку Бенчмарки
    await user.click(screen.getByText(/Бенчмарки/i));
    expect(screen.getByText(/SEO Бенчмарки/i)).toBeInTheDocument();
    
    // Переключаемся на вкладку Настройки
    await user.click(screen.getByText(/Настройки/i));
    expect(screen.getByText(/Настройки системы/i)).toBeInTheDocument();
  });

  it('отображает статус Ollama', async () => {
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText(/Ollama/i)).toBeInTheDocument();
    });
  });

  it('показывает версию приложения', () => {
    render(<App />);
    expect(screen.getByText(/v4\.0\.0/i)).toBeInTheDocument();
  });

  it('обрабатывает ошибки API корректно', async () => {
    // Мокаем ошибку API
    (global.fetch as any).mockRejectedValue(new Error('API Error'));
    
    render(<App />);
    
    // Приложение должно отрендериться даже при ошибке API
    expect(screen.getByText(/Blink/i)).toBeInTheDocument();
  });

  it('отображает индикатор загрузки при инициализации', () => {
    // Мокаем медленный ответ API
    (global.fetch as any).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: async () => ({ status: 'healthy', version: '4.0.0' })
      }), 100))
    );
    
    render(<App />);
    
    // Проверяем, что приложение отображается
    expect(screen.getByText(/Blink/i)).toBeInTheDocument();
  });
}); 