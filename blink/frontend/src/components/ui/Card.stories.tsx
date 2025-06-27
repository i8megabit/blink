import type { Meta, StoryObj } from '@storybook/react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './Card';

const meta: Meta<typeof Card> = {
  title: 'UI/Card',
  component: Card,
  tags: ['autodocs'],
};
export default meta;

type Story = StoryObj<typeof Card>;

export const Basic: Story = {
  render: () => <Card className="p-4">Basic Card</Card>,
};

export const WithHeader: Story = {
  render: () => (
    <Card>
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card description goes here</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card content goes here</p>
      </CardContent>
      <CardFooter>
        <button className="btn btn-primary">Action</button>
      </CardFooter>
    </Card>
  ),
};

export const OnlyContent: Story = {
  render: () => (
    <Card>
      <CardContent>
        <p>Only content inside Card</p>
      </CardContent>
    </Card>
  ),
};

export const WithFooter: Story = {
  render: () => (
    <Card>
      <CardContent>
        <p>Card with footer</p>
      </CardContent>
      <CardFooter>
        <button className="btn btn-secondary">Secondary</button>
      </CardFooter>
    </Card>
  ),
}; 