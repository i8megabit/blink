import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import VersionDisplay from '../VersionDisplay';

// Мокаем fetch
global.fetch = vi.fn();

describe('VersionDisplay Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Мокаем неуспешный ответ API, чтобы использовались значения по умолчанию
    (global.fetch as any).mockRejectedValue(new Error('Network error'));
  });

  it('рендерится без ошибок', () => {
    render(<VersionDisplay />);
    expect(screen.getByText(/v3\.0\.17/i)).toBeInTheDocument();
  });

  it('отображает версию приложения', () => {
    render(<VersionDisplay />);
    expect(screen.getByText(/3\.0\.17/i)).toBeInTheDocument();
  });

  it('имеет правильные стили', () => {
    render(<VersionDisplay />);
    const versionElement = screen.getByText(/v3\.0\.17/i);
    expect(versionElement).toHaveClass('font-mono');
  });

  it('отображается как span элемент', () => {
    render(<VersionDisplay />);
    const versionElement = screen.getByText(/v3\.0\.17/i);
    expect(versionElement.tagName).toBe('SPAN');
  });

  it('отображает дату сборки', () => {
    render(<VersionDisplay />);
    const today = new Date().toISOString().split('T')[0];
    expect(screen.getByText(String(today))).toBeInTheDocument();
  });

  it('отображает разделитель', () => {
    render(<VersionDisplay />);
    expect(screen.getByText('•')).toBeInTheDocument();
  });

  it('загружает версию из API при успешном ответе', async () => {
    // Мокаем успешный ответ API
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        version: '4.1.1',
        buildDate: '2024-01-01',
        commitHash: 'abc1234'
      })
    });

    render(<VersionDisplay />);
    
    // Ждем, пока версия обновится
    await screen.findByText(/v4\.0\.0/i);
    expect(screen.getByText('2024-01-01')).toBeInTheDocument();
  });

  it('использует значения по умолчанию при ошибке API', () => {
    render(<VersionDisplay />);
    expect(screen.getByText(/v3\.0\.17/i)).toBeInTheDocument();
  });
});