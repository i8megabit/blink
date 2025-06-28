import React, { useState, useCallback, useMemo } from 'react';
import { 
  Card, 
  Button, 
  Input, 
  Badge, 
  Progress,
  Logo 
} from './ui';
import { 
  useApi, 
  useNotifications, 
  useTheme 
} from '../hooks';

// Типы для ArchGen
interface DiagramComponent {
  id: string;
  name: string;
  type: 'service' | 'database' | 'api' | 'queue' | 'cache' | 'monitoring' | 'gateway';
  description: string;
  position?: { x: number; y: number };
  color?: string;
}

interface DiagramRelationship {
  id: string;
  from: string;
  to: string;
  type: 'http' | 'database' | 'message' | 'event' | 'sync' | 'async';
  description: string;
  bidirectional?: boolean;
}

interface DiagramStyle {
  theme: 'modern' | 'minimal' | 'corporate' | 'tech' | 'dark';
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    background: string;
  };
  fontFamily: string;
  fontSize: number;
  strokeWidth: number;
  opacity: number;
}

interface DiagramRequest {
  diagram_type: string;
  title: string;
  description: string;
  components: DiagramComponent[];
  relationships: DiagramRelationship[];
  style: DiagramStyle;
  width: number;
  height: number;
  interactive: boolean;
  include_legend: boolean;
}

interface DiagramResponse {
  diagram_id: number;
  svg_content: string;
  quality_score: number;
  generation_time: number;
  model_used: string;
  confidence_score: number;
  validation_result: any;
}

// Предустановленные шаблоны
const DIAGRAM_TEMPLATES = {
  system_architecture: {
    name: 'Системная архитектура',
    description: 'Общая архитектура системы с компонентами и связями',
    icon: '🏗️',
    defaultComponents: [
      { id: 'frontend', name: 'Frontend', type: 'service', description: 'Пользовательский интерфейс' },
      { id: 'api_gateway', name: 'API Gateway', type: 'gateway', description: 'Шлюз API' },
      { id: 'backend', name: 'Backend', type: 'service', description: 'Бизнес-логика' },
      { id: 'database', name: 'Database', type: 'database', description: 'Основная база данных' },
      { id: 'cache', name: 'Cache', type: 'cache', description: 'Кэш-система' }
    ],
    defaultRelationships: [
      { id: '1', from: 'frontend', to: 'api_gateway', type: 'http', description: 'HTTP запросы' },
      { id: '2', from: 'api_gateway', to: 'backend', type: 'http', description: 'API вызовы' },
      { id: '3', from: 'backend', to: 'database', type: 'database', description: 'Запросы к БД' },
      { id: '4', from: 'backend', to: 'cache', type: 'cache', description: 'Кэширование' }
    ]
  },
  microservices: {
    name: 'Микросервисы',
    description: 'Архитектура микросервисов с API Gateway',
    icon: '🔗',
    defaultComponents: [
      { id: 'api_gateway', name: 'API Gateway', type: 'gateway', description: 'Центральный шлюз' },
      { id: 'user_service', name: 'User Service', type: 'service', description: 'Сервис пользователей' },
      { id: 'order_service', name: 'Order Service', type: 'service', description: 'Сервис заказов' },
      { id: 'payment_service', name: 'Payment Service', type: 'service', description: 'Сервис платежей' },
      { id: 'user_db', name: 'User DB', type: 'database', description: 'База пользователей' },
      { id: 'order_db', name: 'Order DB', type: 'database', description: 'База заказов' },
      { id: 'message_queue', name: 'Message Queue', type: 'queue', description: 'Очередь сообщений' }
    ],
    defaultRelationships: [
      { id: '1', from: 'api_gateway', to: 'user_service', type: 'http', description: 'HTTP' },
      { id: '2', from: 'api_gateway', to: 'order_service', type: 'http', description: 'HTTP' },
      { id: '3', from: 'api_gateway', to: 'payment_service', type: 'http', description: 'HTTP' },
      { id: '4', from: 'user_service', to: 'user_db', type: 'database', description: 'DB' },
      { id: '5', from: 'order_service', to: 'order_db', type: 'database', description: 'DB' },
      { id: '6', from: 'order_service', to: 'message_queue', type: 'message', description: 'Events' },
      { id: '7', from: 'payment_service', to: 'message_queue', type: 'message', description: 'Events' }
    ]
  },
  data_flow: {
    name: 'Поток данных',
    description: 'Диаграмма потока данных между компонентами',
    icon: '📊',
    defaultComponents: [
      { id: 'data_source', name: 'Data Source', type: 'service', description: 'Источник данных' },
      { id: 'processor', name: 'Processor', type: 'service', description: 'Обработчик данных' },
      { id: 'storage', name: 'Storage', type: 'database', description: 'Хранилище' },
      { id: 'analytics', name: 'Analytics', type: 'service', description: 'Аналитика' },
      { id: 'output', name: 'Output', type: 'service', description: 'Выходные данные' }
    ],
    defaultRelationships: [
      { id: '1', from: 'data_source', to: 'processor', type: 'event', description: 'Data transfer' },
      { id: '2', from: 'processor', to: 'storage', type: 'database', description: 'Store processed' },
      { id: '3', from: 'storage', to: 'analytics', type: 'sync', description: 'Read for analysis' },
      { id: '4', from: 'analytics', to: 'output', type: 'event', description: 'Analytics results' }
    ]
  },
  deployment: {
    name: 'Развертывание',
    description: 'Диаграмма процесса развертывания',
    icon: '🚀',
    defaultComponents: [
      { id: 'development', name: 'Development', type: 'service', description: 'Среда разработки' },
      { id: 'cicd', name: 'CI/CD', type: 'service', description: 'Непрерывная интеграция' },
      { id: 'staging', name: 'Staging', type: 'service', description: 'Тестовая среда' },
      { id: 'production', name: 'Production', type: 'service', description: 'Продакшн среда' },
      { id: 'monitoring', name: 'Monitoring', type: 'monitoring', description: 'Мониторинг' }
    ],
    defaultRelationships: [
      { id: '1', from: 'development', to: 'cicd', type: 'event', description: 'Code push' },
      { id: '2', from: 'cicd', to: 'staging', type: 'sync', description: 'Deploy to staging' },
      { id: '3', from: 'staging', to: 'production', type: 'sync', description: 'Deploy to prod' },
      { id: '4', from: 'production', to: 'monitoring', type: 'event', description: 'Monitor' }
    ]
  }
};

// Стили по умолчанию
const DEFAULT_STYLES: Record<string, DiagramStyle> = {
  modern: {
    theme: 'modern',
    colors: {
      primary: '#2563eb',
      secondary: '#7c3aed',
      success: '#059669',
      warning: '#d97706',
      error: '#dc2626',
      background: '#ffffff'
    },
    fontFamily: 'Inter, sans-serif',
    fontSize: 14,
    strokeWidth: 2,
    opacity: 0.9
  },
  minimal: {
    theme: 'minimal',
    colors: {
      primary: '#374151',
      secondary: '#6b7280',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      background: '#f9fafb'
    },
    fontFamily: 'SF Pro Display, sans-serif',
    fontSize: 12,
    strokeWidth: 1,
    opacity: 0.8
  },
  corporate: {
    theme: 'corporate',
    colors: {
      primary: '#1f2937',
      secondary: '#4b5563',
      success: '#047857',
      warning: '#b45309',
      error: '#b91c1c',
      background: '#ffffff'
    },
    fontFamily: 'Roboto, sans-serif',
    fontSize: 16,
    strokeWidth: 3,
    opacity: 1.0
  },
  tech: {
    theme: 'tech',
    colors: {
      primary: '#00d4ff',
      secondary: '#ff6b6b',
      success: '#4ecdc4',
      warning: '#ffe66d',
      error: '#ff4757',
      background: '#2d3436'
    },
    fontFamily: 'JetBrains Mono, monospace',
    fontSize: 13,
    strokeWidth: 2,
    opacity: 0.95
  }
};

const ArchGen: React.FC = () => {
  const { theme } = useTheme();
  const { showNotification } = useNotifications();
  const { api } = useApi();

  // Состояние компонента
  const [selectedTemplate, setSelectedTemplate] = useState<string>('system_architecture');
  const [title, setTitle] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [components, setComponents] = useState<DiagramComponent[]>([]);
  const [relationships, setRelationships] = useState<DiagramRelationship[]>([]);
  const [selectedStyle, setSelectedStyle] = useState<string>('modern');
  const [width, setWidth] = useState<number>(800);
  const [height, setHeight] = useState<number>(600);
  const [interactive, setInteractive] = useState<boolean>(true);
  const [includeLegend, setIncludeLegend] = useState<boolean>(true);
  
  // Состояние генерации
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generatedSvg, setGeneratedSvg] = useState<string>('');
  const [generationResult, setGenerationResult] = useState<DiagramResponse | null>(null);

  // Загрузка шаблона
  const loadTemplate = useCallback((templateKey: string) => {
    const template = DIAGRAM_TEMPLATES[templateKey as keyof typeof DIAGRAM_TEMPLATES];
    if (template) {
      setSelectedTemplate(templateKey);
      setComponents(template.defaultComponents);
      setRelationships(template.defaultRelationships);
      setTitle(template.name);
      setDescription(template.description);
    }
  }, []);

  // Добавление компонента
  const addComponent = useCallback(() => {
    const newComponent: DiagramComponent = {
      id: `component_${Date.now()}`,
      name: 'Новый компонент',
      type: 'service',
      description: 'Описание компонента'
    };
    setComponents(prev => [...prev, newComponent]);
  }, []);

  // Удаление компонента
  const removeComponent = useCallback((id: string) => {
    setComponents(prev => prev.filter(c => c.id !== id));
    setRelationships(prev => prev.filter(r => r.from !== id && r.to !== id));
  }, []);

  // Обновление компонента
  const updateComponent = useCallback((id: string, updates: Partial<DiagramComponent>) => {
    setComponents(prev => prev.map(c => c.id === id ? { ...c, ...updates } : c));
  }, []);

  // Добавление связи
  const addRelationship = useCallback(() => {
    const newRelationship: DiagramRelationship = {
      id: `rel_${Date.now()}`,
      from: components[0]?.id || '',
      to: components[1]?.id || '',
      type: 'http',
      description: 'Новая связь'
    };
    setRelationships(prev => [...prev, newRelationship]);
  }, [components]);

  // Удаление связи
  const removeRelationship = useCallback((id: string) => {
    setRelationships(prev => prev.filter(r => r.id !== id));
  }, []);

  // Обновление связи
  const updateRelationship = useCallback((id: string, updates: Partial<DiagramRelationship>) => {
    setRelationships(prev => prev.map(r => r.id === id ? { ...r, ...updates } : r));
  }, []);

  // Генерация диаграммы
  const generateDiagram = useCallback(async () => {
    if (!title.trim() || components.length === 0) {
      showNotification('Заполните заголовок и добавьте хотя бы один компонент', 'warning');
      return;
    }

    setIsGenerating(true);
    try {
      const request: DiagramRequest = {
        diagram_type: selectedTemplate,
        title: title.trim(),
        description: description.trim(),
        components,
        relationships,
        style: DEFAULT_STYLES[selectedStyle],
        width,
        height,
        interactive,
        include_legend
      };

      const response = await api.post<DiagramResponse>('/api/diagrams/generate', request);
      setGeneratedSvg(response.data.svg_content);
      setGenerationResult(response.data);
      
      showNotification(
        `Диаграмма сгенерирована! Качество: ${(response.data.quality_score * 100).toFixed(1)}%`, 
        'success'
      );
    } catch (error) {
      console.error('Ошибка генерации диаграммы:', error);
      showNotification('Ошибка при генерации диаграммы', 'error');
    } finally {
      setIsGenerating(false);
    }
  }, [title, description, components, relationships, selectedTemplate, selectedStyle, width, height, interactive, includeLegend, api, showNotification]);

  // Экспорт SVG
  const exportSvg = useCallback(() => {
    if (!generatedSvg) return;
    
    const blob = new Blob([generatedSvg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/\s+/g, '_')}_diagram.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('SVG файл экспортирован', 'success');
  }, [generatedSvg, title, showNotification]);

  // Сброс к шаблону
  const resetToTemplate = useCallback(() => {
    loadTemplate(selectedTemplate);
  }, [selectedTemplate, loadTemplate]);

  // Текущий шаблон
  const currentTemplate = useMemo(() => 
    DIAGRAM_TEMPLATES[selectedTemplate as keyof typeof DIAGRAM_TEMPLATES], 
    [selectedTemplate]
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Заголовок */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <Logo className="w-8 h-8" />
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              ArchGen - Генератор архитектурных схем
            </h1>
            <Badge variant="success" className="ml-auto">
              AI Powered
            </Badge>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            Создавайте профессиональные SVG диаграммы архитектуры с помощью ИИ
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Панель настройки */}
          <div className="lg:col-span-1 space-y-6">
            {/* Выбор шаблона */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                🎨 Шаблон диаграммы
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(DIAGRAM_TEMPLATES).map(([key, template]) => (
                  <button
                    key={key}
                    onClick={() => loadTemplate(key)}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      selectedTemplate === key
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-2xl mb-2">{template.icon}</div>
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {template.name}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {template.description}
                    </div>
                  </button>
                ))}
              </div>
            </Card>

            {/* Основные настройки */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                ⚙️ Основные настройки
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Заголовок
                  </label>
                  <Input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Название диаграммы"
                    className="w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Описание
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Описание архитектуры"
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none"
                    rows={3}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Ширина
                    </label>
                    <Input
                      type="number"
                      value={width}
                      onChange={(e) => setWidth(Number(e.target.value))}
                      min={400}
                      max={2000}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Высота
                    </label>
                    <Input
                      type="number"
                      value={height}
                      onChange={(e) => setHeight(Number(e.target.value))}
                      min={300}
                      max={1500}
                      className="w-full"
                    />
                  </div>
                </div>
              </div>
            </Card>

            {/* Стиль */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                🎨 Стиль
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(DEFAULT_STYLES).map(([key, style]) => (
                  <button
                    key={key}
                    onClick={() => setSelectedStyle(key)}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      selectedStyle === key
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                      {key}
                    </div>
                    <div className="flex gap-1 mt-2">
                      <div 
                        className="w-4 h-4 rounded"
                        style={{ backgroundColor: style.colors.primary }}
                      />
                      <div 
                        className="w-4 h-4 rounded"
                        style={{ backgroundColor: style.colors.secondary }}
                      />
                      <div 
                        className="w-4 h-4 rounded"
                        style={{ backgroundColor: style.colors.success }}
                      />
                    </div>
                  </button>
                ))}
              </div>
              
              <div className="mt-4 space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={interactive}
                    onChange={(e) => setInteractive(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Интерактивность
                  </span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={includeLegend}
                    onChange={(e) => setIncludeLegend(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Включить легенду
                  </span>
                </label>
              </div>
            </Card>

            {/* Действия */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                🚀 Действия
              </h3>
              <div className="space-y-3">
                <Button
                  onClick={generateDiagram}
                  disabled={isGenerating || !title.trim() || components.length === 0}
                  className="w-full"
                  variant="primary"
                >
                  {isGenerating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      Генерация...
                    </>
                  ) : (
                    '🎨 Сгенерировать диаграмму'
                  )}
                </Button>
                
                <Button
                  onClick={resetToTemplate}
                  variant="secondary"
                  className="w-full"
                >
                  🔄 Сбросить к шаблону
                </Button>
                
                {generatedSvg && (
                  <Button
                    onClick={exportSvg}
                    variant="success"
                    className="w-full"
                  >
                    📥 Экспорт SVG
                  </Button>
                )}
              </div>
            </Card>
          </div>

          {/* Редактор компонентов и связей */}
          <div className="lg:col-span-1 space-y-6">
            {/* Компоненты */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  🧩 Компоненты ({components.length})
                </h3>
                <Button
                  onClick={addComponent}
                  variant="secondary"
                  size="sm"
                >
                  + Добавить
                </Button>
              </div>
              
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {components.map((component) => (
                  <div
                    key={component.id}
                    className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Input
                        value={component.name}
                        onChange={(e) => updateComponent(component.id, { name: e.target.value })}
                        placeholder="Название компонента"
                        className="flex-1 mr-2"
                      />
                      <Button
                        onClick={() => removeComponent(component.id)}
                        variant="error"
                        size="sm"
                      >
                        ✕
                      </Button>
                    </div>
                    
                    <textarea
                      value={component.description}
                      onChange={(e) => updateComponent(component.id, { description: e.target.value })}
                      placeholder="Описание"
                      className="w-full p-2 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none"
                      rows={2}
                    />
                    
                    <div className="mt-2">
                      <select
                        value={component.type}
                        onChange={(e) => updateComponent(component.id, { type: e.target.value as any })}
                        className="w-full p-2 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      >
                        <option value="service">Сервис</option>
                        <option value="database">База данных</option>
                        <option value="api">API</option>
                        <option value="queue">Очередь</option>
                        <option value="cache">Кэш</option>
                        <option value="monitoring">Мониторинг</option>
                        <option value="gateway">Шлюз</option>
                      </select>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Связи */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  🔗 Связи ({relationships.length})
                </h3>
                <Button
                  onClick={addRelationship}
                  variant="secondary"
                  size="sm"
                  disabled={components.length < 2}
                >
                  + Добавить
                </Button>
              </div>
              
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {relationships.map((relationship) => (
                  <div
                    key={relationship.id}
                    className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2 flex-1">
                        <select
                          value={relationship.from}
                          onChange={(e) => updateRelationship(relationship.id, { from: e.target.value })}
                          className="p-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        >
                          {components.map(c => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                          ))}
                        </select>
                        <span className="text-gray-500">→</span>
                        <select
                          value={relationship.to}
                          onChange={(e) => updateRelationship(relationship.id, { to: e.target.value })}
                          className="p-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        >
                          {components.map(c => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                          ))}
                        </select>
                      </div>
                      <Button
                        onClick={() => removeRelationship(relationship.id)}
                        variant="error"
                        size="sm"
                      >
                        ✕
                      </Button>
                    </div>
                    
                    <div className="flex gap-2">
                      <select
                        value={relationship.type}
                        onChange={(e) => updateRelationship(relationship.id, { type: e.target.value as any })}
                        className="flex-1 p-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      >
                        <option value="http">HTTP</option>
                        <option value="database">Database</option>
                        <option value="message">Message</option>
                        <option value="event">Event</option>
                        <option value="sync">Sync</option>
                        <option value="async">Async</option>
                      </select>
                      
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={relationship.bidirectional}
                          onChange={(e) => updateRelationship(relationship.id, { bidirectional: e.target.checked })}
                          className="mr-1"
                        />
                        <span className="text-xs text-gray-600 dark:text-gray-400">2-way</span>
                      </label>
                    </div>
                    
                    <textarea
                      value={relationship.description}
                      onChange={(e) => updateRelationship(relationship.id, { description: e.target.value })}
                      placeholder="Описание связи"
                      className="w-full mt-2 p-2 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none"
                      rows={2}
                    />
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Предварительный просмотр */}
          <div className="lg:col-span-1 space-y-6">
            {/* Результат генерации */}
            {generatedSvg && (
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    🎨 Результат
                  </h3>
                  {generationResult && (
                    <div className="flex items-center gap-2">
                      <Badge variant="success">
                        {(generationResult.quality_score * 100).toFixed(0)}%
                      </Badge>
                      <span className="text-sm text-gray-500">
                        {generationResult.generation_time.toFixed(1)}s
                      </span>
                    </div>
                  )}
                </div>
                
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-white">
                  <div 
                    className="w-full"
                    style={{ 
                      height: `${height}px`,
                      maxHeight: '600px',
                      overflow: 'auto'
                    }}
                    dangerouslySetInnerHTML={{ __html: generatedSvg }}
                  />
                </div>
                
                {generationResult && (
                  <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <div>Модель: {generationResult.model_used}</div>
                      <div>Уверенность: {(generationResult.confidence_score * 100).toFixed(1)}%</div>
                      <div>Время генерации: {generationResult.generation_time.toFixed(2)}s</div>
                    </div>
                  </div>
                )}
              </Card>
            )}

            {/* Прогресс генерации */}
            {isGenerating && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                  ⚡ Генерация диаграммы
                </h3>
                <Progress value={75} className="mb-4" />
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  ИИ анализирует архитектуру и создает профессиональную SVG диаграмму...
                </div>
              </Card>
            )}

            {/* Статистика */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                📊 Статистика
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Компонентов:</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {components.length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Связей:</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {relationships.length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Размер:</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {width} × {height}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Стиль:</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                    {selectedStyle}
                  </span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArchGen; 