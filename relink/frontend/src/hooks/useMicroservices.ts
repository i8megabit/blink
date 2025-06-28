// ===== ХУКИ ДЛЯ МИКРОСЕРВИСОВ =====

import { useState, useEffect, useCallback } from 'react'
import { 
  microserviceManager,
  llmTuningClient,
  monitoringClient,
  testingClient,
  docsClient,
  benchmarkClient,
  searchClient,
  workflowClient
} from '../lib/microservices'
import { 
  Microservice,
  LLMModel,
  ABTestConfig,
  SystemHealth,
  TestSuite,
  DocumentationPage,
  BenchmarkSuite,
  RAGQuery,
  RAGResponse,
  GlobalSearchQuery,
  GlobalSearchResult,
  Workflow,
  WorkflowExecution
} from '../types/microservices'

// 🚀 ХУК ДЛЯ МОНИТОРИНГА СЕРВИСОВ
export const useServicesHealth = () => {
  const [services, setServices] = useState<Microservice[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchServices = useCallback(async () => {
    try {
      setLoading(true)
      const healthData = await microserviceManager.getAllServicesHealth()
      setServices(healthData)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка получения статуса сервисов')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchServices()
    
    // Автоматическое обновление каждые 30 секунд
    const interval = setInterval(fetchServices, 30000)
    
    return () => clearInterval(interval)
  }, [fetchServices])

  return { services, loading, error, refetch: fetchServices }
}

// 🧠 ХУК ДЛЯ LLM МОДЕЛЕЙ
export const useLLMModels = () => {
  const [models, setModels] = useState<LLMModel[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchModels = useCallback(async () => {
    try {
      setLoading(true)
      const data = await llmTuningClient.getModels()
      setModels(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка получения моделей')
    } finally {
      setLoading(false)
    }
  }, [])

  const createModel = useCallback(async (modelData: Partial<LLMModel>) => {
    try {
      const newModel = await llmTuningClient.createModel(modelData)
      setModels(prev => [...prev, newModel])
      return newModel
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка создания модели')
      throw err
    }
  }, [])

  const updateModel = useCallback(async (modelId: string, modelData: Partial<LLMModel>) => {
    try {
      const updatedModel = await llmTuningClient.updateModel(modelId, modelData)
      setModels(prev => prev.map(model => model.id === modelId ? updatedModel : model))
      return updatedModel
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка обновления модели')
      throw err
    }
  }, [])

  const deleteModel = useCallback(async (modelId: string) => {
    try {
      await llmTuningClient.deleteModel(modelId)
      setModels(prev => prev.filter(model => model.id !== modelId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка удаления модели')
      throw err
    }
  }, [])

  useEffect(() => {
    fetchModels()
  }, [fetchModels])

  return { 
    models, 
    loading, 
    error, 
    refetch: fetchModels,
    createModel,
    updateModel,
    deleteModel
  }
}

// 🧪 ХУК ДЛЯ A/B ТЕСТИРОВАНИЯ
export const useABTests = () => {
  const [tests, setTests] = useState<ABTestConfig[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTests = useCallback(async () => {
    try {
      setLoading(true)
      const data = await llmTuningClient.getABTests()
      setTests(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка получения A/B тестов')
    } finally {
      setLoading(false)
    }
  }, [])

  const createTest = useCallback(async (testData: Partial<ABTestConfig>) => {
    try {
      const newTest = await llmTuningClient.createABTest(testData)
      setTests(prev => [...prev, newTest])
      return newTest
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка создания A/B теста')
      throw err
    }
  }, [])

  const startTest = useCallback(async (testId: string) => {
    try {
      const updatedTest = await llmTuningClient.startABTest(testId)
      setTests(prev => prev.map(test => test.id === testId ? updatedTest : test))
      return updatedTest
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка запуска A/B теста')
      throw err
    }
  }, [])

  const stopTest = useCallback(async (testId: string) => {
    try {
      const updatedTest = await llmTuningClient.stopABTest(testId)
      setTests(prev => prev.map(test => test.id === testId ? updatedTest : test))
      return updatedTest
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка остановки A/B теста')
      throw err
    }
  }, [])

  useEffect(() => {
    fetchTests()
  }, [fetchTests])

  return { 
    tests, 
    loading, 
    error, 
    refetch: fetchTests,
    createTest,
    startTest,
    stopTest
  }
}

// 📊 ХУК ДЛЯ МОНИТОРИНГА
export const useSystemMonitoring = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchHealth = useCallback(async () => {
    try {
      setLoading(true)
      const data = await monitoringClient.getSystemHealth()
      setHealth(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка получения состояния системы')
    } finally {
      setLoading(false)
    }
  }, [])

  const acknowledgeAlert = useCallback(async (alertId: string) => {
    try {
      await monitoringClient.acknowledgeAlert(alertId)
      // Обновляем состояние после подтверждения алерта
      fetchHealth()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка подтверждения алерта')
      throw err
    }
  }, [fetchHealth])

  useEffect(() => {
    fetchHealth()
    
    // Автоматическое обновление каждые 10 секунд
    const interval = setInterval(fetchHealth, 10000)
    
    return () => clearInterval(interval)
  }, [fetchHealth])

  return { 
    health, 
    loading, 
    error, 
    refetch: fetchHealth,
    acknowledgeAlert
  }
}

// 🧪 ХУК ДЛЯ ТЕСТИРОВАНИЯ
export const useTesting = () => {
  const [testSuites, setTestSuites] = useState<TestSuite[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTestSuites = useCallback(async () => {
    try {
      setLoading(true)
      const data = await testingClient.getTestSuites()
      setTestSuites(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка получения тестовых наборов')
    } finally {
      setLoading(false)
    }
  }, [])

  const createTestSuite = useCallback(async (suiteData: Partial<TestSuite>) => {
    try {
      const newSuite = await testingClient.createTestSuite(suiteData)
      setTestSuites(prev => [...prev, newSuite])
      return newSuite
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка создания тестового набора')
      throw err
    }
  }, [])

  const runTestSuite = useCallback(async (suiteId: string) => {
    try {
      const result = await testingClient.runTestSuite(suiteId)
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка запуска тестового набора')
      throw err
    }
  }, [])

  useEffect(() => {
    fetchTestSuites()
  }, [fetchTestSuites])

  return { 
    testSuites, 
    loading, 
    error, 
    refetch: fetchTestSuites,
    createTestSuite,
    runTestSuite
  }
}

// 📚 ХУК ДЛЯ ДОКУМЕНТАЦИИ
export const useDocumentation = () => {
  const [searchResults, setSearchResults] = useState<DocumentationPage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const searchDocs = useCallback(async (query: string, filters?: any) => {
    try {
      setLoading(true)
      const results = await docsClient.searchDocs(query, filters)
      setSearchResults(results)
      setError(null)
      return results
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка поиска документации')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const getDocPage = useCallback(async (pageId: string) => {
    try {
      const page = await docsClient.getDocPage(pageId)
      return page
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка получения страницы документации')
      throw err
    }
  }, [])

  return { 
    searchResults, 
    loading, 
    error, 
    searchDocs,
    getDocPage
  }
}

// 🔧 ХУК ДЛЯ БЕНЧМАРКОВ
export const useBenchmarks = () => {
  const [benchmarkSuites, setBenchmarkSuites] = useState<BenchmarkSuite[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchBenchmarkSuites = useCallback(async () => {
    try {
      setLoading(true)
      const data = await benchmarkClient.getBenchmarkSuites()
      setBenchmarkSuites(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка получения наборов бенчмарков')
    } finally {
      setLoading(false)
    }
  }, [])

  const createBenchmarkSuite = useCallback(async (suiteData: Partial<BenchmarkSuite>) => {
    try {
      const newSuite = await benchmarkClient.createBenchmarkSuite(suiteData)
      setBenchmarkSuites(prev => [...prev, newSuite])
      return newSuite
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка создания набора бенчмарков')
      throw err
    }
  }, [])

  const runBenchmarkSuite = useCallback(async (suiteId: string, modelName: string) => {
    try {
      const result = await benchmarkClient.runBenchmarkSuite(suiteId, modelName)
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка запуска бенчмарка')
      throw err
    }
  }, [])

  useEffect(() => {
    fetchBenchmarkSuites()
  }, [fetchBenchmarkSuites])

  return { 
    benchmarkSuites, 
    loading, 
    error, 
    refetch: fetchBenchmarkSuites,
    createBenchmarkSuite,
    runBenchmarkSuite
  }
}

// 🔍 ХУК ДЛЯ ГЛОБАЛЬНОГО ПОИСКА
export const useGlobalSearch = () => {
  const [searchResults, setSearchResults] = useState<GlobalSearchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = useCallback(async (query: GlobalSearchQuery) => {
    try {
      setLoading(true)
      const results = await searchClient.globalSearch(query)
      setSearchResults(results)
      setError(null)
      return results
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка глобального поиска')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const getSuggestions = useCallback(async (query: string) => {
    try {
      const suggestions = await searchClient.getSearchSuggestions(query)
      return suggestions
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка получения подсказок')
      throw err
    }
  }, [])

  return { 
    searchResults, 
    loading, 
    error, 
    search,
    getSuggestions
  }
}

// 🎯 ХУК ДЛЯ WORKFLOW
export const useWorkflows = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchWorkflows = useCallback(async () => {
    try {
      setLoading(true)
      const data = await workflowClient.getWorkflows()
      setWorkflows(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка получения workflow')
    } finally {
      setLoading(false)
    }
  }, [])

  const createWorkflow = useCallback(async (workflowData: Partial<Workflow>) => {
    try {
      const newWorkflow = await workflowClient.createWorkflow(workflowData)
      setWorkflows(prev => [...prev, newWorkflow])
      return newWorkflow
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка создания workflow')
      throw err
    }
  }, [])

  const executeWorkflow = useCallback(async (workflowId: string) => {
    try {
      const execution = await workflowClient.executeWorkflow(workflowId)
      return execution
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка выполнения workflow')
      throw err
    }
  }, [])

  const getWorkflowExecution = useCallback(async (executionId: string) => {
    try {
      const execution = await workflowClient.getWorkflowExecution(executionId)
      return execution
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка получения выполнения workflow')
      throw err
    }
  }, [])

  useEffect(() => {
    fetchWorkflows()
  }, [fetchWorkflows])

  return { 
    workflows, 
    loading, 
    error, 
    refetch: fetchWorkflows,
    createWorkflow,
    executeWorkflow,
    getWorkflowExecution
  }
}

// 🧠 ХУК ДЛЯ RAG
export const useRAG = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const searchRAG = useCallback(async (query: RAGQuery) => {
    try {
      setLoading(true)
      const response = await llmTuningClient.searchRAG(query)
      setError(null)
      return response
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка поиска RAG')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const generateWithRAG = useCallback(async (query: RAGQuery) => {
    try {
      setLoading(true)
      const response = await llmTuningClient.generateWithRAG(query)
      setError(null)
      return response
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка генерации с RAG')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  return { 
    loading, 
    error, 
    searchRAG,
    generateWithRAG
  }
}