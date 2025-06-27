// ===== ОСНОВНЫЕ ТИПЫ ПРИЛОЖЕНИЯ =====

export interface Domain {
  id: number
  name: string
  display_name: string
  description?: string
  language: string
  category?: string
  created_at: string
  updated_at: string
  is_active: boolean
  total_posts: number
  total_analyses: number
  last_analysis_at?: string
  is_indexed: boolean
}

export interface WordPressPost {
  id: number
  title: string
  link: string
  content: string
  excerpt?: string
  content_type?: string
  difficulty_level?: string
  linkability_score?: number
  semantic_richness?: number
  key_concepts?: string[]
  created_at: string
  updated_at: string
}

export interface Recommendation {
  id: number
  source_post_id: number
  target_post_id: number
  anchor_text: string
  reasoning: string
  quality_score: number
  generation_count: number
  improvement_iterations: number
  status: 'active' | 'deprecated' | 'improved'
  semantic_connection_id?: number
  previous_version_id?: number
  improvement_reason?: string
  created_at: string
  updated_at: string
  source_post?: WordPressPost
  target_post?: WordPressPost
}

export interface AnalysisStats {
  current: number
  total: number
  details: string
}

export interface AIThought {
  id: string
  type: 'ai_thinking' | 'enhanced_ai_thinking'
  thought?: string
  thinking_stage?: string
  emoji?: string
  stage: string
  content: string
  confidence: number
  semantic_weight: number
  related_concepts: string[]
  reasoning_chain: string[]
  timestamp: string
}

export interface OllamaStatus {
  status: string
  connection: string
  models_count: number
  available_models: string[]
  timestamp: string
  ready_for_work: boolean
  server_available: boolean
  model_loaded: boolean
  message: string
  last_check: string
}

export interface AnalysisHistory {
  id: number
  domain_id: number
  posts_analyzed: number
  connections_found: number
  recommendations_generated: number
  recommendations: Array<{
    anchor_text: string
    source_title: string
    target_title: string
    reasoning: string
    quality_score: number
  }>
  thematic_analysis: Record<string, any>
  semantic_metrics: Record<string, any>
  quality_assessment: Record<string, any>
  llm_model_used: string
  llm_context_size?: number
  processing_time_seconds?: number
  created_at: string
  completed_at?: string
}

export interface BenchmarkHistory {
  id: number
  name: string
  benchmark_type: string
  status: string
  overall_score: number | null
  quality_score: number | null
  performance_score: number | null
  duration_seconds: number | null
  created_at: string
  completed_at: string | null
}

// ===== API ТИПЫ =====

export interface WPRequest {
  domain: string
  client_id?: string
  comprehensive?: boolean
}

export interface WPResponse {
  status: 'success' | 'error'
  domain: string
  posts_found: number
  recommendations: Recommendation[]
  delta_stats?: {
    new_posts: number
    updated_posts: number
    unchanged_posts: number
    removed_posts: number
    total_posts: number
  }
  analysis_time?: number
  error?: string
}

// ===== WebSocket ТИПЫ =====

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export interface WebSocketMessage {
  type: 'progress' | 'ai_thinking' | 'enhanced_ai_thinking' | 'ollama' | 'error' | 'ping'
  step?: string
  percentage?: number
  current?: number
  total?: number
  details?: string
  thought?: string
  thinking_stage?: string
  emoji?: string
  stage?: string
  content?: string
  confidence?: number
  semantic_weight?: number
  related_concepts?: string[]
  reasoning_chain?: string[]
  timestamp?: string
  thought_id?: string
  info?: any
  message?: string
}

// ===== UI ТИПЫ =====

export type TabType = 'dashboard' | 'analysis' | 'history' | 'benchmarks' | 'settings'

export interface Theme {
  name: string
  colors: {
    primary: string
    secondary: string
    accent: string
    background: string
    foreground: string
    border: string
    muted: string
  }
  fonts: {
    sans: string[]
    mono: string[]
  }
  spacing: Record<string, string>
  borderRadius: Record<string, string>
}

export interface UserPreferences {
  theme: Theme
  notifications: boolean
  auto_refresh: boolean
  language: string
}

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  duration?: number
  timestamp: string
}

export interface Modal {
  id: string
  title: string
  content: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
  onClose?: () => void
}

export interface AppState {
  domains: Domain[]
  currentDomain: Domain | null
  ollamaStatus: OllamaStatus | null
  analysisHistory: AnalysisHistory[]
  benchmarkHistory: BenchmarkHistory[]
  notifications: Notification[]
  modals: Modal[]
  isLoading: boolean
  error: string | null
}

// ===== УТИЛИТАРНЫЕ ТИПЫ =====

export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number
    limit: number
    total: number
    pages: number
  }
}

export type SortDirection = 'asc' | 'desc'

export interface SortConfig {
  key: string
  direction: SortDirection
}

export interface PaginationConfig {
  page: number
  limit: number
  total: number
}

// ===== ПАРАМЕТРЫ ЗАПРОСОВ =====

export interface AnalysisRequest {
  domain: string
  comprehensive?: boolean
  client_id?: string
}

export interface BenchmarkRequest {
  name: string
  description?: string
  benchmark_type: string
  models: string[]
  iterations: number
  client_id?: string
}

// ===== ДОПОЛНИТЕЛЬНЫЕ ТИПЫ =====

export interface BenchmarkRun {
  id: number
  name: string
  description?: string
  benchmark_type: string
  model_config_id: number
  test_cases_config: Record<string, any>
  iterations: number
  results: Record<string, any>
  metrics: Record<string, any>
  started_at: string
  completed_at?: string
  duration_seconds?: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  error_message?: string
  overall_score?: number
  quality_score?: number
  performance_score?: number
  efficiency_score?: number
  created_at: string
}

export interface ModelConfiguration {
  id: number
  model_name: string
  display_name: string
  description?: string
  model_type: string
  is_active: boolean
  is_available: boolean
  quality_score?: number
  created_at: string
  updated_at: string
}

export interface SemanticConnection {
  id: number
  source_post_id: number
  target_post_id: number
  connection_type: string
  strength: number
  confidence: number
  connection_context?: string
  suggested_anchor?: string
  created_at: string
}

export interface ThematicCluster {
  id: number
  cluster_name: string
  cluster_keywords: string[]
  article_count: number
  coherence_score: number
  linkability_potential: number
  evolution_stage: string
  created_at: string
}

export interface AppSettings {
  theme: 'light' | 'dark' | 'system'
  language: string
  autoRefresh: boolean
  refreshInterval: number
  notifications: boolean
  sound: boolean
}

export interface SearchFilters {
  domain?: string
  dateFrom?: string
  dateTo?: string
  status?: string
  type?: string
  limit?: number
}

export interface PaginationInfo {
  page: number
  limit: number
  total: number
  totalPages: number
  hasNext: boolean
  hasPrev: boolean
}

export interface ExportOptions {
  format: 'json' | 'csv' | 'xlsx'
  includeHistory: boolean
  includeStats: boolean
  dateRange?: {
    from: string
    to: string
  }
}

export interface SystemMetrics {
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  active_connections: number
  requests_per_minute: number
  average_response_time: number
  timestamp: string
}

export interface ErrorLog {
  id: string
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical'
  message: string
  stack?: string
  context?: Record<string, any>
  timestamp: string
  user_id?: string
  session_id?: string
}

export interface ExtendedUserPreferences {
  default_comprehensive_analysis: boolean
  auto_save_results: boolean
  email_notifications: boolean
  dashboard_layout: 'grid' | 'list' | 'compact'
  results_per_page: number
  favorite_domains: string[]
  custom_filters: SearchFilters[]
}

// AIUI Design System - TypeScript Types

// Core UI Types
export interface BaseComponentProps {
  className?: string
  children?: React.ReactNode
}

// Form Types
export interface FormField {
  name: string
  label: string
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'textarea' | 'checkbox' | 'radio'
  required?: boolean
  placeholder?: string
  options?: Array<{ value: string; label: string }>
  validation?: {
    pattern?: string
    min?: number
    max?: number
    message?: string
  }
}

// Chart Types
export interface ChartData {
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
    backgroundColor?: string[]
    borderColor?: string[]
    borderWidth?: number
  }>
}

export interface ChartOptions {
  responsive: boolean
  maintainAspectRatio: boolean
  plugins?: {
    legend?: {
      display: boolean
      position: 'top' | 'bottom' | 'left' | 'right'
    }
    tooltip?: {
      enabled: boolean
    }
  }
  scales?: {
    y?: {
      beginAtZero: boolean
    }
  }
} 