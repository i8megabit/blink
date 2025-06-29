import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { AppContext as AppContextType, User, UserSettings, Notification, Alert, SystemMetrics, MicroserviceConfig } from '../types';

interface AppState {
  user: User | null;
  settings: UserSettings;
  notifications: Notification[];
  alerts: Alert[];
  systemMetrics: SystemMetrics | null;
  microservices: MicroserviceConfig[];
  theme: 'light' | 'dark';
  language: 'ru' | 'en';
  isLoading: boolean;
  error: string | null;
}

type AppAction =
  | { type: 'SET_USER'; payload: User | null }
  | { type: 'UPDATE_SETTINGS'; payload: Partial<UserSettings> }
  | { type: 'ADD_NOTIFICATION'; payload: Notification }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'MARK_NOTIFICATION_READ'; payload: string }
  | { type: 'ADD_ALERT'; payload: Alert }
  | { type: 'REMOVE_ALERT'; payload: string }
  | { type: 'ACKNOWLEDGE_ALERT'; payload: string }
  | { type: 'SET_SYSTEM_METRICS'; payload: SystemMetrics }
  | { type: 'SET_MICROSERVICES'; payload: MicroserviceConfig[] }
  | { type: 'SET_THEME'; payload: 'light' | 'dark' }
  | { type: 'SET_LANGUAGE'; payload: 'ru' | 'en' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null };

const initialState: AppState = {
  user: null,
  settings: {
    theme: 'auto',
    language: 'ru',
    notifications: {
      email: true,
      push: true,
      sms: false,
    },
    dashboard: {
      layout: 'grid',
      default_view: 'overview',
      widgets: ['domains', 'metrics', 'alerts'],
    },
    api: {
      rate_limit: 100,
      timeout: 30000,
      retry_attempts: 3,
    },
  },
  notifications: [],
  alerts: [],
  systemMetrics: null,
  microservices: [],
  theme: 'light',
  language: 'ru',
  isLoading: false,
  error: null,
};

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_USER':
      return { ...state, user: action.payload };
    
    case 'UPDATE_SETTINGS':
      return { 
        ...state, 
        settings: { ...state.settings, ...action.payload }
      };
    
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [action.payload, ...state.notifications].slice(0, 50), // Ограничиваем 50 уведомлениями
      };
    
    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload),
      };
    
    case 'MARK_NOTIFICATION_READ':
      return {
        ...state,
        notifications: state.notifications.map(n =>
          n.id === action.payload ? { ...n, read: true } : n
        ),
      };
    
    case 'ADD_ALERT':
      return {
        ...state,
        alerts: [action.payload, ...state.alerts].slice(0, 20), // Ограничиваем 20 алертами
      };
    
    case 'REMOVE_ALERT':
      return {
        ...state,
        alerts: state.alerts.filter(a => a.id !== action.payload),
      };
    
    case 'ACKNOWLEDGE_ALERT':
      return {
        ...state,
        alerts: state.alerts.map(a =>
          a.id === action.payload 
            ? { ...a, acknowledged: true, acknowledged_at: new Date().toISOString() }
            : a
        ),
      };
    
    case 'SET_SYSTEM_METRICS':
      return { ...state, systemMetrics: action.payload };
    
    case 'SET_MICROSERVICES':
      return { ...state, microservices: action.payload };
    
    case 'SET_THEME':
      return { ...state, theme: action.payload };
    
    case 'SET_LANGUAGE':
      return { ...state, language: action.payload };
    
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    
    default:
      return state;
  }
}

const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
} | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Загрузка настроек из localStorage при инициализации
  useEffect(() => {
    const savedSettings = localStorage.getItem('relink_settings');
    const savedTheme = localStorage.getItem('relink_theme');
    const savedLanguage = localStorage.getItem('relink_language');
    
    if (savedSettings) {
      try {
        const settings = JSON.parse(savedSettings);
        dispatch({ type: 'UPDATE_SETTINGS', payload: settings });
      } catch (error) {
        console.error('Failed to parse saved settings:', error);
      }
    }
    
    if (savedTheme) {
      dispatch({ type: 'SET_THEME', payload: savedTheme as 'light' | 'dark' });
    }
    
    if (savedLanguage) {
      dispatch({ type: 'SET_LANGUAGE', payload: savedLanguage as 'ru' | 'en' });
    }
  }, []);

  // Сохранение настроек в localStorage при изменении
  useEffect(() => {
    localStorage.setItem('relink_settings', JSON.stringify(state.settings));
  }, [state.settings]);

  useEffect(() => {
    localStorage.setItem('relink_theme', state.theme);
  }, [state.theme]);

  useEffect(() => {
    localStorage.setItem('relink_language', state.language);
  }, [state.language]);

  // Автоматическое удаление старых уведомлений
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      
      const oldNotifications = state.notifications.filter(n => 
        new Date(n.timestamp) < oneDayAgo
      );
      
      oldNotifications.forEach(n => {
        dispatch({ type: 'REMOVE_NOTIFICATION', payload: n.id });
      });
    }, 60 * 1000); // Проверяем каждую минуту

    return () => clearInterval(interval);
  }, [state.notifications]);

  const value = {
    state,
    dispatch,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}

// Вспомогательные хуки
export function useUser() {
  const { state, dispatch } = useApp();
  return {
    user: state.user,
    setUser: (user: User | null) => dispatch({ type: 'SET_USER', payload: user }),
  };
}

export function useSettings() {
  const { state, dispatch } = useApp();
  return {
    settings: state.settings,
    updateSettings: (settings: Partial<UserSettings>) => 
      dispatch({ type: 'UPDATE_SETTINGS', payload: settings }),
  };
}

export function useNotifications() {
  const { state, dispatch } = useApp();
  return {
    notifications: state.notifications,
    addNotification: (notification: Notification) => 
      dispatch({ type: 'ADD_NOTIFICATION', payload: notification }),
    removeNotification: (id: string) => 
      dispatch({ type: 'REMOVE_NOTIFICATION', payload: id }),
    markAsRead: (id: string) => 
      dispatch({ type: 'MARK_NOTIFICATION_READ', payload: id }),
  };
}

export function useAlerts() {
  const { state, dispatch } = useApp();
  return {
    alerts: state.alerts,
    addAlert: (alert: Alert) => 
      dispatch({ type: 'ADD_ALERT', payload: alert }),
    removeAlert: (id: string) => 
      dispatch({ type: 'REMOVE_ALERT', payload: id }),
    acknowledgeAlert: (id: string) => 
      dispatch({ type: 'ACKNOWLEDGE_ALERT', payload: id }),
  };
}

export function useSystemMetrics() {
  const { state, dispatch } = useApp();
  return {
    systemMetrics: state.systemMetrics,
    setSystemMetrics: (metrics: SystemMetrics) => 
      dispatch({ type: 'SET_SYSTEM_METRICS', payload: metrics }),
  };
}

export function useMicroservices() {
  const { state, dispatch } = useApp();
  return {
    microservices: state.microservices,
    setMicroservices: (microservices: MicroserviceConfig[]) => 
      dispatch({ type: 'SET_MICROSERVICES', payload: microservices }),
  };
}

export function useTheme() {
  const { state, dispatch } = useApp();
  return {
    theme: state.theme,
    setTheme: (theme: 'light' | 'dark') => 
      dispatch({ type: 'SET_THEME', payload: theme }),
  };
}

export function useLanguage() {
  const { state, dispatch } = useApp();
  return {
    language: state.language,
    setLanguage: (language: 'ru' | 'en') => 
      dispatch({ type: 'SET_LANGUAGE', payload: language }),
  };
} 