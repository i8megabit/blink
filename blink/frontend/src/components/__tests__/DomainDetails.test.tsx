import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DomainDetails from '../DomainDetails';

// Мокаем API вызовы
vi.mock('../../hooks/useApi', () => ({
  useApi: () => ({
    getDomainDetails: vi.fn().mockResolvedValue({
      domain: 'example.com',
      score: 85,
      status: 'analyzed',
      seo_score: 90,
      performance_score: 80,
      accessibility_score: 85,
      best_practices_score: 88,
      recommendations: [
        { type: 'error', message: 'Missing meta description', priority: 'high' },
        { type: 'warning', message: 'Slow loading time', priority: 'medium' }
      ],
      links: [
        { url: 'https://example.com/page1', text: 'Page 1', status: 'active' },
        { url: 'https://example.com/page2', text: 'Page 2', status: 'broken' }
      ]
    })
  })
}));

describe('DomainDetails Component', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('рендерится без ошибок', () => {
    render(<DomainDetails domainId="1" />);
    expect(screen.getByText(/Детали домена/i)).toBeInTheDocument();
  });

  it('отображает индикатор загрузки при загрузке данных', () => {
    render(<DomainDetails domainId="1" />);
    expect(screen.getByText(/Загрузка/i)).toBeInTheDocument();
  });

  it('отображает информацию о домене после загрузки', async () => {
    render(<DomainDetails domainId="1" />);
    
    await waitFor(() => {
      expect(screen.getByText('example.com')).toBeInTheDocument();
    });
  });

  it('отображает SEO метрики', async () => {
    render(<DomainDetails domainId="1" />);
    
    await waitFor(() => {
      expect(screen.getByText(/SEO Score/i)).toBeInTheDocument();
      expect(screen.getByText('90')).toBeInTheDocument();
    });
  });

  it('отображает рекомендации', async () => {
    render(<DomainDetails domainId="1" />);
    
    await waitFor(() => {
      expect(screen.getByText(/Рекомендации/i)).toBeInTheDocument();
      expect(screen.getByText(/Missing meta description/i)).toBeInTheDocument();
    });
  });

  it('отображает ссылки', async () => {
    render(<DomainDetails domainId="1" />);
    
    await waitFor(() => {
      expect(screen.getByText(/Ссылки/i)).toBeInTheDocument();
      expect(screen.getByText('Page 1')).toBeInTheDocument();
    });
  });

  it('обрабатывает ошибки загрузки', async () => {
    // Мокаем ошибку API
    vi.mocked(require('../../hooks/useApi').useApi).mockReturnValue({
      getDomainDetails: vi.fn().mockRejectedValue(new Error('Failed to load'))
    });

    render(<DomainDetails domainId="1" />);
    
    await waitFor(() => {
      expect(screen.getByText(/Ошибка загрузки/i)).toBeInTheDocument();
    });
  });

  it('показывает кнопку обновления', async () => {
    render(<DomainDetails domainId="1" />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Обновить/i })).toBeInTheDocument();
    });
  });

  it('обрабатывает клик по кнопке обновления', async () => {
    const mockGetDomainDetails = vi.fn().mockResolvedValue({
      domain: 'example.com',
      score: 85
    });

    vi.mocked(require('../../hooks/useApi').useApi).mockReturnValue({
      getDomainDetails: mockGetDomainDetails
    });

    render(<DomainDetails domainId="1" />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Обновить/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /Обновить/i }));
    
    expect(mockGetDomainDetails).toHaveBeenCalledTimes(2); // Первоначальная загрузка + обновление
  });

  it('отображает статус домена', async () => {
    render(<DomainDetails domainId="1" />);
    
    await waitFor(() => {
      expect(screen.getByText(/Статус/i)).toBeInTheDocument();
      expect(screen.getByText(/analyzed/i)).toBeInTheDocument();
    });
  });

  it('отображает общий балл', async () => {
    render(<DomainDetails domainId="1" />);
    
    await waitFor(() => {
      expect(screen.getByText(/Общий балл/i)).toBeInTheDocument();
      expect(screen.getByText('85')).toBeInTheDocument();
    });
  });
}); 