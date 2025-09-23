'use client'

import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface TradingData {
  time: string
  price: number
  volume: number
  pnl: number
}

const mockData: TradingData[] = [
  { time: '09:00', price: 42500, volume: 120, pnl: 250 },
  { time: '10:00', price: 43200, volume: 150, pnl: 320 },
  { time: '11:00', price: 42800, volume: 110, pnl: 180 },
  { time: '12:00', price: 44100, volume: 180, pnl: 450 },
  { time: '13:00', price: 43900, volume: 160, pnl: 380 },
  { time: '14:00', price: 44500, volume: 200, pnl: 520 },
]

export function TradingChart() {
  const currentPrice = mockData[mockData.length - 1]?.price || 44500
  const previousPrice = mockData[mockData.length - 2]?.price || 43900
  const priceChange = currentPrice - previousPrice
  const priceChangePercent = ((priceChange / previousPrice) * 100).toFixed(2)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Price Chart */}
      <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">BTC/USDT Price</h3>
          <div className="flex items-center space-x-2">
            <span className="text-2xl font-bold text-white">${currentPrice.toLocaleString()}</span>
            <div className={`flex items-center ${priceChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {priceChange >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span className="ml-1">{priceChangePercent}%</span>
            </div>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={mockData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="time" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1F2937', 
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#F9FAFB'
              }} 
            />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke="#10B981" 
              strokeWidth={2}
              dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Volume Chart */}
      <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Trading Volume</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={mockData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="time" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1F2937', 
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#F9FAFB'
              }} 
            />
            <Bar dataKey="volume" fill="#3B82F6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* P&L Chart */}
      <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-6 lg:col-span-2">
        <h3 className="text-lg font-semibold text-white mb-4">P&L Performance</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={mockData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="time" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1F2937', 
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#F9FAFB'
              }} 
            />
            <Line 
              type="monotone" 
              dataKey="pnl" 
              stroke="#F59E0B" 
              strokeWidth={2}
              dot={{ fill: '#F59E0B', strokeWidth: 2, r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}