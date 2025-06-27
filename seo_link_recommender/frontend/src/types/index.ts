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

export interface LinkRecommendation {
  from: string
  to: string
  anchor: string
  comment: string
  quality_score?: number
}

export interface AnalysisStats {
  current: number
  total: number
  details?: string
}

export interface AIThought {
  id: string
  type: 'ai_thinking' | 'enhanced_ai_thinking' | 'progress' | 'ollama' | 'error'
  thought?: string
  thinking_stage?: string
  emoji?: string
  stage?: string
  content?: string
  confidence?: number
  semantic_weight?: number
  related_concepts?: string[]
  reasoning_chain?: string[]
  timestamp: string
}

export interface OllamaStatus {
  ready_for_work: boolean
  server_available: boolean
  model_loaded: boolean
  message: string
  status?: string
  connection?: string
  models_count?: number
  available_models?: string[]
  timestamp?: string
  last_check?: string
}

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: string
  duration?: number
}

export interface AnalysisHistory {
  id: number
  domain_id: number
  posts_analyzed: number
  connections_found: number
  recommendations_generated: number
  llm_model_used: string
  processing_time_seconds?: number
  created_at: string
  completed_at?: string
}

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
  recommendations: LinkRecommendation[]
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

export interface WebSocketMessage {
  type: 'progress' | 'ai_thinking' | 'enhanced_ai_thinking' | 'ollama' | 'error' | 'ping'
  step?: string
  current?: number
  total?: number
  percentage?: number
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
  info?: any
  message?: string
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

// ===== УТИЛИТАРНЫЕ ТИПЫ =====

export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

export interface ApiResponse<T> {
  data?: T
  error?: string
  status: number
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