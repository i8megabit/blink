import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DomainInput } from '../DomainInput';

// Мокаем API хук
vi.mock('../../hooks/useApi', () => ({
  useApi: () => ({
    analyzeDomain: vi.fn().mockResolvedValue({ success: true }),
    getOllamaStatus: vi.fn().mockResolvedValue({ status: 'available' })
  })
}));

// Мокаем уведомления
vi.mock('../../hooks/useNotifications', () => ({
  useNotifications: () => ({
    showNotification: vi.fn(),
    hideNotification: vi.fn(),
    notifications: []
  })
}));

describe('DomainInput Component', () => {
  const user = userEvent.setup();
  const mockOnAnalyze = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('рендерит форму ввода домена', () => {
    render(<DomainInput onAnalyze={mockOnAnalyze} />);
    expect(screen.getByText(/Анализ домена/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/example\.com/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /начать анализ/i })).toBeInTheDocument();
  });

  it('принимает ввод домена', async () => {
    render(<DomainInput onAnalyze={mockOnAnalyze} />);
    
    const input = screen.getByPlaceholderText(/example\.com/i);
    await user.type(input, 'example.com');
    
    expect(input).toHaveValue('example.com');
  });

  it('валидирует правильный формат домена', async () => {
    render(<DomainInput onAnalyze={mockOnAnalyze} />);
    
    const input = screen.getByPlaceholderText(/example\.com/i);
    const submitButton = screen.getByRole('button', { name: /начать анализ/i });
    
    await user.type(input, 'example.com');
    await user.click(submitButton);
    
    // Кнопка должна быть активна для правильного домена
    expect(mockOnAnalyze).toHaveBeenCalledWith('example.com', true);
  });

  it('показывает ошибку для неправильного формата домена', async () => {
    render(<DomainInput onAnalyze={mockOnAnalyze} />);
    
    const input = screen.getByPlaceholderText('example.com');
    
    // Сначала вводим валидный домен, чтобы кнопка стала активной
    await user.type(input, 'example.com');
    
    // Затем заменяем на невалидный с пробелами и специальными символами
    await user.clear(input);
    await user.type(input, 'invalid domain with spaces!');
    
    // Ошибка валидации появляется только при отправке формы
    const submitButton = screen.getByRole('button', { name: /начать анализ/i });
    await user.click(submitButton);
    
    // Должна появиться ошибка валидации
    expect(screen.getByText(/некорректный формат домена/i)).toBeInTheDocument();
  });

  it('показывает ошибку для пустого домена', async () => {
    render(<DomainInput onAnalyze={mockOnAnalyze} />);
    
    const submitButton = screen.getByRole('button', { name: /начать анализ/i });
    await user.click(submitButton);
    
    expect(screen.getByText(/введите домен/i)).toBeInTheDocument();
  });

  it('обрабатывает отправку формы', async () => {
    render(<DomainInput onAnalyze={mockOnAnalyze} />);
    
    const input = screen.getByPlaceholderText(/example\.com/i);
    const submitButton = screen.getByRole('button', { name: /начать анализ/i });
    
    await user.type(input, 'example.com');
    await user.click(submitButton);
    
    expect(mockOnAnalyze).toHaveBeenCalledWith('example.com', true);
  });

  it('показывает состояние загрузки', () => {
    render(<DomainInput onAnalyze={mockOnAnalyze} isLoading={true} />);
    
    const submitButton = screen.getByRole('button', { name: /анализирую/i });
    expect(submitButton).toBeDisabled();
    expect(submitButton).toHaveTextContent(/анализирую/i);
  });

  it('переключает режим анализа', async () => {
    render(<DomainInput onAnalyze={mockOnAnalyze} />);
    
    const checkbox = screen.getByRole('checkbox');
    await user.click(checkbox);
    
    const input = screen.getByPlaceholderText(/example\.com/i);
    const submitButton = screen.getByRole('button', { name: /начать анализ/i });
    
    await user.type(input, 'example.com');
    await user.click(submitButton);
    
    expect(mockOnAnalyze).toHaveBeenCalledWith('example.com', false);
  });

  it('обрабатывает быстрый анализ', async () => {
    render(<DomainInput onAnalyze={mockOnAnalyze} />);
    
    const quickButton = screen.getByRole('button', { name: /example\.com/i });
    await user.click(quickButton);
    
    expect(mockOnAnalyze).toHaveBeenCalledWith('example.com', true);
  });

  it('поддерживает ввод через Enter', async () => {
    render(<DomainInput onAnalyze={mockOnAnalyze} />);
    
    const input = screen.getByPlaceholderText(/example\.com/i);
    await user.type(input, 'example.com');
    await user.keyboard('{Enter}');
    
    expect(mockOnAnalyze).toHaveBeenCalledWith('example.com', true);
  });

  it('показывает подсказки для пользователя', () => {
    render(<DomainInput onAnalyze={mockOnAnalyze} />);
    
    expect(screen.getByText(/введите домен без http:\/\/ или https:\/\//i)).toBeInTheDocument();
    // Используем getAllByText для элементов с одинаковым текстом
    expect(screen.getAllByText(/полный анализ/i)).toHaveLength(2);
    expect(screen.getByText(/базовый анализ/i)).toBeInTheDocument();
  });

  it('отображает информацию о режимах анализа', () => {
    render(<DomainInput onAnalyze={mockOnAnalyze} />);
    
    expect(screen.getByText(/семантический анализ, кластеризация, кумулятивные рекомендации/i)).toBeInTheDocument();
    expect(screen.getByText(/простая индексация и генерация ссылок/i)).toBeInTheDocument();
  });
}); 