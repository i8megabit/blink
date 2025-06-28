import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import ArchGen from '../ArchGen';

// Мокаем хуки
vi.mock('../../hooks/useApi', () => ({
  useApi: () => ({
    api: {
      post: vi.fn().mockResolvedValue({
        data: {
          diagram_id: 1,
          svg_content: '<svg>test</svg>',
          quality_score: 0.85,
          generation_time: 2.5,
          model_used: 'qwen2.5:7b',
          confidence_score: 0.9,
          validation_result: {}
        }
      })
    }
  })
}));

vi.mock('../../hooks/useNotifications', () => ({
  useNotifications: () => ({
    showNotification: vi.fn()
  })
}));

vi.mock('../../hooks/useTheme', () => ({
  useTheme: () => ({
    theme: 'light'
  })
}));

describe('ArchGen Component', () => {
  beforeEach(() => {
    render(<ArchGen />);
  });

  test('рендерится заголовок компонента', () => {
    expect(screen.getByText('ArchGen - Генератор архитектурных схем')).toBeInTheDocument();
  });

  test('отображаются шаблоны диаграмм', () => {
    expect(screen.getByText('Системная архитектура')).toBeInTheDocument();
    expect(screen.getByText('Микросервисы')).toBeInTheDocument();
    expect(screen.getByText('Поток данных')).toBeInTheDocument();
    expect(screen.getByText('Развертывание')).toBeInTheDocument();
  });

  test('можно выбрать шаблон', () => {
    const microservicesButton = screen.getByText('Микросервисы').closest('button');
    fireEvent.click(microservicesButton!);
    
    // Проверяем, что компоненты микросервисов загрузились
    expect(screen.getByText('API Gateway')).toBeInTheDocument();
    expect(screen.getByText('User Service')).toBeInTheDocument();
  });

  test('можно добавить компонент', () => {
    const addButton = screen.getByText('+ Добавить');
    fireEvent.click(addButton);
    
    // Проверяем, что появился новый компонент
    expect(screen.getByDisplayValue('Новый компонент')).toBeInTheDocument();
  });

  test('можно изменить заголовок', () => {
    const titleInput = screen.getByPlaceholderText('Название диаграммы');
    fireEvent.change(titleInput, { target: { value: 'Моя архитектура' } });
    
    expect(titleInput).toHaveValue('Моя архитектура');
  });

  test('кнопка генерации активна при заполненных данных', () => {
    const titleInput = screen.getByPlaceholderText('Название диаграммы');
    fireEvent.change(titleInput, { target: { value: 'Тестовая диаграмма' } });
    
    const generateButton = screen.getByText('🎨 Сгенерировать диаграмму');
    expect(generateButton).not.toBeDisabled();
  });

  test('кнопка генерации неактивна при пустых данных', () => {
    const generateButton = screen.getByText('🎨 Сгенерировать диаграмму');
    expect(generateButton).toBeDisabled();
  });

  test('отображаются стили', () => {
    expect(screen.getByText('modern')).toBeInTheDocument();
    expect(screen.getByText('minimal')).toBeInTheDocument();
    expect(screen.getByText('corporate')).toBeInTheDocument();
    expect(screen.getByText('tech')).toBeInTheDocument();
  });

  test('можно изменить размеры', () => {
    const widthInput = screen.getByDisplayValue('800');
    const heightInput = screen.getByDisplayValue('600');
    
    fireEvent.change(widthInput, { target: { value: '1000' } });
    fireEvent.change(heightInput, { target: { value: '800' } });
    
    expect(widthInput).toHaveValue(1000);
    expect(heightInput).toHaveValue(800);
  });

  test('отображается статистика', () => {
    expect(screen.getByText('Компонентов:')).toBeInTheDocument();
    expect(screen.getByText('Связей:')).toBeInTheDocument();
    expect(screen.getByText('Размер:')).toBeInTheDocument();
    expect(screen.getByText('Стиль:')).toBeInTheDocument();
  });
}); 