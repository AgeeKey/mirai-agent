import React, { useState, useEffect } from 'react'
import { PlusIcon, FunnelIcon } from '@heroicons/react/24/outline'

const DiaryView = () => {
  const [entries, setEntries] = useState([])
  const [filter, setFilter] = useState({ category: '', project: '', days: 30 })
  const [showForm, setShowForm] = useState(false)
  const [newEntry, setNewEntry] = useState({
    category: '',
    title: '',
    content: '',
    tags: '',
    project: '',
    outcome: '',
    metrics: ''
  })

  useEffect(() => {
    loadEntries()
  }, [filter])

  const loadEntries = async () => {
    try {
      const params = new URLSearchParams()
      if (filter.category) params.append('category', filter.category)
      if (filter.project) params.append('project', filter.project)
      params.append('days', filter.days)
      
      const response = await fetch(`/api/v1/diary/entries?${params}`)
      const data = await response.json()
      setEntries(data.entries || [])
    } catch (error) {
      console.error('Failed to load entries:', error)
    }
  }

  const createEntry = async (e) => {
    e.preventDefault()
    try {
      await fetch('/api/v1/diary/entry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newEntry)
      })
      
      setNewEntry({
        category: '',
        title: '',
        content: '',
        tags: '',
        project: '',
        outcome: '',
        metrics: ''
      })
      setShowForm(false)
      loadEntries()
    } catch (error) {
      console.error('Failed to create entry:', error)
    }
  }

  const categories = ['development', 'trading', 'learning', 'analysis', 'planning', 'automation']
  const outcomes = ['successful', 'failed', 'in-progress', 'cancelled']

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Рабочий дневник</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn-primary flex items-center"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Новая запись
        </button>
      </div>

      {/* Форма новой записи */}
      {showForm && (
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Новая запись</h3>
          <form onSubmit={createEntry} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">Категория</label>
                <select
                  value={newEntry.category}
                  onChange={(e) => setNewEntry({...newEntry, category: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-mirai-500 focus:ring-mirai-500"
                  required
                >
                  <option value="">Выберите категорию</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Проект</label>
                <input
                  type="text"
                  value={newEntry.project}
                  onChange={(e) => setNewEntry({...newEntry, project: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-mirai-500 focus:ring-mirai-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Заголовок</label>
              <input
                type="text"
                value={newEntry.title}
                onChange={(e) => setNewEntry({...newEntry, title: e.target.value})}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-mirai-500 focus:ring-mirai-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Содержание</label>
              <textarea
                rows={4}
                value={newEntry.content}
                onChange={(e) => setNewEntry({...newEntry, content: e.target.value})}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-mirai-500 focus:ring-mirai-500"
                required
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Теги</label>
                <input
                  type="text"
                  value={newEntry.tags}
                  onChange={(e) => setNewEntry({...newEntry, tags: e.target.value})}
                  placeholder="тег1,тег2,тег3"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-mirai-500 focus:ring-mirai-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Результат</label>
                <select
                  value={newEntry.outcome}
                  onChange={(e) => setNewEntry({...newEntry, outcome: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-mirai-500 focus:ring-mirai-500"
                >
                  <option value="">Не указано</option>
                  {outcomes.map(outcome => (
                    <option key={outcome} value={outcome}>{outcome}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Метрики (JSON)</label>
                <input
                  type="text"
                  value={newEntry.metrics}
                  onChange={(e) => setNewEntry({...newEntry, metrics: e.target.value})}
                  placeholder='{"время": "2ч", "сложность": 8}'
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-mirai-500 focus:ring-mirai-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="btn-secondary"
              >
                Отмена
              </button>
              <button type="submit" className="btn-primary">
                Сохранить
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Фильтры */}
      <div className="card">
        <div className="flex items-center space-x-4">
                              <FunnelIcon className="h-5 w-5" />
          <select
            value={filter.category}
            onChange={(e) => setFilter({...filter, category: e.target.value})}
            className="rounded-md border-gray-300 shadow-sm focus:border-mirai-500 focus:ring-mirai-500"
          >
            <option value="">Все категории</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          
          <input
            type="text"
            placeholder="Проект"
            value={filter.project}
            onChange={(e) => setFilter({...filter, project: e.target.value})}
            className="rounded-md border-gray-300 shadow-sm focus:border-mirai-500 focus:ring-mirai-500"
          />
          
          <select
            value={filter.days}
            onChange={(e) => setFilter({...filter, days: parseInt(e.target.value)})}
            className="rounded-md border-gray-300 shadow-sm focus:border-mirai-500 focus:ring-mirai-500"
          >
            <option value={7}>Неделя</option>
            <option value={30}>Месяц</option>
            <option value={90}>3 месяца</option>
          </select>
        </div>
      </div>

      {/* Записи */}
      <div className="space-y-4">
        {entries.map((entry) => (
          <div key={entry.id} className="card">
            <div className="flex justify-between items-start mb-3">
              <div>
                <h3 className="text-lg font-medium text-gray-900">{entry.title}</h3>
                <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                  <span>{new Date(entry.timestamp).toLocaleString('ru-RU')}</span>
                  <span className="px-2 py-1 bg-gray-100 rounded-full">{entry.category}</span>
                  {entry.project && (
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                      {entry.project}
                    </span>
                  )}
                  {entry.outcome && (
                    <span className={`px-2 py-1 rounded-full ${
                      entry.outcome === 'successful' ? 'bg-green-100 text-green-800' :
                      entry.outcome === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {entry.outcome}
                    </span>
                  )}
                </div>
              </div>
            </div>
            
            <p className="text-gray-700 mb-3">{entry.content}</p>
            
            {entry.tags && (
              <div className="flex flex-wrap gap-2 mb-3">
                {entry.tags.split(',').map((tag, index) => (
                  <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                    #{tag.trim()}
                  </span>
                ))}
              </div>
            )}
            
            {entry.metrics && (
              <div className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                <strong>Метрики:</strong> {entry.metrics}
              </div>
            )}
          </div>
        ))}
        
        {entries.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">Записей не найдено</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default DiaryView