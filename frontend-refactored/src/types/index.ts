import React from 'react';

// Основные типы для микросервисной архитектуры reLink

export interface MicroserviceConfig {
  name: string;
  url: string;
  port: number;
  health: boolean;
  version: string;
  status: 'online' | 'offline' | 'degraded';
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
  service: string;
  version: string;
}

export interface LoadingState {
  state: 'idle' | 'loading' | 'success' | 'error';
  progress?: number;
  message?: string;
}

// Типы для доменов и анализа
export interface Domain {
  id: string;
  url: string;
  name: string;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  analysis_count: number;
  last_analysis?: AnalysisResult;
}

export interface AnalysisResult {
  id: string;
  domain_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  started_at: string;
  completed_at?: string;
  metrics: AnalysisMetrics;
  recommendations: Recommendation[];
  insights: Insight[];
  errors?: string[];
}

export interface AnalysisMetrics {
  seo_score: number;
  performance_score: number;
  accessibility_score: number;
  best_practices_score: number;
  total_issues: number;
  critical_issues: number;
  warnings: number;
  suggestions: number;
}

export interface Recommendation {
  id: string;
  category: 'seo' | 'performance' | 'accessibility' | 'security' | 'best_practices';
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  impact: string;
  effort: 'low' | 'medium' | 'high';
  implementation: string;
  examples?: string[];
}

export interface Insight {
  id: string;
  type: 'trend' | 'anomaly' | 'opportunity' | 'risk';
  title: string;
  description: string;
  data: any;
  confidence: number;
  created_at: string;
}

// Типы для LLM и AI
export interface LLMModel {
  id: string;
  name: string;
  provider: 'ollama' | 'openai' | 'anthropic';
  version: string;
  status: 'available' | 'busy' | 'offline';
  performance: ModelPerformance;
  cost_per_token: number;
  max_tokens: number;
  context_window: number;
}

export interface ModelPerformance {
  latency_ms: number;
  throughput_tps: number;
  accuracy: number;
  reliability: number;
  last_updated: string;
}

export interface AIAnalysisRequest {
  domain: string;
  model_id?: string;
  analysis_type: 'seo' | 'content' | 'technical' | 'comprehensive';
  priority: 'low' | 'normal' | 'high';
  options: {
    include_competitors?: boolean;
    include_historical_data?: boolean;
    include_predictions?: boolean;
  };
}

export interface AIAnalysisResponse {
  request_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  estimated_completion?: string;
  result?: AIAnalysisResult;
  error?: string;
}

export interface AIAnalysisResult {
  summary: string;
  key_findings: string[];
  recommendations: AIRecommendation[];
  metrics: AIMetrics;
  confidence_score: number;
  model_used: string;
  processing_time_ms: number;
}

export interface AIRecommendation {
  category: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  reasoning: string;
  expected_impact: string;
  implementation_steps: string[];
}

export interface AIMetrics {
  seo_potential: number;
  content_quality: number;
  technical_health: number;
  competitive_position: number;
  growth_potential: number;
}

// Типы для бенчмарков
export interface Benchmark {
  id: string;
  name: string;
  description: string;
  category: 'seo' | 'performance' | 'accessibility' | 'security';
  status: 'active' | 'inactive' | 'deprecated';
  version: string;
  created_at: string;
  updated_at: string;
  metrics: BenchmarkMetrics;
  thresholds: BenchmarkThresholds;
}

export interface BenchmarkMetrics {
  total_runs: number;
  success_rate: number;
  average_score: number;
  best_score: number;
  worst_score: number;
  last_run?: string;
}

export interface BenchmarkThresholds {
  excellent: number;
  good: number;
  needs_improvement: number;
  poor: number;
}

export interface BenchmarkResult {
  id: string;
  benchmark_id: string;
  domain_id: string;
  score: number;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  details: BenchmarkDetail[];
  run_at: string;
  duration_ms: number;
}

export interface BenchmarkDetail {
  metric: string;
  value: number;
  target: number;
  status: 'pass' | 'fail' | 'warning';
  weight: number;
}

// Типы для мониторинга
export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_io: NetworkIO;
  active_connections: number;
  request_rate: number;
  error_rate: number;
  response_time_ms: number;
  timestamp: string;
}

export interface NetworkIO {
  bytes_in: number;
  bytes_out: number;
  packets_in: number;
  packets_out: number;
}

export interface Alert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  service: string;
  timestamp: string;
  acknowledged: boolean;
  acknowledged_at?: string;
  acknowledged_by?: string;
}

// Типы для уведомлений
export interface Notification {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  action?: {
    label: string;
    url: string;
  };
}

// Типы для пользовательских настроек
export interface UserSettings {
  theme: 'light' | 'dark' | 'auto';
  language: 'ru' | 'en';
  notifications: {
    email: boolean;
    push: boolean;
    sms: boolean;
  };
  dashboard: {
    layout: 'grid' | 'list';
    default_view: string;
    widgets: string[];
  };
  api: {
    rate_limit: number;
    timeout: number;
    retry_attempts: number;
  };
}

// Типы для WebSocket сообщений
export interface WebSocketMessage {
  type: 'analysis_update' | 'benchmark_result' | 'system_alert' | 'notification';
  data: any;
  timestamp: string;
  service: string;
}

// Типы для экспорта
export interface ExportOptions {
  format: 'json' | 'csv' | 'pdf' | 'excel';
  include_metadata: boolean;
  include_charts: boolean;
  date_range?: {
    start: string;
    end: string;
  };
  filters?: Record<string, any>;
}

export interface ExportResult {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  download_url?: string;
  expires_at: string;
  file_size?: number;
  created_at: string;
}

// Типы для аутентификации
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'viewer';
  permissions: string[];
  created_at: string;
  last_login?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Типы для роутинга
export interface RouteConfig {
  path: string;
  component: any;
  exact?: boolean;
  requiresAuth?: boolean;
  permissions?: string[];
  title?: string;
}

// Типы для форм
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'textarea' | 'checkbox';
  required?: boolean;
  validation?: any;
  options?: { value: string; label: string }[];
  placeholder?: string;
  help?: string;
}

// Типы для таблиц
export interface TableColumn<T = any> {
  key: keyof T;
  title: string;
  sortable?: boolean;
  filterable?: boolean;
  width?: number;
  render?: (value: any, record: T) => any;
}

export interface TableConfig<T = any> {
  columns: TableColumn<T>[];
  data: T[];
  loading?: boolean;
  pagination?: {
    current: number;
    pageSize: number;
    total: number;
  };
  sorting?: {
    key: keyof T;
    order: 'asc' | 'desc';
  };
  filters?: Record<string, any>;
}

// Типы для графиков
export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string;
  borderColor?: string;
  borderWidth?: number;
  fill?: boolean;
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'pie' | 'doughnut' | 'radar';
  data: ChartData;
  options?: any;
}

// Типы для модальных окон
export interface ModalConfig {
  isOpen: boolean;
  title: string;
  content: any;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  onClose?: () => void;
  onConfirm?: () => void;
  confirmText?: string;
  cancelText?: string;
  showFooter?: boolean;
}

// Типы для контекста приложения
export interface AppContext {
  user: User | null;
  settings: UserSettings;
  notifications: Notification[];
  alerts: Alert[];
  systemMetrics: SystemMetrics | null;
  microservices: MicroserviceConfig[];
  theme: 'light' | 'dark';
  language: 'ru' | 'en';
} 