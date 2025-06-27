import '@testing-library/jest-dom';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { OllamaStatus } from '../OllamaStatus';
import { OllamaStatus as OllamaStatusType } from '../../types';

describe('OllamaStatus Component', () => {
  const user = userEvent.setup();

  const mockStatus: OllamaStatusType = {
    status: 'available',
    connection: 'connected',
    models_count: 2,
    available_models: ['qwen2.5:7b-instruct', 'llama3.1:8b-instruct'],
    timestamp: new Date().toISOString(),
    ready_for_work: true,
    server_available: true,
    model_loaded: true,
    message: 'Готов к работе',
    last_check: new Date().toISOString()
  };

  const mockUnavailableStatus: OllamaStatusType = {
    status: 'unavailable',
    connection: 'disconnected',
    models_count: 0,
    available_models: [],
    timestamp: new Date().toISOString(),
    ready_for_work: false,
    server_available: false,
    model_loaded: false,
    message: 'Недоступен',
    last_check: new Date().toISOString()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('рендерит статус Ollama', () => {
    render(<OllamaStatus status={mockStatus} />);
    expect(screen.getByText(/Статус Ollama/i)).toBeInTheDocument();
  });

  it('показывает готовый к работе статус', () => {
    render(<OllamaStatus status={mockStatus} />);
    const statusMessage = screen.getByText(/Готов к работе/i, { selector: 'p' });
    expect(statusMessage).toBeInTheDocument();
  });

  it('отображает список моделей', () => {
    render(<OllamaStatus status={mockStatus} />);
    expect(screen.getByText(/qwen2\.5:7b-instruct/i)).toBeInTheDocument();
    expect(screen.getByText(/llama3\.1:8b-instruct/i)).toBeInTheDocument();
  });

  it('показывает недоступный статус', () => {
    render(<OllamaStatus status={mockUnavailableStatus} />);
    const statusMessage = screen.getByText(/Недоступен/i, { selector: 'p' });
    expect(statusMessage).toBeInTheDocument();
  });

  it('показывает статус сервера', () => {
    render(<OllamaStatus status={mockStatus} />);
    expect(screen.getByText(/Доступен/i)).toBeInTheDocument();
  });

  it('показывает статус модели', () => {
    render(<OllamaStatus status={mockStatus} />);
    expect(screen.getByText(/Загружена/i)).toBeInTheDocument();
  });

  it('обрабатывает обновление статуса', async () => {
    const mockOnRefresh = vi.fn();
    render(<OllamaStatus status={mockStatus} onRefresh={mockOnRefresh} />);
    
    const refreshButton = screen.getByRole('button', { name: /обновить статус/i });
    await user.click(refreshButton);
    
    expect(mockOnRefresh).toHaveBeenCalledTimes(1);
  });

  it('показывает рекомендации когда недоступен', () => {
    render(<OllamaStatus status={mockUnavailableStatus} />);
    
    expect(screen.getByText(/Рекомендации:/i)).toBeInTheDocument();
    expect(screen.getByText(/Проверьте, что Ollama запущена/i)).toBeInTheDocument();
  });

  it('показывает время последней проверки', () => {
    render(<OllamaStatus status={mockStatus} />);
    expect(screen.getByText(/Последняя проверка:/i)).toBeInTheDocument();
  });

  it('применяет правильные CSS классы для статуса', () => {
    render(<OllamaStatus status={mockStatus} />);
    
    const statusMessage = screen.getByText(/Готов к работе/i, { selector: 'p' });
    expect(statusMessage).toHaveClass('text-green-600');
  });

  it('показывает количество доступных моделей', () => {
    render(<OllamaStatus status={mockStatus} />);
    
    expect(screen.getByText(/qwen2\.5:7b-instruct/i)).toBeInTheDocument();
    expect(screen.getByText(/llama3\.1:8b-instruct/i)).toBeInTheDocument();
  });

  it('показывает индикатор активности когда готов к работе', () => {
    render(<OllamaStatus status={mockStatus} />);
    expect(screen.getByText(/Активен/i)).toBeInTheDocument();
  });

  it('применяет дополнительные CSS классы', () => {
    render(<OllamaStatus status={mockStatus} className="custom-class" />);
    const card = screen.getByText(/Статус Ollama/i).closest('.custom-class');
    expect(card).toBeInTheDocument();
  });

  it('показывает правильные иконки для разных статусов', () => {
    const { rerender } = render(<OllamaStatus status={mockStatus} />);
    
    const statusMessage = screen.getByText(/Готов к работе/i, { selector: 'p' });
    expect(statusMessage).toBeInTheDocument();
    
    rerender(<OllamaStatus status={mockUnavailableStatus} />);
    const unavailableMessage = screen.getByText(/Недоступен/i, { selector: 'p' });
    expect(unavailableMessage).toBeInTheDocument();
  });

  it('показывает сообщение статуса', () => {
    render(<OllamaStatus status={mockStatus} />);
    const statusMessage = screen.getByText(/Готов к работе/i, { selector: 'p' });
    expect(statusMessage).toBeInTheDocument();
  });

  it('показывает подключающийся статус', () => {
    const connectingStatus: OllamaStatusType = {
      ...mockUnavailableStatus,
      server_available: true,
      model_loaded: false,
      message: 'Подключается'
    };
    
    render(<OllamaStatus status={connectingStatus} />);
    const statusMessage = screen.getByText(/Подключается/i, { selector: 'p' });
    expect(statusMessage).toBeInTheDocument();
  });

  it('скрывает кнопку обновления когда готов к работе', () => {
    render(<OllamaStatus status={mockStatus} onRefresh={() => {}} />);
    
    const refreshButton = screen.getByRole('button', { name: /обновить статус/i });
    expect(refreshButton).toBeDisabled();
  });

  it('показывает анимацию на кнопке обновления', () => {
    render(<OllamaStatus status={mockStatus} onRefresh={() => {}} />);
    
    const refreshButton = screen.getByRole('button', { name: /обновить статус/i });
    const refreshIcon = refreshButton.querySelector('.animate-spin');
    expect(refreshIcon).toBeInTheDocument();
  });
}); 