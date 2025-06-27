import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Logo from '../Logo';

describe('Logo Snapshot Tests', () => {
  it('renders default logo correctly', () => {
    const { container } = render(<Logo />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders logo without text correctly', () => {
    const { container } = render(<Logo showText={false} />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders small logo correctly', () => {
    const { container } = render(<Logo size="sm" />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders large logo correctly', () => {
    const { container } = render(<Logo size="lg" />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders extra large logo correctly', () => {
    const { container } = render(<Logo size="xl" />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders white variant correctly', () => {
    const { container } = render(<Logo variant="white" />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders dark variant correctly', () => {
    const { container } = render(<Logo variant="dark" />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders with custom className correctly', () => {
    const { container } = render(<Logo className="custom-class" />);
    expect(container.firstChild).toMatchSnapshot();
  });
}); 