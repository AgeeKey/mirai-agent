'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Target, AlertTriangle, Activity } from 'lucide-react';

interface Trade {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  amount: number;
  price: number;
  pnl: number;
  status: 'OPEN' | 'CLOSED';
  timestamp: Date;
}

interface Position {
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  roi: number;
}

export const TradingPanel = () => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [isLiveTrading, setIsLiveTrading] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');

  // Моковые данные
  useEffect(() => {
    const mockTrades: Trade[] = [
      {
        id: '1',
        symbol: 'BTCUSDT',
        side: 'BUY',
        amount: 0.1,
        price: 43250.00,
        pnl: 125.50,
        status: 'CLOSED',
        timestamp: new Date(Date.now() - 3600000)
      },
      {
        id: '2',
        symbol: 'ETHUSDT',
        side: 'SELL',
        amount: 1.5,
        price: 2645.30,
        pnl: -45.20,
        status: 'CLOSED',
        timestamp: new Date(Date.now() - 1800000)
      },
      {
        id: '3',
        symbol: 'ADAUSDT',
        side: 'BUY',
        amount: 1000,
        price: 0.485,
        pnl: 23.40,
        status: 'OPEN',
        timestamp: new Date(Date.now() - 900000)
      }
    ];

    const mockPositions: Position[] = [
      {
        symbol: 'BTCUSDT',
        side: 'LONG',
        size: 0.05,
        entryPrice: 43100.00,
        currentPrice: 43325.50,
        pnl: 11.28,
        roi: 0.52
      },
      {
        symbol: 'ETHUSDT',
        side: 'SHORT',
        size: 0.8,
        entryPrice: 2680.00,
        currentPrice: 2645.30,
        pnl: 27.76,
        roi: 1.30
      }
    ];

    setTrades(mockTrades);
    setPositions(mockPositions);
  }, []);

  const totalPnL = trades.reduce((sum, trade) => sum + trade.pnl, 0);
  const openPositionsPnL = positions.reduce((sum, pos) => sum + pos.pnl, 0);

  return (
    <div className="space-y-6">
      {/* Заголовок и контролы */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white flex items-center">
          <Activity className="w-6 h-6 mr-2" />
          Торговая Панель
        </h2>
        
        <div className="flex space-x-4">
          <button
            onClick={() => setIsLiveTrading(!isLiveTrading)}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              isLiveTrading 
                ? 'bg-red-500 hover:bg-red-600 text-white' 
                : 'bg-green-500 hover:bg-green-600 text-white'
            }`}
          >
            {isLiveTrading ? '🔴 Остановить' : '🟢 Запустить'} торговлю
          </button>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 backdrop-blur-md rounded-lg p-4 border border-green-300/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-300 text-sm">Общий P&L</p>
              <p className="text-2xl font-bold text-white">${totalPnL.toFixed(2)}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-blue-500/20 to-cyan-500/20 backdrop-blur-md rounded-lg p-4 border border-blue-300/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-300 text-sm">Открытые позиции</p>
              <p className="text-2xl font-bold text-white">${openPositionsPnL.toFixed(2)}</p>
            </div>
            <DollarSign className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-md rounded-lg p-4 border border-purple-300/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-300 text-sm">Активные позиции</p>
              <p className="text-2xl font-bold text-white">{positions.length}</p>
            </div>
            <Target className="w-8 h-8 text-purple-400" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-orange-500/20 to-red-500/20 backdrop-blur-md rounded-lg p-4 border border-orange-300/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-300 text-sm">Статус</p>
              <p className="text-lg font-bold text-white">{isLiveTrading ? 'ТОРГУЮ' : 'ОСТАНОВЛЕН'}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-orange-400" />
          </div>
        </div>
      </div>

      {/* Открытые позиции */}
      <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 border border-white/20">
        <h3 className="text-xl font-bold text-white mb-4">Открытые позиции</h3>
        
        {positions.length > 0 ? (
          <div className="space-y-3">
            {positions.map((position, index) => (
              <div key={index} className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex justify-between items-center">
                  <div className="flex items-center space-x-4">
                    <span className="font-bold text-white">{position.symbol}</span>
                    <span className={`px-2 py-1 rounded text-sm font-medium ${
                      position.side === 'LONG' 
                        ? 'bg-green-500/20 text-green-300' 
                        : 'bg-red-500/20 text-red-300'
                    }`}>
                      {position.side}
                    </span>
                    <span className="text-white/70">Размер: {position.size}</span>
                  </div>
                  
                  <div className="text-right">
                    <div className={`text-lg font-bold ${
                      position.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      ${position.pnl.toFixed(2)}
                    </div>
                    <div className={`text-sm ${
                      position.roi >= 0 ? 'text-green-300' : 'text-red-300'
                    }`}>
                      {position.roi >= 0 ? '+' : ''}{position.roi.toFixed(2)}%
                    </div>
                  </div>
                </div>
                
                <div className="mt-2 flex justify-between text-sm text-white/60">
                  <span>Вход: ${position.entryPrice.toFixed(2)}</span>
                  <span>Текущая: ${position.currentPrice.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-white/60 text-center py-8">Нет открытых позиций</p>
        )}
      </div>

      {/* История сделок */}
      <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 border border-white/20">
        <h3 className="text-xl font-bold text-white mb-4">Последние сделки</h3>
        
        <div className="space-y-3">
          {trades.map((trade) => (
            <div key={trade.id} className="bg-white/5 rounded-lg p-4 border border-white/10">
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-4">
                  <span className="font-bold text-white">{trade.symbol}</span>
                  <span className={`px-2 py-1 rounded text-sm font-medium ${
                    trade.side === 'BUY' 
                      ? 'bg-green-500/20 text-green-300' 
                      : 'bg-red-500/20 text-red-300'
                  }`}>
                    {trade.side}
                  </span>
                  <span className="text-white/70">{trade.amount} @ ${trade.price.toFixed(2)}</span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    trade.status === 'OPEN'
                      ? 'bg-blue-500/20 text-blue-300'
                      : 'bg-gray-500/20 text-gray-300'
                  }`}>
                    {trade.status}
                  </span>
                </div>
                
                <div className="text-right">
                  <div className={`text-lg font-bold ${
                    trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                  </div>
                  <div className="text-xs text-white/60">
                    {trade.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Быстрые действия */}
      <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 border border-white/20">
        <h3 className="text-xl font-bold text-white mb-4">Быстрые действия</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="bg-green-500/20 hover:bg-green-500/30 border border-green-300/30 rounded-lg p-3 text-white transition-all">
            📈 Купить
          </button>
          <button className="bg-red-500/20 hover:bg-red-500/30 border border-red-300/30 rounded-lg p-3 text-white transition-all">
            📉 Продать
          </button>
          <button className="bg-yellow-500/20 hover:bg-yellow-500/30 border border-yellow-300/30 rounded-lg p-3 text-white transition-all">
            ⚡ Закрыть все
          </button>
          <button className="bg-purple-500/20 hover:bg-purple-500/30 border border-purple-300/30 rounded-lg p-3 text-white transition-all">
            🎯 Автотрейд
          </button>
        </div>
      </div>
    </div>
  );
};

export default TradingPanel;