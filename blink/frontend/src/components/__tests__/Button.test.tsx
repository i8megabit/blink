import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Button } from '../ui/Button';

describe('Button Component', () => {
  const user = userEvent.setup();

  it('рендерит текст кнопки', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('вызывает onClick при клике', async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click</Button>);
    
    await user.click(screen.getByRole('button', { name: 'Click' }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('отображает disabled состояние', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button', { name: 'Disabled' })).toBeDisabled();
  });

  it('не вызывает onClick когда disabled', async () => {
    const onClick = vi.fn();
    render(<Button disabled onClick={onClick}>Disabled</Button>);
    
    await user.click(screen.getByRole('button', { name: 'Disabled' }));
    expect(onClick).not.toHaveBeenCalled();
  });

  it('применяет правильные CSS классы для разных вариантов', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-primary', 'text-primary-foreground');

    rerender(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-secondary', 'text-secondary-foreground');

    rerender(<Button variant="outline">Outline</Button>);
    expect(screen.getByRole('button')).toHaveClass('border', 'border-input', 'bg-background');

    rerender(<Button variant="ghost">Ghost</Button>);
    expect(screen.getByRole('button')).toHaveClass('hover:bg-accent', 'hover:text-accent-foreground');

    rerender(<Button variant="destructive">Destructive</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-destructive', 'text-destructive-foreground');
  });

  it('применяет правильные размеры', () => {
    const { rerender } = render(<Button size="sm">Small</Button>);
    expect(screen.getByRole('button')).toHaveClass('h-8', 'px-3', 'text-xs');

    rerender(<Button size="md">Medium</Button>);
    expect(screen.getByRole('button')).toHaveClass('h-10', 'px-4', 'py-2');

    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole('button')).toHaveClass('h-12', 'px-8', 'text-lg');
  });

  it('отображает loading состояние', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByRole('button')).toHaveClass('disabled:opacity-50');
  });

  it('применяет дополнительные CSS классы', () => {
    render(<Button className="custom-class">Custom</Button>);
    expect(screen.getByRole('button')).toHaveClass('custom-class');
  });

  it('передает правильные атрибуты', () => {
    render(
      <Button 
        type="submit" 
        data-testid="submit-btn"
        aria-label="Submit form"
      >
        Submit
      </Button>
    );
    
    const button = screen.getByRole('button', { name: 'Submit form' });
    expect(button).toHaveAttribute('type', 'submit');
    expect(button).toHaveAttribute('data-testid', 'submit-btn');
  });

  it('обрабатывает keyboard navigation', async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Keyboard</Button>);
    
    const button = screen.getByRole('button');
    button.focus();
    
    await user.keyboard('{Enter}');
    expect(onClick).toHaveBeenCalledTimes(1);
    
    await user.keyboard(' ');
    expect(onClick).toHaveBeenCalledTimes(2);
  });

  it('отображает иконку слева по умолчанию', () => {
    const Icon = () => <span data-testid="icon">🔍</span>;
    render(<Button icon={<Icon />}>With Icon</Button>);
    
    expect(screen.getByTestId('icon')).toBeInTheDocument();
    expect(screen.getByText('With Icon')).toBeInTheDocument();
  });

  it('отображает иконку справа когда указано', () => {
    const Icon = () => <span data-testid="icon">🔍</span>;
    render(<Button icon={<Icon />} iconPosition="right">With Icon Right</Button>);
    
    expect(screen.getByTestId('icon')).toBeInTheDocument();
    expect(screen.getByText('With Icon Right')).toBeInTheDocument();
  });

  it('не отображает иконку при loading состоянии', () => {
    const Icon = () => <span data-testid="icon">🔍</span>;
    render(<Button icon={<Icon />} loading>Loading</Button>);
    
    expect(screen.queryByTestId('icon')).not.toBeInTheDocument();
    expect(screen.getByRole('button')).toHaveClass('animate-spin');
  });
}); 