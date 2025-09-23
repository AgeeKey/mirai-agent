'use client';

import React, { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  color: string;
  type: 'dot' | 'line' | 'sakura';
}

interface ParticleBackgroundProps {
  particleCount?: number;
  enableSakura?: boolean;
  enableDataStreams?: boolean;
  className?: string;
}

export function ParticleBackground({ 
  particleCount = 50, 
  enableSakura = true,
  enableDataStreams = true,
  className = ''
}: ParticleBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);
  const particlesRef = useRef<Particle[]>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Настройка размеров canvas
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Цвета частиц
    const colors = [
      'rgba(0, 226, 255, 0.8)',   // Mirai Primary
      'rgba(160, 118, 249, 0.7)', // Mirai Secondary  
      'rgba(255, 107, 193, 0.6)', // Mirai Accent
      'rgba(54, 234, 190, 0.5)',  // Mirai Success
    ];

    // Инициализация частиц
    const initParticles = () => {
      particlesRef.current = [];
      
      for (let i = 0; i < particleCount; i++) {
        // Обычные частицы данных
        particlesRef.current.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.5,
          size: Math.random() * 2 + 1,
          opacity: Math.random() * 0.5 + 0.2,
          color: colors[Math.floor(Math.random() * colors.length)],
          type: 'dot'
        });
      }

      // Добавляем частицы сакуры
      if (enableSakura) {
        for (let i = 0; i < 15; i++) {
          particlesRef.current.push({
            x: Math.random() * canvas.width,
            y: -10,
            vx: (Math.random() - 0.5) * 0.3,
            vy: Math.random() * 1 + 0.5,
            size: Math.random() * 4 + 2,
            opacity: Math.random() * 0.7 + 0.3,
            color: 'rgba(255, 107, 193, 0.8)',
            type: 'sakura'
          });
        }
      }

      // Добавляем потоки данных
      if (enableDataStreams) {
        for (let i = 0; i < 8; i++) {
          particlesRef.current.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: Math.random() * 2 + 1,
            vy: 0,
            size: Math.random() * 30 + 10,
            opacity: Math.random() * 0.3 + 0.1,
            color: 'rgba(0, 226, 255, 0.2)',
            type: 'line'
          });
        }
      }
    };

    // Обновление частиц
    const updateParticles = () => {
      particlesRef.current.forEach(particle => {
        particle.x += particle.vx;
        particle.y += particle.vy;

        // Перезапуск частиц за границами экрана
        if (particle.type === 'sakura') {
          if (particle.y > canvas.height + 10) {
            particle.y = -10;
            particle.x = Math.random() * canvas.width;
          }
          if (particle.x < -10 || particle.x > canvas.width + 10) {
            particle.x = Math.random() * canvas.width;
          }
        } else if (particle.type === 'line') {
          if (particle.x > canvas.width + particle.size) {
            particle.x = -particle.size;
            particle.y = Math.random() * canvas.height;
          }
        } else {
          // Обычные частицы отскакивают от границ
          if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
          if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;
          
          // Удерживаем частицы в границах
          particle.x = Math.max(0, Math.min(canvas.width, particle.x));
          particle.y = Math.max(0, Math.min(canvas.height, particle.y));
        }

        // Мерцание
        particle.opacity += (Math.random() - 0.5) * 0.02;
        particle.opacity = Math.max(0.1, Math.min(1, particle.opacity));
      });
    };

    // Отрисовка частиц
    const drawParticles = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      particlesRef.current.forEach(particle => {
        ctx.save();
        ctx.globalAlpha = particle.opacity;
        
        if (particle.type === 'dot') {
          // Круглые частицы
          ctx.fillStyle = particle.color;
          ctx.beginPath();
          ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
          ctx.fill();
          
          // Добавляем свечение
          ctx.shadowBlur = 10;
          ctx.shadowColor = particle.color;
          ctx.fill();
          
        } else if (particle.type === 'sakura') {
          // Частицы сакуры (ромбики)
          ctx.fillStyle = particle.color;
          ctx.translate(particle.x, particle.y);
          ctx.rotate(Math.PI / 4);
          ctx.fillRect(-particle.size/2, -particle.size/2, particle.size, particle.size);
          
        } else if (particle.type === 'line') {
          // Потоки данных (линии)
          ctx.strokeStyle = particle.color;
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(particle.x, particle.y);
          ctx.lineTo(particle.x + particle.size, particle.y);
          ctx.stroke();
          
          // Добавляем точки на линии
          for (let i = 0; i < particle.size; i += 5) {
            ctx.fillStyle = particle.color;
            ctx.beginPath();
            ctx.arc(particle.x + i, particle.y, 1, 0, Math.PI * 2);
            ctx.fill();
          }
        }
        
        ctx.restore();
      });
    };

    // Соединяем близкие частицы линиями
    const drawConnections = () => {
      const maxDistance = 100;
      
      for (let i = 0; i < particlesRef.current.length; i++) {
        for (let j = i + 1; j < particlesRef.current.length; j++) {
          const p1 = particlesRef.current[i];
          const p2 = particlesRef.current[j];
          
          // Соединяем только точечные частицы
          if (p1.type !== 'dot' || p2.type !== 'dot') continue;
          
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance < maxDistance) {
            const opacity = (1 - distance / maxDistance) * 0.3;
            ctx.save();
            ctx.globalAlpha = opacity;
            ctx.strokeStyle = 'rgba(0, 226, 255, 0.5)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
            ctx.restore();
          }
        }
      }
    };

    // Основной цикл анимации
    const animate = () => {
      updateParticles();
      drawParticles();
      drawConnections();
      animationRef.current = requestAnimationFrame(animate);
    };

    initParticles();
    animate();

    // Очистка
    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [particleCount, enableSakura, enableDataStreams]);

  return (
    <canvas
      ref={canvasRef}
      className={`fixed inset-0 pointer-events-none z-[-1] ${className}`}
      style={{ background: 'transparent' }}
    />
  );
}

// Упрощенная версия для мобильных устройств
export function SimplifiedParticleBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none z-[-1] overflow-hidden">
      {/* Статичные градиентные блики */}
      <div className="absolute top-10 left-10 w-32 h-32 bg-mirai-primary/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute top-1/3 right-20 w-24 h-24 bg-mirai-secondary/15 rounded-full blur-2xl animate-pulse" 
           style={{ animationDelay: '1s' }} />
      <div className="absolute bottom-1/4 left-1/4 w-40 h-40 bg-mirai-accent/10 rounded-full blur-3xl animate-pulse" 
           style={{ animationDelay: '2s' }} />
      
      {/* CSS-анимированные частицы для экономии ресурсов */}
      {Array.from({ length: 20 }).map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 bg-mirai-primary/60 rounded-full animate-pulse"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 3}s`,
            animationDuration: `${2 + Math.random() * 2}s`
          }}
        />
      ))}
    </div>
  );
}

// Хук для определения мощности устройства
export function useDeviceCapabilities() {
  const [isLowPower, setIsLowPower] = React.useState(false);

  React.useEffect(() => {
    // Простая проверка производительности
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isSlowDevice = !gl || isMobile || navigator.hardwareConcurrency < 4;
    
    setIsLowPower(isSlowDevice);
  }, []);

  return { isLowPower };
}

// Автоадаптивный фон
export function AdaptiveParticleBackground(props: ParticleBackgroundProps) {
  const { isLowPower } = useDeviceCapabilities();
  
  if (isLowPower) {
    return <SimplifiedParticleBackground />;
  }
  
  return <ParticleBackground {...props} />;
}