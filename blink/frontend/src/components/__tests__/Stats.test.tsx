import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Stats } from '../Stats';

describe('Stats Component', () => {
  const mockDomain = {
    id: 1,
    domain: 'example.com',
    total_posts: 25,
    is_indexed: true,
    language: 'ru',
    last_analysis_at: '2024-01-01T00:00:00Z'
  };

  const mockAnalysisHistory = [
    {
      id: 1,
      domain: 'example.com',
      posts_analyzed: 20,
      connections_found: 150,
      recommendations_generated: 85,
      processing_time_seconds: 45.5,
      llm_model_used: 'qwen2.5:7b-instruct',
      created_at: '2024-01-01T00:00:00Z'
    }
  ];

  it('рендерится без ошибок', () => {
    render(<Stats domain={mockDomain} analysisHistory={mockAnalysisHistory} />);
    expect(screen.getByText(/Всего постов/i)).toBeInTheDocument();
  });

  it('отображает общее количество постов', () => {
    render(<Stats domain={mockDomain} analysisHistory={mockAnalysisHistory} />);
    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText(/Всего постов/i)).toBeInTheDocument();
  });

  it('отображает количество анализов', () => {
    render(<Stats domain={mockDomain} analysisHistory={mockAnalysisHistory} />);
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText(/Анализов/i)).toBeInTheDocument();
  });

  it('отображает количество найденных связей', () => {
    render(<Stats domain={mockDomain} analysisHistory={mockAnalysisHistory} />);
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText(/Связей найдено/i)).toBeInTheDocument();
  });

  it('отображает количество рекомендаций', () => {
    render(<Stats domain={mockDomain} analysisHistory={mockAnalysisHistory} />);
    expect(screen.getByText('85')).toBeInTheDocument();
    expect(screen.getByText(/Рекомендаций/i)).toBeInTheDocument();
  });

  it('отображает статус индексации домена', () => {
    render(<Stats domain={mockDomain} analysisHistory={mockAnalysisHistory} />);
    expect(screen.getByText(/Индексирован/i)).toBeInTheDocument();
  });

  it('отображает язык домена', () => {
    render(<Stats domain={mockDomain} analysisHistory={mockAnalysisHistory} />);
    expect(screen.getByText(/Язык: ru/i)).toBeInTheDocument();
  });

  it('отображает информацию о последнем анализе', () => {
    render(<Stats domain={mockDomain} analysisHistory={mockAnalysisHistory} />);
    expect(screen.getByText(/Последний анализ/i)).toBeInTheDocument();
  });

  it('отображает время обработки', () => {
    render(<Stats domain={mockDomain} analysisHistory={mockAnalysisHistory} />);
    expect(screen.getByText(/45.5с/i)).toBeInTheDocument();
  });

  it('отображает модель ИИ', () => {
    render(<Stats domain={mockDomain} analysisHistory={mockAnalysisHistory} />);
    expect(screen.getByText(/qwen2.5:7b-instruct/i)).toBeInTheDocument();
  });

  it('работает без домена', () => {
    render(<Stats analysisHistory={mockAnalysisHistory} />);
    expect(screen.getByText(/Анализов/i)).toBeInTheDocument();
  });

  it('работает без истории анализов', () => {
    render(<Stats domain={mockDomain} />);
    expect(screen.getByText(/Всего постов/i)).toBeInTheDocument();
  });

  it('работает с пустыми данными', () => {
    render(<Stats />);
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('отображает все карточки статистики', () => {
    render(<Stats domain={mockDomain} analysisHistory={mockAnalysisHistory} />);
    
    // Проверяем, что все 4 основные карточки отображаются
    expect(screen.getByText(/Всего постов/i)).toBeInTheDocument();
    expect(screen.getByText(/Анализов/i)).toBeInTheDocument();
    expect(screen.getByText(/Связей найдено/i)).toBeInTheDocument();
    expect(screen.getByText(/Рекомендаций/i)).toBeInTheDocument();
  });
}); 