
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface Trade {
  id: string;
  symbol: string;
  action: 'BUY' | 'SELL';
  price: number;
  quantity: number;
  timestamp: string;
  status: 'PENDING' | 'FILLED' | 'CANCELED';
}

interface Portfolio {
  total_value: number;
  profit_loss: number;
  profit_loss_percent: number;
  positions: {
    symbol: string;
    quantity: number;
    entry_price: number;
    current_price: number;
    profit_loss: number;
  }[];
}

const Dashboard: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch trades and portfolio data from API
    const fetchData = async () => {
      try {
        setLoading(true);

        // In a real app, these would be API calls
        // const [tradesRes, portfolioRes] = await Promise.all([
        //   fetch('/api/trades'),
        //   fetch('/api/portfolio')
        // ]);

        // For now, we'll use mock data
        const mockTrades: Trade[] = [
          { id: '1', symbol: 'BTCUSDT', action: 'BUY', price: 30000, quantity: 0.001, timestamp: '2023-01-01T10:00:00Z', status: 'FILLED' },
          { id: '2', symbol: 'ETHUSDT', action: 'SELL', price: 2000, quantity: 0.01, timestamp: '2023-01-01T11:00:00Z', status: 'FILLED' },
          { id: '3', symbol: 'BNBUSDT', action: 'BUY', price: 300, quantity: 0.1, timestamp: '2023-01-01T12:00:00Z', status: 'PENDING' },
        ];

        const mockPortfolio: Portfolio = {
          total_value: 15000,
          profit_loss: 500,
          profit_loss_percent: 3.4,
          positions: [
            { symbol: 'BTCUSDT', quantity: 0.001, entry_price: 29500, current_price: 30000, profit_loss: 5 },
            { symbol: 'ETHUSDT', quantity: 0.01, entry_price: 2050, current_price: 2000, profit_loss: -5 },
          ]
        };

        setTrades(mockTrades);
        setPortfolio(mockPortfolio);
        setError(null);
      } catch (err) {
        setError('Failed to fetch data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  // Format percentage
  const formatPercent = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // Chart data for price history
  const priceChartData = [
    { time: '00:00', BTC: 29500, ETH: 2050 },
    { time: '04:00', BTC: 29600, ETH: 2040 },
    { time: '08:00', BTC: 29800, ETH: 2030 },
    { time: '12:00', BTC: 30000, ETH: 2000 },
    { time: '16:00', BTC: 30100, ETH: 2010 },
    { time: '20:00', BTC: 30200, ETH: 2020 },
    { time: '24:00', BTC: 30000, ETH: 2000 },
  ];

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-500 text-center">Error: {error}</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Trading Dashboard</h1>

      {/* Portfolio Overview */}
      {portfolio && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Portfolio Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded">
              <h3 className="text-gray-500 text-sm">Total Value</h3>
              <p className="text-2xl font-bold">{formatCurrency(portfolio.total_value)}</p>
            </div>
            <div className={`bg-gray-50 p-4 rounded ${portfolio.profit_loss >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
              <h3 className="text-gray-500 text-sm">Profit/Loss</h3>
              <p className={`text-2xl font-bold ${portfolio.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(portfolio.profit_loss)}
              </p>
            </div>
            <div className={`bg-gray-50 p-4 rounded ${portfolio.profit_loss_percent >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
              <h3 className="text-gray-500 text-sm">P/L %</h3>
              <p className={`text-2xl font-bold ${portfolio.profit_loss_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatPercent(portfolio.profit_loss_percent)}
              </p>
            </div>
          </div>

          {/* Positions */}
          <h3 className="text-lg font-medium mb-4">Current Positions</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entry Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P/L</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {portfolio.positions.map((position, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{position.symbol}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{position.quantity}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatCurrency(position.entry_price)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatCurrency(position.current_price)}</td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${position.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(position.profit_loss)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Price Chart */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Price History</h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={priceChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="BTC" stroke="#8884d8" activeDot={{ r: 8 }} />
              <Line type="monotone" dataKey="ETH" stroke="#82ca9d" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Trades */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Recent Trades</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {trades.map((trade) => (
                <tr key={trade.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatTimestamp(trade.timestamp)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{trade.symbol}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      trade.action === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {trade.action}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatCurrency(trade.price)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{trade.quantity}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      trade.status === 'FILLED' ? 'bg-green-100 text-green-800' :
                      trade.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {trade.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
