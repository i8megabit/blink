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
        </Router>
      </SWRConfig>
    </QueryClientProvider>
  );
}

export default App; 