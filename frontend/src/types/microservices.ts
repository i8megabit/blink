export interface Microservice {
  name: string;
  port: number;
  description: string;
  status: 'active' | 'inactive' | 'unknown';
  health?: HealthStatus;
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'unknown';
  timestamp: string;
  response_time?: number;
  error?: string;
}

export interface ServiceEndpoint {
  path: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  description: string;
  parameters?: Record<string, any>;
}

export interface ServiceAPI {
  service: string;
  base_url: string;
  endpoints: ServiceEndpoint[];
  swagger_url?: string;
}

export interface MicroserviceConfig {
  services: Microservice[];
  default_timeout: number;
  retry_attempts: number;
  circuit_breaker: {
    failure_threshold: number;
    recovery_timeout: number;
  };
} 