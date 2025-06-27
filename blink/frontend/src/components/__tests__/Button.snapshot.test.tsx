import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Button } from '../ui/Button';

describe('Button Snapshot', () => {
  it('рендерится с текстом', () => {
    const { container } = render(<Button>Click me</Button>);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с иконкой', () => {
    const Icon = () => <span>🔍</span>;
    const { container } = render(<Button icon={<Icon />}>Search</Button>);
    expect(container).toMatchSnapshot();
  });

  it('рендерится в loading состоянии', () => {
    const { container } = render(<Button loading>Loading</Button>);
    expect(container).toMatchSnapshot();
  });

  it('рендерится в disabled состоянии', () => {
    const { container } = render(<Button disabled>Disabled</Button>);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с variant primary', () => {
    const { container } = render(<Button variant="primary">Primary</Button>);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с variant secondary', () => {
    const { container } = render(<Button variant="secondary">Secondary</Button>);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с variant outline', () => {
    const { container } = render(<Button variant="outline">Outline</Button>);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с variant ghost', () => {
    const { container } = render(<Button variant="ghost">Ghost</Button>);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с size sm', () => {
    const { container } = render(<Button size="sm">Small</Button>);
    expect(container).toMatchSnapshot();
  });

  it('рендерится с size lg', () => {
    const { container } = render(<Button size="lg">Large</Button>);
    expect(container).toMatchSnapshot();
  });
}); 