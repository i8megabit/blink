import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Input } from '../ui/Input';

describe('Input Component', () => {
  const user = userEvent.setup();

  it('рендерит input элемент', () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
  });

  it('принимает и отображает значение', () => {
    render(<Input value="test value" onChange={() => {}} />);
    expect(screen.getByDisplayValue('test value')).toBeInTheDocument();
  });

  it('вызывает onChange при вводе', async () => {
    const onChange = vi.fn();
    render(<Input onChange={onChange} />);
    
    const input = screen.getByRole('textbox');
    await user.type(input, 'hello');
    
    expect(onChange).toHaveBeenCalledTimes(5); // по одному разу на каждый символ
  });

  it('отображает disabled состояние', () => {
    render(<Input disabled placeholder="Disabled" />);
    expect(screen.getByPlaceholderText('Disabled')).toBeDisabled();
  });

  it('применяет правильные CSS классы', () => {
    render(<Input className="custom-class" />);
    expect(screen.getByRole('textbox')).toHaveClass('custom-class');
  });

  it('передает правильные атрибуты', () => {
    render(
      <Input 
        type="email"
        name="email"
        id="email-input"
        data-testid="email-field"
        aria-label="Email address"
        placeholder="Enter email"
      />
    );
    
    const input = screen.getByRole('textbox', { name: 'Email address' });
    expect(input).toHaveAttribute('type', 'email');
    expect(input).toHaveAttribute('name', 'email');
    expect(input).toHaveAttribute('id', 'email-input');
    expect(input).toHaveAttribute('data-testid', 'email-field');
  });

  it('обрабатывает keyboard navigation', async () => {
    const onChange = vi.fn();
    render(<Input onChange={onChange} />);
    
    const input = screen.getByRole('textbox');
    input.focus();
    
    await user.keyboard('test');
    expect(onChange).toHaveBeenCalled();
  });

  it('отображает ошибку когда предоставлена', () => {
    render(<Input error="This field is required" />);
    expect(screen.getByText('This field is required')).toBeInTheDocument();
  });

  it('применяет error стили', () => {
    render(<Input error="Error message" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-destructive');
  });

  it('отображает label когда предоставлен', () => {
    render(<Input label="Email Address" />);
    expect(screen.getByText('Email Address')).toBeInTheDocument();
  });

  it('связывает label с input через id', () => {
    render(<Input label="Email Address" id="email" />);
    const input = screen.getByRole('textbox');
    const label = screen.getByText('Email Address');
    expect(input).toHaveAttribute('id', 'email');
    expect(label).toHaveAttribute('for', 'email');
  });

  it('отображает required индикатор', () => {
    render(<Input label="Email Address" required />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('required');
  });

  it('обрабатывает ref корректно', () => {
    const ref = vi.fn();
    render(<Input ref={ref} />);
    expect(ref).toHaveBeenCalled();
  });
}); 