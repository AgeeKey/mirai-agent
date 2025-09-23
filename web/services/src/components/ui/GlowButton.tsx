'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface GlowButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'success' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  glowIntensity?: 'low' | 'medium' | 'high';
  children: React.ReactNode;
}

const variantStyles = {
  primary: 'bg-gradient-to-r from-mirai-primary to-mirai-secondary hover:shadow-neon-primary',
  secondary: 'bg-gradient-to-r from-mirai-secondary to-mirai-accent hover:shadow-neon-secondary',
  accent: 'bg-gradient-to-r from-mirai-accent to-mirai-primary hover:shadow-neon-accent',
  success: 'bg-gradient-to-r from-mirai-success to-mirai-primary hover:shadow-[0_0_20px_rgba(54,234,190,0.5)]',
  danger: 'bg-gradient-to-r from-mirai-error to-mirai-accent hover:shadow-[0_0_20px_rgba(255,58,118,0.5)]'
};

const sizeStyles = {
  sm: 'px-4 py-2 text-sm',
  md: 'px-6 py-3 text-base',
  lg: 'px-8 py-4 text-lg'
};

const glowStyles = {
  low: 'hover:shadow-[0_0_10px_currentColor]',
  medium: 'hover:shadow-[0_0_20px_currentColor]',
  high: 'hover:shadow-[0_0_30px_currentColor]'
};

export function GlowButton({ 
  variant = 'primary', 
  size = 'md',
  glowIntensity = 'medium',
  className,
  children,
  disabled,
  ...props 
}: GlowButtonProps) {
  return (
    <button
      className={cn(
        // Базовые стили
        'relative inline-flex items-center justify-center gap-2 rounded-xl font-semibold',
        'transition-all duration-300 ease-out transform',
        'border-0 cursor-pointer overflow-hidden',
        'active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed',
        
        // Hover эффекты
        'hover:-translate-y-1 hover:scale-105',
        
        // Варианты цветов
        variantStyles[variant],
        
        // Размеры
        sizeStyles[size],
        
        // Свечение
        glowStyles[glowIntensity],
        
        // Отключенное состояние
        disabled && 'opacity-50 cursor-not-allowed hover:transform-none hover:shadow-none',
        
        className
      )}
      disabled={disabled}
      {...props}
    >
      {/* Анимированная полоса света */}
      <div className="absolute inset-0 opacity-0 hover:opacity-100 transition-opacity duration-500">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent 
                        -translate-x-full hover:translate-x-full transition-transform duration-700 ease-out" />
      </div>
      
      {/* Содержимое кнопки */}
      <span className="relative z-10 flex items-center gap-2">
        {children}
      </span>
      
      {/* Внутреннее свечение */}
      <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-white/10 to-white/5 
                      opacity-0 hover:opacity-100 transition-opacity duration-300" />
    </button>
  );
}

// Специализированные кнопки
export function MiraiPrimaryButton(props: Omit<GlowButtonProps, 'variant'>) {
  return <GlowButton variant="primary" {...props} />;
}

export function MiraiSecondaryButton(props: Omit<GlowButtonProps, 'variant'>) {
  return <GlowButton variant="secondary" {...props} />;
}

export function MiraiDangerButton(props: Omit<GlowButtonProps, 'variant'>) {
  return <GlowButton variant="danger" {...props} />;
}

// Кнопка с пульсирующим эффектом для критических действий
export function PulseButton({ className, ...props }: GlowButtonProps) {
  return (
    <GlowButton 
      className={cn(
        'animate-pulse hover:animate-none',
        'shadow-[0_0_20px_rgba(255,58,118,0.7)]',
        className
      )}
      variant="danger"
      {...props} 
    />
  );
}

// Кнопка в стиле киберпанк
export function CyberButton({ className, children, ...props }: GlowButtonProps) {
  return (
    <button
      className={cn(
        'relative px-6 py-3 font-mono font-bold text-white bg-transparent',
        'border-2 border-mirai-primary rounded-none',
        'transition-all duration-300 ease-out',
        'hover:bg-mirai-primary hover:text-mirai-dark',
        'hover:shadow-[0_0_20px_rgba(0,226,255,0.5)]',
        'active:scale-95',
        'before:content-[""] before:absolute before:inset-0',
        'before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent',
        'before:-translate-x-full before:transition-transform before:duration-700',
        'hover:before:translate-x-full',
        className
      )}
      {...props}
    >
      <span className="relative z-10">{children}</span>
    </button>
  );
}