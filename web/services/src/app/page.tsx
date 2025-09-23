'use client';

import { useState, useEffect } from 'react';
import MiraiDashboard from '@/components/MiraiDashboard';
import MiraiChanInterface from '@/components/MiraiChanInterface';
import DomainSwitcher from '@/components/DomainSwitcher';

export default function Home() {
  const [currentDomain, setCurrentDomain] = useState<'mirai-agent' | 'mirai-chan'>('mirai-agent');
  const [isTransitioning, setIsTransitioning] = useState(false);

  const handleDomainChange = async (newDomain: 'mirai-agent' | 'mirai-chan') => {
    if (newDomain === currentDomain) return;
    
    setIsTransitioning(true);
    
    // Анимация перехода
    setTimeout(() => {
      setCurrentDomain(newDomain);
      setTimeout(() => setIsTransitioning(false), 300);
    }, 300);
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Переключатель доменов */}
      <DomainSwitcher 
        currentDomain={currentDomain}
        onDomainChange={handleDomainChange}
      />

      {/* Анимация перехода */}
      {isTransitioning && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="text-white text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-xl font-medium">
              Переключение на {currentDomain === 'mirai-agent' ? 'Mirai-chan' : 'Mirai Agent'}...
            </p>
          </div>
        </div>
      )}

      {/* Основные интерфейсы */}
      <div className={`transition-all duration-500 ${isTransitioning ? 'opacity-0 scale-95' : 'opacity-100 scale-100'}`}>
        {currentDomain === 'mirai-agent' ? (
          <MiraiDashboard />
        ) : (
          <MiraiChanInterface />
        )}
      </div>
    </div>
  );
}