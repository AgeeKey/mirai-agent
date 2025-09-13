'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/Card';
import { Table } from '@/components/Table';
import { apiClient } from '@/lib/api';
import Link from 'next/link';

interface Order {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  status: 'FILLED' | 'PENDING' | 'CANCELLED';
  timestamp: string;
}

export default function OrdersPage() {
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [activeOrders, setActiveOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'recent' | 'active'>('recent');

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const [recentData, activeData] = await Promise.all([
          apiClient.get('/orders/recent?limit=50'),
          apiClient.get('/orders/active')
        ]);
        
        setRecentOrders(recentData.data?.orders || []);
        setActiveOrders(activeData.data?.orders || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch orders');
      } finally {
        setIsLoading(false);
      }
    };

    fetchOrders();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchOrders, 30000);
    return () => clearInterval(interval);
  }, []);

  const orderColumns = [
    {
      key: 'id',
      header: 'Order ID',
      render: (value: string) => (
        <span className="font-mono text-xs">{value?.slice(0, 8) || 'N/A'}</span>
      )
    },
    {
      key: 'symbol',
      header: 'Symbol',
      render: (value: string) => (
        <span className="font-semibold">{value || 'N/A'}</span>
      )
    },
    {
      key: 'side',
      header: 'Side',
      render: (value: string) => (
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          value === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {value || 'N/A'}
        </span>
      )
    },
    {
      key: 'quantity',
      header: 'Quantity',
      render: (value: number) => value?.toFixed(4) || '0.0000'
    },
    {
      key: 'price',
      header: 'Price',
      render: (value: number) => `$${value?.toFixed(2) || '0.00'}`
    },
    {
      key: 'status',
      header: 'Status',
      render: (value: string) => (
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          value === 'FILLED' ? 'bg-green-100 text-green-800' :
          value === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {value || 'N/A'}
        </span>
      )
    },
    {
      key: 'timestamp',
      header: 'Time',
      render: (value: string) => {
        if (!value) return 'N/A';
        try {
          return new Date(value).toLocaleString();
        } catch {
          return 'Invalid date';
        }
      }
    }
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading orders...</p>
        </div>
      </div>
    );
  }

  const currentOrders = activeTab === 'recent' ? recentOrders : activeOrders;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
            <div className="flex space-x-4">
              <Link href="/dashboard" className="text-indigo-600 hover:text-indigo-800">
                ← Dashboard
              </Link>
              <Link href="/risk" className="text-indigo-600 hover:text-indigo-800">
                Risk Config
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-indigo-600">{recentOrders.length}</div>
              <div className="text-sm text-gray-600">Recent Orders</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{activeOrders.length}</div>
              <div className="text-sm text-gray-600">Active Orders</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {recentOrders.filter(order => order.status === 'FILLED').length}
              </div>
              <div className="text-sm text-gray-600">Filled Orders</div>
            </div>
          </Card>
        </div>

        <Card title="Order History">
          <div className="mb-4">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex">
                <button
                  onClick={() => setActiveTab('recent')}
                  className={`py-2 px-4 border-b-2 font-medium text-sm ${
                    activeTab === 'recent'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Recent Orders ({recentOrders.length})
                </button>
                <button
                  onClick={() => setActiveTab('active')}
                  className={`py-2 px-4 border-b-2 font-medium text-sm ${
                    activeTab === 'active'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Active Orders ({activeOrders.length})
                </button>
              </nav>
            </div>
          </div>

          <Table
            columns={orderColumns}
            data={currentOrders}
            emptyMessage={
              activeTab === 'recent' 
                ? 'No recent orders found' 
                : 'No active orders found'
            }
          />

          {currentOrders.length === 0 && (
            <div className="text-center py-8">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p className="text-gray-500 text-lg">
                {activeTab === 'recent' 
                  ? 'No recent orders to display' 
                  : 'No active orders at the moment'}
              </p>
              <p className="text-gray-400 text-sm mt-2">
                {activeTab === 'recent' 
                  ? 'Orders will appear here once trading begins' 
                  : 'New orders will show up here when placed'}
              </p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}