'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ChartBarIcon, 
  CpuChipIcon, 
  CurrencyDollarIcon,
  BoltIcon,
  ShieldCheckIcon,
  Cog6ToothIcon,
  PowerIcon,
  EyeIcon,
  UserIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { useWebSocket, WebSocketStatus } from '../../components/WebSocketManager';
import { useNotifications, NotificationManager } from '../../components/NotificationManager';
import { SystemStatusIndicator } from '../../components/SystemStatus';
import { useApi } from '../../components/ApiClient';
import TradingViewWidget from '../../components/TradingViewWidget';
import PerformanceChart from '../../components/PerformanceChart';
import PortfolioDistribution from '../../components/PortfolioDistribution';

export default function DashboardPage() {
  const [isDemo, setIsDemo] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isTrading, setIsTrading] = useState(true);
  
  // API client
  const api = useApi();
  
  // Notifications
  const { notifications, addNotification, removeNotification } = useNotifications();
  
  // WebSocket connection
  const { isConnected, connectionStatus, sendMessage } = useWebSocket({
    onMessage: (data) => {
      // Обработка сообщений от WebSocket
      if (data.type === 'signal') {
        addNotification({
          type: 'info',
          title: 'Новый AI сигнал',
          message: `${data.symbol}: ${data.signal} (${data.confidence}%)`,
          duration: 10000,
        });
      } else if (data.type === 'trade_executed') {
        addNotification({
          type: 'success',
          title: 'Сделка выполнена',
          message: `${data.symbol}: ${data.side} ${data.quantity} по цене ${data.price}`,
          duration: 8000,
        });
      }
    },
    onConnect: () => {
      addNotification({
        type: 'success',
        title: 'Подключение установлено',
        message: 'Соединение с торговым сервером активно',
        duration: 3000,
      });
    },
    onDisconnect: () => {
      addNotification({
        type: 'warning',
        title: 'Подключение потеряно',
        message: 'Попытка переподключения...',
        duration: 5000,
      });
    },
  });

  useEffect(() => {
    // Проверяем, демо режим или нет
    const urlParams = new URLSearchParams(window.location.search);
    setIsDemo(urlParams.get('demo') === 'true');

    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const portfolioData = {
    labels: ['9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'],
    datasets: [{
      label: 'Портфель (USDT)',
      data: [120000, 122000, 118000, 125000, 123000, 127000, 125840, 128000],
      borderColor: 'rgb(59, 130, 246)',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      tension: 0.4
    }]
  };

  const portfolioAllocation = {
    labels: ['Bitcoin', 'Ethereum', 'Solana', 'Cardano', 'Polkadot', 'Cash'],
    datasets: [{
      data: [35, 28, 15, 10, 7, 5],
      backgroundColor: [
        '#F59E0B', // Bitcoin orange
        '#8B5CF6', // Ethereum purple  
        '#10B981', // Solana green
        '#3B82F6', // Cardano blue
        '#EF4444', // Polkadot red
        '#6B7280'  // Cash gray
      ],
      borderWidth: 0
    }]
  };

  const portfolioStats = [
    { 
      name: 'Общий баланс', 
      value: isDemo ? '125,840.50' : '***,***.***', 
      currency: 'USDT',
      change: '+12.5%',
      trend: 'up',
      icon: CurrencyDollarIcon 
    },
    { 
      name: 'Сегодняшняя прибыль', 
      value: isDemo ? '+2,384.20' : '+*,***.***', 
      currency: 'USDT',
      change: '+3.8%',
      trend: 'up',
      icon: ArrowTrendingUpIcon 
    },
    { 
      name: 'Активных позиций', 
      value: '7', 
      currency: '',
      change: '+2',
      trend: 'up',
      icon: ChartBarIcon 
    },
    { 
      name: 'AI Score', 
      value: '94.2', 
      currency: '%',
      change: '+1.2%',
      trend: 'up',
      icon: CpuChipIcon 
    },
  ];

  const activePositions = [
    { symbol: 'BTC/USDT', side: 'LONG', size: '0.25', entry: '67,250.00', current: '68,100.00', pnl: '+850.00', pnlPercent: '+1.26%' },
    { symbol: 'ETH/USDT', side: 'SHORT', size: '5.0', entry: '3,420.00', current: '3,385.00', pnl: '+175.00', pnlPercent: '+1.02%' },
    { symbol: 'SOL/USDT', side: 'LONG', size: '15.0', entry: '185.50', current: '189.20', pnl: '+55.50', pnlPercent: '+1.99%' },
  ];

  const aiSignals = [
    { time: '14:32', symbol: 'BTC/USDT', signal: 'BUY', confidence: '95%', price: '68,150.00' },
    { time: '14:28', symbol: 'ETH/USDT', signal: 'SELL', confidence: '87%', price: '3,380.00' },
    { time: '14:25', symbol: 'ADA/USDT', signal: 'BUY', confidence: '92%', price: '0.485' },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Notification Manager */}
      <NotificationManager notifications={notifications} onRemove={removeNotification} />
      
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                AI Mirai
              </h1>
              {isDemo && (
                <span className="px-3 py-1 bg-orange-500/20 border border-orange-500/50 rounded-full text-orange-400 text-sm font-medium">
                  ДЕМО РЕЖИМ
                </span>
              )}
            </div>

            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm text-gray-400">Текущее время</div>
                <div className="font-mono text-green-400">
                  {currentTime.toLocaleTimeString('ru-RU')}
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <WebSocketStatus isConnected={isConnected} connectionStatus={connectionStatus} />
                <button className="p-2 text-gray-400 hover:text-white transition-colors">
                  <Cog6ToothIcon className="h-5 w-5" />
                </button>
                <button className="p-2 text-gray-400 hover:text-white transition-colors">
                  <UserIcon className="h-5 w-5" />
                </button>
                <Link 
                  href="/"
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
                >
                  Выйти
                </Link>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Trading Status */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold mb-4">Торговый статус</h2>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsTrading(!isTrading)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                isTrading
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-red-600 hover:bg-red-700 text-white'
              }`}
            >
              <PowerIcon className="h-5 w-5" />
              <span>{isTrading ? 'Торговля активна' : 'Торговля остановлена'}</span>
            </motion.button>
          </div>
        </div>

        {/* Trading Charts */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Торговые графики</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
              <h3 className="text-lg font-medium mb-4 text-white">TradingView графики</h3>
              <TradingViewWidget 
                symbol="BINANCE:BTCUSDT"
                theme="dark"
                height={400}
              />
            </div>
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
              <h3 className="text-lg font-medium mb-4 text-white">Доходность портфеля</h3>
              <PerformanceChart 
                data={portfolioData}
                type="line"
                height={400}
              />
            </div>
          </div>
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h3 className="text-lg font-medium mb-4 text-white">Распределение активов</h3>
            <PortfolioDistribution 
              data={portfolioAllocation}
              height={300}
            />
          </div>
        </div>

        {/* Portfolio Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {portfolioStats.map((stat, index) => (
            <motion.div
              key={stat.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6 hover:border-purple-500/50 transition-all duration-300"
            >
              <div className="flex items-center justify-between mb-4">
                <stat.icon className="h-8 w-8 text-purple-400" />
                <div className={`text-sm font-medium ${
                  stat.trend === 'up' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {stat.change}
                </div>
              </div>
              <div className="text-2xl font-bold text-white mb-1">
                {stat.value} {stat.currency}
              </div>
              <div className="text-gray-400 text-sm">{stat.name}</div>
            </motion.div>
          ))}
        </div>

        {/* Active Positions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Активные позиции</h2>
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-700/50">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">Символ</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">Сторона</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">Размер</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">Цена входа</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">Текущая цена</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">P&L</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {activePositions.map((position, index) => (
                    <tr key={index} className="hover:bg-gray-700/30 transition-colors">
                      <td className="px-6 py-4 font-medium text-white">{position.symbol}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          position.side === 'LONG' 
                            ? 'bg-green-500/20 text-green-400' 
                            : 'bg-red-500/20 text-red-400'
                        }`}>
                          {position.side}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-300">{position.size}</td>
                      <td className="px-6 py-4 text-gray-300">${position.entry}</td>
                      <td className="px-6 py-4 text-gray-300">${position.current}</td>
                      <td className="px-6 py-4">
                        <div className="text-green-400">+${position.pnl}</div>
                        <div className="text-green-400 text-xs">{position.pnlPercent}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* AI Signals */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">AI Сигналы</h2>
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <div className="space-y-4">
              {aiSignals.map((signal, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 bg-gray-700/30 rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <div className="text-sm text-gray-400">{signal.time}</div>
                    <div className="font-medium text-white">{signal.symbol}</div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      signal.signal === 'BUY' 
                        ? 'bg-green-500/20 text-green-400' 
                        : 'bg-red-500/20 text-red-400'
                    }`}>
                      {signal.signal}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-sm text-gray-400">
                      Уверенность: <span className="text-purple-400">{signal.confidence}</span>
                    </div>
                    <div className="font-medium text-white">${signal.price}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Link href="/analytics">
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="p-6 bg-blue-600/20 border border-blue-500/50 rounded-xl text-center hover:bg-blue-600/30 transition-all duration-300 cursor-pointer"
            >
              <ChartBarIcon className="h-8 w-8 mx-auto mb-2 text-blue-400" />
              <div className="font-medium text-white mb-1">Аналитика</div>
              <div className="text-sm text-gray-400">Подробная отчетность</div>
            </motion.div>
          </Link>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="p-6 bg-purple-600/20 border border-purple-500/50 rounded-xl text-center hover:bg-purple-600/30 transition-all duration-300"
          >
            <CpuChipIcon className="h-8 w-8 mx-auto mb-2 text-purple-400" />
            <div className="font-medium text-white mb-1">AI Настройки</div>
            <div className="text-sm text-gray-400">Конфигурация стратегий</div>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="p-6 bg-green-600/20 border border-green-500/50 rounded-xl text-center hover:bg-green-600/30 transition-all duration-300"
          >
            <ShieldCheckIcon className="h-8 w-8 mx-auto mb-2 text-green-400" />
            <div className="font-medium text-white mb-1">Риск-менеджмент</div>
            <div className="text-sm text-gray-400">Управление рисками</div>
          </motion.button>

          {/* System Status */}
          <div>
            <SystemStatusIndicator />
          </div>
        </div>
      </main>
    </div>
  );
}