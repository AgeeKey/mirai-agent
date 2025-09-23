'use client';

import { useState, useEffect } from 'react';
import { Brain, TrendingUp, PieChart, BarChart3, Target, Zap, AlertCircle } from 'lucide-react';

interface AnalyticsData {
  winRate: number;
  totalTrades: number;
  avgProfit: number;
  maxDrawdown: number;
  sharpeRatio: number;
  portfolio: {
    totalValue: number;
    dayChange: number;
    weekChange: number;
    monthChange: number;
  };
  predictions: {
    symbol: string;
    direction: 'UP' | 'DOWN';
    confidence: number;
    timeframe: string;
  }[];
}

export const AnalyticsPanel = () => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState('24h');
  const [aiInsights, setAiInsights] = useState<string[]>([]);

  useEffect(() => {
    // Моковые данные аналитики
    const mockData: AnalyticsData = {
      winRate: 68.5,
      totalTrades: 247,
      avgProfit: 23.45,
      maxDrawdown: -8.2,
      sharpeRatio: 1.85,
      portfolio: {
        totalValue: 12567.89,
        dayChange: 2.34,
        weekChange: 8.91,
        monthChange: 15.67
      },
      predictions: [
        { symbol: 'BTCUSDT', direction: 'UP', confidence: 87, timeframe: '4h' },
        { symbol: 'ETHUSDT', direction: 'DOWN', confidence: 73, timeframe: '1h' },
        { symbol: 'ADAUSDT', direction: 'UP', confidence: 65, timeframe: '2h' }
      ]
    };

    const insights = [
      "🧠 AI обнаружил паттерн восходящего треугольника на BTCUSDT",
      "📊 Объем торгов увеличился на 45% за последний час",
      "⚡ Рекомендуется снизить позицию по ETHUSDT из-за высокой волатильности",
      "🎯 Прогноз: вероятность роста BTC в следующие 4 часа составляет 87%",
      "🔍 Обнаружена дивергенция RSI на графике ETH - возможен разворот"
    ];

    setAnalyticsData(mockData);
    setAiInsights(insights);
  }, []);

  if (!analyticsData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white flex items-center">
          <Brain className="w-6 h-6 mr-2" />
          AI Аналитика
        </h2>
        
        <div className="flex space-x-2">
          {['1h', '4h', '24h', '7d'].map((timeframe) => (
            <button
              key={timeframe}
              onClick={() => setSelectedTimeframe(timeframe)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                selectedTimeframe === timeframe
                  ? 'bg-blue-500 text-white'
                  : 'bg-white/20 text-white/70 hover:bg-white/30'
              }`}
            >
              {timeframe}
            </button>
          ))}
        </div>
      </div>

      {/* Основные метрики */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 backdrop-blur-md rounded-lg p-4 border border-green-300/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-300 text-sm">Win Rate</p>
              <p className="text-2xl font-bold text-white">{analyticsData.winRate}%</p>
            </div>
            <Target className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-blue-500/20 to-cyan-500/20 backdrop-blur-md rounded-lg p-4 border border-blue-300/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-300 text-sm">Всего сделок</p>
              <p className="text-2xl font-bold text-white">{analyticsData.totalTrades}</p>
            </div>
            <BarChart3 className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-md rounded-lg p-4 border border-purple-300/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-300 text-sm">Ср. прибыль</p>
              <p className="text-2xl font-bold text-white">${analyticsData.avgProfit}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-purple-400" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 backdrop-blur-md rounded-lg p-4 border border-yellow-300/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-yellow-300 text-sm">Sharpe Ratio</p>
              <p className="text-2xl font-bold text-white">{analyticsData.sharpeRatio}</p>
            </div>
            <Zap className="w-8 h-8 text-yellow-400" />
          </div>
        </div>
      </div>

      {/* Портфель */}
      <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 border border-white/20">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center">
          <PieChart className="w-5 h-5 mr-2" />
          Портфель
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center">
            <p className="text-white/60 text-sm">Общая стоимость</p>
            <p className="text-2xl font-bold text-white">${analyticsData.portfolio.totalValue.toFixed(2)}</p>
          </div>
          
          <div className="text-center">
            <p className="text-white/60 text-sm">За день</p>
            <p className={`text-xl font-bold ${analyticsData.portfolio.dayChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {analyticsData.portfolio.dayChange >= 0 ? '+' : ''}{analyticsData.portfolio.dayChange}%
            </p>
          </div>
          
          <div className="text-center">
            <p className="text-white/60 text-sm">За неделю</p>
            <p className={`text-xl font-bold ${analyticsData.portfolio.weekChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {analyticsData.portfolio.weekChange >= 0 ? '+' : ''}{analyticsData.portfolio.weekChange}%
            </p>
          </div>
          
          <div className="text-center">
            <p className="text-white/60 text-sm">За месяц</p>
            <p className={`text-xl font-bold ${analyticsData.portfolio.monthChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {analyticsData.portfolio.monthChange >= 0 ? '+' : ''}{analyticsData.portfolio.monthChange}%
            </p>
          </div>
        </div>
      </div>

      {/* AI Прогнозы */}
      <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 border border-white/20">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center">
          <Brain className="w-5 h-5 mr-2" />
          AI Прогнозы
        </h3>
        
        <div className="grid gap-4">
          {analyticsData.predictions.map((prediction, index) => (
            <div key={index} className="bg-white/5 rounded-lg p-4 border border-white/10">
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-4">
                  <span className="font-bold text-white">{prediction.symbol}</span>
                  <span className={`px-2 py-1 rounded text-sm font-medium ${
                    prediction.direction === 'UP'
                      ? 'bg-green-500/20 text-green-300'
                      : 'bg-red-500/20 text-red-300'
                  }`}>
                    {prediction.direction === 'UP' ? '📈 РОСТ' : '📉 ПАДЕНИЕ'}
                  </span>
                  <span className="text-white/70 text-sm">{prediction.timeframe}</span>
                </div>
                
                <div className="text-right">
                  <div className="text-lg font-bold text-white">{prediction.confidence}%</div>
                  <div className="text-xs text-white/60">уверенность</div>
                </div>
              </div>
              
              {/* Полоса уверенности */}
              <div className="mt-3">
                <div className="bg-white/20 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      prediction.confidence >= 80 ? 'bg-green-500' :
                      prediction.confidence >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${prediction.confidence}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Инсайты */}
      <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 border border-white/20">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center">
          <AlertCircle className="w-5 h-5 mr-2" />
          AI Инсайты
        </h3>
        
        <div className="space-y-3">
          {aiInsights.map((insight, index) => (
            <div key={index} className="bg-blue-500/10 border border-blue-300/30 rounded-lg p-3">
              <p className="text-white/90">{insight}</p>
            </div>
          ))}
        </div>
      </div>

      {/* График производительности (placeholder) */}
      <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 border border-white/20">
        <h3 className="text-xl font-bold text-white mb-4">График производительности</h3>
        
        <div className="h-64 bg-white/5 rounded-lg flex items-center justify-center border border-white/10">
          <div className="text-center">
            <BarChart3 className="w-16 h-16 text-white/30 mx-auto mb-4" />
            <p className="text-white/60">График будет здесь</p>
            <p className="text-white/40 text-sm">Интеграция с Chart.js в разработке</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPanel;