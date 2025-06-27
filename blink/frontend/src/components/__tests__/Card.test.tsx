import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/Card';

describe('Card Components', () => {
  describe('Card', () => {
    it('рендерит card контейнер', () => {
      render(<Card>Card content</Card>);
      expect(screen.getByText('Card content')).toBeInTheDocument();
    });

    it('применяет правильные CSS классы', () => {
      render(<Card className="custom-class">Content</Card>);
      const card = screen.getByText('Content').closest('div');
      expect(card).toHaveClass('custom-class');
    });

    it('передает правильные атрибуты', () => {
      render(<Card data-testid="test-card">Content</Card>);
      expect(screen.getByTestId('test-card')).toBeInTheDocument();
    });
  });

  describe('CardHeader', () => {
    it('рендерит header секцию', () => {
      render(<CardHeader>Header content</CardHeader>);
      expect(screen.getByText('Header content')).toBeInTheDocument();
    });

    it('применяет правильные CSS классы', () => {
      render(<CardHeader className="custom-header">Header</CardHeader>);
      const header = screen.getByText('Header').closest('div');
      expect(header).toHaveClass('custom-header');
    });
  });

  describe('CardTitle', () => {
    it('рендерит заголовок', () => {
      render(<CardTitle>Card Title</CardTitle>);
      expect(screen.getByText('Card Title')).toBeInTheDocument();
    });

    it('использует правильный HTML тег', () => {
      render(<CardTitle>Title</CardTitle>);
      const title = screen.getByText('Title');
      expect(title.tagName).toBe('H3');
    });

    it('применяет правильные CSS классы', () => {
      render(<CardTitle className="custom-title">Title</CardTitle>);
      expect(screen.getByText('Title')).toHaveClass('custom-title');
    });
  });

  describe('CardDescription', () => {
    it('рендерит описание', () => {
      render(<CardDescription>Card description</CardDescription>);
      expect(screen.getByText('Card description')).toBeInTheDocument();
    });

    it('использует правильный HTML тег', () => {
      render(<CardDescription>Description</CardDescription>);
      const description = screen.getByText('Description');
      expect(description.tagName).toBe('P');
    });

    it('применяет правильные CSS классы', () => {
      render(<CardDescription className="custom-desc">Description</CardDescription>);
      expect(screen.getByText('Description')).toHaveClass('custom-desc');
    });
  });

  describe('CardContent', () => {
    it('рендерит содержимое', () => {
      render(<CardContent>Card content</CardContent>);
      expect(screen.getByText('Card content')).toBeInTheDocument();
    });

    it('применяет правильные CSS классы', () => {
      render(<CardContent className="custom-content">Content</CardContent>);
      const content = screen.getByText('Content').closest('div');
      expect(content).toHaveClass('custom-content');
    });
  });

  describe('CardFooter', () => {
    it('рендерит footer секцию', () => {
      render(<CardFooter>Footer content</CardFooter>);
      expect(screen.getByText('Footer content')).toBeInTheDocument();
    });

    it('применяет правильные CSS классы', () => {
      render(<CardFooter className="custom-footer">Footer</CardFooter>);
      const footer = screen.getByText('Footer').closest('div');
      expect(footer).toHaveClass('custom-footer');
    });
  });

  describe('Card Composition', () => {
    it('правильно композирует все части карточки', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Test Title</CardTitle>
            <CardDescription>Test Description</CardDescription>
          </CardHeader>
          <CardContent>Test Content</CardContent>
          <CardFooter>Test Footer</CardFooter>
        </Card>
      );

      expect(screen.getByText('Test Title')).toBeInTheDocument();
      expect(screen.getByText('Test Description')).toBeInTheDocument();
      expect(screen.getByText('Test Content')).toBeInTheDocument();
      expect(screen.getByText('Test Footer')).toBeInTheDocument();
    });

    it('поддерживает вложенные компоненты', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Nested Title</CardTitle>
          </CardHeader>
          <CardContent>
            <div data-testid="nested-content">Nested content</div>
          </CardContent>
        </Card>
      );

      expect(screen.getByText('Nested Title')).toBeInTheDocument();
      expect(screen.getByTestId('nested-content')).toBeInTheDocument();
    });
  });
}); 