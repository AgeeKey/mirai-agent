'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';
import { 
  BarChart3, TrendingUp, TrendingDown, PieChart, Activity,
  Target, Zap, Shield, Star, Award, Clock, DollarSign,
  Percent, ArrowUpRight, ArrowDownRight, Eye, Filter
} from 'lucide-react';
import { HolographicPanel } from '../ui/HolographicPanel';
import { GlowButton } from '../ui/GlowButton';

interface AnalyticsData {
  totalPnL: number;
  totalTrades: number;
  winRate: number;
  profitFactor: number;
  sharpeRatio: number;
  maxDrawdown: number;
  averageWin: number;
  averageLoss: number;
  totalVolume: number;
  activeStrategies: number;
  bestStrategy: string;
  worstStrategy: string;
  monthlyData: Array<{
    month: string;
    pnl: number;
    trades: number;
    winRate: number;
  }>;
  dailyData: Array<{
    date: string;
    pnl: number;
    volume: number;
    trades: number;
  }>;
  strategyPerformance: Array<{
    name: string;
    pnl: number;
    trades: number;
    winRate: number;
    risk: number;
  }>;
  riskMetrics: {
    var95: number;
    var99: number;
    beta: number;
    alpha: number;
    volatility: number;
  };
}

interface AnalyticsDashboardProps {
  data?: AnalyticsData;
  className?: string;
}

type TimeRange = '24h' | '7d' | '30d' | '90d' | '1y' | 'all';

const MetricCard = ({ 
  title, 
  value, 
  change, 
  icon: Icon, 
  color = 'mirai-primary',
  isPercentage = false,
  isCurrency = false,
  size = 'normal'
}: {
  title: string;
  value: number;
  change?: number;
  icon: any;
  color?: string;
  isPercentage?: boolean;
  isCurrency?: boolean;
  size?: 'small' | 'normal' | 'large';
}) => {
  const formatValue = (val: number) => {
    if (isCurrency) {
      return val >= 1000 ? `$${(val / 1000).toFixed(1)}K` : `$${val.toFixed(2)}`;
    }
    if (isPercentage) {
      return `${val.toFixed(2)}%`;
    }
    return val.toLocaleString();
  };

  const isPositive = change !== undefined ? change >= 0 : value >= 0;
  
  return (
    <div className={cn(
      'relative p-4 rounded-lg bg-mirai-panel/20 border border-mirai-primary/20',
      'hover:border-mirai-primary/40 transition-all duration-300',
      size === 'large' && 'p-6',
      size === 'small' && 'p-3'
    )}>
      
      {/* Glow effect based on value */}
      {(value > 0 || (change !== undefined && change > 0)) && (
        <div className={cn(
          'absolute inset-0 rounded-lg opacity-10',
          `bg-${color}`,
          'animate-pulse'
        )} />
      )}
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-2">
          <div className={cn('p-2 rounded-lg', `bg-${color}/20`)}>
            <Icon className={cn('w-5 h-5', `text-${color}`, size === 'small' && 'w-4 h-4')} />
          </div>
          
          {change !== undefined && (
            <div className={cn(
              'flex items-center gap-1 text-sm font-medium',
              isPositive ? 'text-mirai-success' : 'text-mirai-error'
            )}>
              {isPositive ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
              {Math.abs(change).toFixed(2)}%
            </div>
          )}
        </div>
        
        <div>
          <h3 className={cn(
            'text-gray-300 text-sm',
            size === 'large' && 'text-base',
            size === 'small' && 'text-xs'
          )}>
            {title}
          </h3>
          <p className={cn(
            'text-white font-bold text-xl mt-1',
            size === 'large' && 'text-3xl',
            size === 'small' && 'text-lg',
            value > 0 ? `text-${color}` : value < 0 ? 'text-mirai-error' : 'text-gray-400'
          )}>
            {formatValue(value)}
          </p>
        </div>
      </div>
    </div>
  );
};

const PerformanceChart = ({ data, type }: { data: any[], type: 'line' | 'bar' }) => {
  const maxValue = Math.max(...data.map(d => Math.abs(d.pnl || d.value || 0)));
  
  return (
    <div className="h-40 flex items-end justify-between gap-1 p-4">
      {data.map((item, index) => {
        const height = Math.abs(item.pnl || item.value || 0) / maxValue * 100;
        const isPositive = (item.pnl || item.value || 0) >= 0;
        
        return (
          <div key={index} className="flex-1 flex flex-col items-center">
            <div 
              className={cn(
                'w-full max-w-8 rounded-t transition-all duration-500',
                isPositive 
                  ? 'bg-gradient-to-t from-mirai-success to-green-400' 
                  : 'bg-gradient-to-t from-mirai-error to-red-400',
                'hover:opacity-80 cursor-pointer'
              )}
              style={{ height: `${Math.max(height, 2)}%` }}
              title={`${item.date || item.month}: ${item.pnl || item.value}${typeof (item.pnl || item.value) === 'number' ? '%' : ''}`}
            />
            <span className="text-xs text-gray-400 mt-1 rotate-45 origin-bottom-left">
              {(item.date || item.month || '').slice(-2)}
            </span>
          </div>
        );
      })}
    </div>
  );
};

const StrategyRadar = ({ strategies }: { strategies: any[] }) => {
  const maxRisk = Math.max(...strategies.map(s => s.risk));
  const maxPnL = Math.max(...strategies.map(s => Math.abs(s.pnl)));
  
  return (
    <div className="relative w-48 h-48 mx-auto">
      {/* Radar background rings */}
      {[1, 2, 3, 4, 5].map(ring => (
        <div
          key={ring}
          className="absolute border border-mirai-primary/20 rounded-full"
          style={{
            width: `${ring * 20}%`,
            height: `${ring * 20}%`,
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)'
          }}
        />
      ))}
      
      {/* Strategy points */}
      {strategies.slice(0, 8).map((strategy, index) => {
        const angle = (index / strategies.length) * 2 * Math.PI;
        const risk = (strategy.risk / maxRisk) * 40 + 10; // 10-50% radius
        const x = 50 + Math.cos(angle) * risk;
        const y = 50 + Math.sin(angle) * risk;
        const pnlIntensity = Math.abs(strategy.pnl) / maxPnL;
        
        return (
          <div
            key={strategy.name}
            className={cn(
              'absolute w-3 h-3 rounded-full transition-all duration-300 hover:scale-150',
              strategy.pnl >= 0 ? 'bg-mirai-success' : 'bg-mirai-error',
              'cursor-pointer'
            )}
            style={{
              left: `${x}%`,
              top: `${y}%`,
              transform: 'translate(-50%, -50%)',
              opacity: 0.6 + pnlIntensity * 0.4,
              boxShadow: strategy.pnl >= 0 
                ? `0 0 ${10 + pnlIntensity * 20}px rgba(34,197,94,0.6)`
                : `0 0 ${10 + pnlIntensity * 20}px rgba(239,68,68,0.6)`
            }}
            title={`${strategy.name}: PnL $${strategy.pnl}, Risk ${strategy.risk}%`}
          />
        );
      })}
      
      {/* Center point */}
      <div className="absolute w-2 h-2 bg-mirai-primary rounded-full top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
    </div>
  );
};

export function AnalyticsDashboard({ data, className, ...props }: AnalyticsDashboardProps) {
  const [selectedTimeRange, setSelectedTimeRange] = useState<TimeRange>('30d');
  const [selectedView, setSelectedView] = useState<'overview' | 'performance' | 'risk' | 'strategies'>('overview');
  const [animationEnabled, setAnimationEnabled] = useState(true);

  // Demo data if none provided
  const analyticsData: AnalyticsData = data || {
    totalPnL: 12450.67,
    totalTrades: 342,
    winRate: 68.5,
    profitFactor: 1.85,
    sharpeRatio: 2.34,
    maxDrawdown: -8.2,
    averageWin: 245.30,
    averageLoss: -132.50,
    totalVolume: 2450000,
    activeStrategies: 7,
    bestStrategy: 'Momentum Alpha',
    worstStrategy: 'Mean Reversion',
    monthlyData: [
      { month: 'Jan', pnl: 1250, trades: 45, winRate: 72 },
      { month: 'Feb', pnl: 890, trades: 38, winRate: 65 },
      { month: 'Mar', pnl: 2100, trades: 52, winRate: 75 },
      { month: 'Apr', pnl: -450, trades: 28, winRate: 43 },
      { month: 'May', pnl: 1680, trades: 41, winRate: 69 },
      { month: 'Jun', pnl: 3420, trades: 58, winRate: 78 }
    ],
    dailyData: Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().slice(5, 10),
      pnl: (Math.random() - 0.4) * 1000,
      volume: Math.random() * 100000,
      trades: Math.floor(Math.random() * 20) + 5
    })),
    strategyPerformance: [
      { name: 'Momentum Alpha', pnl: 3450, trades: 89, winRate: 76, risk: 15 },
      { name: 'Mean Reversion', pnl: -230, trades: 45, winRate: 42, risk: 25 },
      { name: 'Arbitrage Bot', pnl: 1680, trades: 156, winRate: 85, risk: 8 },
      { name: 'Breakout Hunter', pnl: 2100, trades: 67, winRate: 68, risk: 30 },
      { name: 'Grid Trading', pnl: 890, trades: 234, winRate: 62, risk: 12 },
      { name: 'DCA Strategy', pnl: 1250, trades: 78, winRate: 71, risk: 18 },
      { name: 'Scalping Pro', pnl: 2800, trades: 445, winRate: 58, risk: 35 }
    ],
    riskMetrics: {
      var95: -2.5,
      var99: -4.8,
      beta: 0.75,
      alpha: 0.08,
      volatility: 18.5
    }
  };

  const timeRanges = [
    { value: '24h', label: '24H' },
    { value: '7d', label: '7D' },
    { value: '30d', label: '30D' },
    { value: '90d', label: '3M' },
    { value: '1y', label: '1Y' },
    { value: 'all', label: 'ALL' }
  ];

  const views = [
    { value: 'overview', label: 'Overview', icon: Eye },
    { value: 'performance', label: 'Performance', icon: TrendingUp },
    { value: 'risk', label: 'Risk', icon: Shield },
    { value: 'strategies', label: 'Strategies', icon: Target }
  ];

  return (
    <div className={cn('space-y-6', className)} {...props}>
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gradient-primary mb-2">Analytics Dashboard</h2>
          <p className="text-gray-300">Performance insights and market analysis</p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Animation toggle */}
          <button
            onClick={() => setAnimationEnabled(!animationEnabled)}
            className={cn(
              'p-2 rounded-lg transition-colors',
              animationEnabled 
                ? 'bg-mirai-primary/20 text-mirai-primary' 
                : 'bg-gray-600/20 text-gray-400'
            )}
          >
            <Zap className="w-4 h-4" />
          </button>
          
          {/* Time range selector */}
          <div className="flex bg-mirai-panel/30 rounded-lg p-1">
            {timeRanges.map(range => (
              <button
                key={range.value}
                onClick={() => setSelectedTimeRange(range.value as TimeRange)}
                className={cn(
                  'px-3 py-1 text-sm rounded transition-colors',
                  selectedTimeRange === range.value
                    ? 'bg-mirai-primary text-white'
                    : 'text-gray-400 hover:text-white'
                )}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* View selector */}
      <div className="flex bg-mirai-panel/20 rounded-lg p-1">
        {views.map(view => {
          const IconComponent = view.icon;
          return (
            <button
              key={view.value}
              onClick={() => setSelectedView(view.value as any)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all duration-300',
                selectedView === view.value
                  ? 'bg-mirai-primary text-white shadow-neon-primary'
                  : 'text-gray-400 hover:text-white hover:bg-mirai-panel/30'
              )}
            >
              <IconComponent className="w-4 h-4" />
              {view.label}
            </button>
          );
        })}
      </div>

      {/* Overview */}
      {selectedView === 'overview' && (
        <div className="space-y-6">
          
          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              title="Total P&L"
              value={analyticsData.totalPnL}
              change={15.2}
              icon={DollarSign}
              color="mirai-success"
              isCurrency
              size="large"
            />
            <MetricCard
              title="Win Rate"
              value={analyticsData.winRate}
              change={2.3}
              icon={Target}
              color="mirai-primary"
              isPercentage
              size="large"
            />
            <MetricCard
              title="Total Trades"
              value={analyticsData.totalTrades}
              change={8.7}
              icon={Activity}
              color="mirai-secondary"
              size="large"
            />
            <MetricCard
              title="Sharpe Ratio"
              value={analyticsData.sharpeRatio}
              change={5.1}
              icon={Award}
              color="mirai-accent"
              size="large"
            />
          </div>

          {/* Performance Chart */}
          <HolographicPanel className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-white">Daily Performance</h3>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Activity className="w-4 h-4" />
                Last 30 days
              </div>
            </div>
            <PerformanceChart data={analyticsData.dailyData} type="bar" />
          </HolographicPanel>

          {/* Secondary Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              title="Profit Factor"
              value={analyticsData.profitFactor}
              icon={TrendingUp}
              color="mirai-success"
            />
            <MetricCard
              title="Max Drawdown"
              value={analyticsData.maxDrawdown}
              icon={TrendingDown}
              color="mirai-error"
              isPercentage
            />
            <MetricCard
              title="Active Strategies"
              value={analyticsData.activeStrategies}
              icon={Star}
              color="mirai-accent"
            />
            <MetricCard
              title="Total Volume"
              value={analyticsData.totalVolume}
              icon={BarChart3}
              color="mirai-secondary"
              isCurrency
            />
          </div>
        </div>
      )}

      {/* Performance View */}
      {selectedView === 'performance' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          <HolographicPanel className="p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Monthly P&L</h3>
            <PerformanceChart data={analyticsData.monthlyData} type="bar" />
          </HolographicPanel>

          <HolographicPanel className="p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Win/Loss Analysis</h3>
            <div className="space-y-4">
              <MetricCard
                title="Average Win"
                value={analyticsData.averageWin}
                icon={TrendingUp}
                color="mirai-success"
                isCurrency
              />
              <MetricCard
                title="Average Loss"
                value={analyticsData.averageLoss}
                icon={TrendingDown}
                color="mirai-error"
                isCurrency
              />
              <div className="p-4 bg-mirai-panel/20 rounded-lg">
                <div className="text-sm text-gray-300 mb-2">Win/Loss Ratio</div>
                <div className="text-2xl font-bold text-mirai-primary">
                  {(analyticsData.averageWin / Math.abs(analyticsData.averageLoss)).toFixed(2)}:1
                </div>
              </div>
            </div>
          </HolographicPanel>
        </div>
      )}

      {/* Risk View */}
      {selectedView === 'risk' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          <HolographicPanel className="p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Risk Metrics</h3>
            <div className="space-y-4">
              <MetricCard
                title="VaR (95%)"
                value={analyticsData.riskMetrics.var95}
                icon={Shield}
                color="mirai-warning"
                isPercentage
              />
              <MetricCard
                title="VaR (99%)"
                value={analyticsData.riskMetrics.var99}
                icon={Shield}
                color="mirai-error"
                isPercentage
              />
              <MetricCard
                title="Beta"
                value={analyticsData.riskMetrics.beta}
                icon={Activity}
                color="mirai-primary"
              />
              <MetricCard
                title="Alpha"
                value={analyticsData.riskMetrics.alpha}
                icon={Star}
                color="mirai-success"
                isPercentage
              />
            </div>
          </HolographicPanel>

          <HolographicPanel className="p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Volatility Analysis</h3>
            <div className="text-center">
              <div className="text-4xl font-bold text-mirai-accent mb-2">
                {analyticsData.riskMetrics.volatility}%
              </div>
              <div className="text-gray-300 mb-4">Annualized Volatility</div>
              
              {/* Volatility visualization */}
              <div className="relative w-32 h-32 mx-auto">
                <div className="absolute inset-0 border-4 border-mirai-panel/30 rounded-full"></div>
                <div 
                  className="absolute inset-0 border-4 border-mirai-accent rounded-full transition-all duration-1000"
                  style={{
                    clipPath: `polygon(50% 50%, 50% 0%, ${50 + (analyticsData.riskMetrics.volatility / 100) * 50}% 0%, 50% 50%)`
                  }}
                ></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <Zap className="w-8 h-8 text-mirai-accent" />
                </div>
              </div>
            </div>
          </HolographicPanel>
        </div>
      )}

      {/* Strategies View */}
      {selectedView === 'strategies' && (
        <div className="space-y-6">
          
          {/* Strategy Radar */}
          <HolographicPanel className="p-6">
            <h3 className="text-xl font-semibold text-white mb-4 text-center">Strategy Risk/Return Map</h3>
            <StrategyRadar strategies={analyticsData.strategyPerformance} />
            <div className="text-center text-sm text-gray-400 mt-4">
              Distance from center = Risk Level • Color intensity = P&L
            </div>
          </HolographicPanel>

          {/* Strategy Performance Table */}
          <HolographicPanel className="p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Strategy Performance</h3>
            <div className="space-y-3">
              {analyticsData.strategyPerformance.map((strategy, index) => (
                <div key={strategy.name} className="p-3 bg-mirai-panel/20 rounded-lg border border-mirai-primary/10">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className={cn(
                        'w-3 h-3 rounded-full',
                        strategy.pnl >= 0 ? 'bg-mirai-success' : 'bg-mirai-error'
                      )} />
                      <span className="font-semibold text-white">{strategy.name}</span>
                    </div>
                    <div className={cn(
                      'text-sm font-mono',
                      strategy.pnl >= 0 ? 'text-mirai-success' : 'text-mirai-error'
                    )}>
                      {strategy.pnl >= 0 ? '+' : ''}${strategy.pnl}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-gray-400">Trades</div>
                      <div className="text-white">{strategy.trades}</div>
                    </div>
                    <div>
                      <div className="text-gray-400">Win Rate</div>
                      <div className="text-white">{strategy.winRate}%</div>
                    </div>
                    <div>
                      <div className="text-gray-400">Risk</div>
                      <div className="text-white">{strategy.risk}%</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </HolographicPanel>
        </div>
      )}
    </div>
  );
}