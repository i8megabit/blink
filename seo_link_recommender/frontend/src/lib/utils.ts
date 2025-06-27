import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

// AIUI Design System - Utility Functions

/**
 * Объединяет классы Tailwind с правильным порядком
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Форматирует дату в читаемый вид
 */
export function formatDate(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * Форматирует время выполнения
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}с`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}м ${remainingSeconds.toFixed(0)}с`
}

/**
 * Форматирует число с разделителями
 */
export function formatNumber(num: number): string {
  return new Intl.NumberFormat('ru-RU').format(num)
}

/**
 * Форматирует процент
 */
export function formatPercentage(value: number, total: number): string {
  const percentage = (value / total) * 100
  return `${percentage.toFixed(1)}%`
}

/**
 * Обрезает текст до указанной длины
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

/**
 * Генерирует уникальный ID
 */
export function generateId(): string {
  return `id_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Проверяет, является ли значение пустым
 */
export function isEmpty(value: any): boolean {
  if (value === null || value === undefined) return true
  if (typeof value === 'string') return value.trim().length === 0
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'object') return Object.keys(value).length === 0
  return false
}

/**
 * Дебаунс функция
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

/**
 * Троттлинг функция
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

/**
 * Копирует текст в буфер обмена
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (error) {
    console.error('Ошибка копирования в буфер обмена:', error)
    return false
  }
}

/**
 * Скачивает файл
 */
export function downloadFile(content: string, filename: string, type: string = 'text/plain'): void {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * Валидация email
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Валидация URL
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * Получает цвет для статуса
 */
export function getStatusColor(status: string): string {
  const colors = {
    success: 'text-green-600 bg-green-50 border-green-200',
    error: 'text-red-600 bg-red-50 border-red-200',
    warning: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    info: 'text-blue-600 bg-blue-50 border-blue-200',
    pending: 'text-gray-600 bg-gray-50 border-gray-200',
    running: 'text-blue-600 bg-blue-50 border-blue-200',
    completed: 'text-green-600 bg-green-50 border-green-200',
    failed: 'text-red-600 bg-red-50 border-red-200'
  }
  return colors[status as keyof typeof colors] || colors.info
}

/**
 * Получает иконку для статуса
 */
export function getStatusIcon(status: string): string {
  const icons = {
    success: '✓',
    error: '✗',
    warning: '⚠',
    info: 'ℹ',
    pending: '⏳',
    running: '🔄',
    completed: '✅',
    failed: '❌'
  }
  return icons[status as keyof typeof icons] || icons.info
}

/**
 * Форматирует размер файла
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Б'
  const k = 1024
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * Создает градиент для прогресс-бара
 */
export function createProgressGradient(percentage: number): string {
  if (percentage < 30) return 'from-red-500 to-orange-500'
  if (percentage < 70) return 'from-yellow-500 to-orange-500'
  return 'from-green-500 to-emerald-500'
}

/**
 * Очищает домен от протокола и слешей
 */
export function cleanDomain(domain: string): string {
  return domain
    .replace(/^https?:\/\//, '')
    .replace(/^www\./, '')
    .replace(/\/$/, '')
}

/**
 * Задержка выполнения
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Проверяет, является ли устройство мобильным
 */
export function isMobile(): boolean {
  return window.innerWidth < 768
}

/**
 * Проверяет, является ли устройство планшетом
 */
export function isTablet(): boolean {
  return window.innerWidth >= 768 && window.innerWidth < 1024
}

/**
 * Проверяет, является ли устройство десктопом
 */
export function isDesktop(): boolean {
  return window.innerWidth >= 1024
} 