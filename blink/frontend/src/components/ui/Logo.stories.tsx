import type { Meta, StoryObj } from '@storybook/react';
import Logo from './Logo';

const meta: Meta<typeof Logo> = {
  title: 'UI/Logo',
  component: Logo,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg', 'xl'],
    },
    variant: {
      control: { type: 'select' },
      options: ['default', 'white', 'dark'],
    },
    showText: {
      control: { type: 'boolean' },
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

// 🏆 Основные варианты
export const Default: Story = {
  args: {
    size: 'md',
    variant: 'default',
    showText: true,
  },
};

export const Large: Story = {
  args: {
    size: 'lg',
    variant: 'default',
    showText: true,
  },
};

export const IconOnly: Story = {
  args: {
    size: 'md',
    variant: 'default',
    showText: false,
  },
};

// 🎨 Варианты цветов
export const White: Story = {
  args: {
    size: 'md',
    variant: 'white',
    showText: true,
  },
  parameters: {
    backgrounds: { default: 'dark' },
  },
};

export const Dark: Story = {
  args: {
    size: 'md',
    variant: 'dark',
    showText: true,
  },
  parameters: {
    backgrounds: { default: 'dark' },
  },
};

// 📏 Размеры
export const Small: Story = {
  args: {
    size: 'sm',
    variant: 'default',
    showText: true,
  },
};

export const ExtraLarge: Story = {
  args: {
    size: 'xl',
    variant: 'default',
    showText: true,
  },
};

// 🎯 Все варианты
export const AllVariants: Story = {
  render: () => (
    <div className="space-y-8 p-8">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Размеры</h3>
        <div className="flex items-center gap-4">
          <Logo size="sm" />
          <Logo size="md" />
          <Logo size="lg" />
          <Logo size="xl" />
        </div>
      </div>
      
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Варианты цветов</h3>
        <div className="flex items-center gap-4">
          <Logo variant="default" />
          <div className="bg-gray-800 p-2 rounded">
            <Logo variant="white" />
          </div>
          <div className="bg-gray-900 p-2 rounded">
            <Logo variant="dark" />
          </div>
        </div>
      </div>
      
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Только иконка</h3>
        <div className="flex items-center gap-4">
          <Logo size="sm" showText={false} />
          <Logo size="md" showText={false} />
          <Logo size="lg" showText={false} />
          <Logo size="xl" showText={false} />
        </div>
      </div>
    </div>
  ),
}; 