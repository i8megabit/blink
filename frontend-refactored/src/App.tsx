import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AppProvider } from './context/AppContext';
import { ThemeProvider } from './context/ThemeContext';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Domains } from './pages/Domains';
import { Analysis } from './pages/Analysis';
import { Testing } from './pages/Testing';
import { Monitoring } from './pages/Monitoring';
import { Documentation } from './pages/Documentation';
import { Settings } from './pages/Settings';
import { Login } from './pages/Login';
import { ProtectedRoute } from './components/ProtectedRoute';
import './styles/globals.css';

// Создание клиента React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 минут
      gcTime: 10 * 60 * 1000, // 10 минут
      retry: (failureCount, error: any) => {
        // Не повторяем запросы для ошибок 4xx
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AppProvider>
          <Router>
            <div className="App">
              <Routes>
                {/* Публичные маршруты */}
                <Route path="/login" element={<Login />} />
                
                {/* Защищенные маршруты */}
                <Route path="/" element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }>
                  <Route index element={<Dashboard />} />
                  <Route path="domains" element={<Domains />} />
                  <Route path="analysis" element={<Analysis />} />
                  <Route path="testing" element={<Testing />} />
                  <Route path="monitoring" element={<Monitoring />} />
                  <Route path="docs" element={<Documentation />} />
                  <Route path="settings" element={<Settings />} />
                </Route>
                
                {/* 404 страница */}
                <Route path="*" element={
                  <div className="flex items-center justify-center min-h-screen">
                    <div className="text-center">
                      <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
                        404 - Страница не найдена
                      </h1>
                      <p className="text-gray-600 dark:text-gray-400 mb-8">
                        Запрашиваемая страница не существует
                      </p>
                      <a
                        href="/"
                        className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        Вернуться на главную
                      </a>
                    </div>
                  </div>
                } />
              </Routes>
              
              {/* Глобальные уведомления */}
              <Toaster
                position="top-right"
                toastOptions={{
                  duration: 4000,
                  style: {
                    background: '#363636',
                    color: '#fff',
                  },
                  success: {
                    duration: 3000,
                    iconTheme: {
                      primary: '#10B981',
                      secondary: '#fff',
                    },
                  },
                  error: {
                    duration: 5000,
                    iconTheme: {
                      primary: '#EF4444',
                      secondary: '#fff',
                    },
                  },
                }}
              />
            </div>
          </Router>
        </AppProvider>
      </ThemeProvider>
      
      {/* React Query DevTools (только в development) */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}

export default App; 