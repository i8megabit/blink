import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DomainDetails from '../DomainDetails';

// Мокаем fetch
global.fetch = vi.fn();

describe('DomainDetails Component', () => {
  const user = userEvent.setup();
  const mockOnBack = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Мокаем успешный ответ API
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        posts: [
          {
            id: 1,
            title: 'Test Post 1',
            link: 'https://example.com/post1',
            content_type: 'article',
            difficulty_level: 'medium',
            linkability_score: 85,
            semantic_richness: 90,
            created_at: '2024-01-01T00:00:00Z',
            key_concepts: ['SEO', 'Marketing']
          },
          {
            id: 2,
            title: 'Test Post 2',
            link: 'https://example.com/post2',
            content_type: 'guide',
            difficulty_level: 'easy',
            linkability_score: 75,
            semantic_richness: 80,
            created_at: '2024-01-02T00:00:00Z',
            key_concepts: ['Content', 'Strategy']
          }
        ]
      })
    });
  });

  it('рендерится без ошибок', () => {
    render(<DomainDetails domain="example.com" onBack={mockOnBack} />);
    expect(screen.getByText(/Загрузка/i)).toBeInTheDocument();
  });

  it('отображает индикатор загрузки при загрузке данных', () => {
    render(<DomainDetails domain="example.com" onBack={mockOnBack} />);
    expect(screen.getByText(/Загрузка/i)).toBeInTheDocument();
  });

  it('отображает информацию о домене после загрузки', async () => {
    render(<DomainDetails domain="example.com" onBack={mockOnBack} />);
    
    await waitFor(() => {
      expect(screen.getByText('example.com')).toBeInTheDocument();
    });
  });

  it('отображает количество статей', async () => {
    render(<DomainDetails domain="example.com" onBack={mockOnBack} />);
    
    await waitFor(() => {
      expect(screen.getByText(/2 статей/i)).toBeInTheDocument();
    });
  });

  it('отображает вкладки', async () => {
    render(<DomainDetails domain="example.com" onBack={mockOnBack} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Обзор/i)).toBeInTheDocument();
      expect(screen.getByText(/Статьи/i)).toBeInTheDocument();
      expect(screen.getByText(/Аналитика/i)).toBeInTheDocument();
    });
  });

  it('переключается между вкладками', async () => {
    render(<DomainDetails domain="example.com" onBack={mockOnBack} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Обзор/i)).toBeInTheDocument();
    });

    await user.click(screen.getByText(/Статьи/i));
    expect(screen.getByText('Test Post 1')).toBeInTheDocument();
  });

  it('обрабатывает клик по кнопке "Назад"', async () => {
    render(<DomainDetails domain="example.com" onBack={mockOnBack} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Назад/i)).toBeInTheDocument();
    });

    await user.click(screen.getByText(/Назад/i));
    expect(mockOnBack).toHaveBeenCalledTimes(1);
  });

  it('обрабатывает ошибки загрузки', async () => {
    // Мокаем ошибку API
    (global.fetch as any).mockRejectedValue(new Error('Failed to load'));

    render(<DomainDetails domain="example.com" onBack={mockOnBack} />);
    
    await waitFor(() => {
      expect(screen.getByText('example.com')).toBeInTheDocument();
    });
  });

  it('отображает статистику в обзоре', async () => {
    render(<DomainDetails domain="example.com" onBack={mockOnBack} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Всего статей/i)).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  it('отображает статьи во вкладке "Статьи"', async () => {
    render(<DomainDetails domain="example.com" onBack={mockOnBack} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Статьи/i)).toBeInTheDocument();
    });

    await user.click(screen.getByText(/Статьи/i));
    
    expect(screen.getByText('Test Post 1')).toBeInTheDocument();
    expect(screen.getByText('Test Post 2')).toBeInTheDocument();
  });

  it('отображает типы контента', async () => {
    render(<DomainDetails domain="example.com" onBack={mockOnBack} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Статьи/i)).toBeInTheDocument();
    });

    await user.click(screen.getByText(/Статьи/i));
    
    expect(screen.getByText('📄')).toBeInTheDocument(); // article icon
    expect(screen.getByText('📖')).toBeInTheDocument(); // guide icon
  });

  it('отображает уровни сложности', async () => {
    render(<DomainDetails domain="example.com" onBack={mockOnBack} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Статьи/i)).toBeInTheDocument();
    });

    await user.click(screen.getByText(/Статьи/i));
    
    expect(screen.getByText('Средний')).toBeInTheDocument();
    expect(screen.getByText('Легкий')).toBeInTheDocument();
  });
}); 