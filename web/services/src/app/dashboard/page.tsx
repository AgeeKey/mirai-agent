'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/Card';
import { apiClient } from '@/lib/api';
import Link from 'next/link';

interface StatusData {
  mode: string;
  testnet: boolean;
  uptime: string;
  version: string;
  last_heartbeat: string;
  environment: string;
}

interface OrderData {
  orders: any[];
  total: number;
}

export default function DashboardPage() {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [orders, setOrders] = useState<OrderData | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusData, ordersData, logsData] = await Promise.all([
          apiClient.get<StatusData>('/status'),
          apiClient.get<OrderData>('/orders/recent?limit=5'),
          apiClient.get<{logs: string[]}>('/logs/tail?lines=10')
        ]);
        
        setStatus(statusData.data);
        setOrders(ordersData.data);
        setLogs(logsData.data?.logs || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">Error: {error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">Mirai Control Panel</h1>
            <div className="flex space-x-4">
              <Link href="/risk" className="text-indigo-600 hover:text-indigo-800">
                Risk Config
              </Link>
              <Link href="/orders" className="text-indigo-600 hover:text-indigo-800">
                Orders
              </Link>
              <button 
                onClick={() => {
                  apiClient.logout();
                  window.location.href = '/login';
                }}
                className="text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card title="Bot Status">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Mode:</span>
                <span className={`font-semibold ${
                  status?.mode === 'DRY_RUN' ? 'text-yellow-600' : 'text-green-600'
                }`}>
                  {status?.mode || 'Unknown'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Network:</span>
                <span className={`font-semibold ${
                  status?.testnet ? 'text-orange-600' : 'text-blue-600'
                }`}>
                  {status?.testnet ? 'Testnet' : 'Mainnet'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Version:</span>
                <span className="font-mono text-sm">{status?.version || 'Unknown'}</span>
              </div>
            </div>
          </Card>

          <Card title="System Health">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className="text-green-600 font-semibold">Running</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Environment:</span>
                <span className="font-semibold">{status?.environment || 'Unknown'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Last Update:</span>
                <span className="text-sm text-gray-500">
                  {status?.last_heartbeat ? new Date(status.last_heartbeat).toLocaleTimeString() : 'Unknown'}
                </span>
              </div>
            </div>
          </Card>

          <Card title="Recent Orders">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Orders:</span>
                <span className="font-semibold">{orders?.total || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Active:</span>
                <span className="font-semibold">0</span>
              </div>
              <div className="text-center pt-2">
                <Link 
                  href="/orders" 
                  className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                >
                  View All Orders →
                </Link>
              </div>
            </div>
          </Card>

          <Card title="Risk Status">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Daily P&L:</span>
                <span className="text-green-600 font-semibold">$0.00</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Max Loss:</span>
                <span className="text-gray-600 font-semibold">$100.00</span>
              </div>
              <div className="text-center pt-2">
                <Link 
                  href="/risk" 
                  className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                >
                  Configure Risk →
                </Link>
              </div>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card title="Recent Logs">
            <div className="bg-gray-900 text-green-400 p-4 rounded font-mono text-xs overflow-y-auto max-h-64">
              {logs.length > 0 ? (
                logs.map((log, index) => (
                  <div key={index} className="mb-1">{log}</div>
                ))
              ) : (
                <div className="text-gray-500">No logs available</div>
              )}
            </div>
          </Card>

          <Card title="Quick Actions">
            <div className="space-y-3">
              <button className="w-full px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700">
                Enable Dry Run Mode
              </button>
              <button className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
                Start Trading (Test)
              </button>
              <button className="w-full px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
                Emergency Stop
              </button>
              <div className="text-xs text-gray-500 mt-2">
                Note: Actions currently in view-only mode
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}