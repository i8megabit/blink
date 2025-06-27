import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Stats } from '../Stats';

describe('Stats Component', () => {
  const mockDomain = {
    id: 1,
    name: 'example.com',
    display_name: 'Example Domain',
    language: 'ru',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    is_active: true,
    total_posts: 25,
    total_analyses: 5,
    last_analysis_at: '2024-01-01T00:00:00Z',
    is_indexed: true
  };

  const mockAnalysisHistory = [
    {
      id: 1,
      domain_id: 1,
      posts_analyzed: 20,
      connections_found: 150,
      recommendations_generated: 85,
      recommendations: [
        {
          anchor_text: 'SEO оптимизация',
          source_title: 'Как оптимизировать сайт',
          target_title: 'Основы SEO',
          reasoning: 'Семантическая связь',
          quality_score: 0.9
        }
      ],
      thematic_analysis: {
        main_themes: ['SEO', 'Marketing'],
        coherence_score: 0.85
      },
      semantic_metrics: {
        average_similarity: 0.75,
        concept_diversity: 0.8
      },
      quality_assessment: {
        overall_quality: 0.88,
        content_relevance: 0.92
      },
      llm_model_used: 'qwen2.5:7b-instruct',
      processing_time_seconds: 45.5,
      created_at: '2024-01-01T00:00:00Z',
      completed_at: '2024-01-01T00:01:00Z'
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
    expect(screen.getAllByText('150').length).toBeGreaterThan(0);
    expect(screen.getByText(/Связей найдено/i)).toBeInTheDocument();
  });

  it('отображает количество рекомендаций', () => {
    render(<Stats domain={mockDomain} analysisHistory={mockAnalysisHistory} />);
    expect(screen.getAllByText('85').length).toBeGreaterThan(0);
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
    expect(screen.getAllByText(/Последний анализ/i).length).toBeGreaterThan(0);
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
    expect(screen.getAllByText('0').length).toBeGreaterThan(0);
  });

  it('отображает все карточки статистики', () => {
    render(<Stats domain={mockDomain} analysisHistory={mockAnalysisHistory} />);
    
    // Проверяем, что все 4 основные карточки отображаются
    expect(screen.getByText(/Всего постов/i)).toBeInTheDocument();
    expect(screen.getByText(/Анализов/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Связей найдено/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Рекомендаций/i).length).toBeGreaterThan(0);
  });
}); 