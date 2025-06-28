// ===== МИКРОСЕРВИСНАЯ АРХИТЕКТУРА TYPES =====

// 🚀 LLM TUNING MICROSERVICE TYPES
export interface LLMModel {
  id: string
  name: string
  display_name: string
  version: string
  model_type: 'base' | 'tuned' | 'custom'
  status: 'available' | 'loading' | 'error' | 'unavailable'
  parameters: number
  context_length: number
  quality_score?: number
  performance_score?: number
  last_used?: string
  created_at: string
  updated_at: string
}

export interface ABTestConfig {
  id: string
  name: string
  description: string
  models: string[]
  test_cases: ABTestCase[]
  traffic_split: Record<string, number>
  metrics: string[]
  duration_hours: number
  status: 'draft' | 'running' | 'completed' | 'paused'
  created_at: string
  started_at?: string
  completed_at?: string
}

export interface ABTestCase {
  id: string
  name: string
  input_text: string
  expected_output?: string
  category: string
  difficulty: 'easy' | 'medium' | 'hard'
  weight: number
}

export interface ABTestResult {
  test_id: string
  model_name: string
  test_case_id: string
  input: string
  output: string
  quality_score: number
  performance_metrics: {
    response_time_ms: number
    tokens_per_second: number
    memory_usage_mb: number
  }
  user_feedback?: {
    rating: number
    comment?: string
  }
  timestamp: string
}

export interface RAGDocument {
  id: string
  content: string
  metadata: Record<string, any>
  embedding?: number[]
  source: string
  created_at: string
  updated_at: string
}

export interface RAGQuery {
  query: string
  top_k: number
  similarity_threshold: number
  filters?: Record<string, any>
}

export interface RAGResponse {
  answer: string
  sources: RAGDocument[]
  confidence: number
  reasoning: string
  metadata: {
    tokens_used: number
    response_time_ms: number
    model_used: string
  }
}

// 📊 MONITORING MICROSERVICE TYPES
export interface SystemHealth {
  overall_status: 'healthy' | 'warning' | 'critical'
  services: ServiceHealth[]
  resources: ResourceUsage
  alerts: Alert[]
  last_check: string
}

export interface ServiceHealth {
  name: string
  status: 'healthy' | 'warning' | 'critical' | 'unknown'
  response_time_ms: number
  uptime_percentage: number
  last_check: string
  error_message?: string
}

export interface ResourceUsage {
  cpu: {
    usage_percent: number
    cores: number
    temperature?: number
  }
  memory: {
    used_mb: number
    total_mb: number
    usage_percent: number
  }
  disk: {
    used_gb: number
    total_gb: number
    usage_percent: number
  }
  network: {
    bytes_sent: number
    bytes_received: number
    connections: number
  }
}

export interface Alert {
  id: string
  level: 'info' | 'warning' | 'critical'
  title: string
  message: string
  service: string
  timestamp: string
  acknowledged: boolean
  resolved: boolean
}

// 🧪 TESTING MICROSERVICE TYPES
export interface TestSuite {
  id: string
  name: string
  description: string
  test_cases: TestCase[]
  environment: TestEnvironment
  status: 'draft' | 'running' | 'completed' | 'failed'
  created_at: string
  started_at?: string
  completed_at?: string
}

export interface TestCase {
  id: string
  name: string
  description: string
  type: 'unit' | 'integration' | 'e2e' | 'performance'
  endpoint: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  headers?: Record<string, string>
  body?: any
  expected_status: number
  expected_response?: any
  timeout_ms: number
  retries: number
}

export interface TestEnvironment {
  name: string
  base_url: string
  variables: Record<string, string>
  headers: Record<string, string>
}

export interface TestResult {
  test_id: string
  test_case_id: string
  status: 'passed' | 'failed' | 'skipped' | 'error'
  duration_ms: number
  response: {
    status: number
    headers: Record<string, string>
    body: any
  }
  error?: string
  timestamp: string
}

// 📚 DOCS MICROSERVICE TYPES
export interface DocumentationPage {
  id: string
  title: string
  content: string
  category: string
  tags: string[]
  version: string
  author: string
  created_at: string
  updated_at: string
  read_time_minutes: number
}

export interface DocumentationSearch {
  query: string
  category?: string
  tags?: string[]
  version?: string
  limit: number
  offset: number
}

export interface DocumentationSearchResult {
  pages: DocumentationPage[]
  total: number
  query_time_ms: number
  suggestions: string[]
}

// 🔧 BENCHMARK MICROSERVICE TYPES
export interface BenchmarkSuite {
  id: string
  name: string
  description: string
  category: string
  metrics: BenchmarkMetric[]
  test_data: BenchmarkTestData[]
  created_at: string
  updated_at: string
}

export interface BenchmarkMetric {
  name: string
  description: string
  unit: string
  higher_is_better: boolean
  weight: number
}

export interface BenchmarkTestData {
  id: string
  name: string
  category: string
  data: any
  metadata: Record<string, any>
}

export interface BenchmarkRun {
  id: string
  suite_id: string
  model_name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  results: BenchmarkResult[]
  summary: BenchmarkSummary
  started_at: string
  completed_at?: string
  duration_seconds?: number
}

export interface BenchmarkResult {
  metric_name: string
  value: number
  unit: string
  rank?: number
  percentile?: number
}

export interface BenchmarkSummary {
  overall_score: number
  quality_score: number
  performance_score: number
  efficiency_score: number
  total_metrics: number
  passed_metrics: number
  failed_metrics: number
}

// 🌐 API GATEWAY TYPES
export interface ServiceRegistry {
  services: Microservice[]
  health_check_interval: number
  last_updated: string
}

export interface Microservice {
  name: string
  version: string
  status: 'healthy' | 'warning' | 'critical' | 'unknown'
  endpoints: ServiceEndpoint[]
  health_url: string
  metrics_url?: string
  documentation_url?: string
  last_heartbeat: string
}

export interface ServiceEndpoint {
  path: string
  method: string
  description: string
  rate_limit?: number
  requires_auth: boolean
  deprecated: boolean
}

// 🔄 INTEGRATION TYPES
export interface ServiceIntegration {
  service_name: string
  base_url: string
  api_version: string
  authentication: AuthConfig
  rate_limits: RateLimitConfig
  retry_config: RetryConfig
  timeout_ms: number
  enabled: boolean
}

export interface AuthConfig {
  type: 'none' | 'api_key' | 'bearer' | 'oauth2'
  api_key?: string
  bearer_token?: string
  oauth2_config?: OAuth2Config
}

export interface OAuth2Config {
  client_id: string
  client_secret: string
  token_url: string
  scope: string
}

export interface RateLimitConfig {
  requests_per_minute: number
  burst_limit: number
  window_size_ms: number
}

export interface RetryConfig {
  max_retries: number
  backoff_factor: number
  max_backoff_ms: number
  retry_on_status_codes: number[]
}

// 📈 ANALYTICS TYPES
export interface AnalyticsEvent {
  id: string
  event_type: string
  user_id?: string
  session_id: string
  timestamp: string
  properties: Record<string, any>
  context: {
    user_agent: string
    ip_address?: string
    referrer?: string
    page_url: string
  }
}

export interface AnalyticsMetric {
  name: string
  value: number
  unit: string
  timestamp: string
  tags: Record<string, string>
}

export interface AnalyticsDashboard {
  id: string
  name: string
  description: string
  widgets: AnalyticsWidget[]
  refresh_interval: number
  created_at: string
  updated_at: string
}

export interface AnalyticsWidget {
  id: string
  type: 'chart' | 'metric' | 'table' | 'list'
  title: string
  query: string
  config: Record<string, any>
  position: {
    x: number
    y: number
    width: number
    height: number
  }
}

// 🎨 UI INTEGRATION TYPES
export interface ServiceCard {
  service: Microservice
  metrics: ServiceMetrics
  actions: ServiceAction[]
  status: 'online' | 'offline' | 'warning' | 'maintenance'
}

export interface ServiceMetrics {
  response_time_ms: number
  requests_per_minute: number
  error_rate: number
  uptime_percentage: number
  last_24h_requests: number
}

export interface ServiceAction {
  name: string
  label: string
  icon: string
  action: () => void
  disabled?: boolean
  loading?: boolean
}

// 🔍 SEARCH TYPES
export interface GlobalSearchQuery {
  query: string
  filters: {
    services?: string[]
    categories?: string[]
    date_from?: string
    date_to?: string
  }
  limit: number
  offset: number
}

export interface GlobalSearchResult {
  results: SearchResult[]
  total: number
  query_time_ms: number
  suggestions: string[]
  facets: SearchFacet[]
}

export interface SearchResult {
  id: string
  type: 'domain' | 'analysis' | 'benchmark' | 'documentation' | 'test'
  title: string
  description: string
  url: string
  service: string
  relevance_score: number
  created_at: string
  updated_at: string
  metadata: Record<string, any>
}

export interface SearchFacet {
  name: string
  values: Array<{
    value: string
    count: number
  }>
}

// 🎯 WORKFLOW TYPES
export interface Workflow {
  id: string
  name: string
  description: string
  steps: WorkflowStep[]
  triggers: WorkflowTrigger[]
  status: 'draft' | 'active' | 'paused' | 'archived'
  created_at: string
  updated_at: string
}

export interface WorkflowStep {
  id: string
  name: string
  type: 'analysis' | 'benchmark' | 'test' | 'notification' | 'export'
  service: string
  config: Record<string, any>
  dependencies: string[]
  timeout_seconds: number
  retry_config: RetryConfig
}

export interface WorkflowTrigger {
  type: 'manual' | 'schedule' | 'webhook' | 'event'
  config: Record<string, any>
}

export interface WorkflowExecution {
  id: string
  workflow_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  current_step: string
  progress: number
  results: Record<string, any>
  started_at: string
  completed_at?: string
  error?: string
}

// 🎨 THEME & BRANDING TYPES
export interface ServiceTheme {
  service_name: string
  colors: {
    primary: string
    secondary: string
    accent: string
    success: string
    warning: string
    error: string
  }
  logo_url?: string
  favicon_url?: string
  custom_css?: string
}

export interface ServiceBranding {
  name: string
  display_name: string
  description: string
  version: string
  theme: ServiceTheme
  features: string[]
  capabilities: string[]
  documentation_url?: string
  support_url?: string
} 