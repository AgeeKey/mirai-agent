import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, Activity, Shield, Bot, Wifi, WifiOff } from 'lucide-react';

interface TradingData {
  balance: { total: number; available: number; used: number };
  daily_pnl: number;
  win_rate: number;
  risk_level: string;
  ai_confidence: number;
  strategies: Record<string, { status: string; win_rate: number }>;
}

interface Trade {
  id: number;
  symbol: string;
  action: string;
  price: number;
  quantity: number;
  pnl: number;
  timestamp: string;
  strategy: string;
}

const MiraiDashboard = () => {
  const [tradingData, setTradingData] = useState<TradingData | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const [liveData, setLiveData] = useState<any>({});

  const API_BASE = 'http://localhost:8001';

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch trading status
        const statusResponse = await fetch(`${API_BASE}/api/trading/status`);
        const statusData = await statusResponse.json();
        setTradingData(statusData);

        // Fetch recent trades
        const tradesResponse = await fetch(`${API_BASE}/api/trading/trades`);
        const tradesData = await tradesResponse.json();
        setTrades(tradesData.trades);

        // Fetch performance data
        const perfResponse = await fetch(`${API_BASE}/api/trading/performance`);
        const perfData = await perfResponse.json();
        setPerformanceData(perfData.performance);

        setIsConnected(true);
      } catch (error) {
        console.error('Failed to fetch data:', error);
        setIsConnected(false);
      }
    };

    fetchData();
  }, []);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8001/ws/trading');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setWsConnection(ws);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'price_update') {
        setLiveData(data.data);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWsConnection(null);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, []);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  if (!tradingData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">🤖 Загрузка Mirai Agent...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">🤖 Mirai Agent</h1>
            <p className="text-slate-300">AI-Powered Trading Dashboard</p>
          </div>
          <div className="flex items-center space-x-4">
            <Badge variant={isConnected ? "success" : "destructive"} className="px-4 py-2">
              {isConnected ? (
                <>
                  <Wifi className="mr-2 h-4 w-4" />
                  Connected
                </>
              ) : (
                <>
                  <WifiOff className="mr-2 h-4 w-4" />
                  Disconnected
                </>
              )}
            </Badge>
            {wsConnection && (
              <Badge variant="success" className="px-4 py-2">
                🔴 Live Data
              </Badge>
            )}
            <Button className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700">
              <Bot className="mr-2 h-4 w-4" />
              Agent Control
            </Button>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-300">Daily P&L</CardTitle>
              <DollarSign className="h-4 w-4 text-green-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-400">
                {formatCurrency(liveData.current_pnl || tradingData.daily_pnl)}
              </div>
              <p className="text-xs text-slate-400">
                <TrendingUp className="inline h-3 w-3 mr-1" />
                +12.3% from yesterday
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-300">Win Rate</CardTitle>
              <Activity className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-400">{tradingData.win_rate}%</div>
              <p className="text-xs text-slate-400">
                Last 50 trades
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-300">Risk Level</CardTitle>
              <Shield className="h-4 w-4 text-yellow-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-400 capitalize">
                {tradingData.risk_level}
              </div>
              <p className="text-xs text-slate-400">
                3/6 daily trades used
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-300">AI Confidence</CardTitle>
              <Bot className="h-4 w-4 text-purple-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-400">
                {(liveData.ai_confidence || tradingData.ai_confidence).toFixed(2)}
              </div>
              <p className="text-xs text-slate-400">
                High confidence mode
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Live Prices */}
        {liveData.BTCUSDT && (
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur">
            <CardHeader>
              <CardTitle className="text-white">Live Prices</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-slate-700/50">
                  <div className="text-sm text-slate-400">BTC/USDT</div>
                  <div className="text-xl font-bold text-white">
                    ${liveData.BTCUSDT?.toLocaleString()}
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-slate-700/50">
                  <div className="text-sm text-slate-400">ETH/USDT</div>
                  <div className="text-xl font-bold text-white">
                    ${liveData.ETHUSDT?.toLocaleString()}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Charts and Trades */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur">
            <CardHeader>
              <CardTitle className="text-white">Performance Chart</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={performanceData}>
                  <defs>
                    <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1f2937', 
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#fff'
                    }} 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="pnl" 
                    stroke="#10b981" 
                    fillOpacity={1} 
                    fill="url(#colorPnl)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur">
            <CardHeader>
              <CardTitle className="text-white">Recent Trades</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {trades.map((trade) => (
                  <div key={trade.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-700/50">
                    <div className="flex items-center space-x-3">
                      <Badge variant={trade.action === 'BUY' ? 'success' : 'destructive'}>
                        {trade.action}
                      </Badge>
                      <div>
                        <p className="text-sm font-medium text-white">{trade.symbol}</p>
                        <p className="text-xs text-slate-400">
                          {trade.quantity} @ ${trade.price.toLocaleString()}
                        </p>
                        <p className="text-xs text-purple-400">{trade.strategy}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-medium ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {trade.pnl >= 0 ? '+' : ''}${trade.pnl}
                      </p>
                      <p className="text-xs text-slate-400">{formatTime(trade.timestamp)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Strategy Status */}
        <Card className="bg-slate-800/50 border-slate-700 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-white">Active Strategies</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(tradingData.strategies).map(([name, strategy]) => {
                const displayName = name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                let statusVariant: "success" | "secondary" | "warning" = "secondary";
                
                if (strategy.status === "active") statusVariant = "success";
                else if (strategy.status === "paused") statusVariant = "warning";
                
                return (
                  <div key={name} className="p-4 rounded-lg bg-slate-700/50 border border-slate-600">
                    <h3 className="text-lg font-semibold text-white mb-2">{displayName}</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Status:</span>
                        <Badge variant={statusVariant} className="capitalize">{strategy.status}</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Win Rate:</span>
                        <span className="text-green-400">{strategy.win_rate}%</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
};

export default MiraiDashboard;