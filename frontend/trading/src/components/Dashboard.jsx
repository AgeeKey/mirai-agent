import React, { useState, useEffect } from 'react'
import { 
  CurrencyDollarIcon, 
  TrendingUpIcon, 
  TrendingDownIcon,
  ChartBarIcon,
  ClockIcon
} from '@heroicons/react/24/outline'

const Dashboard = ({ systemStatus }) => {
  const [metrics, setMetrics] = useState(null)
  const [recentEntries, setRecentEntries] = useState([])

  useEffect(() => {
    // Загружаем аналитику
    fetch('/api/v1/analytics/dashboard')
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(err => console.error('Failed to fetch metrics:', err))

    // Загружаем последние записи дневника
    fetch('/api/v1/diary/entries?days=7')
      .then(res => res.json())
      .then(data => setRecentEntries(data.entries?.slice(0, 5) || []))
      .catch(err => console.error('Failed to fetch diary entries:', err))
  }, [])

  const stats = [
    {
      name: 'Баланс',
      value: systemStatus?.balance || '0.00',
      unit: 'USDT',
      icon: CurrencyDollarIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      name: 'Активные позиции',
      value: systemStatus?.positions?.length || 0,
      unit: '',
      icon: ChartBarIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      name: 'Записей в дневнике',
      value: metrics?.summary?.diary_entries_week || 0,
      unit: 'за неделю',
      icon: ClockIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Дашборд Mirai</h1>
        <p className="mt-1 text-sm text-gray-600">
          Автономный ИИ-агент для торговли и аналитики
        </p>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((item) => (
          <div key={item.name} className="card">
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${item.bgColor}`}>
                <item.icon className={`h-6 w-6 ${item.color}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{item.name}</p>
                <div className="flex items-baseline">
                  <p className="text-2xl font-semibold text-gray-900">{item.value}</p>
                  {item.unit && (
                    <p className="ml-2 text-sm text-gray-500">{item.unit}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Статус системы */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Статус системы</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              {systemStatus?.dry_run ? 'Демо-режим' : 'Боевой режим'}
            </span>
          </div>
          <div>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Торговля: {systemStatus?.trading_active ? 'Активна' : 'Остановлена'}
            </span>
          </div>
        </div>
      </div>

      {/* Последние записи дневника */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Последние записи</h3>
        <div className="space-y-3">
          {recentEntries.length > 0 ? (
            recentEntries.map((entry) => (
              <div key={entry.id} className="border-l-4 border-mirai-500 pl-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">{entry.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{entry.content?.substring(0, 100)}...</p>
                  </div>
                  <span className="text-xs text-gray-500">{entry.category}</span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-500">Записей пока нет</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard