import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  domainsService, 
  routerService, 
  testingService, 
  monitoringService, 
  docsService,
  checkMicroservicesHealth,
  getMicroservicesConfig
} from '../services/api';
import { 
  Domain, 
  AnalysisResult, 
  LLMModel, 
  SystemMetrics, 
  Alert,
  Notification,
  Benchmark,
  BenchmarkResult
} from '../types';

// Хуки для работы с доменами
export function useDomains() {
  return useQuery({
    queryKey: ['domains'],
    queryFn: async () => {
      const response = await domainsService.getDomains();
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch domains');
      }
      return response.data as Domain[];
    },
    staleTime: 5 * 60 * 1000, // 5 минут
    gcTime: 10 * 60 * 1000, // 10 минут
  });
}

export function useDomain(id: string) {
  return useQuery({
    queryKey: ['domains', id],
    queryFn: async () => {
      const response = await domainsService.getDomain(id);
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch domain');
      }
      return response.data as Domain;
    },
    enabled: !!id,
    staleTime: 2 * 60 * 1000, // 2 минуты
  });
}

export function useCreateDomain() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (domain: { url: string; name?: string }) => {
      const response = await domainsService.createDomain(domain);
      if (!response.success) {
        throw new Error(response.error || 'Failed to create domain');
      }
      return response.data as Domain;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['domains'] });
    },
  });
}

export function useUpdateDomain() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const response = await domainsService.updateDomain(id, data);
      if (!response.success) {
        throw new Error(response.error || 'Failed to update domain');
      }
      return response.data as Domain;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['domains'] });
      queryClient.invalidateQueries({ queryKey: ['domains', data.id] });
    },
  });
}

export function useDeleteDomain() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await domainsService.deleteDomain(id);
      if (!response.success) {
        throw new Error(response.error || 'Failed to delete domain');
      }
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['domains'] });
    },
  });
}

export function useAnalyzeDomain() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, options }: { id: string; options?: any }) => {
      const response = await domainsService.analyzeDomain(id, options);
      if (!response.success) {
        throw new Error(response.error || 'Failed to analyze domain');
      }
      return response.data as AnalysisResult;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['domains'] });
      queryClient.invalidateQueries({ queryKey: ['analysis_history'] });
      queryClient.setQueryData(['analysis', data.id], data);
    },
  });
}

export function useAnalysisHistory(domainId?: string) {
  return useQuery({
    queryKey: ['analysis_history', domainId],
    queryFn: async () => {
      const response = await domainsService.getAnalysisHistory(domainId);
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch analysis history');
      }
      return response.data as AnalysisResult[];
    },
    staleTime: 2 * 60 * 1000, // 2 минуты
  });
}

// Хуки для работы с LLM роутером
export function useLLMModels() {
  return useQuery({
    queryKey: ['llm_models'],
    queryFn: async () => {
      const response = await routerService.getModels();
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch LLM models');
      }
      return response.data as LLMModel[];
    },
    staleTime: 1 * 60 * 1000, // 1 минута
  });
}

export function useModelPerformance(modelId: string) {
  return useQuery({
    queryKey: ['model_performance', modelId],
    queryFn: async () => {
      const response = await routerService.getModelPerformance(modelId);
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch model performance');
      }
      return response.data;
    },
    enabled: !!modelId,
    staleTime: 30 * 1000, // 30 секунд
  });
}

export function useRouteRequest() {
  return useMutation({
    mutationFn: async (request: any) => {
      const response = await routerService.routeRequest(request);
      if (!response.success) {
        throw new Error(response.error || 'Failed to route request');
      }
      return response.data;
    },
  });
}

export function useBatchProcess() {
  return useMutation({
    mutationFn: async (requests: any[]) => {
      const response = await routerService.batchProcess(requests);
      if (!response.success) {
        throw new Error(response.error || 'Failed to process batch');
      }
      return response.data;
    },
  });
}

export function useEfficiencyMetrics() {
  return useQuery({
    queryKey: ['efficiency_metrics'],
    queryFn: async () => {
      const response = await routerService.getEfficiencyMetrics();
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch efficiency metrics');
      }
      return response.data;
    },
    staleTime: 30 * 1000, // 30 секунд
  });
}

// Хуки для работы с тестированием
export function useTestHistory() {
  return useQuery({
    queryKey: ['test_history'],
    queryFn: async () => {
      const response = await testingService.getTestHistory();
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch test history');
      }
      return response.data as BenchmarkResult[];
    },
    staleTime: 2 * 60 * 1000, // 2 минуты
  });
}

export function useRunTest() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (testConfig: any) => {
      const response = await testingService.runTest(testConfig);
      if (!response.success) {
        throw new Error(response.error || 'Failed to run test');
      }
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['test_history'] });
    },
  });
}

export function useTestResults(testId: string) {
  return useQuery({
    queryKey: ['test_results', testId],
    queryFn: async () => {
      const response = await testingService.getTestResults(testId);
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch test results');
      }
      return response.data;
    },
    enabled: !!testId,
    staleTime: 1 * 60 * 1000, // 1 минута
  });
}

// Хуки для работы с мониторингом
export function useSystemMetrics() {
  return useQuery({
    queryKey: ['system_metrics'],
    queryFn: async () => {
      const response = await monitoringService.getSystemMetrics();
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch system metrics');
      }
      return response.data as SystemMetrics;
    },
    staleTime: 10 * 1000, // 10 секунд
    refetchInterval: 30 * 1000, // Обновление каждые 30 секунд
  });
}

export function useServiceHealth() {
  return useQuery({
    queryKey: ['service_health'],
    queryFn: async () => {
      const response = await monitoringService.getServiceHealth();
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch service health');
      }
      return response.data;
    },
    staleTime: 30 * 1000, // 30 секунд
    refetchInterval: 60 * 1000, // Обновление каждую минуту
  });
}

export function useAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      const response = await monitoringService.getAlerts();
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch alerts');
      }
      return response.data as Alert[];
    },
    staleTime: 30 * 1000, // 30 секунд
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (alertId: string) => {
      const response = await monitoringService.acknowledgeAlert(alertId);
      if (!response.success) {
        throw new Error(response.error || 'Failed to acknowledge alert');
      }
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}

export function usePerformanceMetrics(timeRange?: string) {
  return useQuery({
    queryKey: ['performance_metrics', timeRange],
    queryFn: async () => {
      const response = await monitoringService.getPerformanceMetrics(timeRange);
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch performance metrics');
      }
      return response.data;
    },
    staleTime: 1 * 60 * 1000, // 1 минута
  });
}

// Хуки для работы с документацией
export function useDocumentation(path?: string) {
  return useQuery({
    queryKey: ['documentation', path],
    queryFn: async () => {
      const response = await docsService.getDocumentation(path);
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch documentation');
      }
      return response.data;
    },
    staleTime: 10 * 60 * 1000, // 10 минут
  });
}

export function useSearchDocs() {
  return useMutation({
    mutationFn: async (query: string) => {
      const response = await docsService.searchDocs(query);
      if (!response.success) {
        throw new Error(response.error || 'Failed to search documentation');
      }
      return response.data;
    },
  });
}

export function useApiDocs() {
  return useQuery({
    queryKey: ['api_docs'],
    queryFn: async () => {
      const response = await docsService.getApiDocs();
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch API docs');
      }
      return response.data;
    },
    staleTime: 30 * 60 * 1000, // 30 минут
  });
}

export function useVersion() {
  return useQuery({
    queryKey: ['version'],
    queryFn: async () => {
      const response = await docsService.getVersion();
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch version');
      }
      return response.data;
    },
    staleTime: 60 * 60 * 1000, // 1 час
  });
}

// Хуки для работы с микросервисами
export function useMicroservicesHealth() {
  return useQuery({
    queryKey: ['microservices_health'],
    queryFn: checkMicroservicesHealth,
    staleTime: 30 * 1000, // 30 секунд
    refetchInterval: 60 * 1000, // Обновление каждую минуту
  });
}

export function useMicroservicesConfig() {
  return useQuery({
    queryKey: ['microservices_config'],
    queryFn: getMicroservicesConfig,
    staleTime: 60 * 60 * 1000, // 1 час
  });
} 