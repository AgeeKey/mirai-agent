'use client';

import React, { useState, useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { 
  Bell, X, CheckCircle, AlertTriangle, Info, TrendingUp, 
  TrendingDown, Shield, Zap, Star, DollarSign, Activity 
} from 'lucide-react';

export type NotificationType = 
  | 'success' | 'warning' | 'error' | 'info' 
  | 'trade' | 'profit' | 'loss' | 'system';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actions?: Array<{
    label: string;
    action: () => void;
    variant?: 'primary' | 'secondary' | 'danger';
  }>;
  data?: any; // Additional data for trade notifications
}

interface NotificationSystemProps {
  className?: string;
}

interface ToastProps {
  notification: Notification;
  onDismiss: (id: string) => void;
  onAction: (id: string, actionIndex: number) => void;
}

const notificationConfig = {
  success: {
    icon: CheckCircle,
    color: 'text-mirai-success',
    bg: 'bg-mirai-success/10',
    border: 'border-mirai-success/30',
    glow: 'shadow-[0_0_20px_rgba(34,197,94,0.2)]'
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-mirai-warning',
    bg: 'bg-mirai-warning/10',
    border: 'border-mirai-warning/30',
    glow: 'shadow-[0_0_20px_rgba(251,191,36,0.2)]'
  },
  error: {
    icon: AlertTriangle,
    color: 'text-mirai-error',
    bg: 'bg-mirai-error/10',
    border: 'border-mirai-error/30',
    glow: 'shadow-[0_0_20px_rgba(239,68,68,0.2)]'
  },
  info: {
    icon: Info,
    color: 'text-mirai-primary',
    bg: 'bg-mirai-primary/10',
    border: 'border-mirai-primary/30',
    glow: 'shadow-neon-primary'
  },
  trade: {
    icon: Activity,
    color: 'text-mirai-secondary',
    bg: 'bg-mirai-secondary/10',
    border: 'border-mirai-secondary/30',
    glow: 'shadow-neon-secondary'
  },
  profit: {
    icon: TrendingUp,
    color: 'text-mirai-success',
    bg: 'bg-gradient-to-r from-mirai-success/10 to-green-500/10',
    border: 'border-mirai-success/30',
    glow: 'shadow-[0_0_30px_rgba(34,197,94,0.3)] animate-pulse'
  },
  loss: {
    icon: TrendingDown,
    color: 'text-mirai-error',
    bg: 'bg-gradient-to-r from-mirai-error/10 to-red-500/10',
    border: 'border-mirai-error/30',
    glow: 'shadow-[0_0_30px_rgba(239,68,68,0.3)]'
  },
  system: {
    icon: Shield,
    color: 'text-mirai-accent',
    bg: 'bg-mirai-accent/10',
    border: 'border-mirai-accent/30',
    glow: 'shadow-neon-accent'
  }
};

function Toast({ notification, onDismiss, onAction }: ToastProps) {
  const [isVisible, setIsVisible] = useState(false);
  const config = notificationConfig[notification.type];
  const IconComponent = config.icon;

  useEffect(() => {
    setIsVisible(true);
    
    // Auto-dismiss after 5 seconds for non-critical notifications
    if (!['error', 'profit', 'loss'].includes(notification.type)) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, []);

  const handleDismiss = () => {
    setIsVisible(false);
    setTimeout(() => onDismiss(notification.id), 300);
  };

  const getSpecialEffects = () => {
    switch (notification.type) {
      case 'profit':
        return (
          <>
            {/* Sparkle effects for profit */}
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="absolute w-1 h-1 bg-mirai-success rounded-full animate-ping"
                style={{
                  top: `${20 + Math.random() * 60}%`,
                  left: `${20 + Math.random() * 60}%`,
                  animationDelay: `${i * 0.2}s`,
                  animationDuration: '1s'
                }}
              />
            ))}
          </>
        );
      case 'loss':
        return (
          <div className="absolute inset-0 bg-mirai-error/5 animate-pulse rounded-lg" />
        );
      case 'trade':
        return (
          <div className="absolute left-0 top-0 w-1 h-full bg-gradient-to-b from-mirai-secondary to-mirai-primary animate-pulse rounded-l-lg" />
        );
      default:
        return null;
    }
  };

  return (
    <div
      className={cn(
        'relative w-80 p-4 rounded-lg border backdrop-blur-sm transition-all duration-300 overflow-hidden',
        config.bg,
        config.border,
        config.glow,
        isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
      )}
    >
      {getSpecialEffects()}
      
      <div className="relative z-10">
        <div className="flex items-start gap-3">
          <div className={cn('flex-shrink-0 mt-0.5', config.color)}>
            <IconComponent className="w-5 h-5" />
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-sm font-semibold text-white truncate">
                {notification.title}
              </h3>
              
              {/* Special badges for trade notifications */}
              {notification.type === 'profit' && (
                <div className="flex items-center gap-1 px-2 py-0.5 bg-mirai-success/20 rounded text-xs text-mirai-success">
                  <Star className="w-3 h-3" />
                  WIN
                </div>
              )}
              {notification.type === 'loss' && (
                <div className="flex items-center gap-1 px-2 py-0.5 bg-mirai-error/20 rounded text-xs text-mirai-error">
                  <TrendingDown className="w-3 h-3" />
                  LOSS
                </div>
              )}
            </div>
            
            <p className="text-sm text-gray-300 leading-relaxed">
              {notification.message}
            </p>
            
            {/* Trade-specific data */}
            {notification.data && (notification.type === 'profit' || notification.type === 'loss' || notification.type === 'trade') && (
              <div className="mt-2 p-2 bg-black/20 rounded text-xs space-y-1">
                {notification.data.symbol && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Symbol:</span>
                    <span className="text-white font-mono">{notification.data.symbol}</span>
                  </div>
                )}
                {notification.data.amount && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Amount:</span>
                    <span className="text-white font-mono">{notification.data.amount}</span>
                  </div>
                )}
                {notification.data.pnl !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">P&L:</span>
                    <span className={cn(
                      'font-mono font-semibold',
                      notification.data.pnl >= 0 ? 'text-mirai-success' : 'text-mirai-error'
                    )}>
                      {notification.data.pnl >= 0 ? '+' : ''}${notification.data.pnl.toFixed(2)}
                    </span>
                  </div>
                )}
              </div>
            )}
            
            {/* Actions */}
            {notification.actions && notification.actions.length > 0 && (
              <div className="flex gap-2 mt-3">
                {notification.actions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => onAction(notification.id, index)}
                    className={cn(
                      'px-3 py-1 text-xs rounded transition-colors',
                      action.variant === 'danger'
                        ? 'bg-mirai-error/20 text-mirai-error hover:bg-mirai-error/30'
                        : action.variant === 'secondary'
                        ? 'bg-gray-600/20 text-gray-300 hover:bg-gray-600/30'
                        : 'bg-mirai-primary/20 text-mirai-primary hover:bg-mirai-primary/30'
                    )}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}
            
            <div className="flex items-center justify-between mt-2">
              <span className="text-xs text-gray-500">
                {notification.timestamp.toLocaleTimeString()}
              </span>
            </div>
          </div>
          
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

export function NotificationSystem({ className, ...props }: NotificationSystemProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Create audio context for notification sounds
    if (typeof window !== 'undefined') {
      audioRef.current = new Audio();
    }
  }, []);

  const playNotificationSound = (type: NotificationType) => {
    if (!audioRef.current) return;
    
    // Different tones for different notification types
    const frequencies = {
      success: 800,
      profit: 1000,
      warning: 600,
      error: 400,
      loss: 300,
      trade: 750,
      info: 650,
      system: 550
    };
    
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(frequencies[type], audioContext.currentTime);
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.3);
    } catch (e) {
      // Fallback for browsers that don't support Web Audio API
      console.log('Notification sound not supported');
    }
  };

  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date(),
      read: false
    };
    
    setNotifications(prev => [newNotification, ...prev.slice(0, 49)]); // Keep max 50 notifications
    setUnreadCount(prev => prev + 1);
    
    // Play sound
    playNotificationSound(notification.type);
    
    return newNotification.id;
  };

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);
  };

  const handleAction = (notificationId: string, actionIndex: number) => {
    const notification = notifications.find(n => n.id === notificationId);
    if (notification?.actions?.[actionIndex]) {
      notification.actions[actionIndex].action();
      markAsRead(notificationId);
    }
  };

  const clearAll = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  // Get recent notifications for toast display
  const recentNotifications = notifications.slice(0, 3);
  const toastNotifications = recentNotifications.filter(n => !n.read);

  // Expose functions globally for use by other components
  useEffect(() => {
    (window as any).miraiNotifications = {
      success: (title: string, message: string, actions?: any) => 
        addNotification({ type: 'success', title, message, actions }),
      warning: (title: string, message: string, actions?: any) => 
        addNotification({ type: 'warning', title, message, actions }),
      error: (title: string, message: string, actions?: any) => 
        addNotification({ type: 'error', title, message, actions }),
      info: (title: string, message: string, actions?: any) => 
        addNotification({ type: 'info', title, message, actions }),
      trade: (title: string, message: string, data?: any, actions?: any) => 
        addNotification({ type: 'trade', title, message, data, actions }),
      profit: (title: string, message: string, data: any, actions?: any) => 
        addNotification({ type: 'profit', title, message, data, actions }),
      loss: (title: string, message: string, data: any, actions?: any) => 
        addNotification({ type: 'loss', title, message, data, actions }),
      system: (title: string, message: string, actions?: any) => 
        addNotification({ type: 'system', title, message, actions })
    };
  }, []);

  return (
    <>
      {/* Notification Bell Button */}
      <div className={cn('relative', className)} {...props}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            'relative p-2 rounded-lg transition-all duration-300',
            'bg-mirai-panel/30 hover:bg-mirai-panel/50',
            'border border-mirai-primary/20 hover:border-mirai-primary/40',
            'text-mirai-primary hover:text-white',
            unreadCount > 0 && 'animate-pulse'
          )}
        >
          <Bell className="w-5 h-5" />
          
          {unreadCount > 0 && (
            <div className="absolute -top-1 -right-1 w-5 h-5 bg-mirai-error rounded-full flex items-center justify-center text-xs font-bold text-white animate-pulse">
              {unreadCount > 99 ? '99+' : unreadCount}
            </div>
          )}
        </button>

        {/* Notification Panel */}
        {isOpen && (
          <div className="absolute right-0 top-full mt-2 w-80 max-h-96 bg-mirai-panel/90 backdrop-blur-md rounded-lg border border-mirai-primary/20 shadow-neon-primary overflow-hidden z-50">
            
            {/* Header */}
            <div className="p-4 border-b border-mirai-primary/20">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Notifications</h3>
                <div className="flex gap-2">
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllAsRead}
                      className="text-xs text-mirai-primary hover:text-white transition-colors"
                    >
                      Mark all read
                    </button>
                  )}
                  <button
                    onClick={clearAll}
                    className="text-xs text-gray-400 hover:text-white transition-colors"
                  >
                    Clear all
                  </button>
                </div>
              </div>
            </div>

            {/* Notification List */}
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-gray-400">
                  <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No notifications</p>
                </div>
              ) : (
                <div className="space-y-1">
                  {notifications.map((notification) => {
                    const config = notificationConfig[notification.type];
                    const IconComponent = config.icon;
                    
                    return (
                      <div
                        key={notification.id}
                        className={cn(
                          'p-3 border-l-2 cursor-pointer transition-colors',
                          config.border,
                          notification.read 
                            ? 'bg-transparent hover:bg-mirai-panel/20' 
                            : 'bg-mirai-primary/5 hover:bg-mirai-primary/10'
                        )}
                        onClick={() => markAsRead(notification.id)}
                      >
                        <div className="flex items-start gap-3">
                          <div className={cn('flex-shrink-0 mt-0.5', config.color)}>
                            <IconComponent className="w-4 h-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="text-sm font-medium text-white truncate">
                                {notification.title}
                              </h4>
                              {!notification.read && (
                                <div className="w-2 h-2 bg-mirai-primary rounded-full flex-shrink-0" />
                              )}
                            </div>
                            <p className="text-xs text-gray-300 line-clamp-2">
                              {notification.message}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                              {notification.timestamp.toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Toast Notifications */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toastNotifications.map((notification) => (
          <Toast
            key={notification.id}
            notification={notification}
            onDismiss={dismissNotification}
            onAction={handleAction}
          />
        ))}
      </div>
    </>
  );
}

// Utility functions for easy notification creation
export const notify = {
  success: (title: string, message: string, actions?: any) => {
    if ((window as any).miraiNotifications) {
      (window as any).miraiNotifications.success(title, message, actions);
    }
  },
  warning: (title: string, message: string, actions?: any) => {
    if ((window as any).miraiNotifications) {
      (window as any).miraiNotifications.warning(title, message, actions);
    }
  },
  error: (title: string, message: string, actions?: any) => {
    if ((window as any).miraiNotifications) {
      (window as any).miraiNotifications.error(title, message, actions);
    }
  },
  info: (title: string, message: string, actions?: any) => {
    if ((window as any).miraiNotifications) {
      (window as any).miraiNotifications.info(title, message, actions);
    }
  },
  trade: (title: string, message: string, data?: any, actions?: any) => {
    if ((window as any).miraiNotifications) {
      (window as any).miraiNotifications.trade(title, message, data, actions);
    }
  },
  profit: (title: string, message: string, data: any, actions?: any) => {
    if ((window as any).miraiNotifications) {
      (window as any).miraiNotifications.profit(title, message, data, actions);
    }
  },
  loss: (title: string, message: string, data: any, actions?: any) => {
    if ((window as any).miraiNotifications) {
      (window as any).miraiNotifications.loss(title, message, data, actions);
    }
  },
  system: (title: string, message: string, actions?: any) => {
    if ((window as any).miraiNotifications) {
      (window as any).miraiNotifications.system(title, message, actions);
    }
  }
};

// Demo notifications for testing
export const createDemoNotifications = () => {
  setTimeout(() => notify.profit('Trade Executed! 🎯', 'BTC long position closed successfully', {
    symbol: 'BTCUSDT',
    amount: '0.1 BTC',
    pnl: 245.67
  }), 1000);
  
  setTimeout(() => notify.trade('New Signal Detected', 'RSI divergence found on ETH 1H chart', {
    symbol: 'ETHUSDT',
    signal: 'Bullish',
    confidence: '85%'
  }), 3000);
  
  setTimeout(() => notify.warning('Risk Alert', 'Portfolio exposure above 80% threshold'), 5000);
  
  setTimeout(() => notify.system('Shield Upgraded! ⚡', 'Risk protection level increased to Elite'), 7000);
};