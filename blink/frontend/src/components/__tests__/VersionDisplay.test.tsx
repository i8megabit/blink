import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import VersionDisplay from '../VersionDisplay';

describe('VersionDisplay Component', () => {
  it('рендерится без ошибок', () => {
    render(<VersionDisplay />);
    expect(screen.getByText(/v4\.0\.0/i)).toBeInTheDocument();
  });

  it('отображает версию приложения', () => {
    render(<VersionDisplay />);
    expect(screen.getByText(/4\.0\.0/i)).toBeInTheDocument();
  });

  it('имеет правильные стили', () => {
    render(<VersionDisplay />);
    const versionElement = screen.getByText(/v4\.0\.0/i);
    expect(versionElement).toHaveClass('text-xs', 'text-muted-foreground');
  });

  it('отображается как span элемент', () => {
    render(<VersionDisplay />);
    const versionElement = screen.getByText(/v4\.0\.0/i);
    expect(versionElement.tagName).toBe('SPAN');
  });
}); 