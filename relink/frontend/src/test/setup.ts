import '@testing-library/jest-dom';
import { vi, beforeAll, afterAll } from 'vitest';

// Мокаем ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Мокаем IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Мокаем matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Мокаем getComputedStyle
Object.defineProperty(window, 'getComputedStyle', {
  value: () => ({
    getPropertyValue: () => '',
  }),
});

// Мокаем CSS.supports
Object.defineProperty(window, 'CSS', {
  value: {
    supports: vi.fn(),
  },
});

// Мокаем console для тестов
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

beforeAll(() => {
  console.error = vi.fn();
  console.warn = vi.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
  console.warn = originalConsoleWarn;
});

// Мокаем fetch если не мокирован
if (!global.fetch) {
  global.fetch = vi.fn();
}

// Мокаем WebSocket
global.WebSocket = vi.fn().mockImplementation(() => ({
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  send: vi.fn(),
  close: vi.fn(),
  readyState: 1
})) as any;

// Мокаем URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'mocked-url');
global.URL.revokeObjectURL = vi.fn();

// Мокаем FileReader
global.FileReader = vi.fn().mockImplementation(() => ({
  readAsText: vi.fn(),
  readAsDataURL: vi.fn(),
  result: '',
  onload: null,
  onerror: null,
})) as any;

// Мокаем localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
};
global.localStorage = localStorageMock as Storage;

// Мокаем sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
};
global.sessionStorage = sessionStorageMock as Storage;

// Мокаем crypto для генерации UUID
Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: vi.fn(() => 'test-uuid'),
  },
});

// Мокаем requestAnimationFrame
global.requestAnimationFrame = vi.fn((cb) => setTimeout(cb, 0)) as any;
global.cancelAnimationFrame = vi.fn();

// Мокаем scrollTo
global.scrollTo = vi.fn();

// Мокаем getBoundingClientRect
Element.prototype.getBoundingClientRect = vi.fn(() => ({
  width: 120,
  height: 120,
  top: 0,
  left: 0,
  bottom: 0,
  right: 0,
  x: 0,
  y: 0,
  toJSON: () => ({}),
})) as any;

// Мокаем offsetWidth и offsetHeight
Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
  configurable: true,
  value: 120,
});

Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
  configurable: true,
  value: 120,
});

// Мокаем clientWidth и clientHeight
Object.defineProperty(HTMLElement.prototype, 'clientWidth', {
  configurable: true,
  value: 120,
});

Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
  configurable: true,
  value: 120,
});

// Мокаем scrollWidth и scrollHeight
Object.defineProperty(HTMLElement.prototype, 'scrollWidth', {
  configurable: true,
  value: 120,
});

Object.defineProperty(HTMLElement.prototype, 'scrollHeight', {
  configurable: true,
  value: 120,
}); 