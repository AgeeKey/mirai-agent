import React from 'react'

const AnalyticsView = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Аналитика</h1>
      
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Аналитические данные</h3>
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">Модуль аналитики в разработке</p>
          <p className="text-sm text-gray-400">
            Здесь будут графики производительности, статистика торговли
            и другие аналитические данные
          </p>
        </div>
      </div>
    </div>
  )
}

export default AnalyticsView