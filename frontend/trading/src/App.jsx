import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import TradingView from './components/TradingView'
import DiaryView from './components/DiaryView'
import AnalyticsView from './components/AnalyticsView'
import Navigation from './components/Navigation'

function App() {
  const [systemStatus, setSystemStatus] = useState(null)

  useEffect(() => {
    // Проверяем статус системы при загрузке
    fetch('/api/v1/trading/status')
      .then(res => res.json())
      .then(data => setSystemStatus(data))
      .catch(err => console.error('Failed to fetch system status:', err))
  }, [])

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        
        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard systemStatus={systemStatus} />} />
            <Route path="/trading" element={<TradingView />} />
            <Route path="/diary" element={<DiaryView />} />
            <Route path="/analytics" element={<AnalyticsView />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App