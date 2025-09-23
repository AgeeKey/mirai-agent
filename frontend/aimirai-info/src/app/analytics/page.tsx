'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ChartBarIcon, 
  TrendingUpIcon,
  TrendingDownIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  ClockIcon,
  ShieldCheckIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import PerformanceChart from '../../components/PerformanceChart';
import PortfolioDistribution from '../../components/PortfolioDistribution';

interface AnalyticsData {
  performance: {
    totalReturn: number;
    annualizedReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
    profitFactor: number;
    averageTrade: number;
    totalTrades: number;
  };
  riskMetrics: {
    valueAtRisk: number;
    expectedShortfall: number;
    beta: number;
    alpha: number;
    volatility: number;
    correlation: number;
  };
  periods: {
    daily: number;
    weekly: number;
    monthly: number;
    yearly: number;
  };
  strategies: Array<{
    name: string;
    performance: number;
    trades: number;
    winRate: number;
    avgDuration: string;
    status: 'active' | 'paused' | 'inactive';
  }>;
  backtesting: Array<{
    period: string;
    initialCapital: number;
    finalCapital: number;
    return: number;
    sharpe: number;
    maxDrawdown: number;
  }>;
}

export default function AnalyticsPage() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<'7d' | '30d' | '90d' | '1y'>('30d');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalyticsData();
  }, [selectedPeriod]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    try {
      // В реальном приложении здесь будет API вызов
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setAnalyticsData({
        performance: {
          totalReturn: 34.7,
          annualizedReturn: 42.3,
          sharpeRatio: 1.85,
          maxDrawdown: -8.2,
          winRate: 67.4,
          profitFactor: 2.34,
          averageTrade: 156.78,
          totalTrades: 247,
        },
        riskMetrics: {
          valueAtRisk: -2.3,
          expectedShortfall: -4.1,
          beta: 0.78,
          alpha: 0.15,
          volatility: 18.5,
          correlation: 0.65,
        },
        periods: {
          daily: 0.12,
          weekly: 0.85,
          monthly: 3.67,
          yearly: 34.7,
        },
        strategies: [
          {
            name: 'AI Trend Following',
            performance: 28.4,
            trades: 156,
            winRate: 72.1,
            avgDuration: '2.3 дня',
            status: 'active',
          },
          {
            name: 'Mean Reversion',
            performance: 15.2,
            trades: 91,
            winRate: 61.5,
            avgDuration: '1.8 дня',
            status: 'active',
          },
          {
            name: 'Momentum Scalping',
            performance: -2.1,
            trades: 203,
            winRate: 58.1,
            avgDuration: '4.2 часа',
            status: 'paused',
          },
        ],
        backtesting: [
          {
            period: '2024 Q1',
            initialCapital: 100000,
            finalCapital: 128400,
            return: 28.4,
            sharpe: 1.92,
            maxDrawdown: -5.7,
          },
          {
            period: '2023 Q4',
            initialCapital: 100000,
            finalCapital: 115200,
            return: 15.2,
            sharpe: 1.45,
            maxDrawdown: -8.1,
          },
          {
            period: '2023 Q3',
            initialCapital: 100000,
            finalCapital: 109800,
            return: 9.8,
            sharpe: 1.23,
            maxDrawdown: -6.4,
          },
        ],
      });
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const performanceData = {
    labels: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг'],
    datasets: [{
      label: 'Доходность портфеля (%)',
      data: [2.1, 5.3, 8.7, 12.4, 15.8, 22.1, 28.5, 34.7],
      borderColor: 'rgb(16, 185, 129)',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      tension: 0.4
    }, {
      label: 'Benchmark (%)',
      data: [1.2, 3.1, 5.8, 7.9, 9.2, 11.5, 14.2, 16.8],
      borderColor: 'rgb(107, 114, 128)',
      backgroundColor: 'rgba(107, 114, 128, 0.1)',
      tension: 0.4
    }]
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="flex items-center space-x-3">
          <ArrowPathIcon className="h-8 w-8 animate-spin text-blue-400" />
          <span className="text-xl">Загрузка аналитики...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Расширенная аналитика
              </h1>
              <p className="text-gray-400 mt-2">Детальная отчетность по торговой деятельности</p>
            </div>
            
            {/* Period Selector */}
            <div className="flex space-x-2">
              {[
                { key: '7d', label: '7 дней' },
                { key: '30d', label: '30 дней' },
                { key: '90d', label: '90 дней' },
                { key: '1y', label: '1 год' },
              ].map((period) => (
                <button
                  key={period.key}
                  onClick={() => setSelectedPeriod(period.key as any)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    selectedPeriod === period.key
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {period.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Performance Metrics */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-6">Показатели эффективности</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <TrendingUpIcon className="h-8 w-8 text-green-400" />
                <span className="text-2xl font-bold text-green-400">
                  +{analyticsData?.performance.totalReturn}%
                </span>
              </div>
              <h3 className="text-sm font-medium text-gray-400 mb-1">Общая доходность</h3>
              <p className="text-xs text-gray-500">За выбранный период</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <ChartBarIcon className="h-8 w-8 text-blue-400" />
                <span className="text-2xl font-bold text-blue-400">
                  {analyticsData?.performance.sharpeRatio}
                </span>
              </div>
              <h3 className="text-sm font-medium text-gray-400 mb-1">Коэффициент Шарпа</h3>
              <p className="text-xs text-gray-500">Риск-скорректированная доходность</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <TrendingDownIcon className="h-8 w-8 text-red-400" />
                <span className="text-2xl font-bold text-red-400">
                  {analyticsData?.performance.maxDrawdown}%
                </span>
              </div>
              <h3 className="text-sm font-medium text-gray-400 mb-1">Максимальная просадка</h3>
              <p className="text-xs text-gray-500">Максимальные убытки</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <CurrencyDollarIcon className="h-8 w-8 text-yellow-400" />
                <span className="text-2xl font-bold text-yellow-400">
                  {analyticsData?.performance.winRate}%
                </span>
              </div>
              <h3 className="text-sm font-medium text-gray-400 mb-1">Процент прибыльных сделок</h3>
              <p className="text-xs text-gray-500">Точность торговых сигналов</p>
            </motion.div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Performance Chart */}
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Динамика доходности</h3>
            <PerformanceChart data={performanceData} type="line" height={300} />
          </div>

          {/* Risk Metrics */}
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Риск-метрики</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Value at Risk (5%)</span>
                <span className="text-red-400 font-medium">
                  {analyticsData?.riskMetrics.valueAtRisk}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Expected Shortfall</span>
                <span className="text-red-400 font-medium">
                  {analyticsData?.riskMetrics.expectedShortfall}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Beta</span>
                <span className="text-blue-400 font-medium">
                  {analyticsData?.riskMetrics.beta}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Alpha</span>
                <span className="text-green-400 font-medium">
                  {analyticsData?.riskMetrics.alpha}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Волатильность</span>
                <span className="text-yellow-400 font-medium">
                  {analyticsData?.riskMetrics.volatility}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Strategy Performance */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-6">Производительность стратегий</h2>
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-700/50">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Стратегия
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Доходность
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Сделки
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Win Rate
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Срок удержания
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Статус
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {analyticsData?.strategies.map((strategy, index) => (
                    <tr key={index} className="hover:bg-gray-700/30">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-white">
                          {strategy.name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`text-sm font-medium ${
                          strategy.performance > 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {strategy.performance > 0 ? '+' : ''}{strategy.performance}%
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {strategy.trades}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {strategy.winRate}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {strategy.avgDuration}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          strategy.status === 'active' 
                            ? 'bg-green-500/20 text-green-400'
                            : strategy.status === 'paused'
                            ? 'bg-yellow-500/20 text-yellow-400'
                            : 'bg-gray-500/20 text-gray-400'
                        }`}>
                          {strategy.status === 'active' ? 'Активна' : 
                           strategy.status === 'paused' ? 'Приостановлена' : 'Неактивна'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Backtesting Results */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-6">Результаты бэктестирования</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {analyticsData?.backtesting.map((result, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">{result.period}</h3>
                  <CalendarIcon className="h-5 w-5 text-gray-400" />
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400 text-sm">Начальный капитал</span>
                    <span className="text-white font-medium">
                      ${result.initialCapital.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400 text-sm">Итоговый капитал</span>
                    <span className="text-white font-medium">
                      ${result.finalCapital.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400 text-sm">Доходность</span>
                    <span className="text-green-400 font-medium">
                      +{result.return}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400 text-sm">Sharpe Ratio</span>
                    <span className="text-blue-400 font-medium">
                      {result.sharpe}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400 text-sm">Max Drawdown</span>
                    <span className="text-red-400 font-medium">
                      {result.maxDrawdown}%
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Export Options */}
        <div className="text-center">
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Экспорт отчетов</h3>
            <div className="flex justify-center space-x-4">
              <button className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors">
                📊 Скачать PDF отчет
              </button>
              <button className="px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg font-medium transition-colors">
                📈 Экспорт в Excel
              </button>
              <button className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium transition-colors">
                📧 Отправить на email
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}