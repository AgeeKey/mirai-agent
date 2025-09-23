'use client';

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';

export type MiraiEmotion = 
  | 'neutral'      // 😐 Спокойное состояние
  | 'happy'        // 😊 Прибыль, успех
  | 'excited'      // 🤩 Большая прибыль
  | 'worried'      // 😰 Убыток, риск
  | 'thinking'     // 🤔 Анализ рынка
  | 'focused'      // ⚡ Активная торговля
  | 'sleeping'     // 💤 Ожидание/рынок закрыт
  | 'disappointed' // 😞 Большой убыток
  | 'confident';   // 😎 Уверенность в стратегии

export interface TradingStatus {
  isTrading: boolean;
  pnl: number;
  winRate: number;
  activePositions: number;
  marketStatus: 'open' | 'closed' | 'volatile';
  lastUpdate: Date;
}

interface MiraiAvatarProps {
  emotion?: MiraiEmotion;
  tradingStatus?: TradingStatus;
  message?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  interactive?: boolean;
  autoEmotions?: boolean;
  className?: string;
  onAvatarClick?: () => void;
}

// SVG иконки для эмоций (упрощенные версии)
const EmotionFaces = {
  neutral: (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      {/* Лицо */}
      <circle cx="50" cy="50" r="45" fill="url(#faceGradient)" stroke="currentColor" strokeWidth="2"/>
      {/* Глаза */}
      <circle cx="35" cy="40" r="6" fill="currentColor"/>
      <circle cx="65" cy="40" r="6" fill="currentColor"/>
      {/* Рот */}
      <path d="M 40 65 Q 50 70 60 65" stroke="currentColor" strokeWidth="2" fill="none"/>
    </svg>
  ),
  happy: (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      <circle cx="50" cy="50" r="45" fill="url(#faceGradient)" stroke="currentColor" strokeWidth="2"/>
      {/* Улыбающиеся глаза */}
      <path d="M 30 35 Q 35 30 40 35" stroke="currentColor" strokeWidth="2" fill="none"/>
      <path d="M 60 35 Q 65 30 70 35" stroke="currentColor" strokeWidth="2" fill="none"/>
      {/* Улыбка */}
      <path d="M 35 60 Q 50 75 65 60" stroke="currentColor" strokeWidth="3" fill="none"/>
    </svg>
  ),
  excited: (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      <circle cx="50" cy="50" r="45" fill="url(#faceGradient)" stroke="currentColor" strokeWidth="2"/>
      {/* Звезды в глазах */}
      <text x="35" y="45" fontSize="12" textAnchor="middle" fill="currentColor">✨</text>
      <text x="65" y="45" fontSize="12" textAnchor="middle" fill="currentColor">✨</text>
      {/* Большая улыбка */}
      <path d="M 30 58 Q 50 80 70 58" stroke="currentColor" strokeWidth="3" fill="none"/>
    </svg>
  ),
  worried: (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      <circle cx="50" cy="50" r="45" fill="url(#faceGradient)" stroke="currentColor" strokeWidth="2"/>
      {/* Обеспокоенные брови */}
      <path d="M 28 30 L 42 35" stroke="currentColor" strokeWidth="2"/>
      <path d="M 72 30 L 58 35" stroke="currentColor" strokeWidth="2"/>
      {/* Большие глаза */}
      <circle cx="35" cy="42" r="8" fill="currentColor"/>
      <circle cx="65" cy="42" r="8" fill="currentColor"/>
      {/* Грустный рот */}
      <path d="M 35 70 Q 50 60 65 70" stroke="currentColor" strokeWidth="2" fill="none"/>
    </svg>
  ),
  thinking: (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      <circle cx="50" cy="50" r="45" fill="url(#faceGradient)" stroke="currentColor" strokeWidth="2"/>
      {/* Глаза смотрят вверх */}
      <circle cx="35" cy="38" r="6" fill="currentColor"/>
      <circle cx="65" cy="38" r="6" fill="currentColor"/>
      {/* Задумчивый рот */}
      <path d="M 45 65 Q 50 68 55 65" stroke="currentColor" strokeWidth="2" fill="none"/>
      {/* Думающие символы */}
      <text x="75" y="25" fontSize="8" fill="currentColor">?</text>
      <text x="80" y="15" fontSize="6" fill="currentColor">...</text>
    </svg>
  ),
  focused: (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      <circle cx="50" cy="50" r="45" fill="url(#faceGradient)" stroke="currentColor" strokeWidth="2"/>
      {/* Сфокусированные глаза */}
      <rect x="30" y="37" width="10" height="6" fill="currentColor"/>
      <rect x="60" y="37" width="10" height="6" fill="currentColor"/>
      {/* Прямая линия рта */}
      <path d="M 40 65 L 60 65" stroke="currentColor" strokeWidth="2"/>
    </svg>
  ),
  sleeping: (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      <circle cx="50" cy="50" r="45" fill="url(#faceGradient)" stroke="currentColor" strokeWidth="2"/>
      {/* Закрытые глаза */}
      <path d="M 30 40 Q 35 35 40 40" stroke="currentColor" strokeWidth="2" fill="none"/>
      <path d="M 60 40 Q 65 35 70 40" stroke="currentColor" strokeWidth="2" fill="none"/>
      {/* Спящий рот */}
      <circle cx="50" cy="65" r="3" fill="none" stroke="currentColor" strokeWidth="1"/>
      {/* ZZZ */}
      <text x="75" y="25" fontSize="8" fill="currentColor">Z</text>
      <text x="80" y="18" fontSize="6" fill="currentColor">z</text>
      <text x="83" y="12" fontSize="4" fill="currentColor">z</text>
    </svg>
  ),
  disappointed: (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      <circle cx="50" cy="50" r="45" fill="url(#faceGradient)" stroke="currentColor" strokeWidth="2"/>
      {/* Грустные брови */}
      <path d="M 30 32 L 40 38" stroke="currentColor" strokeWidth="2"/>
      <path d="M 70 32 L 60 38" stroke="currentColor" strokeWidth="2"/>
      {/* Грустные глаза */}
      <circle cx="35" cy="42" r="5" fill="currentColor"/>
      <circle cx="65" cy="42" r="5" fill="currentColor"/>
      {/* Очень грустный рот */}
      <path d="M 30 75 Q 50 55 70 75" stroke="currentColor" strokeWidth="2" fill="none"/>
    </svg>
  ),
  confident: (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      <circle cx="50" cy="50" r="45" fill="url(#faceGradient)" stroke="currentColor" strokeWidth="2"/>
      {/* Уверенные глаза */}
      <path d="M 28 38 L 42 40" stroke="currentColor" strokeWidth="2"/>
      <circle cx="35" cy="42" r="5" fill="currentColor"/>
      <path d="M 72 38 L 58 40" stroke="currentColor" strokeWidth="2"/>
      <circle cx="65" cy="42" r="5" fill="currentColor"/>
      {/* Самодовольная улыбка */}
      <path d="M 38 62 Q 50 70 62 62" stroke="currentColor" strokeWidth="2" fill="none"/>
    </svg>
  )
};

const sizeClasses = {
  sm: 'w-16 h-16',
  md: 'w-24 h-24',
  lg: 'w-32 h-32',
  xl: 'w-48 h-48'
};

export function MiraiAvatar({
  emotion = 'neutral',
  tradingStatus,
  message,
  size = 'md',
  interactive = true,
  autoEmotions = true,
  className,
  onAvatarClick,
  ...props
}: MiraiAvatarProps) {
  const [currentEmotion, setCurrentEmotion] = useState<MiraiEmotion>(emotion);
  const [isAnimating, setIsAnimating] = useState(false);
  const [showMessage, setShowMessage] = useState(false);

  // Автоматическое определение эмоций на основе торгового статуса
  useEffect(() => {
    if (!autoEmotions || !tradingStatus) return;

    let newEmotion: MiraiEmotion = 'neutral';

    if (tradingStatus.marketStatus === 'closed') {
      newEmotion = 'sleeping';
    } else if (tradingStatus.isTrading) {
      if (tradingStatus.pnl > 100) {
        newEmotion = 'excited';
      } else if (tradingStatus.pnl > 0) {
        newEmotion = 'happy';
      } else if (tradingStatus.pnl < -100) {
        newEmotion = 'disappointed';
      } else if (tradingStatus.pnl < 0) {
        newEmotion = 'worried';
      } else if (tradingStatus.activePositions > 0) {
        newEmotion = 'focused';
      } else {
        newEmotion = 'thinking';
      }
    } else {
      if (tradingStatus.winRate > 70) {
        newEmotion = 'confident';
      } else {
        newEmotion = 'neutral';
      }
    }

    if (newEmotion !== currentEmotion) {
      setIsAnimating(true);
      setTimeout(() => {
        setCurrentEmotion(newEmotion);
        setIsAnimating(false);
      }, 150);
    }
  }, [tradingStatus, autoEmotions, currentEmotion]);

  // Показ сообщения
  useEffect(() => {
    if (message) {
      setShowMessage(true);
      const timer = setTimeout(() => setShowMessage(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  // Определение цвета на основе эмоции
  const getEmotionColor = (emotion: MiraiEmotion) => {
    switch (emotion) {
      case 'happy':
      case 'excited':
        return 'text-mirai-success';
      case 'worried':
      case 'disappointed':
        return 'text-mirai-error';
      case 'focused':
        return 'text-mirai-primary';
      case 'confident':
        return 'text-mirai-accent';
      case 'thinking':
        return 'text-mirai-secondary';
      default:
        return 'text-white';
    }
  };

  const handleAvatarClick = () => {
    if (!interactive) return;
    
    setIsAnimating(true);
    setTimeout(() => setIsAnimating(false), 300);
    
    if (onAvatarClick) {
      onAvatarClick();
    }
  };

  return (
    <div className={cn('relative flex flex-col items-center', className)} {...props}>
      {/* Аватар */}
      <div 
        className={cn(
          'relative',
          sizeClasses[size],
          'transition-all duration-300 ease-out',
          interactive && 'cursor-pointer hover:scale-110',
          isAnimating && 'scale-90',
          getEmotionColor(currentEmotion)
        )}
        onClick={handleAvatarClick}
      >
        {/* Голографический контур */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-mirai-primary via-mirai-secondary to-mirai-accent opacity-50 blur-md animate-pulse" />
        
        {/* Основной аватар */}
        <div className="relative z-10 w-full h-full rounded-full bg-mirai-dark/80 backdrop-blur-sm border border-current shadow-lg overflow-hidden">
          {/* Градиенты для SVG */}
          <svg width="0" height="0">
            <defs>
              <linearGradient id="faceGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="rgba(160, 118, 249, 0.3)" />
                <stop offset="100%" stopColor="rgba(0, 226, 255, 0.3)" />
              </linearGradient>
            </defs>
          </svg>
          
          {/* Лицо */}
          <div className="w-full h-full flex items-center justify-center p-2">
            {EmotionFaces[currentEmotion]}
          </div>
          
          {/* Индикатор торгового статуса */}
          {tradingStatus && (
            <div className="absolute bottom-1 right-1 w-3 h-3 rounded-full">
              {tradingStatus.isTrading ? (
                <div className="w-full h-full bg-mirai-success rounded-full animate-pulse shadow-neon-primary" />
              ) : (
                <div className="w-full h-full bg-gray-400 rounded-full" />
              )}
            </div>
          )}
          
          {/* Частицы вокруг при активности */}
          {tradingStatus?.isTrading && (
            <div className="absolute inset-0 pointer-events-none">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="absolute w-1 h-1 bg-mirai-primary rounded-full animate-ping"
                  style={{
                    top: `${20 + Math.random() * 60}%`,
                    left: `${20 + Math.random() * 60}%`,
                    animationDelay: `${i * 0.5}s`,
                    animationDuration: `${1 + Math.random()}s`
                  }}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Сообщение в пузыре */}
      {showMessage && message && (
        <div className="absolute -top-16 left-1/2 transform -translate-x-1/2 z-20">
          <div className="relative bg-mirai-panel/90 backdrop-blur-sm border border-mirai-primary/50 rounded-xl px-4 py-2 text-sm text-white shadow-lg max-w-xs">
            {message}
            {/* Стрелка */}
            <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-mirai-panel border-r border-b border-mirai-primary/50 rotate-45" />
          </div>
        </div>
      )}

      {/* Информация о торговом статусе */}
      {tradingStatus && size !== 'sm' && (
        <div className="mt-2 text-center text-xs text-gray-300 space-y-1">
          <div className="flex items-center gap-2 justify-center">
            <span className={cn(
              'w-2 h-2 rounded-full',
              tradingStatus.isTrading ? 'bg-mirai-success animate-pulse' : 'bg-gray-400'
            )} />
            <span>{tradingStatus.isTrading ? 'Trading' : 'Idle'}</span>
          </div>
          
          {tradingStatus.pnl !== 0 && (
            <div className={cn(
              'font-mono text-xs',
              tradingStatus.pnl > 0 ? 'text-mirai-success' : 'text-mirai-error'
            )}>
              {tradingStatus.pnl > 0 ? '+' : ''}${tradingStatus.pnl.toFixed(2)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Готовые варианты аватаров
export function HappyMirai(props: Omit<MiraiAvatarProps, 'emotion'>) {
  return <MiraiAvatar emotion="happy" {...props} />;
}

export function TradingMirai(props: Omit<MiraiAvatarProps, 'emotion'>) {
  return <MiraiAvatar emotion="focused" {...props} />;
}

export function ThinkingMirai(props: Omit<MiraiAvatarProps, 'emotion'>) {
  return <MiraiAvatar emotion="thinking" {...props} />;
}

// Интерактивный компонент с чатом
interface MiraiChatProps {
  tradingStatus?: TradingStatus;
  onSendMessage?: (message: string) => void;
  className?: string;
}

export function MiraiChat({ tradingStatus, onSendMessage, className }: MiraiChatProps) {
  const [currentMessage, setCurrentMessage] = useState<string>('');
  const [messages] = useState<string[]>([
    "Sempai, добро пожаловать! Готова к новым торгам! (◕‿◕)",
    "Анализирую рынок... 🤔",
    "Sugoi! Хорошие возможности для входа! ✨"
  ]);

  useEffect(() => {
    // Автоматические сообщения на основе статуса
    if (tradingStatus) {
      let newMessage = '';
      
      if (tradingStatus.pnl > 50) {
        newMessage = "Yatta! Прибыль растет! (｡◕‿◕｡)";
      } else if (tradingStatus.pnl < -30) {
        newMessage = "Gomen... Стоп-лосс сработал (╥﹏╥)";
      } else if (tradingStatus.isTrading) {
        newMessage = "Отслеживаю позицию... ⚡";
      }
      
      if (newMessage && newMessage !== currentMessage) {
        setCurrentMessage(newMessage);
      }
    }
  }, [tradingStatus, currentMessage]);

  return (
    <div className={cn('flex flex-col items-center space-y-4', className)}>
      <MiraiAvatar 
        tradingStatus={tradingStatus}
        message={currentMessage}
        size="lg"
        autoEmotions={true}
      />
      
      {/* Быстрые сообщения */}
      <div className="flex flex-wrap gap-2 justify-center max-w-md">
        {messages.map((msg, index) => (
          <button
            key={index}
            onClick={() => setCurrentMessage(msg)}
            className="px-3 py-1 text-xs bg-mirai-panel/50 hover:bg-mirai-panel border border-mirai-primary/30 rounded-full transition-colors"
          >
            {msg.slice(0, 20)}...
          </button>
        ))}
      </div>
    </div>
  );
}