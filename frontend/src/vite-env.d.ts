/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_VERSION: string
  readonly VITE_REACT_APP_DEBUG: string
  readonly VITE_REACT_APP_ENABLE_PROFILING: string
  readonly VITE_REACT_APP_ENABLE_DETAILED_LOGGING: string
  readonly VITE_REACT_APP_API_BASE_URL: string
  readonly VITE_REACT_APP_WS_BASE_URL: string
  // больше переменных окружения...
}

interface ImportMeta {
  readonly env: ImportMetaEnv
} 