'use client';

import { useState, useEffect } from 'react';
import { Settings, Bot, User, Activity, Shield, Star, Zap, Mic, ChartColumn, Brain } from 'lucide-react';

interface DomainSwitcherProps {
  currentDomain: 'mirai-agent' | 'mirai-chan';
  onDomainChange: (domain: 'mirai-agent' | 'mirai-chan') => void;
}

export default function DomainSwitcher({ currentDomain, onDomainChange }: DomainSwitcherProps) {
  const [isTransitioning, setIsTransitioning] = useState(false);

  const handleSwitch = async (newDomain: 'mirai-agent' | 'mirai-chan') => {
    if (newDomain === currentDomain) return;
    
    setIsTransitioning(true);
    
    // Анимация перехода
    setTimeout(() => {
      onDomainChange(newDomain);
      setIsTransitioning(false);
    }, 300);
  };

  return (
    <div className="fixed top-4 right-4 z-50 flex gap-2">
      {/* Mirai Agent Domain */}
      <button
        onClick={() => handleSwitch('mirai-agent')}
        className={`
          relative overflow-hidden rounded-xl px-4 py-2 font-semibold transition-all duration-300
          ${currentDomain === 'mirai-agent' 
            ? 'bg-gradient-to-r from-mirai-primary to-mirai-secondary text-white shadow-neon-primary' 
            : 'bg-white/10 text-gray-300 hover:bg-white/20 hover:text-white'
          }
          ${isTransitioning ? 'animate-pulse' : ''}
        `}
        disabled={isTransitioning}
      >
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4" />
          <span className="text-sm">Trading</span>
        </div>
        {currentDomain === 'mirai-agent' && (
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
        )}
      </button>

      {/* Mirai-chan Domain */}
      <button
        onClick={() => handleSwitch('mirai-chan')}
        className={`
          relative overflow-hidden rounded-xl px-4 py-2 font-semibold transition-all duration-300
          ${currentDomain === 'mirai-chan' 
            ? 'bg-gradient-to-r from-pink-500 to-purple-500 text-white shadow-[0_0_20px_rgba(236,72,153,0.5)]' 
            : 'bg-white/10 text-gray-300 hover:bg-white/20 hover:text-white'
          }
          ${isTransitioning ? 'animate-pulse' : ''}
        `}
        disabled={isTransitioning}
      >
        <div className="flex items-center gap-2">
          <Star className="w-4 h-4" />
          <span className="text-sm">AI Chan</span>
        </div>
        {currentDomain === 'mirai-chan' && (
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
        )}
      </button>

      {/* Transition Overlay */}
      {isTransitioning && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-40">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-mirai-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-white">Переключение интерфейса...</p>
          </div>
        </div>
      )}
    </div>
  );
}

// Hook для управления доменами
export function useDomainSwitcher() {
  const [currentDomain, setCurrentDomain] = useState<'mirai-agent' | 'mirai-chan'>('mirai-agent');

  const switchDomain = (domain: 'mirai-agent' | 'mirai-chan') => {
    setCurrentDomain(domain);
    // Сохраняем в localStorage
    localStorage.setItem('mirai-current-domain', domain);
  };

  useEffect(() => {
    // Восстанавливаем из localStorage
    const saved = localStorage.getItem('mirai-current-domain') as 'mirai-agent' | 'mirai-chan';
    if (saved) {
      setCurrentDomain(saved);
    }
  }, []);

  return { currentDomain, switchDomain };
}