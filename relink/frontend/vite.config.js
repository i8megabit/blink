import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [],
  root: '.',
  publicDir: 'public',
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
        timeout: 120000, // 2 минуты для длительных операций
      },
      '/ws': {
        target: 'ws://backend:8000',
        ws: true,
        changeOrigin: true
      }
    },
    hmr: {
      port: 3001
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true, // Включаем sourcemap для отладки
    minify: 'esbuild',
    target: 'es2015',
    rollupOptions: {
      input: {
        main: './index-vite.html'  // Используем Vite версию HTML
      },
      output: {
        manualChunks: undefined
      }
    },
    chunkSizeWarningLimit: 1000
  },
  optimizeDeps: {
    include: []
  },
  css: {
    postcss: './postcss.config.js'
  },
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '2.0.0'),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  }
}) 