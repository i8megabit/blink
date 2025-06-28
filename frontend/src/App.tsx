// @ts-nocheck
import React, { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import { DomainInput } from './components/DomainInput'
import { DomainsList } from './components/DomainsList'
import { AnalysisProgress } from './components/AnalysisProgress'
import { Recommendations } from './components/Recommendations'
import { Notifications } from './components/Notifications'
import { OllamaStatus } from './components/OllamaStatus'
import { AIAnalysisFlow } from './components/AIAnalysisFlow'
import Metrics from './components/Metrics'
import Charts from './components/Charts'
import Export from './components/Export'
import { AnalysisHistory } from './components/AnalysisHistory'
import { Benchmarks } from './components/Benchmarks'
import { BenchmarkDetails } from './components/BenchmarkDetails'
import { Settings } from './components/Settings'
import Insights from './components/Insights'
import Analytics from './components/Analytics'
import { useWebSocket } from './hooks/useWebSocket'
import { useNotifications } from './hooks/useNotifications'
import { useTheme } from './hooks/useTheme'
import { Domain, Recommendation, AnalysisStats, AIThought, OllamaStatus as OllamaStatusType, WebSocketMessage, BenchmarkHistory } from './types'
import { Dashboard } from './pages/Dashboard'
import './App.css'

function App() {
  return (
    <div className="App">
      <Dashboard />
    </div>
  )
}

export default App 