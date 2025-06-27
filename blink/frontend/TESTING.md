# 🧪 Тестирование Blink Frontend

## Обзор

Проект Blink использует современный стек тестирования для обеспечения качества кода:

- **Vitest** - быстрый тестовый раннер
- **React Testing Library** - тестирование компонентов
- **@testing-library/user-event** - симуляция пользовательских действий
- **jsdom** - DOM окружение для тестов

## Структура тестов

```
src/
├── components/
│   ├── __tests__/           # Тесты компонентов
│   │   ├── App.test.tsx
│   │   ├── Button.test.tsx
│   │   ├── Input.test.tsx
│   │   ├── Card.test.tsx
│   │   ├── DomainInput.test.tsx
│   │   └── OllamaStatus.test.tsx
│   └── ui/
│       └── __tests__/       # Тесты UI компонентов
├── hooks/
│   └── __tests__/           # Тесты хуков
│       ├── useApi.test.ts
│       └── useNotifications.test.ts
└── test/
    └── setup.ts             # Настройка тестового окружения
```

## Команды тестирования

### Основные команды

```bash
# Запуск тестов в watch режиме
npm run test

# Запуск тестов с UI интерфейсом
npm run test:ui

# Запуск тестов один раз
npm run test:run

# Запуск тестов с покрытием
npm run test:coverage

# Запуск тестов в watch режиме
npm run test:watch

# Обновление снапшотов
npm run test:update
```

### Дополнительные команды

```bash
# Проверка типов
npm run type-check

# Линтинг
npm run lint

# Форматирование кода
npm run format

# Проверка форматирования
npm run format:check
```

## Написание тестов

### Тестирование компонентов

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Button } from '../Button';

describe('Button Component', () => {
  const user = userEvent.setup();

  it('рендерит кнопку с текстом', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('вызывает onClick при клике', async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click</Button>);
    
    await user.click(screen.getByRole('button', { name: 'Click' }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
```

### Тестирование хуков

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useApi } from '../useApi';

describe('useApi Hook', () => {
  it('возвращает данные при успешном запросе', async () => {
    const { result } = renderHook(() => useApi());
    
    await result.current.execute();
    
    await waitFor(() => {
      expect(result.current.data).toBeDefined();
      expect(result.current.loading).toBe(false);
    });
  });
});
```

### Тестирование API вызовов

```typescript
// Мокаем fetch
global.fetch = vi.fn();

it('делает API запрос', async () => {
  (global.fetch as any).mockResolvedValue({
    ok: true,
    json: async () => ({ data: 'test' })
  });

  const { result } = renderHook(() => useApi());
  await result.current.execute();
  
  expect(global.fetch).toHaveBeenCalledWith('/api/endpoint');
});
```

## Лучшие практики

### 1. Используйте семантические селекторы

```typescript
// ✅ Хорошо
screen.getByRole('button', { name: 'Submit' })
screen.getByLabelText('Email address')
screen.getByPlaceholderText('Enter your email')

// ❌ Плохо
screen.getByTestId('submit-button')
screen.getByClassName('btn-primary')
```

### 2. Тестируйте поведение, а не реализацию

```typescript
// ✅ Хорошо - тестируем поведение
it('показывает сообщение об ошибке при неверном email', async () => {
  render(<EmailForm />);
  await user.type(screen.getByLabelText('Email'), 'invalid-email');
  await user.click(screen.getByRole('button', { name: 'Submit' }));
  expect(screen.getByText('Invalid email format')).toBeInTheDocument();
});

// ❌ Плохо - тестируем реализацию
it('вызывает validateEmail с правильными параметрами', () => {
  const validateEmail = vi.fn();
  // ...
});
```

### 3. Используйте setup функции

```typescript
describe('UserProfile', () => {
  const user = userEvent.setup();
  
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('обновляет профиль', async () => {
    // тест
  });
});
```

### 4. Мокайте внешние зависимости

```typescript
// Мокаем API
vi.mock('../hooks/useApi', () => ({
  useApi: () => ({
    getData: vi.fn().mockResolvedValue({ data: 'test' })
  })
}));

// Мокаем уведомления
vi.mock('../hooks/useNotifications', () => ({
  useNotifications: () => ({
    showNotification: vi.fn(),
    notifications: []
  })
}));
```

## Покрытие кода

Проект стремится к 80% покрытию кода тестами:

- **branches**: 80%
- **functions**: 80%
- **lines**: 80%
- **statements**: 80%

### Просмотр покрытия

```bash
npm run test:coverage
```

Отчет будет доступен в `coverage/` директории.

## Отладка тестов

### Использование UI интерфейса

```bash
npm run test:ui
```

Откроется веб-интерфейс для интерактивного тестирования.

### Отладка в IDE

Добавьте в `vitest.config.ts`:

```typescript
test: {
  globals: true,
  environment: 'jsdom',
  setupFiles: ['./src/test/setup.ts'],
  // Добавьте для отладки
  testTimeout: 10000,
  hookTimeout: 10000,
}
```

### Логирование

```typescript
it('debug test', () => {
  render(<Component />);
  screen.debug(); // Выведет DOM в консоль
});
```

## CI/CD интеграция

Тесты автоматически запускаются в CI/CD пайплайне:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: npm run test:coverage

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Частые проблемы

1. **Ошибки с моками**
   ```typescript
   // Убедитесь, что моки очищаются
   beforeEach(() => {
     vi.clearAllMocks();
   });
   ```

2. **Асинхронные тесты**
   ```typescript
   // Используйте waitFor для асинхронных операций
   await waitFor(() => {
     expect(screen.getByText('Loaded')).toBeInTheDocument();
   });
   ```

3. **Ошибки с DOM**
   ```typescript
   // Проверьте, что jsdom настроен правильно
   test: {
     environment: 'jsdom'
   }
   ```

### Полезные команды

```bash
# Очистка кэша
npm run test -- --clearCache

# Запуск конкретного теста
npm run test Button.test.tsx

# Запуск тестов с verbose выводом
npm run test -- --verbose
```

## Дополнительные ресурсы

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Testing Library User Event](https://testing-library.com/docs/user-event/intro/)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom) 