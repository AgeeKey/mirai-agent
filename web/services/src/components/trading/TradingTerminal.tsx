'use client';

import React, { useState, useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { 
  TrendingUp, TrendingDown, Target, Shield, Zap, 
  BarChart3, Activity, Timer, DollarSign, Percent,
  PlayCircle, StopCircle, Settings, AlertTriangle
} from 'lucide-react';
import { GlowButton } from '../ui/GlowButton';
import { HolographicPanel } from '../ui/HolographicPanel';
import { apiClient, TradingOrder, TradingPosition, MarketData } from '@/lib/api';

export type OrderType = 'market' | 'limit' | 'stop' | 'stop_limit';
export type OrderSide = 'buy' | 'sell';
export type TimeFrame = '1m' | '5m' | '15m' | '1h' | '4h' | '1d';

interface TradingTerminalProps {
  className?: string;
}

interface OrderForm {
  symbol: string;
  type: OrderType;
  side: OrderSide;
  amount: number;
  price?: number;
  stopPrice?: number;
  leverage: number;
}

const symbols = [
  'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT', 
  'MATICUSDT', 'LINKUSDT', 'AVAXUSDT', 'ATOMUSDT', 'XRPUSDT'
];

const timeframes = [
  { value: '1m', label: '1m' },
  { value: '5m', label: '5m' },
  { value: '15m', label: '15m' },
  { value: '1h', label: '1h' },
  { value: '4h', label: '4h' },
  { value: '1d', label: '1d' }
];

const orderTypes = [
  { value: 'market', label: 'Market', icon: '⚡' },
  { value: 'limit', label: 'Limit', icon: '🎯' },
  { value: 'stop', label: 'Stop', icon: '🛡️' },
  { value: 'stop_limit', label: 'Stop Limit', icon: '🎚️' }
];

export function TradingTerminal({ className, ...props }: TradingTerminalProps) {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState<TimeFrame>('1h');
  const [positions, setPositions] = useState<TradingPosition[]>([]);
  const [orders, setOrders] = useState<TradingOrder[]>([]);
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [orderForm, setOrderForm] = useState<OrderForm>({
    symbol: 'BTCUSDT',
    type: 'market',
    side: 'buy',
    amount: 0,
    leverage: 1
  });

  // WebSocket connections
  const wsRef = useRef<WebSocket | null>(null);
  const marketWsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    loadInitialData();
    connectWebSocket();
    
    return () => {
      disconnectWebSocket();
    };
  }, []);

  const loadInitialData = async () => {
    setIsLoading(true);
    try {
      const [positionsRes, ordersRes, marketRes] = await Promise.all([
        apiClient.getPositions(),
        apiClient.getOrders(),
        apiClient.getMarketData(symbols)
      ]);

      if (positionsRes.success) setPositions(positionsRes.data || []);
      if (ordersRes.success) setOrders(ordersRes.data || []);
      if (marketRes.success) setMarketData(marketRes.data || []);
    } catch (err) {
      setError('Failed to load trading data');
    } finally {
      setIsLoading(false);
    }
  };

  const connectWebSocket = () => {
    // Trading WebSocket
    wsRef.current = apiClient.connectTradingWebSocket();
    if (wsRef.current) {
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleTradingUpdate(data);
      };
    }

    // Market Data WebSocket
    marketWsRef.current = apiClient.connectMarketWebSocket();
    if (marketWsRef.current) {
      marketWsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMarketUpdate(data);
      };
    }
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (marketWsRef.current) {
      marketWsRef.current.close();
      marketWsRef.current = null;
    }
  };

  const handleTradingUpdate = (data: any) => {
    switch (data.type) {
      case 'position_update':
        setPositions(prev => {
          const index = prev.findIndex(p => p.id === data.position.id);
          if (index >= 0) {
            const newPositions = [...prev];
            newPositions[index] = data.position;
            return newPositions;
          } else {
            return [...prev, data.position];
          }
        });
        break;
      case 'order_update':
        setOrders(prev => {
          const index = prev.findIndex(o => o.id === data.order.id);
          if (index >= 0) {
            const newOrders = [...prev];
            newOrders[index] = data.order;
            return newOrders;
          } else {
            return [...prev, data.order];
          }
        });
        break;
    }
  };

  const handleMarketUpdate = (data: any) => {
    if (data.type === 'price_update') {
      setMarketData(prev => {
        const index = prev.findIndex(m => m.symbol === data.symbol);
        if (index >= 0) {
          const newData = [...prev];
          newData[index] = { ...newData[index], ...data.data };
          return newData;
        }
        return prev;
      });
    }
  };

  const handleOrderSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.createOrder(orderForm);
      if (response.success) {
        // Reset form
        setOrderForm(prev => ({ ...prev, amount: 0 }));
        // Reload orders
        const ordersRes = await apiClient.getOrders();
        if (ordersRes.success) setOrders(ordersRes.data || []);
      } else {
        setError(response.error || 'Failed to create order');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancelOrder = async (orderId: string) => {
    try {
      const response = await apiClient.cancelOrder(orderId);
      if (response.success) {
        setOrders(prev => prev.filter(o => o.id !== orderId));
      } else {
        setError(response.error || 'Failed to cancel order');
      }
    } catch (err) {
      setError('Network error');
    }
  };

  const handleClosePosition = async (positionId: string) => {
    try {
      const response = await apiClient.closePosition(positionId);
      if (response.success) {
        setPositions(prev => prev.filter(p => p.id !== positionId));
      } else {
        setError(response.error || 'Failed to close position');
      }
    } catch (err) {
      setError('Network error');
    }
  };

  const getCurrentPrice = (symbol: string): number => {
    const market = marketData.find(m => m.symbol === symbol);
    return market?.price || 0;
  };

  const getPriceChange = (symbol: string): { change: number; percent: number } => {
    const market = marketData.find(m => m.symbol === symbol);
    return {
      change: market?.change24h || 0,
      percent: market?.changePercent24h || 0
    };
  };

  return (
    <div className={cn('space-y-6', className)} {...props}>
      
      {/* Header with Symbol Selection */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold text-gradient-primary">Trading Terminal</h2>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Activity className="w-4 h-4" />
            <span>Live Market</span>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <select 
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="bg-mirai-panel/30 border border-mirai-primary/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-mirai-primary"
          >
            {symbols.map(symbol => {
              const priceData = getPriceChange(symbol);
              return (
                <option key={symbol} value={symbol}>
                  {symbol} {priceData.percent !== 0 && (
                    <span className={priceData.percent > 0 ? 'text-mirai-success' : 'text-mirai-error'}>
                      ({priceData.percent > 0 ? '+' : ''}{priceData.percent.toFixed(2)}%)
                    </span>
                  )}
                </option>
              );
            })}
          </select>
          
          <div className="flex bg-mirai-panel/30 rounded-lg p-1">
            {timeframes.map(tf => (
              <button
                key={tf.value}
                onClick={() => setSelectedTimeframe(tf.value as TimeFrame)}
                className={cn(
                  'px-3 py-1 text-xs rounded transition-colors',
                  selectedTimeframe === tf.value 
                    ? 'bg-mirai-primary text-white' 
                    : 'text-gray-400 hover:text-white'
                )}
              >
                {tf.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-mirai-error/20 border border-mirai-error/50 rounded-lg p-3 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-mirai-error" />
          <span className="text-mirai-error text-sm">{error}</span>
          <button 
            onClick={() => setError(null)}
            className="ml-auto text-mirai-error hover:text-white"
          >
            ×
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Order Form */}
        <div className="lg:col-span-1">
          <HolographicPanel className="p-6">
            <h3 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
              <Target className="w-5 h-5 text-mirai-primary" />
              Place Order
            </h3>
            
            <form onSubmit={handleOrderSubmit} className="space-y-4">
              
              {/* Order Type Selection */}
              <div>
                <label className="block text-sm text-gray-300 mb-2">Order Type</label>
                <div className="grid grid-cols-2 gap-2">
                  {orderTypes.map(type => (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => setOrderForm(prev => ({ ...prev, type: type.value as OrderType }))}
                      className={cn(
                        'p-2 rounded-lg text-xs font-semibold transition-all duration-300',
                        'border border-current',
                        orderForm.type === type.value
                          ? 'bg-mirai-primary text-white border-mirai-primary'
                          : 'bg-mirai-panel/30 text-gray-300 border-gray-600 hover:border-mirai-primary/50'
                      )}
                    >
                      <div className="flex items-center gap-1">
                        <span>{type.icon}</span>
                        <span>{type.label}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Buy/Sell Toggle */}
              <div>
                <label className="block text-sm text-gray-300 mb-2">Side</label>
                <div className="flex rounded-lg overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setOrderForm(prev => ({ ...prev, side: 'buy' }))}
                    className={cn(
                      'flex-1 py-2 px-4 text-sm font-semibold transition-colors',
                      orderForm.side === 'buy'
                        ? 'bg-mirai-success text-white'
                        : 'bg-mirai-panel/30 text-gray-300 hover:bg-mirai-success/20'
                    )}
                  >
                    <TrendingUp className="w-4 h-4 inline mr-1" />
                    BUY
                  </button>
                  <button
                    type="button"
                    onClick={() => setOrderForm(prev => ({ ...prev, side: 'sell' }))}
                    className={cn(
                      'flex-1 py-2 px-4 text-sm font-semibold transition-colors',
                      orderForm.side === 'sell'
                        ? 'bg-mirai-error text-white'
                        : 'bg-mirai-panel/30 text-gray-300 hover:bg-mirai-error/20'
                    )}
                  >
                    <TrendingDown className="w-4 h-4 inline mr-1" />
                    SELL
                  </button>
                </div>
              </div>

              {/* Amount Input */}
              <div>
                <label className="block text-sm text-gray-300 mb-2">Amount</label>
                <input
                  type="number"
                  step="0.00001"
                  min="0"
                  value={orderForm.amount}
                  onChange={(e) => setOrderForm(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
                  className="w-full bg-mirai-panel/30 border border-mirai-primary/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-mirai-primary"
                  placeholder="0.00"
                />
              </div>

              {/* Price Input (for limit orders) */}
              {(orderForm.type === 'limit' || orderForm.type === 'stop_limit') && (
                <div>
                  <label className="block text-sm text-gray-300 mb-2">Price</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={orderForm.price || ''}
                    onChange={(e) => setOrderForm(prev => ({ ...prev, price: parseFloat(e.target.value) || undefined }))}
                    className="w-full bg-mirai-panel/30 border border-mirai-primary/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-mirai-primary"
                    placeholder={getCurrentPrice(orderForm.symbol).toString()}
                  />
                </div>
              )}

              {/* Stop Price Input */}
              {(orderForm.type === 'stop' || orderForm.type === 'stop_limit') && (
                <div>
                  <label className="block text-sm text-gray-300 mb-2">Stop Price</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={orderForm.stopPrice || ''}
                    onChange={(e) => setOrderForm(prev => ({ ...prev, stopPrice: parseFloat(e.target.value) || undefined }))}
                    className="w-full bg-mirai-panel/30 border border-mirai-primary/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-mirai-primary"
                    placeholder="Stop price"
                  />
                </div>
              )}

              {/* Leverage Slider */}
              <div>
                <label className="block text-sm text-gray-300 mb-2">
                  Leverage: {orderForm.leverage}x
                </label>
                <input
                  type="range"
                  min="1"
                  max="100"
                  value={orderForm.leverage}
                  onChange={(e) => setOrderForm(prev => ({ ...prev, leverage: parseInt(e.target.value) }))}
                  className="w-full h-2 bg-mirai-panel/30 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>1x</span>
                  <span>50x</span>
                  <span>100x</span>
                </div>
              </div>

              {/* Submit Button */}
              <GlowButton
                type="submit"
                disabled={isLoading || orderForm.amount <= 0}
                variant={orderForm.side === 'buy' ? 'primary' : 'accent'}
                className="w-full"
              >
                <div className="flex items-center justify-center gap-2">
                  {isLoading ? (
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <PlayCircle className="w-4 h-4" />
                  )}
                  {orderForm.side === 'buy' ? 'Place Buy Order' : 'Place Sell Order'}
                </div>
              </GlowButton>
            </form>
          </HolographicPanel>
        </div>

        {/* Market Data & Charts */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Current Price Display */}
          <HolographicPanel className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-bold text-white">{selectedSymbol}</h3>
                <div className="flex items-center gap-4 mt-2">
                  <span className="text-3xl font-mono text-mirai-primary">
                    ${getCurrentPrice(selectedSymbol).toLocaleString()}
                  </span>
                  <div className={cn(
                    'flex items-center gap-1 text-lg font-semibold',
                    getPriceChange(selectedSymbol).percent >= 0 ? 'text-mirai-success' : 'text-mirai-error'
                  )}>
                    {getPriceChange(selectedSymbol).percent >= 0 ? (
                      <TrendingUp className="w-5 h-5" />
                    ) : (
                      <TrendingDown className="w-5 h-5" />
                    )}
                    <span>
                      {getPriceChange(selectedSymbol).percent >= 0 ? '+' : ''}
                      {getPriceChange(selectedSymbol).percent.toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="text-right space-y-1">
                <div className="text-sm text-gray-400">24h Volume</div>
                <div className="text-lg font-mono text-white">
                  ${marketData.find(m => m.symbol === selectedSymbol)?.volume24h?.toLocaleString() || 'N/A'}
                </div>
              </div>
            </div>
          </HolographicPanel>

          {/* Chart Placeholder */}
          <HolographicPanel className="p-6 h-64">
            <div className="flex items-center justify-center h-full text-gray-400">
              <div className="text-center">
                <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Trading Chart</p>
                <p className="text-sm">Chart integration coming soon</p>
              </div>
            </div>
          </HolographicPanel>
        </div>
      </div>

      {/* Open Positions & Orders */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Open Positions */}
        <HolographicPanel className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-mirai-secondary" />
            Open Positions ({positions.length})
          </h3>
          
          <div className="space-y-3">
            {positions.length === 0 ? (
              <p className="text-gray-400 text-center py-8">No open positions</p>
            ) : (
              positions.map(position => (
                <div key={position.id} className="bg-mirai-panel/20 rounded-lg p-3 border border-mirai-primary/10">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-white">{position.symbol}</span>
                      <span className={cn(
                        'px-2 py-1 text-xs rounded',
                        position.side === 'long' 
                          ? 'bg-mirai-success/20 text-mirai-success' 
                          : 'bg-mirai-error/20 text-mirai-error'
                      )}>
                        {position.side.toUpperCase()}
                      </span>
                    </div>
                    <button
                      onClick={() => handleClosePosition(position.id)}
                      className="text-mirai-error hover:text-white text-sm"
                    >
                      <StopCircle className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <div className="text-gray-400">Size</div>
                      <div className="text-white font-mono">{position.size}</div>
                    </div>
                    <div>
                      <div className="text-gray-400">Entry</div>
                      <div className="text-white font-mono">${position.entryPrice}</div>
                    </div>
                    <div>
                      <div className="text-gray-400">PnL</div>
                      <div className={cn(
                        'font-mono',
                        position.pnl >= 0 ? 'text-mirai-success' : 'text-mirai-error'
                      )}>
                        {position.pnl >= 0 ? '+' : ''}${position.pnl.toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </HolographicPanel>

        {/* Open Orders */}
        <HolographicPanel className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
            <Timer className="w-5 h-5 text-mirai-accent" />
            Open Orders ({orders.filter(o => o.status === 'pending').length})
          </h3>
          
          <div className="space-y-3">
            {orders.filter(o => o.status === 'pending').length === 0 ? (
              <p className="text-gray-400 text-center py-8">No pending orders</p>
            ) : (
              orders.filter(o => o.status === 'pending').map(order => (
                <div key={order.id} className="bg-mirai-panel/20 rounded-lg p-3 border border-mirai-primary/10">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-white">{order.symbol}</span>
                      <span className={cn(
                        'px-2 py-1 text-xs rounded',
                        order.side === 'buy' 
                          ? 'bg-mirai-success/20 text-mirai-success' 
                          : 'bg-mirai-error/20 text-mirai-error'
                      )}>
                        {order.side.toUpperCase()}
                      </span>
                      <span className="px-2 py-1 text-xs bg-mirai-primary/20 text-mirai-primary rounded">
                        {order.type.toUpperCase()}
                      </span>
                    </div>
                    <button
                      onClick={() => handleCancelOrder(order.id)}
                      className="text-mirai-error hover:text-white text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <div className="text-gray-400">Amount</div>
                      <div className="text-white font-mono">{order.amount}</div>
                    </div>
                    <div>
                      <div className="text-gray-400">Price</div>
                      <div className="text-white font-mono">
                        {order.price ? `$${order.price}` : 'Market'}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-400">Status</div>
                      <div className="text-mirai-warning capitalize">{order.status}</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </HolographicPanel>
      </div>
    </div>
  );
}

// Демо-данные для тестирования
export const demoTradingData = {
  positions: [
    {
      id: '1',
      symbol: 'BTCUSDT',
      side: 'long' as const,
      size: 0.1,
      entryPrice: 43250.00,
      currentPrice: 43580.00,
      pnl: 33.00,
      pnlPercent: 0.76,
      unrealizedPnl: 33.00,
      margin: 4325.00,
      leverage: 10,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  ],
  orders: [
    {
      id: '1',
      symbol: 'ETHUSDT',
      type: 'limit' as const,
      side: 'buy' as const,
      amount: 1.0,
      price: 2650.00,
      status: 'pending' as const,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  ],
  marketData: [
    {
      symbol: 'BTCUSDT',
      price: 43580.00,
      change24h: 1250.00,
      changePercent24h: 2.95,
      volume24h: 28450000000,
      high24h: 44100.00,
      low24h: 42800.00,
      lastUpdate: new Date().toISOString()
    }
  ]
};