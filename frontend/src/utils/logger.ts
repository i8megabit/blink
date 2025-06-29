/**
 * 🚀 Расширенная система логирования для reLink Frontend
 * Профилирование запросов, детальное логирование и мониторинг производительности
 */

export interface LogLevel {
  DEBUG: 0;
  INFO: 1;
  WARN: 2;
  ERROR: 3;
  FATAL: 4;
}

export interface LogEntry {
  timestamp: string;
  level: keyof LogLevel;
  message: string;
  data?: any;
  context?: string;
  performance?: {
    duration?: number;
    memory?: number;
    cpu?: number;
  };
  request?: {
    url?: string;
    method?: string;
    status?: number;
    duration?: number;
  };
  user?: {
    id?: string;
    session?: string;
  };
  stack?: string;
}

export interface PerformanceMetrics {
  requestId: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  memory?: number;
  cpu?: number;
  url?: string;
  method?: string;
  status?: number;
}

class AdvancedLogger {
  private static instance: AdvancedLogger;
  private logLevel: keyof LogLevel = 'INFO';
  private enableProfiling: boolean = false;
  private enableDetailedLogging: boolean = false;
  private performanceMetrics: Map<string, PerformanceMetrics> = new Map();
  private requestCount: number = 0;
  private errorCount: number = 0;
  private warningCount: number = 0;

  private constructor() {
    this.initializeLogger();
    this.setupGlobalErrorHandling();
    this.setupPerformanceMonitoring();
  }

  public static getInstance(): AdvancedLogger {
    if (!AdvancedLogger.instance) {
      AdvancedLogger.instance = new AdvancedLogger();
    }
    return AdvancedLogger.instance;
  }

  private initializeLogger(): void {
    // Читаем настройки из переменных окружения
    this.enableProfiling = import.meta.env.VITE_REACT_APP_ENABLE_PROFILING === 'true';
    this.enableDetailedLogging = import.meta.env.VITE_REACT_APP_ENABLE_DETAILED_LOGGING === 'true';
    
    // Устанавливаем уровень логирования
    const debugMode = import.meta.env.VITE_REACT_APP_DEBUG === 'true';
    this.logLevel = debugMode ? 'DEBUG' : 'INFO';

    // Логируем инициализацию
    this.info('🚀 AdvancedLogger инициализирован', {
      enableProfiling: this.enableProfiling,
      enableDetailedLogging: this.enableDetailedLogging,
      logLevel: this.logLevel,
      timestamp: new Date().toISOString()
    });
  }

  private setupGlobalErrorHandling(): void {
    // Перехват глобальных ошибок
    window.addEventListener('error', (event) => {
      this.error('🌐 Глобальная ошибка JavaScript', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error?.stack
      });
    });

    // Перехват необработанных промисов
    window.addEventListener('unhandledrejection', (event) => {
      this.error('❌ Необработанное отклонение промиса', {
        reason: event.reason,
        promise: event.promise
      });
    });

    // Перехват ошибок загрузки ресурсов
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.warn('📦 Ошибка загрузки ресурса', {
          target: event.target,
          type: event.type,
          url: (event.target as any)?.src || (event.target as any)?.href
        });
      }
    }, true);
  }

  private setupPerformanceMonitoring(): void {
    if (!this.enableProfiling) return;

    // Мониторинг производительности
    if ('performance' in window) {
      // Наблюдаем за метриками веб-виталов
      if ('PerformanceObserver' in window) {
        try {
          const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              this.debug('📊 Метрика производительности', {
                name: entry.name,
                entryType: entry.entryType,
                startTime: entry.startTime,
                duration: entry.duration,
                navigationType: (entry as any).navigationType
              });
            }
          });

          observer.observe({ entryTypes: ['navigation', 'resource', 'paint', 'largest-contentful-paint'] });
        } catch (error) {
          this.warn('⚠️ Не удалось настроить PerformanceObserver', { error });
        }
      }

      // Мониторинг памяти (если доступен)
      if ('memory' in performance) {
        setInterval(() => {
          const memory = (performance as any).memory;
          this.debug('🧠 Использование памяти', {
            usedJSHeapSize: memory.usedJSHeapSize,
            totalJSHeapSize: memory.totalJSHeapSize,
            jsHeapSizeLimit: memory.jsHeapSizeLimit
          });
        }, 30000); // Каждые 30 секунд
      }
    }
  }

  private shouldLog(level: keyof LogLevel): boolean {
    const levels: LogLevel = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3, FATAL: 4 };
    return levels[level] >= levels[this.logLevel];
  }

  private formatLogEntry(level: keyof LogLevel, message: string, data?: any, context?: string): LogEntry {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context: context || 'app',
      data
    };

    // Добавляем информацию о производительности если включено профилирование
    if (this.enableProfiling && data?.performance) {
      entry.performance = data.performance;
    }

    // Добавляем информацию о запросе если есть
    if (data?.request) {
      entry.request = data.request;
    }

    // Добавляем информацию о пользователе если есть
    if (data?.user) {
      entry.user = data.user;
    }

    // Добавляем стек для ошибок
    if (level === 'ERROR' || level === 'FATAL') {
      entry.stack = new Error().stack;
    }

    return entry;
  }

  private outputToConsole(entry: LogEntry): void {
    const { timestamp, level, message, data, context } = entry;
    const prefix = `[${timestamp}] [${level}] [${context}]`;
    
    const emoji = {
      DEBUG: '🔍',
      INFO: 'ℹ️',
      WARN: '⚠️',
      ERROR: '❌',
      FATAL: '💥'
    }[level];

    const styledPrefix = `%c${emoji} ${prefix}`;
    const style = this.getConsoleStyle(level);

    if (data) {
      console.group(styledPrefix, style, message);
      console.log('📋 Данные:', data);
      if (entry.performance) {
        console.log('⚡ Производительность:', entry.performance);
      }
      if (entry.request) {
        console.log('🌐 Запрос:', entry.request);
      }
      if (entry.stack) {
        console.log('📚 Стек:', entry.stack);
      }
      console.groupEnd();
    } else {
      console.log(styledPrefix, style, message);
    }
  }

  private getConsoleStyle(level: keyof LogLevel): string {
    const styles = {
      DEBUG: 'color: #6c757d; font-weight: bold;',
      INFO: 'color: #007bff; font-weight: bold;',
      WARN: 'color: #ffc107; font-weight: bold;',
      ERROR: 'color: #dc3545; font-weight: bold;',
      FATAL: 'color: #721c24; font-weight: bold; background: #f8d7da;'
    };
    return styles[level];
  }

  private log(level: keyof LogLevel, message: string, data?: any, context?: string): void {
    if (!this.shouldLog(level)) return;

    const entry = this.formatLogEntry(level, message, data, context);
    
    // Выводим в консоль
    this.outputToConsole(entry);

    // Обновляем счетчики
    this.updateCounters(level);

    // Отправляем в аналитику если включено детальное логирование
    if (this.enableDetailedLogging) {
      this.sendToAnalytics(entry);
    }
  }

  private updateCounters(level: keyof LogLevel): void {
    switch (level) {
      case 'ERROR':
      case 'FATAL':
        this.errorCount++;
        break;
      case 'WARN':
        this.warningCount++;
        break;
    }
  }

  private sendToAnalytics(entry: LogEntry): void {
    // Отправляем логи в аналитику (можно настроить отправку на сервер)
    try {
      if (window.gtag) {
        window.gtag('event', 'log_entry', {
          log_level: entry.level,
          log_message: entry.message,
          log_context: entry.context,
          timestamp: entry.timestamp
        });
      }
    } catch (error) {
      // Игнорируем ошибки аналитики
    }
  }

  // Публичные методы логирования
  public debug(message: string, data?: any, context?: string): void {
    this.log('DEBUG', message, data, context);
  }

  public info(message: string, data?: any, context?: string): void {
    this.log('INFO', message, data, context);
  }

  public warn(message: string, data?: any, context?: string): void {
    this.log('WARN', message, data, context);
  }

  public error(message: string, data?: any, context?: string): void {
    this.log('ERROR', message, data, context);
  }

  public fatal(message: string, data?: any, context?: string): void {
    this.log('FATAL', message, data, context);
  }

  // Методы для профилирования запросов
  public startRequestProfiling(url: string, method: string = 'GET'): string {
    if (!this.enableProfiling) return '';

    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const metrics: PerformanceMetrics = {
      requestId,
      startTime: performance.now(),
      url,
      method
    };

    this.performanceMetrics.set(requestId, metrics);
    this.requestCount++;

    this.debug('🚀 Начало профилирования запроса', {
      requestId,
      url,
      method,
      startTime: metrics.startTime
    });

    return requestId;
  }

  public endRequestProfiling(requestId: string, status?: number, data?: any): void {
    if (!this.enableProfiling || !requestId) return;

    const metrics = this.performanceMetrics.get(requestId);
    if (!metrics) return;

    metrics.endTime = performance.now();
    metrics.duration = metrics.endTime - metrics.startTime;
    metrics.status = status;

    // Получаем информацию о памяти
    if ('memory' in performance) {
      metrics.memory = (performance as any).memory.usedJSHeapSize;
    }

    this.debug('✅ Завершение профилирования запроса', {
      requestId,
      url: metrics.url,
      method: metrics.method,
      status: metrics.status,
      duration: `${metrics.duration.toFixed(2)}ms`,
      memory: metrics.memory ? `${(metrics.memory / 1024 / 1024).toFixed(2)}MB` : undefined,
      data
    });

    // Удаляем метрики из памяти
    this.performanceMetrics.delete(requestId);
  }

  // Методы для получения статистики
  public getStats(): any {
    return {
      requestCount: this.requestCount,
      errorCount: this.errorCount,
      warningCount: this.warningCount,
      activeRequests: this.performanceMetrics.size,
      enableProfiling: this.enableProfiling,
      enableDetailedLogging: this.enableDetailedLogging,
      logLevel: this.logLevel
    };
  }

  // Метод для экспорта логов
  public exportLogs(): LogEntry[] {
    // В реальной реализации здесь можно собрать все логи
    return [];
  }
}

// Создаем глобальный экземпляр логгера
export const logger = AdvancedLogger.getInstance();

// Утилиты для удобного использования
export const logDebug = (message: string, data?: any, context?: string) => 
  logger.debug(message, data, context);

export const logInfo = (message: string, data?: any, context?: string) => 
  logger.info(message, data, context);

export const logWarn = (message: string, data?: any, context?: string) => 
  logger.warn(message, data, context);

export const logError = (message: string, data?: any, context?: string) => 
  logger.error(message, data, context);

export const logFatal = (message: string, data?: any, context?: string) => 
  logger.fatal(message, data, context);

// Хук для React компонентов
export const useLogger = (context?: string) => {
  return {
    debug: (message: string, data?: any) => logger.debug(message, data, context),
    info: (message: string, data?: any) => logger.info(message, data, context),
    warn: (message: string, data?: any) => logger.warn(message, data, context),
    error: (message: string, data?: any) => logger.error(message, data, context),
    fatal: (message: string, data?: any) => logger.fatal(message, data, context),
    startRequestProfiling: (url: string, method?: string) => logger.startRequestProfiling(url, method),
    endRequestProfiling: (requestId: string, status?: number, data?: any) => logger.endRequestProfiling(requestId, status, data),
    getStats: () => logger.getStats()
  };
};

// Расширение типов для gtag
declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
  }
}

export default logger; 