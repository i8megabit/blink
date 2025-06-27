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
  from: string
  to: string
  anchor: string
  comment: string
  quality_score?: number
}

export interface AnalysisStats {
  current?: number
  total?: number
  details?: string
  postsAnalyzed?: number
  connectionsFound?: number
  recommendationsGenerated?: number
  processingTime?: number
}

export interface AIThought {
  id?: string
  thought_id?: string
  type?: 'ai_thinking' | 'enhanced_ai_thinking' | 'progress' | 'ollama' | 'error'
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
  status: 'ready' | 'connecting' | 'error'
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
  llm_model_used: string
  processing_time_seconds: number | null
  created_at: string
  completed_at: string | null
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
  type: 'progress' | 'error' | 'ollama' | 'ai_thinking' | 'enhanced_ai_thinking' | 'ping'
  step?: string
  current?: number
  total?: number
  percentage?: number
  details?: string
  message?: string
  error?: string
  info?: any
  thought?: string
  thinking_stage?: string
  emoji?: string
  thought_id?: string
  stage?: string
  content?: string
  confidence?: number
  semantic_weight?: number
  related_concepts?: string[]
  reasoning_chain?: string[]
  timestamp: string
}

// ===== UI ТИПЫ =====

export type TabType = 'dashboard' | 'analysis' | 'history' | 'benchmarks' | 'settings'

export interface Theme {
  mode: 'light' | 'dark' | 'system'
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
  details?: string
  timestamp: Date
  duration?: number
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

export interface ApiResponse<T = any> {
  status: 'success' | 'error'
  data?: T
  error?: string
  message?: string
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
  benchmark_type: string
  status: string
  overall_score?: number
  quality_score?: number
  performance_score?: number
  duration_seconds?: number
  created_at: string
  completed_at?: string
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