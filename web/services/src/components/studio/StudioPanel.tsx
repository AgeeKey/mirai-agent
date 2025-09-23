'use client';

import { useState } from 'react';
import { Star, Palette, Music, Code, Image, Wand2, Download, Share2 } from 'lucide-react';

interface StudioProject {
  id: string;
  name: string;
  type: 'art' | 'music' | 'code' | 'animation';
  thumbnail: string;
  created: Date;
  description: string;
}

export const StudioPanel = () => {
  const [activeTab, setActiveTab] = useState('gallery');
  const [projects, setProjects] = useState<StudioProject[]>([]);
  const [isCreating, setIsCreating] = useState(false);

  const studioTabs = [
    { id: 'gallery', name: 'Галерея', icon: <Image className="w-4 h-4" /> },
    { id: 'create', name: 'Создать', icon: <Palette className="w-4 h-4" /> },
    { id: 'music', name: 'Музыка', icon: <Music className="w-4 h-4" /> },
    { id: 'code', name: 'Код', icon: <Code className="w-4 h-4" /> },
  ];

  const creativeTools = [
    {
      name: 'AI Художник',
      description: 'Создание уникальных изображений с помощью ИИ',
      icon: '🎨',
      action: () => console.log('AI Art Generation'),
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      name: 'Музыкальный композитор',
      description: 'Генерация мелодий и ритмов',
      icon: '🎵',
      action: () => console.log('Music Generation'),
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      name: 'Анимация',
      description: 'Создание движущихся изображений',
      icon: '🎬',
      action: () => console.log('Animation Creation'),
      gradient: 'from-green-500 to-emerald-500'
    },
    {
      name: 'Код-генератор',
      description: 'Автоматическое создание кода',
      icon: '💻',
      action: () => console.log('Code Generation'),
      gradient: 'from-orange-500 to-red-500'
    }
  ];

  const renderGallery = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold text-white">Мои творения</h3>
        <button className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg transition-all">
          Новый проект
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="text-center py-16">
          <Star className="w-16 h-16 text-white/30 mx-auto mb-4" />
          <p className="text-white/60 text-lg mb-2">Пока нет проектов</p>
          <p className="text-white/40">Создайте свой первый шедевр!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <div key={project.id} className="bg-white/10 backdrop-blur-md rounded-lg overflow-hidden border border-white/20 hover:border-white/40 transition-all">
              <div className="h-48 bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <span className="text-6xl">{project.type === 'art' ? '🎨' : project.type === 'music' ? '🎵' : project.type === 'code' ? '💻' : '🎬'}</span>
              </div>
              <div className="p-4">
                <h4 className="font-bold text-white mb-2">{project.name}</h4>
                <p className="text-white/70 text-sm mb-3">{project.description}</p>
                <div className="flex justify-between items-center">
                  <span className="text-white/50 text-xs">{project.created.toLocaleDateString()}</span>
                  <div className="flex space-x-2">
                    <button className="p-1 text-white/70 hover:text-white">
                      <Download className="w-4 h-4" />
                    </button>
                    <button className="p-1 text-white/70 hover:text-white">
                      <Share2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderCreate = () => (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-white flex items-center">
        <Wand2 className="w-5 h-5 mr-2" />
        Творческие инструменты
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {creativeTools.map((tool, index) => (
          <button
            key={index}
            onClick={tool.action}
            className={`p-6 rounded-lg bg-gradient-to-r ${tool.gradient} hover:scale-105 transition-all duration-300 text-left group`}
          >
            <div className="flex items-start space-x-4">
              <span className="text-4xl">{tool.icon}</span>
              <div>
                <h4 className="text-white font-bold text-lg mb-2 group-hover:scale-105 transition-transform">
                  {tool.name}
                </h4>
                <p className="text-white/90">{tool.description}</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* AI Промпт интерфейс */}
      <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 border border-white/20">
        <h4 className="text-lg font-bold text-white mb-4">AI Промпт генератор</h4>
        <div className="space-y-4">
          <textarea
            placeholder="Опишите что вы хотите создать... (например: 'Нарисуй футуристический город в стиле киберпанк')"
            className="w-full h-32 bg-white/10 border border-white/20 rounded-lg p-3 text-white placeholder-white/50 resize-none focus:border-purple-400 focus:outline-none"
          />
          <div className="flex justify-between items-center">
            <div className="flex space-x-2">
              <button className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-lg text-sm hover:bg-purple-500/30 transition-all">
                🎨 Арт
              </button>
              <button className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-lg text-sm hover:bg-blue-500/30 transition-all">
                🎵 Музыка
              </button>
              <button className="px-3 py-1 bg-green-500/20 text-green-300 rounded-lg text-sm hover:bg-green-500/30 transition-all">
                💻 Код
              </button>
            </div>
            <button
              onClick={() => setIsCreating(true)}
              disabled={isCreating}
              className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-6 py-2 rounded-lg font-medium transition-all disabled:opacity-50"
            >
              {isCreating ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Создаю...
                </div>
              ) : (
                'Создать ✨'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderMusic = () => (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-white flex items-center">
        <Music className="w-5 h-5 mr-2" />
        Музыкальная студия
      </h3>

      {/* Виртуальный синтезатор */}
      <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 border border-white/20">
        <h4 className="text-lg font-bold text-white mb-4">Виртуальный синтезатор</h4>
        
        {/* Клавиши пианино (упрощенная версия) */}
        <div className="flex space-x-1 mb-6">
          {['C', 'D', 'E', 'F', 'G', 'A', 'B'].map((note, index) => (
            <button
              key={note}
              className="bg-white hover:bg-gray-200 h-16 w-12 rounded-b-lg transition-all border border-gray-300 flex items-end justify-center pb-2 text-black font-bold"
              onClick={() => console.log(`Playing ${note}`)}
            >
              {note}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="bg-gradient-to-r from-blue-500 to-cyan-500 p-4 rounded-lg text-white font-medium hover:scale-105 transition-all">
            🎹 Пианино
          </button>
          <button className="bg-gradient-to-r from-purple-500 to-pink-500 p-4 rounded-lg text-white font-medium hover:scale-105 transition-all">
            🎸 Гитара
          </button>
          <button className="bg-gradient-to-r from-orange-500 to-red-500 p-4 rounded-lg text-white font-medium hover:scale-105 transition-all">
            🥁 Барабаны
          </button>
          <button className="bg-gradient-to-r from-green-500 to-emerald-500 p-4 rounded-lg text-white font-medium hover:scale-105 transition-all">
            🎤 Вокал
          </button>
        </div>
      </div>

      {/* Генератор мелодий */}
      <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 border border-white/20">
        <h4 className="text-lg font-bold text-white mb-4">AI Композитор</h4>
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <select className="bg-white/10 border border-white/20 rounded-lg p-2 text-white">
              <option>Классическая</option>
              <option>Джаз</option>
              <option>Рок</option>
              <option>Электронная</option>
              <option>Амбиент</option>
            </select>
            <select className="bg-white/10 border border-white/20 rounded-lg p-2 text-white">
              <option>Минорная</option>
              <option>Мажорная</option>
            </select>
            <select className="bg-white/10 border border-white/20 rounded-lg p-2 text-white">
              <option>Медленный</option>
              <option>Средний</option>
              <option>Быстрый</option>
            </select>
          </div>
          <button className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 rounded-lg font-medium hover:scale-105 transition-all">
            🎵 Создать мелодию
          </button>
        </div>
      </div>
    </div>
  );

  const renderCode = () => (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-white flex items-center">
        <Code className="w-5 h-5 mr-2" />
        Код-студия
      </h3>

      {/* Код редактор */}
      <div className="bg-black/50 backdrop-blur-md rounded-lg p-6 border border-white/20">
        <div className="flex justify-between items-center mb-4">
          <h4 className="text-lg font-bold text-white">AI Код генератор</h4>
          <div className="flex space-x-2">
            <button className="px-3 py-1 bg-green-500/20 text-green-300 rounded text-sm">JavaScript</button>
            <button className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded text-sm">Python</button>
            <button className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded text-sm">TypeScript</button>
          </div>
        </div>
        
        <textarea
          placeholder="Опишите функцию которую хотите создать..."
          className="w-full h-32 bg-gray-900 border border-gray-700 rounded p-3 text-green-400 font-mono text-sm resize-none focus:border-blue-400 focus:outline-none"
        />
        
        <div className="mt-4 bg-gray-900 rounded p-4 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Сгенерированный код:</span>
            <button className="text-blue-400 hover:text-blue-300 text-sm">Копировать</button>
          </div>
          <pre className="text-green-400 text-sm font-mono">
{`function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

// Пример использования
console.log(fibonacci(10)); // 55`}
          </pre>
        </div>
        
        <button className="w-full mt-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white py-2 rounded font-medium hover:scale-105 transition-all">
          💻 Генерировать код
        </button>
      </div>

      {/* Шаблоны кода */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          { name: 'Trading Bot', desc: 'Торговый бот для криптовалют', icon: '🤖' },
          { name: 'API Client', desc: 'Клиент для работы с API', icon: '🌐' },
          { name: 'Data Analyzer', desc: 'Анализатор данных', icon: '📊' },
          { name: 'Web Scraper', desc: 'Парсер веб-страниц', icon: '🕷️' }
        ].map((template, index) => (
          <button
            key={index}
            className="p-4 bg-white/10 hover:bg-white/20 rounded-lg border border-white/20 text-left transition-all"
          >
            <div className="flex items-center space-x-3">
              <span className="text-2xl">{template.icon}</span>
              <div>
                <h5 className="text-white font-medium">{template.name}</h5>
                <p className="text-white/60 text-sm">{template.desc}</p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Заголовок и табы */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white flex items-center">
          <Star className="w-6 h-6 mr-2" />
          Mirai Studio
        </h2>
      </div>

      {/* Навигация */}
      <div className="flex space-x-2 border-b border-white/20">
        {studioTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-t-lg transition-all flex items-center space-x-2 ${
              activeTab === tab.id
                ? 'bg-white/20 text-white border-b-2 border-purple-400'
                : 'text-white/60 hover:text-white hover:bg-white/10'
            }`}
          >
            {tab.icon}
            <span>{tab.name}</span>
          </button>
        ))}
      </div>

      {/* Контент табов */}
      <div className="min-h-96">
        {activeTab === 'gallery' && renderGallery()}
        {activeTab === 'create' && renderCreate()}
        {activeTab === 'music' && renderMusic()}
        {activeTab === 'code' && renderCode()}
      </div>
    </div>
  );
};

export default StudioPanel;