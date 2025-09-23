'use client'

import React, { useState, useEffect } from 'react'
import { Activity, TrendingUp, DollarSign, Users, AlertCircle, CheckCircle } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string
  change?: string
  trend?: 'up' | 'down' | 'stable'
  icon: React.ReactNode
  color?: string
}

function MetricCard({ title, value, change, trend, icon, color = "blue" }: MetricCardProps) {
  const getTrendColor = () => {
    switch (trend) {
      case 'up': return 'text-green-400'
      case 'down': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  const getCardColor = () => {
    switch (color) {
      case 'green': return 'border-green-500/30 bg-green-500/10'
      case 'red': return 'border-red-500/30 bg-red-500/10'
      case 'yellow': return 'border-yellow-500/30 bg-yellow-500/10'
      case 'purple': return 'border-purple-500/30 bg-purple-500/10'
      default: return 'border-blue-500/30 bg-blue-500/10'
    }
  }

  return (
    <div className={`bg-gray-900/50 border rounded-lg p-6 transition-all duration-200 hover:shadow-lg ${getCardColor()}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="text-gray-400">{icon}</div>
        {trend && (
          <div className={`flex items-center ${getTrendColor()}`}>
            <TrendingUp className={`w-4 h-4 ${trend === 'down' ? 'rotate-180' : ''}`} />
          </div>
        )}
      </div>
      <div className="space-y-2">
        <h3 className="text-2xl font-bold text-white">{value}</h3>
        <p className="text-sm text-gray-400">{title}</p>
        {change && (
          <p className={`text-sm ${getTrendColor()}`}>
            {change}
          </p>
        )}
      </div>
    </div>
  )
}

interface SystemStatus {
  trading: boolean
  api: boolean
  websocket: boolean
  database: boolean
}

export function RealTimeMetrics() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    trading: true,
    api: true,
    websocket: true,
    database: true
  })

  const [metrics, setMetrics] = useState({
    totalPnL: '+$1,247.83',
    dailyTrades: '24',
    activePositions: '3',
    winRate: '68.5%',
    equity: '$10,602.16',
    drawdown: '-2.1%'
  })

  useEffect(() => {
    // Симуляция real-time обновлений
    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        totalPnL: `+$${(Math.random() * 2000 + 1000).toFixed(2)}`,
        dailyTrades: Math.floor(Math.random() * 50 + 10).toString(),
        winRate: `${(Math.random() * 30 + 60).toFixed(1)}%`
      }))

      // Случайные изменения статуса системы
      setSystemStatus(prev => ({
        ...prev,
        websocket: Math.random() > 0.1, // 90% uptime
        database: Math.random() > 0.05   // 95% uptime
      }))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const StatusIndicator = ({ label, status }: { label: string, status: boolean }) => (
    <div className="flex items-center space-x-2">
      <div className={`w-2 h-2 rounded-full ${status ? 'bg-green-400' : 'bg-red-400'} ${status ? 'animate-pulse' : ''}`}></div>
      <span className={`text-sm ${status ? 'text-green-400' : 'text-red-400'}`}>{label}</span>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* System Status */}
      <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Activity className="w-5 h-5 mr-2" />
          Статус системы
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatusIndicator label="Trading Engine" status={systemStatus.trading} />
          <StatusIndicator label="FastAPI" status={systemStatus.api} />
          <StatusIndicator label="WebSocket" status={systemStatus.websocket} />
          <StatusIndicator label="Database" status={systemStatus.database} />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <MetricCard
          title="Общая прибыль"
          value={metrics.totalPnL}
          change="+12.5% за день"
          trend="up"
          icon={<DollarSign className="w-6 h-6" />}
          color="green"
        />
        
        <MetricCard
          title="Сделки сегодня"
          value={metrics.dailyTrades}
          change="+3 за час"
          trend="up"
          icon={<Activity className="w-6 h-6" />}
          color="blue"
        />
        
        <MetricCard
          title="Активные позиции"
          value={metrics.activePositions}
          change="Без изменений"
          trend="stable"
          icon={<TrendingUp className="w-6 h-6" />}
          color="yellow"
        />
        
        <MetricCard
          title="Процент побед"
          value={metrics.winRate}
          change="+2.1% за неделю"
          trend="up"
          icon={<CheckCircle className="w-6 h-6" />}
          color="green"
        />
        
        <MetricCard
          title="Общий капитал"
          value={metrics.equity}
          change="+$247 сегодня"
          trend="up"
          icon={<Users className="w-6 h-6" />}
          color="purple"
        />
        
        <MetricCard
          title="Максимальная просадка"
          value={metrics.drawdown}
          change="Улучшение"
          trend="up"
          icon={<AlertCircle className="w-6 h-6" />}
          color="red"
        />
      </div>
    </div>
  )
}