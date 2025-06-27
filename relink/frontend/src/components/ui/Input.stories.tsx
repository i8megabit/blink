import type { Meta, StoryObj } from '@storybook/react';
import { Input } from './Input';
import { Search, Eye } from 'lucide-react';

const meta: Meta<typeof Input> = {
  title: 'UI/Input',
  component: Input,
  tags: ['autodocs'],
};
export default meta;

type Story = StoryObj<typeof Input>;

export const Basic: Story = {
  args: {
    label: 'Email',
    placeholder: 'Введите email',
  },
};

export const WithError: Story = {
  args: {
    label: 'Email',
    placeholder: 'Введите email',
    error: 'Некорректный email',
  },
};

export const WithIcons: Story = {
  args: {
    label: 'Поиск',
    placeholder: 'Поиск...',
    leftIcon: <Search className="w-4 h-4" />,
    rightIcon: <Eye className="w-4 h-4" />,
  },
};

export const Disabled: Story = {
  args: {
    label: 'Disabled',
    placeholder: 'Нельзя ввести',
    disabled: true,
  },
}; 