'use client';

import { useEffect, useRef } from 'react';

declare global {
  interface Window {
    TradingView: any;
  }
}

interface TradingViewWidgetProps {
  symbol?: string;
  theme?: 'light' | 'dark';
  width?: string | number;
  height?: string | number;
  interval?: string;
  container_id?: string;
}

const TradingViewWidget: React.FC<TradingViewWidgetProps> = ({
  symbol = 'BINANCE:BTCUSDT',
  theme = 'dark',
  width = '100%',
  height = 500,
  interval = '15',
  container_id = 'tradingview_widget'
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Создаем уникальный ID для каждого виджета
    const widgetId = `${container_id}_${Math.random().toString(36).substr(2, 9)}`;
    
    if (containerRef.current) {
      containerRef.current.id = widgetId;
    }

    // Загружаем TradingView скрипт если еще не загружен
    const loadTradingViewScript = () => {
      return new Promise<void>((resolve) => {
        if (window.TradingView) {
          resolve();
          return;
        }

        const script = document.createElement('script');
        script.src = 'https://s3.tradingview.com/tv.js';
        script.async = true;
        script.onload = () => resolve();
        document.head.appendChild(script);
      });
    };

    const initWidget = async () => {
      await loadTradingViewScript();
      
      if (window.TradingView && containerRef.current) {
        new window.TradingView.widget({
          autosize: true,
          symbol: symbol,
          interval: interval,
          timezone: 'Europe/Moscow',
          theme: theme,
          style: '1',
          locale: 'ru',
          toolbar_bg: '#1f2937',
          enable_publishing: false,
          hide_side_toolbar: false,
          allow_symbol_change: true,
          details: true,
          hotlist: true,
          calendar: true,
          container_id: widgetId,
          width: width,
          height: height,
          studies: [
            'MASimple@tv-basicstudies',
            'RSI@tv-basicstudies',
            'MACD@tv-basicstudies'
          ],
          overrides: {
            'paneProperties.background': '#111827',
            'paneProperties.vertGridProperties.color': '#374151',
            'paneProperties.horzGridProperties.color': '#374151',
            'symbolWatermarkProperties.transparency': 90,
            'scalesProperties.textColor': '#9ca3af',
            'mainSeriesProperties.candleStyle.upColor': '#10b981',
            'mainSeriesProperties.candleStyle.downColor': '#ef4444',
            'mainSeriesProperties.candleStyle.borderUpColor': '#10b981',
            'mainSeriesProperties.candleStyle.borderDownColor': '#ef4444',
            'mainSeriesProperties.candleStyle.wickUpColor': '#10b981',
            'mainSeriesProperties.candleStyle.wickDownColor': '#ef4444'
          }
        });
      }
    };

    initWidget();

    // Cleanup при размонтировании
    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [symbol, theme, width, height, interval, container_id]);

  return (
    <div className="trading-view-widget w-full h-full bg-gray-900 rounded-lg overflow-hidden">
      <div 
        ref={containerRef}
        className="w-full h-full"
        style={{ height: typeof height === 'number' ? `${height}px` : height }}
      />
    </div>
  );
};

export default TradingViewWidget;