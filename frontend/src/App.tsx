import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SWRConfig } from 'swr';

// Компоненты
import { Layout } from '@/components/Layout';
import { Dashboard } from '@/pages/Dashboard';
import { Services } from '@/pages/Services';
import { Monitoring } from '@/pages/Monitoring';
import { LLMTuning } from '@/pages/LLMTuning';
import { Benchmarks } from '@/pages/Benchmarks';
import ConsoleLogger from '@/components/ConsoleLogger';

// Утилиты
import { logger } from '@/utils/logger';

// Стили
import '@/styles/index.css';

// Создаем клиент для React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // 30 секунд
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// Конфигурация SWR
const swrConfig = {
  refreshInterval: 30000, // 30 секунд
  revalidateOnFocus: false,
  revalidateOnReconnect: true,
  errorRetryCount: 2,
};

function App() {
  // Логируем инициализацию приложения
  logger.info('🚀 Приложение reLink инициализируется', {
    version: import.meta.env.VITE_APP_VERSION || '1.0.0',
    environment: import.meta.env.MODE,
    debug: import.meta.env.VITE_REACT_APP_DEBUG,
    profiling: import.meta.env.VITE_REACT_APP_ENABLE_PROFILING,
    detailedLogging: import.meta.env.VITE_REACT_APP_ENABLE_DETAILED_LOGGING
  });

  return (
    <QueryClientProvider client={queryClient}>
      <SWRConfig value={swrConfig}>
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/services" element={<Services />} />
              <Route path="/monitoring" element={<Monitoring />} />
              <Route path="/llm-tuning" element={<LLMTuning />} />
              <Route path="/benchmarks" element={<Benchmarks />} />
            </Routes>
          </Layout>
          
          {/* Компонент для отображения логов в консоли */}
          <ConsoleLogger 
            enabled={import.meta.env.VITE_REACT_APP_ENABLE_DETAILED_LOGGING === 'true'}
            showStats={true}
            maxLogs={200}
          />
        </Router>
      </SWRConfig>
    </QueryClientProvider>
  );
}

export default App; 