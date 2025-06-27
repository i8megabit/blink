import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../ui/Card';

describe('Card Snapshot', () => {
  it('рендерится с заголовком', () => {
    const { container } = render(
      <Card>
        <CardHeader>
          <CardTitle>Test Card</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Card content</p>
        </CardContent>
      </Card>
    );
    expect(container).toMatchSnapshot();
  });

  it('рендерится без заголовка', () => {
    const { container } = render(
      <Card>
        <CardContent>
          <p>Card content</p>
        </CardContent>
      </Card>
    );
    expect(container).toMatchSnapshot();
  });

  it('рендерится с описанием', () => {
    const { container } = render(
      <Card>
        <CardHeader>
          <CardTitle>Analytics</CardTitle>
          <p>Analytics description</p>
        </CardHeader>
        <CardContent>
          <p>Analytics content</p>
        </CardContent>
      </Card>
    );
    expect(container).toMatchSnapshot();
  });

  it('рендерится с footer', () => {
    const { container } = render(
      <Card>
        <CardHeader>
          <CardTitle>Actions Card</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Card with actions</p>
        </CardContent>
        <CardFooter>
          <button>Action</button>
        </CardFooter>
      </Card>
    );
    expect(container).toMatchSnapshot();
  });

  it('рендерится с кастомными классами', () => {
    const { container } = render(
      <Card className="bg-blue-100">
        <CardHeader className="bg-blue-50">
          <CardTitle className="text-blue-900">Custom Card</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Custom styled content</p>
        </CardContent>
      </Card>
    );
    expect(container).toMatchSnapshot();
  });
}); 