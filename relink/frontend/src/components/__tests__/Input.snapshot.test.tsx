import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Input } from '../ui/Input';

describe('Input Snapshot', () => {
  it('рендерится с placeholder', () => {
    const { container } = render(<Input placeholder="Enter text" />);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с label', () => {
    const { container } = render(<Input label="Email Address" />);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с label и id', () => {
    const { container } = render(<Input label="Email Address" id="email" />);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с error', () => {
    const { container } = render(<Input error="Invalid email" />);
    expect(container).toMatchSnapshot();
  });

  it('рендерится как required', () => {
    const { container } = render(<Input label="Email Address" required />);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с типом password', () => {
    const { container } = render(<Input type="password" label="Password" />);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с типом email', () => {
    const { container } = render(<Input type="email" label="Email" />);
    expect(container).toMatchSnapshot();
  });

  it('рендерится в disabled состоянии', () => {
    const { container } = render(<Input disabled placeholder="Disabled input" />);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с кастомными классами', () => {
    const { container } = render(<Input className="bg-blue-50" placeholder="Custom styled" />);
    expect(container).toMatchSnapshot();
  });
}); 