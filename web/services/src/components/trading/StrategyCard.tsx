'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Star, TrendingUp, TrendingDown, Activity, Zap, Shield, Brain } from 'lucide-react';

export type StrategyRarity = 'common' | 'rare' | 'epic' | 'legendary';
export type StrategyType = 'trend' | 'scalp' | 'arbitrage' | 'ml' | 'grid' | 'dca';

export interface Strategy {
  id: string;
  name: string;
  type: StrategyType;
  rarity: StrategyRarity;
  description: string;
  winRate: number;
  pnl: number;
  trades: number;
  maxDrawdown: number;
  sharpeRatio: number;
  isActive: boolean;
  risk: 'low' | 'medium' | 'high';
  author?: string;
  price?: number; // Цена в маркетплейсе
}

interface StrategyCardProps {
  strategy: Strategy;
  onActivate?: (strategy: Strategy) => void;
  onDeactivate?: (strategy: Strategy) => void;
  onPurchase?: (strategy: Strategy) => void;
  showPrice?: boolean;
  className?: string;
}

const rarityStyles = {
  common: {
    border: 'border-gray-500',
    glow: 'hover:shadow-[0_0_20px_rgba(107,114,128,0.5)]',
    accent: 'text-gray-400',
    bg: 'from-gray-800/50 to-gray-700/50',
    particle: 'bg-gray-400'
  },
  rare: {
    border: 'border-mirai-primary',
    glow: 'hover:shadow-neon-primary',
    accent: 'text-mirai-primary',
    bg: 'from-mirai-primary/20 to-blue-800/50',
    particle: 'bg-mirai-primary'
  },
  epic: {
    border: 'border-mirai-secondary',
    glow: 'hover:shadow-neon-secondary',
    accent: 'text-mirai-secondary',
    bg: 'from-mirai-secondary/20 to-purple-800/50',
    particle: 'bg-mirai-secondary'
  },
  legendary: {
    border: 'border-mirai-accent',
    glow: 'hover:shadow-neon-accent',
    accent: 'text-mirai-accent',
    bg: 'from-mirai-accent/20 to-pink-800/50',
    particle: 'bg-mirai-accent'
  }
};

const typeIcons = {
  trend: <TrendingUp className="w-5 h-5" />,
  scalp: <Zap className="w-5 h-5" />,
  arbitrage: <Activity className="w-5 h-5" />,
  ml: <Brain className="w-5 h-5" />,
  grid: <Shield className="w-5 h-5" />,
  dca: <TrendingDown className="w-5 h-5" />
};

const riskColors = {
  low: 'text-mirai-success',
  medium: 'text-mirai-warning',
  high: 'text-mirai-error'
};

export function StrategyCard({
  strategy,
  onActivate,
  onDeactivate,
  onPurchase,
  showPrice = false,
  className,
  ...props
}: StrategyCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);
  
  const rarity = rarityStyles[strategy.rarity];
  
  const renderStars = (rating: number) => {
    const stars = Math.round(rating / 20); // Convert to 1-5 scale
    return Array.from({ length: 5 }).map((_, i) => (
      <Star
        key={i}
        className={cn(
          'w-3 h-3',
          i < stars ? 'fill-yellow-400 text-yellow-400' : 'text-gray-600'
        )}
      />
    ));
  };

  const handleCardClick = () => {
    setIsFlipped(!isFlipped);
  };

  const handleActionClick = (e: React.MouseEvent, action: 'activate' | 'deactivate' | 'purchase') => {
    e.stopPropagation();
    
    switch (action) {
      case 'activate':
        onActivate?.(strategy);
        break;
      case 'deactivate':
        onDeactivate?.(strategy);
        break;
      case 'purchase':
        onPurchase?.(strategy);
        break;
    }
  };

  return (
    <div 
      className={cn(
        'relative w-64 h-80 perspective-1000 cursor-pointer',
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleCardClick}
      {...props}
    >
      {/* Card Container */}
      <div className={cn(
        'relative w-full h-full transition-transform duration-700 transform-style-3d',
        isFlipped && 'rotate-y-180'
      )}>
        
        {/* Front Side */}
        <div className={cn(
          'absolute inset-0 w-full h-full backface-hidden',
          'bg-gradient-to-br', rarity.bg,
          'border-2', rarity.border,
          'rounded-xl overflow-hidden',
          'transition-all duration-300',
          isHovered && rarity.glow,
          isHovered && 'scale-105 -translate-y-2'
        )}>
          
          {/* Holographic Shimmer Effect */}
          <div className="absolute inset-0 opacity-30">
            <div className={cn(
              'absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent',
              'transform -skew-x-12 transition-transform duration-1000',
              isHovered ? 'translate-x-full' : '-translate-x-full'
            )} />
          </div>

          {/* Animated Particles */}
          {strategy.rarity !== 'common' && (
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              {Array.from({ length: strategy.rarity === 'legendary' ? 8 : 4 }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    'absolute w-1 h-1 rounded-full opacity-70 animate-pulse',
                    rarity.particle
                  )}
                  style={{
                    top: `${10 + Math.random() * 80}%`,
                    left: `${10 + Math.random() * 80}%`,
                    animationDelay: `${i * 0.5}s`,
                    animationDuration: `${2 + Math.random()}s`
                  }}
                />
              ))}
            </div>
          )}

          {/* Header */}
          <div className="relative z-10 p-4">
            <div className="flex items-center justify-between mb-2">
              <div className={cn('flex items-center gap-2', rarity.accent)}>
                {typeIcons[strategy.type]}
                <span className="text-xs font-bold uppercase tracking-wide">
                  {strategy.type}
                </span>
              </div>
              <div className="flex items-center gap-1">
                {renderStars(strategy.winRate)}
              </div>
            </div>
            
            <h3 className="text-lg font-bold text-white mb-1 truncate">
              {strategy.name}
            </h3>
            
            <p className="text-xs text-gray-300 line-clamp-2">
              {strategy.description}
            </p>
          </div>

          {/* Stats */}
          <div className="relative z-10 px-4 py-2 space-y-2">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-400">Win Rate</span>
                <div className={cn('font-bold', strategy.winRate > 60 ? 'text-mirai-success' : 'text-mirai-error')}>
                  {strategy.winRate}%
                </div>
              </div>
              <div>
                <span className="text-gray-400">P&L</span>
                <div className={cn('font-bold', strategy.pnl > 0 ? 'text-mirai-success' : 'text-mirai-error')}>
                  {strategy.pnl > 0 ? '+' : ''}${strategy.pnl}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-400">Trades</span>
                <div className="font-bold text-white">{strategy.trades}</div>
              </div>
              <div>
                <span className="text-gray-400">Risk</span>
                <div className={cn('font-bold uppercase', riskColors[strategy.risk])}>
                  {strategy.risk}
                </div>
              </div>
            </div>
          </div>

          {/* Status Indicator */}
          <div className="absolute bottom-4 left-4 flex items-center gap-2">
            <div className={cn(
              'w-2 h-2 rounded-full',
              strategy.isActive ? 'bg-mirai-success animate-pulse' : 'bg-gray-500'
            )} />
            <span className="text-xs text-gray-400">
              {strategy.isActive ? 'Active' : 'Inactive'}
            </span>
          </div>

          {/* Price Tag */}
          {showPrice && strategy.price && (
            <div className="absolute top-4 right-4 bg-mirai-accent/90 text-white px-2 py-1 rounded-lg text-xs font-bold">
              ${strategy.price}
            </div>
          )}

          {/* Rarity Badge */}
          <div className={cn(
            'absolute bottom-4 right-4 px-2 py-1 rounded-lg text-xs font-bold uppercase',
            'border', rarity.border, rarity.accent,
            'bg-black/30 backdrop-blur-sm'
          )}>
            {strategy.rarity}
          </div>
        </div>

        {/* Back Side */}
        <div className={cn(
          'absolute inset-0 w-full h-full backface-hidden rotate-y-180',
          'bg-gradient-to-br from-mirai-dark/90 to-black/90',
          'border-2', rarity.border,
          'rounded-xl p-4',
          'transition-all duration-300'
        )}>
          <div className="h-full flex flex-col justify-between">
            
            {/* Detailed Stats */}
            <div className="space-y-3">
              <h3 className="text-lg font-bold text-white">{strategy.name}</h3>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Max Drawdown:</span>
                  <span className="text-mirai-error">{strategy.maxDrawdown}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Sharpe Ratio:</span>
                  <span className="text-white">{strategy.sharpeRatio}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Total Trades:</span>
                  <span className="text-white">{strategy.trades}</span>
                </div>
                {strategy.author && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Author:</span>
                    <span className="text-mirai-primary">{strategy.author}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-2">
              {showPrice && strategy.price ? (
                <button
                  onClick={(e) => handleActionClick(e, 'purchase')}
                  className="w-full bg-mirai-accent hover:bg-mirai-accent/80 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                >
                  Purchase ${strategy.price}
                </button>
              ) : (
                <>
                  {strategy.isActive ? (
                    <button
                      onClick={(e) => handleActionClick(e, 'deactivate')}
                      className="w-full bg-mirai-error hover:bg-mirai-error/80 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                    >
                      Deactivate
                    </button>
                  ) : (
                    <button
                      onClick={(e) => handleActionClick(e, 'activate')}
                      className="w-full bg-mirai-success hover:bg-mirai-success/80 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                    >
                      Activate
                    </button>
                  )}
                </>
              )}
              
              <button
                onClick={handleCardClick}
                className="w-full bg-mirai-panel hover:bg-mirai-panel/80 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
              >
                ← Back
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Предустановленные стратегии для демонстрации
export const demoStrategies: Strategy[] = [
  {
    id: '1',
    name: 'Trend Master',
    type: 'trend',
    rarity: 'epic',
    description: 'Advanced trend following with ML predictions',
    winRate: 74,
    pnl: 2547.83,
    trades: 127,
    maxDrawdown: 8.5,
    sharpeRatio: 2.3,
    isActive: true,
    risk: 'medium',
    author: 'Mirai Team'
  },
  {
    id: '2',
    name: 'Scalp Lightning',
    type: 'scalp',
    rarity: 'rare',
    description: 'High-frequency scalping strategy',
    winRate: 68,
    pnl: 1234.56,
    trades: 456,
    maxDrawdown: 12.3,
    sharpeRatio: 1.8,
    isActive: false,
    risk: 'high',
    author: 'Community'
  },
  {
    id: '3',
    name: 'Arbitrage Genius',
    type: 'arbitrage',
    rarity: 'legendary',
    description: 'Multi-exchange arbitrage opportunities',
    winRate: 89,
    pnl: 5678.90,
    trades: 89,
    maxDrawdown: 3.2,
    sharpeRatio: 4.1,
    isActive: true,
    risk: 'low',
    author: 'Elite Trader',
    price: 299
  },
  {
    id: '4',
    name: 'Basic Grid',
    type: 'grid',
    rarity: 'common',
    description: 'Simple grid trading strategy',
    winRate: 52,
    pnl: 345.67,
    trades: 234,
    maxDrawdown: 15.7,
    sharpeRatio: 1.2,
    isActive: false,
    risk: 'medium'
  }
];

// Компонент для отображения коллекции стратегий
interface StrategyCollectionProps {
  strategies: Strategy[];
  onStrategyAction?: (action: string, strategy: Strategy) => void;
  showPrices?: boolean;
  className?: string;
}

export function StrategyCollection({
  strategies,
  onStrategyAction,
  showPrices = false,
  className
}: StrategyCollectionProps) {
  return (
    <div className={cn('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6', className)}>
      {strategies.map((strategy) => (
        <StrategyCard
          key={strategy.id}
          strategy={strategy}
          showPrice={showPrices}
          onActivate={(s) => onStrategyAction?.('activate', s)}
          onDeactivate={(s) => onStrategyAction?.('deactivate', s)}
          onPurchase={(s) => onStrategyAction?.('purchase', s)}
        />
      ))}
    </div>
  );
}