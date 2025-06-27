import { render, screen } from '@testing-library/react';
import Logo from '../Logo';

describe('Logo Component', () => {
  it('renders logo with text by default', () => {
    render(<Logo />);
    expect(screen.getByText('Relink')).toBeInTheDocument();
  });

  it('renders logo without text when showText is false', () => {
    render(<Logo showText={false} />);
    expect(screen.queryByText('Relink')).not.toBeInTheDocument();
  });

  it('applies correct size classes', () => {
    const { rerender } = render(<Logo size="sm" />);
    expect(screen.getByText('Relink').closest('div')).toHaveClass('w-16', 'h-8');

    rerender(<Logo size="md" />);
    expect(screen.getByText('Relink').closest('div')).toHaveClass('w-24', 'h-10');

    rerender(<Logo size="lg" />);
    expect(screen.getByText('Relink').closest('div')).toHaveClass('w-32', 'h-12');

    rerender(<Logo size="xl" />);
    expect(screen.getByText('Relink').closest('div')).toHaveClass('w-40', 'h-16');
  });

  it('applies correct variant classes', () => {
    const { rerender } = render(<Logo variant="default" />);
    expect(screen.getByText('Relink')).toHaveClass('text-gray-900');

    rerender(<Logo variant="white" />);
    expect(screen.getByText('Relink')).toHaveClass('text-white');

    rerender(<Logo variant="dark" />);
    expect(screen.getByText('Relink')).toHaveClass('text-gray-100');
  });

  it('applies custom className', () => {
    render(<Logo className="custom-class" />);
    expect(screen.getByText('Relink').closest('div')).toHaveClass('custom-class');
  });

  it('renders SVG icon', () => {
    render(<Logo />);
    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveAttribute('viewBox', '0 0 24 24');
  });

  it('renders with correct text size classes', () => {
    const { rerender } = render(<Logo size="sm" />);
    expect(screen.getByText('Relink')).toHaveClass('text-sm');

    rerender(<Logo size="md" />);
    expect(screen.getByText('Relink')).toHaveClass('text-base');

    rerender(<Logo size="lg" />);
    expect(screen.getByText('Relink')).toHaveClass('text-lg');

    rerender(<Logo size="xl" />);
    expect(screen.getByText('Relink')).toHaveClass('text-xl');
  });
}); 