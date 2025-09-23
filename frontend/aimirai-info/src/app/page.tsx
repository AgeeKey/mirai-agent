'use client';

import { useState, useEffect } from 'react';
import { ChevronRightIcon, CpuChipIcon, ShieldCheckIcon, ChartBarIcon, BoltIcon } from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';

export default function HomePage() {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const stats = [
    { name: 'Активных стратегий', value: '24', icon: CpuChipIcon },
    { name: 'Точность сигналов', value: '94.2%', icon: ChartBarIcon },
    { name: 'Защищенных транзакций', value: '1M+', icon: ShieldCheckIcon },
    { name: 'Время отклика', value: '<50ms', icon: BoltIcon },
  ];

  const features = [
    {
      name: 'AI-движок принятия решений',
      description: 'Продвинутые алгоритмы машинного обучения анализируют рынок 24/7',
      icon: CpuChipIcon,
    },
    {
      name: 'Интеллектуальное управление рисками',
      description: 'Автоматическая защита капитала с настраиваемыми лимитами',
      icon: ShieldCheckIcon,
    },
    {
      name: 'Мгновенное исполнение',
      description: 'Высокоскоростные торговые операции с минимальной задержкой',
      icon: BoltIcon,
    },
    {
      name: 'Аналитическая панель',
      description: 'Детальная отчетность и визуализация торговых результатов',
      icon: ChartBarIcon,
    },
  ];

  return (
    <div className="relative overflow-hidden">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-6 sm:px-8">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 via-blue-500/5 to-green-500/10"></div>
        
        <div className="relative max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl sm:text-7xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-green-400 bg-clip-text text-transparent mb-6">
              AI Mirai
            </h1>
            <p className="text-xl sm:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto leading-relaxed">
              Революционная платформа автономной торговли, использующая искусственный интеллект для максимизации прибыли и минимизации рисков
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => window.location.href = '/register'}
                className="group px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg font-semibold text-white shadow-lg hover:shadow-xl transition-all duration-300"
              >
                Начать торговлю
                <ChevronRightIcon className="ml-2 h-5 w-5 inline-block group-hover:translate-x-1 transition-transform duration-300" />
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => window.location.href = '/dashboard?demo=true'}
                className="px-8 py-4 border border-gray-600 rounded-lg font-semibold text-white hover:bg-gray-800 transition-all duration-300"
              >
                Демо режим
              </motion.button>
            </div>

            {/* Real-time Clock */}
            <div className="mb-16">
              <p className="text-sm text-gray-400 mb-2">Текущее время торговых сессий</p>
              <div className="text-2xl font-mono text-green-400">
                {currentTime.toLocaleString('ru-RU', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                })}
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 px-6 sm:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="bg-gray-900/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6 text-center hover:border-purple-500/50 transition-all duration-300"
              >
                <stat.icon className="h-8 w-8 mx-auto mb-4 text-purple-400" />
                <div className="text-3xl font-bold text-white mb-2">{stat.value}</div>
                <div className="text-gray-400">{stat.name}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 sm:px-8">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-white mb-4">
              Технологии будущего торговли
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Наша платформа объединяет передовые AI-технологии для создания наиболее эффективной торговой системы
            </p>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.name}
                initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="group bg-gray-900/30 backdrop-blur-sm border border-gray-700 rounded-xl p-8 hover:border-purple-500/50 hover:bg-gray-800/50 transition-all duration-300"
              >
                <feature.icon className="h-12 w-12 text-purple-400 mb-6 group-hover:scale-110 transition-transform duration-300" />
                <h3 className="text-xl font-semibold text-white mb-4">{feature.name}</h3>
                <p className="text-gray-300 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 sm:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 backdrop-blur-sm border border-purple-500/30 rounded-2xl p-12"
          >
            <h2 className="text-3xl font-bold text-white mb-6">
              Готовы начать автономную торговлю?
            </h2>
            <p className="text-xl text-gray-300 mb-8">
              Присоединяйтесь к революции AI-трейдинга и откройте новые возможности для роста капитала
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => window.location.href = '/register'}
              className="px-10 py-4 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg font-semibold text-white shadow-lg hover:shadow-xl transition-all duration-300"
            >
              Создать аккаунт
            </motion.button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 sm:px-8 border-t border-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                AI Mirai
              </h3>
              <p className="text-gray-400 mt-2">Автономная торговая платформа будущего</p>
            </div>
            <div className="flex space-x-6 text-gray-400">
              <a href="/login" className="hover:text-white transition-colors">Вход</a>
              <a href="/register" className="hover:text-white transition-colors">Регистрация</a>
              <a href="/dashboard?demo=true" className="hover:text-white transition-colors">Демо</a>
              <a href="#" className="hover:text-white transition-colors">API</a>
              <a href="#" className="hover:text-white transition-colors">Поддержка</a>
              <a href="#" className="hover:text-white transition-colors">Контакты</a>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-800 text-center text-gray-400">
            <p>&copy; 2025 AI Mirai. Все права защищены.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
