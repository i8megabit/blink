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
    // Выбираем первый шаблон
    const templateButtons = screen.getAllByText('Системная архитектура');
    expect(templateButtons.length).toBeGreaterThan(0);
    fireEvent.click(templateButtons[0]);

    // Проверяем, что компоненты микросервисов загрузились
    const apiGatewayOptions = screen.getAllByText('API Gateway');
    expect(apiGatewayOptions.length).toBeGreaterThan(0);
    // Используем функцию-мэтчер для поиска 'User Service'
    const userServiceOptions = screen.getAllByText((content) => content.includes('User Service'));
    expect(userServiceOptions.length).toBeGreaterThan(0);
  });

  test('можно добавить компонент', () => {
    // Считаем количество полей до клика
    const beforeInputs = screen.getAllByPlaceholderText('Название компонента').length;
    // Находим первую активную кнопку "+ Добавить"
    const addButtons = screen.getAllByText('+ Добавить');
    const addButton = addButtons.find(btn => !btn.hasAttribute('disabled')) || addButtons[0];
    fireEvent.click(addButton);
    // Считаем количество полей после клика
    const afterInputs = screen.getAllByPlaceholderText('Название компонента').length;
    expect(afterInputs).toBeGreaterThan(beforeInputs);
  });

  test('можно изменить заголовок', () => {
    const titleInput = screen.getByPlaceholderText('Название диаграммы');
    fireEvent.change(titleInput, { target: { value: 'Моя архитектура' } });
    
    expect(titleInput).toHaveValue('Моя архитектура');
  });

  test('кнопка генерации активна при заполненных данных', () => {
    // Заполняем обязательные поля
    const titleInput = screen.getByPlaceholderText('Название диаграммы');
    fireEvent.change(titleInput, { target: { value: 'Test Diagram' } });

    // Выбираем шаблон
    const templateButtons = screen.getAllByText('Системная архитектура');
    fireEvent.click(templateButtons[0]);

    // Добавляем компонент
    const addButtons = screen.getAllByText('+ Добавить');
    const addButton = addButtons.find(btn => !btn.hasAttribute('disabled')) || addButtons[0];
    fireEvent.click(addButton);

    // Заполняем название компонента
    const componentInputs = screen.getAllByPlaceholderText('Название компонента');
    fireEvent.change(componentInputs[0], { target: { value: 'API Gateway' } });

    // Кнопка генерации должна быть активна
    const generateButton = screen.getByText('🎨 Сгенерировать диаграмму');
    expect(generateButton).not.toBeDisabled();
  });

  test('кнопка генерации неактивна при пустых данных', () => {
    const generateButton = screen.getByText('🎨 Сгенерировать диаграмму');
    expect(generateButton).toBeDisabled();
  });

  test('отображаются стили', () => {
    expect(screen.getAllByText('modern').length).toBeGreaterThan(0);
    expect(screen.getAllByText('minimal').length).toBeGreaterThan(0);
    expect(screen.getAllByText('corporate').length).toBeGreaterThan(0);
    expect(screen.getAllByText('tech').length).toBeGreaterThan(0);
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