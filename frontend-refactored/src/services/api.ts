import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { ApiResponse, MicroserviceConfig } from '../types';

// Конфигурация микросервисов
const MICROSERVICES: Record<string, MicroserviceConfig> = {
  backend: {
    name: 'backend',
    url: process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000',
    port: 8000,
    health: true,
    version: '4.1.2',
    status: 'online'
  },
  docs: {
    name: 'docs',
    url: process.env.REACT_APP_DOCS_URL || 'http://localhost:8001',
    port: 8001,
    health: true,
    version: '4.1.2',
    status: 'online'
  },
  router: {
    name: 'router',
    url: process.env.REACT_APP_ROUTER_URL || 'http://localhost:8004',
    port: 8004,
    health: true,
    version: '4.1.2',
    status: 'online'
  },
  testing: {
    name: 'testing',
    url: process.env.REACT_APP_TESTING_URL || 'http://localhost:8003',
    port: 8003,
    health: true,
    version: '4.1.2',
    status: 'online'
  },
  monitoring: {
    name: 'monitoring',
    url: process.env.REACT_APP_MONITORING_URL || 'http://localhost:8002',
    port: 8002,
    health: true,
    version: '4.1.2',
    status: 'online'
  }
};

// Создание экземпляров axios для каждого микросервиса
const apiInstances: Record<string, AxiosInstance> = {};

Object.entries(MICROSERVICES).forEach(([name, config]) => {
  apiInstances[name] = axios.create({
    baseURL: config.url,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  });

  // Интерцептор для логирования запросов
  apiInstances[name].interceptors.request.use(
    (config) => {
      console.log(`[API] ${name} -> ${config.method?.toUpperCase()} ${config.url}`);
      return config;
    },
    (error) => {
      console.error(`[API] ${name} request error:`, error);
      return Promise.reject(error);
    }
  );

  // Интерцептор для обработки ответов
  apiInstances[name].interceptors.response.use(
    (response: AxiosResponse) => {
      console.log(`[API] ${name} <- ${response.status} ${response.config.url}`);
      return response;
    },
    (error) => {
      console.error(`[API] ${name} response error:`, error);
      return Promise.reject(error);
    }
  );
});

// Базовый класс для API сервисов
export abstract class BaseApiService {
  protected instance: AxiosInstance;
  protected serviceName: string;

  constructor(serviceName: string) {
    this.serviceName = serviceName;
    this.instance = apiInstances[serviceName];
    
    if (!this.instance) {
      throw new Error(`API instance for service '${serviceName}' not found`);
    }
  }

  protected async request<T>(config: any): Promise<ApiResponse<T>> {
    try {
      const response = await this.instance.request(config);
      return {
        success: true,
        data: response.data,
        timestamp: new Date().toISOString(),
        service: this.serviceName,
        version: MICROSERVICES[this.serviceName].version
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.error || error.message || 'Unknown error',
        message: error.response?.data?.message || 'Request failed',
        timestamp: new Date().toISOString(),
        service: this.serviceName,
        version: MICROSERVICES[this.serviceName].version
      };
    }
  }

  protected async get<T>(url: string, params?: any): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'GET',
      url,
      params
    });
  }

  protected async post<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'POST',
      url,
      data
    });
  }

  protected async put<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'PUT',
      url,
      data
    });
  }

  protected async delete<T>(url: string): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'DELETE',
      url
    });
  }

  protected async patch<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'PATCH',
      url,
      data
    });
  }
}

// Сервис для работы с доменами (Backend)
export class DomainsService extends BaseApiService {
  constructor() {
    super('backend');
  }

  async getDomains(): Promise<ApiResponse<any[]>> {
    return this.get('/api/v1/domains');
  }

  async getDomain(id: string): Promise<ApiResponse<any>> {
    return this.get(`/api/v1/domains/${id}`);
  }

  async createDomain(domain: { url: string; name?: string }): Promise<ApiResponse<any>> {
    return this.post('/api/v1/domains', domain);
  }

  async updateDomain(id: string, data: any): Promise<ApiResponse<any>> {
    return this.put(`/api/v1/domains/${id}`, data);
  }

  async deleteDomain(id: string): Promise<ApiResponse<void>> {
    return this.delete(`/api/v1/domains/${id}`);
  }

  async analyzeDomain(id: string, options?: any): Promise<ApiResponse<any>> {
    return this.post(`/api/v1/domains/${id}/analyze`, options);
  }

  async getAnalysisHistory(domainId?: string): Promise<ApiResponse<any[]>> {
    const params = domainId ? { domain_id: domainId } : {};
    return this.get('/api/v1/analysis_history', params);
  }
}

// Сервис для работы с LLM роутером
export class RouterService extends BaseApiService {
  constructor() {
    super('router');
  }

  async routeRequest(request: any): Promise<ApiResponse<any>> {
    return this.post('/api/v1/route', request);
  }

  async getModels(): Promise<ApiResponse<any[]>> {
    return this.get('/api/v1/models');
  }

  async getModelPerformance(modelId: string): Promise<ApiResponse<any>> {
    return this.get(`/api/v1/models/${modelId}/performance`);
  }

  async batchProcess(requests: any[]): Promise<ApiResponse<any[]>> {
    return this.post('/api/v1/batch', { requests });
  }

  async getEfficiencyMetrics(): Promise<ApiResponse<any>> {
    return this.get('/api/v1/efficiency');
  }
}

// Сервис для работы с тестированием
export class TestingService extends BaseApiService {
  constructor() {
    super('testing');
  }

  async runTest(testConfig: any): Promise<ApiResponse<any>> {
    return this.post('/api/v1/tests/run', testConfig);
  }

  async getTestResults(testId: string): Promise<ApiResponse<any>> {
    return this.get(`/api/v1/tests/${testId}/results`);
  }

  async getTestHistory(): Promise<ApiResponse<any[]>> {
    return this.get('/api/v1/tests/history');
  }

  async createTest(testConfig: any): Promise<ApiResponse<any>> {
    return this.post('/api/v1/tests', testConfig);
  }

  async updateTest(testId: string, testConfig: any): Promise<ApiResponse<any>> {
    return this.put(`/api/v1/tests/${testId}`, testConfig);
  }

  async deleteTest(testId: string): Promise<ApiResponse<void>> {
    return this.delete(`/api/v1/tests/${testId}`);
  }
}

// Сервис для работы с мониторингом
export class MonitoringService extends BaseApiService {
  constructor() {
    super('monitoring');
  }

  async getSystemMetrics(): Promise<ApiResponse<any>> {
    return this.get('/api/v1/metrics/system');
  }

  async getServiceHealth(): Promise<ApiResponse<any[]>> {
    return this.get('/api/v1/health/services');
  }

  async getAlerts(): Promise<ApiResponse<any[]>> {
    return this.get('/api/v1/alerts');
  }

  async acknowledgeAlert(alertId: string): Promise<ApiResponse<any>> {
    return this.post(`/api/v1/alerts/${alertId}/acknowledge`);
  }

  async getPerformanceMetrics(timeRange?: string): Promise<ApiResponse<any>> {
    const params = timeRange ? { time_range: timeRange } : {};
    return this.get('/api/v1/metrics/performance', params);
  }
}

// Сервис для работы с документацией
export class DocsService extends BaseApiService {
  constructor() {
    super('docs');
  }

  async getDocumentation(path?: string): Promise<ApiResponse<any>> {
    const url = path ? `/api/v1/docs/${path}` : '/api/v1/docs';
    return this.get(url);
  }

  async searchDocs(query: string): Promise<ApiResponse<any[]>> {
    return this.get('/api/v1/docs/search', { q: query });
  }

  async getApiDocs(): Promise<ApiResponse<any>> {
    return this.get('/api/v1/docs/api');
  }

  async getVersion(): Promise<ApiResponse<any>> {
    return this.get('/api/v1/version');
  }
}

// Экспорт экземпляров сервисов
export const domainsService = new DomainsService();
export const routerService = new RouterService();
export const testingService = new TestingService();
export const monitoringService = new MonitoringService();
export const docsService = new DocsService();

// Функция для проверки здоровья всех микросервисов
export async function checkMicroservicesHealth(): Promise<Record<string, boolean>> {
  const healthStatus: Record<string, boolean> = {};
  
  for (const [name, config] of Object.entries(MICROSERVICES)) {
    try {
      const response = await apiInstances[name].get('/health');
      healthStatus[name] = response.status === 200;
    } catch (error) {
      healthStatus[name] = false;
    }
  }
  
  return healthStatus;
}

// Функция для получения конфигурации микросервисов
export function getMicroservicesConfig(): Record<string, MicroserviceConfig> {
  return { ...MICROSERVICES };
} 