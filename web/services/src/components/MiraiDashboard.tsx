'use client'

import React, { useState, useEffect } from 'react'
import { Bot, BarChart3, Activity, Mic, Brain, TrendingUp, Shield, Zap, Star } from 'lucide-react'
import { MiraiChat, TradingStatus } from './mirai/MiraiAvatar'
import KillSwitch from './KillSwitch'
import { GlowButton, MiraiPrimaryButton, MiraiDangerButton } from './ui/GlowButton'
import { HolographicPanel, StatPanel, ProgressPanel } from './ui/HolographicPanel'
import { AdaptiveParticleBackground } from './ui/ParticleBackground'
import TradingPanel from './trading/TradingPanel'
import AnalyticsPanel from './analytics/AnalyticsPanel'
import StudioPanel from './studio/StudioPanel'

export default function MiraiDashboard() {
  const [activeTab, setActiveTab] = useState('overview')
  const [tradingStatus, setTradingStatus] = useState<TradingStatus>({
    isTrading: true,
    pnl: 1247.83,
    winRate: 68.5,
    activePositions: 3,
    marketStatus: 'open',
    lastUpdate: new Date()
  })

  // Симуляция обновления данных
  useEffect(() => {
    const interval = setInterval(() => {
      setTradingStatus(prev => ({
        ...prev,
        pnl: prev.pnl + (Math.random() - 0.5) * 50,
        lastUpdate: new Date()
      }))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const tabs = [
    { id: 'overview', name: 'Обзор', icon: <BarChart3 className="w-4 h-4" /> },
    { id: 'trading', name: 'Торговля', icon: <Activity className="w-4 h-4" /> },
    { id: 'analytics', name: 'Аналитика', icon: <Brain className="w-4 h-4" /> },
    { id: 'emergency', name: 'Kill Switch', icon: <Shield className="w-4 h-4" /> },
    { id: 'studio', name: 'Studio', icon: <Star className="w-4 h-4" /> },
  ]

  return (
    <div className="min-h-screen relative">
      {/* Анимированный фон */}
      <AdaptiveParticleBackground />
      
      {/* Подключение кастомной темы */}
      <link rel="stylesheet" href="/styles/mirai-theme.css" />
      
      {/* Основной градиентный фон */}
      <div className="absolute inset-0 bg-gradient-to-br from-mirai-dark via-blue-900/50 to-purple-900/50" />
      
      {/* Header */}
      <header className="relative z-10 bg-black/20 backdrop-blur-md border-b border-mirai-primary/20">
        <HolographicPanel variant="glass" size="sm" className="border-0 rounded-none">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-mirai-primary to-mirai-secondary rounded-lg flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white neon-glow-primary">Mirai Agent</h1>
                  <p className="text-xs text-gray-300">誉明 - Автономная торговая система v3.0</p>
                </div>
              </div>
              
              {/* Status Indicators */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-mirai-success rounded-full animate-pulse" />
                  <span className="text-sm text-mirai-success">Online</span>
                </div>
                <MiraiPrimaryButton size="sm">
                  <Shield className="w-4 h-4" />
                  Settings
                </MiraiPrimaryButton>
              </div>
            </div>
          </div>
        </HolographicPanel>
      </header>

      {/* Navigation */}
      <nav className="relative z-10 bg-black/10 backdrop-blur-sm border-b border-mirai-primary/10">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-2 border-b-2 font-medium text-sm transition-all duration-300 ${
                  activeTab === tab.id
                    ? 'border-mirai-primary text-mirai-primary shadow-neon-primary'
                    : 'border-transparent text-gray-300 hover:text-white hover:border-mirai-secondary'
                }`}
              >
                {tab.icon}
                <span>{tab.name}</span>
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'emergency' ? (
          <KillSwitch />
        ) : activeTab === 'trading' ? (
          <TradingPanel />
        ) : activeTab === 'analytics' ? (
          <AnalyticsPanel />
        ) : activeTab === 'studio' ? (
          <StudioPanel />
        ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* Mirai Avatar Section */}
          <div className="lg:col-span-1">
            <HolographicPanel variant="cyber" size="lg" animated className="h-fit">
              <h3 className="text-lg font-semibold mb-4 text-center text-gradient-primary">
                Mirai-chan
              </h3>
              <MiraiChat 
                tradingStatus={tradingStatus}
                className="w-full"
              />
              
              {/* Quick Actions */}
              <div className="mt-6 space-y-3">
                <MiraiPrimaryButton size="sm" className="w-full">
                  <Zap className="w-4 h-4" />
                  Emergency Stop
                </MiraiPrimaryButton>
                <GlowButton variant="secondary" size="sm" className="w-full">
                  <Mic className="w-4 h-4" />
                  Voice Chat
                </GlowButton>
              </div>
            </HolographicPanel>
          </div>

          {/* Main Dashboard Content */}
          <div className="lg:col-span-3 space-y-6">
            
            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <StatPanel
                title="Portfolio P&L"
                value={`$${tradingStatus.pnl.toFixed(2)}`}
                subtitle="Today's performance"
                icon={<TrendingUp className="w-4 h-4" />}
                trend={tradingStatus.pnl > 0 ? 'up' : 'down'}
              />
              
              <StatPanel
                title="Active Positions" 
                value={tradingStatus.activePositions}
                subtitle="Currently trading"
                icon={<Activity className="w-4 h-4" />}
                trend="neutral"
              />
              
              <StatPanel
                title="Win Rate"
                value={`${tradingStatus.winRate}%`}
                subtitle="Success ratio"
                icon={<Star className="w-4 h-4" />}
                trend={tradingStatus.winRate > 60 ? 'up' : 'down'}
              />
            </div>

            {/* Progress Indicators */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <ProgressPanel
                title="Daily Drawdown"
                current={15}
                max={100}
                type="hp"
              />
              
              <ProgressPanel
                title="Available Capital"
                current={85}
                max={100}
                type="mp"
              />
            </div>

            {/* Main Trading Panel */}
            <HolographicPanel variant="neon" size="xl">
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-gradient-primary">Trading Overview</h2>
                  <div className="flex gap-3">
                    <MiraiPrimaryButton size="sm">
                      <Activity className="w-4 h-4" />
                      Start Trading
                    </MiraiPrimaryButton>
                    <MiraiDangerButton size="sm">
                      <Shield className="w-4 h-4" />
                      Kill Switch
                    </MiraiDangerButton>
                  </div>
                </div>

                {/* Trading Chart Placeholder */}
                <div className="relative h-64 bg-black/30 rounded-xl border border-mirai-primary/30 overflow-hidden">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <Brain className="w-12 h-12 text-mirai-secondary mx-auto mb-4 animate-pulse" />
                      <h3 className="text-lg font-semibold text-gradient-secondary mb-2">
                        Advanced Trading Chart
                      </h3>
                      <p className="text-gray-400">
                        Real-time market data and AI predictions
                      </p>
                    </div>
                  </div>
                  
                  {/* Scanning effect */}
                  <div className="absolute inset-0 opacity-20">
                    <div className="absolute w-full h-[2px] bg-gradient-to-r from-transparent via-mirai-primary to-transparent animate-cyber-scan" />
                  </div>
                </div>

                {/* Recent Trades */}
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-white mb-4">Recent Trades</h3>
                  <div className="space-y-2">
                    {[
                      { symbol: 'BTCUSDT', side: 'BUY', pnl: +127.50, time: '14:32' },
                      { symbol: 'ETHUSDT', side: 'SELL', pnl: -23.10, time: '14:28' },
                      { symbol: 'ADAUSDT', side: 'BUY', pnl: +89.30, time: '14:15' },
                    ].map((trade, index) => (
                      <HolographicPanel key={index} variant="glass" size="sm">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="font-mono text-sm">{trade.symbol}</span>
                            <span className={`px-2 py-1 rounded text-xs ${
                              trade.side === 'BUY' 
                                ? 'bg-mirai-success/20 text-mirai-success' 
                                : 'bg-mirai-error/20 text-mirai-error'
                            }`}>
                              {trade.side}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`font-mono ${
                              trade.pnl > 0 ? 'text-mirai-success' : 'text-mirai-error'
                            }`}>
                              {trade.pnl > 0 ? '+' : ''}${trade.pnl}
                            </span>
                            <span className="text-gray-400 text-xs">{trade.time}</span>
                          </div>
                        </div>
                      </HolographicPanel>
                    ))}
                  </div>
                </div>
              </div>
            </HolographicPanel>
          </div>
        </div>
        )}
      </main>
    </div>
  )
}
