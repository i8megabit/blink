import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../../App';

// Мокаем fetch для тестов
global.fetch = vi.fn();

// Мокаем API вызовы
vi.mock('../../hooks/useApi', () => ({
  useApi: () => ({
    getOllamaStatus: vi.fn().mockResolvedValue({
      status: 'available',
      models: ['qwen2.5:7b-instruct']
    }),
    getDomains: vi.fn().mockResolvedValue([]),
    getAnalysisHistory: vi.fn().mockResolvedValue([]),
    getBenchmarks: vi.fn().mockResolvedValue([])
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

describe('App Component', () => {
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

  it('renders without crashing', () => {
    render(<App />);
    expect(screen.getByText(/Blink/i)).toBeInTheDocument();
  });

  it('displays main navigation tabs', () => {
    render(<App />);
    
    // Проверяем основные навигационные элементы
    expect(screen.getByText(/Дашборд/i)).toBeInTheDocument();
    expect(screen.getByText(/Домены/i)).toBeInTheDocument();
    expect(screen.getByText(/История/i)).toBeInTheDocument();
    expect(screen.getByText(/Бенчмарки/i)).toBeInTheDocument();
    expect(screen.getByText(/Настройки/i)).toBeInTheDocument();
  });

  it('shows correct title', () => {
    render(<App />);
    expect(screen.getByText('Blink')).toBeInTheDocument();
  });

  it('displays dashboard content', () => {
    render(<App />);
    
    // Проверяем основные элементы дашборда
    expect(screen.getByText(/Всего доменов/i)).toBeInTheDocument();
    expect(screen.getByText(/Анализ домена/i)).toBeInTheDocument();
    expect(screen.getByText(/Начать анализ/i)).toBeInTheDocument();
  });
}); 