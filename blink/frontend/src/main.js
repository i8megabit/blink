// Основной файл для Vite
console.log('🚀 Blink (Vite) - Основной модуль загружен!');

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
  console.log('📱 DOM загружен, инициализируем приложение...');
  
  // Инициализируем Feather Icons
  if (window.feather) {
    feather.replace();
  }
  
  // Загружаем данные
  checkOllamaStatus();
  loadDomains();
  loadAnalysisHistory();
  loadBenchmarkHistory();
});

// Проверка статуса Ollama
async function checkOllamaStatus() {
  const statusElement = document.getElementById('ollama-status');
  if (!statusElement) return;
  
  try {
    const response = await fetch('http://localhost:8000/api/v1/ollama_status');
    const data = await response.json();
    
    if (data.ready_for_work) {
      statusElement.className = 'status-indicator status-success';
      statusElement.innerHTML = `
        <i data-feather="check-circle"></i>
        Ollama: Готова к работе (${data.models_count} моделей)
      `;
    } else {
      statusElement.className = 'status-indicator status-warning';
      statusElement.innerHTML = `
        <i data-feather="alert-circle"></i>
        Ollama: ${data.message || 'Недоступна'}
      `;
    }
    feather.replace();
  } catch (error) {
    statusElement.className = 'status-indicator status-error';
    statusElement.innerHTML = `
      <i data-feather="x-circle"></i>
      Ollama: Ошибка подключения
    `;
    feather.replace();
  }
}

// Загрузка доменов
async function loadDomains() {
  const container = document.getElementById('domains-container');
  if (!container) return;
  
  try {
    const response = await fetch('http://localhost:8000/api/v1/domains');
    const data = await response.json();
    
    if (data.domains && data.domains.length > 0) {
      const domainsHtml = data.domains.map(domain => `
        <div class="domain-card">
          <div class="domain-name">${domain.name}</div>
          <div class="domain-stats">
            <div class="stat-item">
              <i data-feather="file-text"></i>
              ${domain.total_posts} статей
            </div>
            <div class="stat-item">
              <i data-feather="bar-chart-2"></i>
              ${domain.total_analyses} анализов
            </div>
            <div class="stat-item">
              <i data-feather="clock"></i>
              ${domain.updated_at ? new Date(domain.updated_at).toLocaleString('ru-RU') : 'Не обновлялся'}
            </div>
          </div>
        </div>
      `).join('');
      container.innerHTML = domainsHtml;
    } else {
      container.innerHTML = `
        <div class="status-indicator status-warning">
          <i data-feather="alert-circle"></i>
          Домены не найдены
        </div>
      `;
    }
    feather.replace();
  } catch (error) {
    container.innerHTML = `
      <div class="status-indicator status-error">
        <i data-feather="x-circle"></i>
        Ошибка загрузки доменов
      </div>
    `;
    feather.replace();
  }
}

// Загрузка истории анализов
async function loadAnalysisHistory() {
  const container = document.getElementById('analysis-history');
  if (!container) return;
  
  try {
    const response = await fetch('http://localhost:8000/api/v1/analysis_history');
    const data = await response.json();
    
    if (data.history && data.history.length > 0) {
      const historyHtml = data.history.slice(0, 5).map(analysis => `
        <div class="domain-card">
          <div class="domain-name">Анализ #${analysis.id}</div>
          <div class="domain-stats">
            <div class="stat-item">
              <i data-feather="file-text"></i>
              ${analysis.posts_analyzed} статей
            </div>
            <div class="stat-item">
              <i data-feather="link"></i>
              ${analysis.connections_found} связей
            </div>
            <div class="stat-item">
              <i data-feather="clock"></i>
              ${new Date(analysis.created_at).toLocaleString('ru-RU')}
            </div>
          </div>
        </div>
      `).join('');
      container.innerHTML = historyHtml;
    } else {
      container.innerHTML = `
        <div class="status-indicator status-warning">
          <i data-feather="alert-circle"></i>
          История анализов пуста
        </div>
      `;
    }
    feather.replace();
  } catch (error) {
    container.innerHTML = `
      <div class="status-indicator status-error">
        <i data-feather="x-circle"></i>
        Ошибка загрузки истории
      </div>
    `;
    feather.replace();
  }
}

// Загрузка истории бенчмарков
async function loadBenchmarkHistory() {
  const container = document.getElementById('benchmark-history');
  if (!container) return;
  
  try {
    const response = await fetch('http://localhost:8000/api/v1/benchmark_history');
    const data = await response.json();
    
    if (data.benchmarks && data.benchmarks.length > 0) {
      const benchmarksHtml = data.benchmarks.slice(0, 5).map(benchmark => `
        <div class="domain-card">
          <div class="domain-name">${benchmark.name}</div>
          <div class="domain-stats">
            <div class="stat-item">
              <i data-feather="activity"></i>
              ${benchmark.benchmark_type}
            </div>
            <div class="stat-item">
              <i data-feather="award"></i>
              ${benchmark.overall_score ? benchmark.overall_score.toFixed(2) : 'N/A'}
            </div>
            <div class="stat-item">
              <i data-feather="clock"></i>
              ${new Date(benchmark.created_at).toLocaleString('ru-RU')}
            </div>
          </div>
        </div>
      `).join('');
      container.innerHTML = benchmarksHtml;
    } else {
      container.innerHTML = `
        <div class="status-indicator status-warning">
          <i data-feather="alert-circle"></i>
          История бенчмарков пуста
        </div>
      `;
    }
    feather.replace();
  } catch (error) {
    container.innerHTML = `
      <div class="status-indicator status-error">
        <i data-feather="x-circle"></i>
        Ошибка загрузки бенчмарков
      </div>
    `;
    feather.replace();
  }
}

// Экспортируем функции для глобального использования
window.checkOllamaStatus = checkOllamaStatus;
window.loadDomains = loadDomains;
window.loadAnalysisHistory = loadAnalysisHistory;
window.loadBenchmarkHistory = loadBenchmarkHistory;