'use client';

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Shield, AlertTriangle, TrendingDown, Activity, Zap } from 'lucide-react';

export type ShieldLevel = 1 | 2 | 3 | 4 | 5;
export type RiskLevel = 'safe' | 'low' | 'medium' | 'high' | 'critical';

export interface RiskMetrics {
  drawdown: number;        // Текущая просадка в %
  maxDrawdown: number;     // Максимальная просадка в %
  exposure: number;        // Текущая экспозиция в %
  leverage: number;        // Плечо
  portfolioHealth: number; // Здоровье портфеля в %
  riskScore: number;       // Общий риск-скор 0-100
  shieldLevel: ShieldLevel;
  lastUpdate: Date;
}

interface RiskShieldProps {
  metrics: RiskMetrics;
  onShieldLevelChange?: (level: ShieldLevel) => void;
  onEmergencyStop?: () => void;
  className?: string;
}

const shieldConfigs = {
  1: {
    name: 'Basic Shield',
    color: 'from-gray-400 to-gray-600',
    glow: 'shadow-[0_0_20px_rgba(107,114,128,0.5)]',
    particles: 'bg-gray-400',
    icon: '🛡️',
    description: 'Минимальная защита'
  },
  2: {
    name: 'Enhanced Shield',
    color: 'from-mirai-primary to-blue-600',
    glow: 'shadow-neon-primary',
    particles: 'bg-mirai-primary',
    icon: '⚡',
    description: 'Улучшенная защита'
  },
  3: {
    name: 'Advanced Shield',
    color: 'from-mirai-secondary to-purple-600',
    glow: 'shadow-neon-secondary',
    particles: 'bg-mirai-secondary',
    icon: '💜',
    description: 'Продвинутая защита'
  },
  4: {
    name: 'Elite Shield',
    color: 'from-mirai-accent to-pink-600',
    glow: 'shadow-neon-accent',
    particles: 'bg-mirai-accent',
    icon: '⭐',
    description: 'Элитная защита'
  },
  5: {
    name: 'Ultimate Shield',
    color: 'from-yellow-400 to-orange-500',
    glow: 'shadow-[0_0_30px_rgba(251,191,36,0.8)]',
    particles: 'bg-yellow-400',
    icon: '👑',
    description: 'Максимальная защита'
  }
};

const getRiskLevel = (riskScore: number): RiskLevel => {
  if (riskScore <= 20) return 'safe';
  if (riskScore <= 40) return 'low';
  if (riskScore <= 60) return 'medium';
  if (riskScore <= 80) return 'high';
  return 'critical';
};

const getRiskColor = (level: RiskLevel) => {
  switch (level) {
    case 'safe': return 'text-mirai-success';
    case 'low': return 'text-green-400';
    case 'medium': return 'text-mirai-warning';
    case 'high': return 'text-orange-400';
    case 'critical': return 'text-mirai-error';
  }
};

export function RiskShield({
  metrics,
  onShieldLevelChange,
  onEmergencyStop,
  className,
  ...props
}: RiskShieldProps) {
  const [isCharging, setIsCharging] = useState(false);
  const [shieldAnimation, setShieldAnimation] = useState('');
  
  const riskLevel = getRiskLevel(metrics.riskScore);
  const shieldConfig = shieldConfigs[metrics.shieldLevel];
  
  useEffect(() => {
    // Анимация при критическом риске
    if (riskLevel === 'critical') {
      setShieldAnimation('animate-pulse');
    } else {
      setShieldAnimation('');
    }
  }, [riskLevel]);

  const handleShieldUpgrade = () => {
    if (metrics.shieldLevel < 5) {
      setIsCharging(true);
      setTimeout(() => {
        onShieldLevelChange?.(Math.min(5, metrics.shieldLevel + 1) as ShieldLevel);
        setIsCharging(false);
      }, 1500);
    }
  };

  const handleEmergencyStop = () => {
    onEmergencyStop?.();
  };

  return (
    <div className={cn('relative p-6 space-y-6', className)} {...props}>
      
      {/* Главный щит */}
      <div className="relative flex items-center justify-center">
        
        {/* Фоновые кольца защиты */}
        <div className="absolute inset-0 flex items-center justify-center">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className={cn(
                'absolute rounded-full border-2 opacity-30',
                shieldConfig.color.includes('gray') ? 'border-gray-400' : 'border-current',
                shieldAnimation
              )}
              style={{
                width: `${120 + i * 40}px`,
                height: `${120 + i * 40}px`,
                animationDelay: `${i * 0.5}s`
              }}
            />
          ))}
        </div>

        {/* Основной щит */}
        <div className={cn(
          'relative w-32 h-32 rounded-full',
          'bg-gradient-to-br', shieldConfig.color,
          'flex items-center justify-center',
          'border-4 border-current',
          shieldConfig.glow,
          'transition-all duration-500',
          isCharging && 'scale-110 animate-pulse'
        )}>
          
          {/* Центральная иконка */}
          <div className="text-4xl animate-pulse">
            {shieldConfig.icon}
          </div>
          
          {/* Частицы энергии */}
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className={cn(
                'absolute w-2 h-2 rounded-full opacity-70',
                shieldConfig.particles,
                'animate-ping'
              )}
              style={{
                top: `${20 + Math.random() * 60}%`,
                left: `${20 + Math.random() * 60}%`,
                animationDelay: `${i * 0.3}s`,
                animationDuration: `${1.5 + Math.random()}s`
              }}
            />
          ))}
          
          {/* Уровень щита */}
          <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
            <div className="bg-black/70 backdrop-blur-sm px-2 py-1 rounded-lg text-xs font-bold text-white border border-current">
              Level {metrics.shieldLevel}
            </div>
          </div>
        </div>

        {/* Индикатор зарядки */}
        {isCharging && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-40 h-40 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Информация о щите */}
      <div className="text-center space-y-2">
        <h3 className="text-lg font-bold text-white">{shieldConfig.name}</h3>
        <p className="text-sm text-gray-300">{shieldConfig.description}</p>
      </div>

      {/* Статистики защиты */}
      <div className="grid grid-cols-2 gap-4">
        
        {/* HP Bar (Portfolio Health) */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-300">Portfolio HP</span>
            <span className="text-xs font-mono">{metrics.portfolioHealth}%</span>
          </div>
          <div className="w-full h-3 bg-black/30 rounded-full overflow-hidden">
            <div 
              className={cn(
                'h-full transition-all duration-500 rounded-full',
                metrics.portfolioHealth > 70 ? 'bg-gradient-to-r from-mirai-success to-green-400' :
                metrics.portfolioHealth > 40 ? 'bg-gradient-to-r from-mirai-warning to-yellow-400' :
                'bg-gradient-to-r from-mirai-error to-red-400 animate-pulse'
              )}
              style={{ width: `${metrics.portfolioHealth}%` }}
            />
          </div>
        </div>

        {/* Drawdown */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-mirai-error" />
            <span className="text-sm text-gray-300">Drawdown</span>
            <span className="text-xs font-mono text-mirai-error">{metrics.drawdown}%</span>
          </div>
          <div className="w-full h-3 bg-black/30 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-mirai-error to-red-600 transition-all duration-500 rounded-full"
              style={{ width: `${(metrics.drawdown / metrics.maxDrawdown) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Общий риск-скор */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className={cn('w-5 h-5', getRiskColor(riskLevel))} />
            <span className="text-sm text-gray-300">Risk Level</span>
          </div>
          <span className={cn('text-sm font-bold uppercase', getRiskColor(riskLevel))}>
            {riskLevel}
          </span>
        </div>
        
        <div className="relative w-full h-4 bg-black/30 rounded-full overflow-hidden">
          <div 
            className={cn(
              'h-full transition-all duration-500 rounded-full',
              riskLevel === 'safe' ? 'bg-gradient-to-r from-mirai-success to-green-400' :
              riskLevel === 'low' ? 'bg-gradient-to-r from-green-400 to-mirai-warning' :
              riskLevel === 'medium' ? 'bg-gradient-to-r from-mirai-warning to-orange-400' :
              riskLevel === 'high' ? 'bg-gradient-to-r from-orange-400 to-mirai-error' :
              'bg-gradient-to-r from-mirai-error to-red-600 animate-pulse'
            )}
            style={{ width: `${metrics.riskScore}%` }}
          />
          
          {/* Числовое значение */}
          <div className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white">
            {metrics.riskScore}/100
          </div>
        </div>
      </div>

      {/* Дополнительные метрики */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Exposure:</span>
          <span className="text-white">{metrics.exposure}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Leverage:</span>
          <span className="text-white">{metrics.leverage}x</span>
        </div>
      </div>

      {/* Кнопки управления */}
      <div className="flex gap-3">
        <button
          onClick={handleShieldUpgrade}
          disabled={metrics.shieldLevel >= 5 || isCharging}
          className={cn(
            'flex-1 py-2 px-4 rounded-lg font-semibold transition-all duration-300',
            'bg-gradient-to-r from-mirai-primary to-blue-600',
            'hover:from-blue-500 hover:to-blue-700',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'text-white border border-mirai-primary/50',
            isCharging && 'animate-pulse'
          )}
        >
          <div className="flex items-center justify-center gap-2">
            <Zap className="w-4 h-4" />
            {isCharging ? 'Charging...' : 'Upgrade Shield'}
          </div>
        </button>
        
        <button
          onClick={handleEmergencyStop}
          className="px-4 py-2 bg-gradient-to-r from-mirai-error to-red-600 hover:from-red-500 hover:to-red-700 text-white rounded-lg font-semibold transition-all duration-300 border border-mirai-error/50"
        >
          <Activity className="w-4 h-4" />
        </button>
      </div>

      {/* Время последнего обновления */}
      <div className="text-center text-xs text-gray-500">
        Last update: {metrics.lastUpdate.toLocaleTimeString()}
      </div>
    </div>
  );
}

// Демо-данные для тестирования
export const demoRiskMetrics: RiskMetrics = {
  drawdown: 8.5,
  maxDrawdown: 15.0,
  exposure: 75.0,
  leverage: 3.0,
  portfolioHealth: 82,
  riskScore: 35,
  shieldLevel: 2,
  lastUpdate: new Date()
};

// Компонент мини-щита для компактного отображения
interface MiniRiskShieldProps {
  metrics: RiskMetrics;
  onClick?: () => void;
  className?: string;
}

export function MiniRiskShield({ metrics, onClick, className }: MiniRiskShieldProps) {
  const riskLevel = getRiskLevel(metrics.riskScore);
  const shieldConfig = shieldConfigs[metrics.shieldLevel];

  return (
    <button
      onClick={onClick}
      className={cn(
        'relative w-16 h-16 rounded-full transition-all duration-300 hover:scale-110',
        'bg-gradient-to-br', shieldConfig.color,
        'border-2 border-current',
        shieldConfig.glow,
        className
      )}
    >
      <div className="text-lg">{shieldConfig.icon}</div>
      
      {/* Индикатор риска */}
      <div className={cn(
        'absolute -top-1 -right-1 w-4 h-4 rounded-full border-2 border-mirai-dark',
        riskLevel === 'safe' ? 'bg-mirai-success' :
        riskLevel === 'low' ? 'bg-green-400' :
        riskLevel === 'medium' ? 'bg-mirai-warning' :
        riskLevel === 'high' ? 'bg-orange-400' :
        'bg-mirai-error animate-pulse'
      )} />
    </button>
  );
}

// Компонент полного риск-дашборда
interface RiskDashboardProps {
  metrics: RiskMetrics;
  onMetricsUpdate?: (metrics: RiskMetrics) => void;
  className?: string;
}

export function RiskDashboard({ metrics, onMetricsUpdate, className }: RiskDashboardProps) {
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  return (
    <div className={cn('space-y-6', className)}>
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gradient-primary mb-2">Risk Management</h2>
        <p className="text-gray-300">Portfolio protection system</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Главный щит */}
        <div className="bg-mirai-panel/30 backdrop-blur-sm rounded-xl border border-mirai-primary/20 p-6">
          <RiskShield 
            metrics={metrics}
            onShieldLevelChange={(level) => onMetricsUpdate?.({...metrics, shieldLevel: level})}
          />
        </div>

        {/* Детальная статистика */}
        <div className="space-y-4">
          <div className="bg-mirai-panel/30 backdrop-blur-sm rounded-xl border border-mirai-primary/20 p-4">
            <h3 className="text-lg font-semibold mb-4 text-white">Risk Breakdown</h3>
            
            <div className="space-y-3">
              {[
                { key: 'Portfolio Health', value: metrics.portfolioHealth, max: 100, unit: '%', icon: '❤️' },
                { key: 'Current Drawdown', value: metrics.drawdown, max: metrics.maxDrawdown, unit: '%', icon: '📉' },
                { key: 'Market Exposure', value: metrics.exposure, max: 100, unit: '%', icon: '🎯' },
                { key: 'Leverage Factor', value: metrics.leverage, max: 10, unit: 'x', icon: '⚖️' }
              ].map((item) => (
                <div key={item.key} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2 text-gray-300">
                      <span>{item.icon}</span>
                      {item.key}
                    </span>
                    <span className="font-mono text-white">
                      {item.value}{item.unit}
                    </span>
                  </div>
                  <div className="w-full h-2 bg-black/30 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-mirai-primary to-mirai-secondary transition-all duration-500"
                      style={{ width: `${(item.value / item.max) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}