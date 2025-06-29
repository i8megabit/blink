import { useMicroservices } from '@/hooks/useMicroservices';
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ClockIcon,
  ServerIcon,
  ChartBarIcon,
  CogIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';
import { cn } from '@/utils/cn';

const serviceIcons = {
  'llm-tuning': CogIcon,
  'backend': ServerIcon,
  'router': ServerIcon,
  'benchmark': BeakerIcon,
  'monitoring': ChartBarIcon,
  'rag': ServerIcon,
};

export function Dashboard() {
  const { servicesHealth, loading, error, refreshHealth } = useMicroservices();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon className="h-5 w-5 text-success-500" />;
      case 'unhealthy':
        return <XCircleIcon className="h-5 w-5 text-error-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-warning-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-success-100 text-success-800';
      case 'unhealthy':
        return 'bg-error-100 text-error-800';
      default:
        return 'bg-warning-100 text-warning-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-error-50 p-4">
        <div className="flex">
          <XCircleIcon className="h-5 w-5 text-error-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-error-800">Ошибка загрузки</h3>
            <p className="mt-1 text-sm text-error-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Обзор состояния всех микросервисов
          </p>
        </div>
        <button
          onClick={refreshHealth}
          className="btn-primary"
        >
          Обновить
        </button>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircleIcon className="h-6 w-6 text-success-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Здоровые сервисы</p>
              <p className="text-2xl font-semibold text-gray-900">
                {Object.values(servicesHealth).filter(h => h.status === 'healthy').length}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <XCircleIcon className="h-6 w-6 text-error-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Проблемные сервисы</p>
              <p className="text-2xl font-semibold text-gray-900">
                {Object.values(servicesHealth).filter(h => h.status === 'unhealthy').length}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ClockIcon className="h-6 w-6 text-warning-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Неизвестный статус</p>
              <p className="text-2xl font-semibold text-gray-900">
                {Object.values(servicesHealth).filter(h => h.status === 'unknown').length}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ServerIcon className="h-6 w-6 text-primary-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Всего сервисов</p>
              <p className="text-2xl font-semibold text-gray-900">
                {Object.keys(servicesHealth).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Список сервисов */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Состояние сервисов</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Object.entries(servicesHealth).map(([serviceName, health]) => {
            const Icon = serviceIcons[serviceName as keyof typeof serviceIcons] || ServerIcon;
            return (
              <div key={serviceName} className="flex items-center p-4 border border-gray-200 rounded-lg">
                <div className="flex-shrink-0">
                  <Icon className="h-8 w-8 text-gray-400" />
                </div>
                <div className="ml-4 flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-gray-900 capitalize">
                      {serviceName.replace('-', ' ')}
                    </h3>
                    {getStatusIcon(health.status)}
                  </div>
                  <div className="mt-1 flex items-center justify-between">
                    <span className={cn('badge', getStatusColor(health.status))}>
                      {health.status === 'healthy' ? 'Работает' : 
                       health.status === 'unhealthy' ? 'Ошибка' : 'Неизвестно'}
                    </span>
                    {health.response_time && (
                      <span className="text-xs text-gray-500">
                        {health.response_time}ms
                      </span>
                    )}
                  </div>
                  {health.error && (
                    <p className="mt-1 text-xs text-error-600">{health.error}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
} 