'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface HolographicPanelProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'glass' | 'neon' | 'cyber' | 'ethereal';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  animated?: boolean;
  glowBorder?: boolean;
}

const variantStyles = {
  glass: 'bg-white/10 backdrop-blur-md border border-white/20',
  neon: 'bg-mirai-dark/80 backdrop-blur-sm border border-mirai-primary/50 shadow-[0_0_20px_rgba(0,226,255,0.3)]',
  cyber: 'bg-black/70 backdrop-blur-lg border-2 border-mirai-accent/60 shadow-[0_0_30px_rgba(255,107,193,0.4)]',
  ethereal: 'bg-gradient-to-br from-white/5 to-white/15 backdrop-blur-xl border border-white/30'
};

const sizeStyles = {
  sm: 'p-4 rounded-lg',
  md: 'p-6 rounded-xl',
  lg: 'p-8 rounded-2xl',
  xl: 'p-12 rounded-3xl'
};

export function HolographicPanel({ 
  children, 
  className, 
  variant = 'glass',
  size = 'md',
  animated = false,
  glowBorder = false,
  ...props 
}: HolographicPanelProps & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'relative transition-all duration-300 ease-out',
        'hover:translate-y-[-2px]',
        variantStyles[variant],
        sizeStyles[size],
        animated && 'animate-pulse',
        glowBorder && 'hover:shadow-[0_0_25px_rgba(0,226,255,0.4)]',
        className
      )}
      {...props}
    >
      {/* Голографические блики */}
      <div className="absolute inset-0 rounded-inherit opacity-30 pointer-events-none">
        <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-white/60 to-transparent" />
        <div className="absolute top-0 left-0 w-[2px] h-full bg-gradient-to-b from-transparent via-white/60 to-transparent" />
      </div>
      
      {/* Анимированные частицы света */}
      {animated && (
        <div className="absolute inset-0 rounded-inherit overflow-hidden pointer-events-none">
          <div className="absolute w-2 h-2 bg-mirai-primary rounded-full opacity-70 animate-ping 
                          top-1/4 left-1/4" style={{ animationDelay: '0s' }} />
          <div className="absolute w-1 h-1 bg-mirai-accent rounded-full opacity-60 animate-ping 
                          top-3/4 right-1/4" style={{ animationDelay: '1s' }} />
          <div className="absolute w-1.5 h-1.5 bg-mirai-secondary rounded-full opacity-50 animate-ping 
                          bottom-1/4 left-3/4" style={{ animationDelay: '2s' }} />
        </div>
      )}
      
      {/* Содержимое */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}

// Специализированные панели
export function GlassPanel({ className, ...props }: Omit<HolographicPanelProps, 'variant'>) {
  return <HolographicPanel variant="glass" className={className} {...props} />;
}

export function NeonPanel({ className, ...props }: Omit<HolographicPanelProps, 'variant'>) {
  return <HolographicPanel variant="neon" className={className} {...props} />;
}

export function CyberPanel({ className, ...props }: Omit<HolographicPanelProps, 'variant'>) {
  return <HolographicPanel variant="cyber" className={className} {...props} />;
}

// Панель со статистикой
interface StatPanelProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

export function StatPanel({ title, value, subtitle, icon, trend, className }: StatPanelProps) {
  const trendColors = {
    up: 'text-mirai-success',
    down: 'text-mirai-error',
    neutral: 'text-white'
  };

  const trendIcons = {
    up: '↗',
    down: '↘',
    neutral: '→'
  };

  return (
    <HolographicPanel 
      variant="glass" 
      size="md"
      className={cn('hover:border-mirai-primary/50 transition-colors', className)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 text-sm text-gray-300 mb-1">
            {icon}
            <span>{title}</span>
          </div>
          <div className={cn('text-2xl font-bold', trendColors[trend || 'neutral'])}>
            {value}
          </div>
          {subtitle && (
            <div className="text-xs text-gray-400 mt-1 flex items-center gap-1">
              {trend && <span>{trendIcons[trend]}</span>}
              {subtitle}
            </div>
          )}
        </div>
      </div>
    </HolographicPanel>
  );
}

// Панель с прогресс-баром в стиле аниме
interface ProgressPanelProps {
  title: string;
  current: number;
  max: number;
  type?: 'hp' | 'mp' | 'xp' | 'shield';
  className?: string;
}

export function ProgressPanel({ title, current, max, type = 'hp', className }: ProgressPanelProps) {
  const percentage = Math.min((current / max) * 100, 100);
  
  const typeStyles = {
    hp: 'bg-gradient-to-r from-red-500 to-red-400',
    mp: 'bg-gradient-to-r from-blue-500 to-cyan-400',
    xp: 'bg-gradient-to-r from-yellow-500 to-orange-400',
    shield: 'bg-gradient-to-r from-purple-500 to-indigo-400'
  };

  const typeIcons = {
    hp: '❤️',
    mp: '💙',
    xp: '⭐',
    shield: '🛡️'
  };

  return (
    <HolographicPanel variant="glass" size="sm" className={className}>
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2">
            <span>{typeIcons[type]}</span>
            {title}
          </span>
          <span className="font-mono">{current}/{max}</span>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full h-3 bg-black/30 rounded-full overflow-hidden">
          <div 
            className={cn(
              'h-full transition-all duration-500 ease-out rounded-full',
              typeStyles[type],
              percentage < 25 && type === 'hp' && 'animate-pulse'
            )}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    </HolographicPanel>
  );
}

// Панель с эффектом сканирования
export function ScanPanel({ children, className, ...props }: HolographicPanelProps) {
  return (
    <HolographicPanel 
      variant="cyber" 
      className={cn('relative overflow-hidden', className)}
      {...props}
    >
      {/* Эффект сканирования */}
      <div className="absolute inset-0 opacity-20 pointer-events-none">
        <div className="absolute w-full h-[2px] bg-gradient-to-r from-transparent via-mirai-primary to-transparent
                        animate-pulse" 
             style={{ 
               animation: 'scan-line 3s linear infinite',
               top: '0%'
             }} />
      </div>
      
      {children}
      
      <style jsx>{`
        @keyframes scan-line {
          0% { top: 0%; opacity: 0; }
          5% { opacity: 1; }
          95% { opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
      `}</style>
    </HolographicPanel>
  );
}