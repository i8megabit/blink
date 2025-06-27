import React from 'react';

const AnalysisProgress = ({ analysisStats, isAnalyzing }) => {
  if (!isAnalyzing && !analysisStats) {
    return null;
  }

  return (
    <div className="step-card">
      <div className="step-number">
        {isAnalyzing ? '⚡' : '✅'}
      </div>
      <h3 className="step-title">
        {isAnalyzing ? 'Анализ в процессе...' : 'Анализ завершен'}
      </h3>
      
      {analysisStats && (
        <div className="status-indicator status-success">
          <div className="progress-info">
            <div className="progress-step">{analysisStats.step}</div>
            <div className="progress-details">
              Шаг {analysisStats.current} из {analysisStats.total} ({analysisStats.percentage}%)
            </div>
            {analysisStats.details && (
              <div className="progress-details-small">{analysisStats.details}</div>
            )}
          </div>
          
          <div className="progress-bar-container">
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${analysisStats.percentage}%` }}
              />
            </div>
          </div>
        </div>
      )}
      
      {isAnalyzing && !analysisStats && (
        <div className="status-indicator status-loading">
          <div className="loading-spinner" />
          <span>Подготовка к анализу...</span>
        </div>
      )}
    </div>
  );
};

export default AnalysisProgress; 