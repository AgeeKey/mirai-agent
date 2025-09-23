#!/usr/bin/env python3
"""
Mirai Agent - Simple Trading Agent Launcher
Запуск торгового агента без сложных зависимостей
"""
import asyncio
import sys
import os
import logging
from datetime import datetime

# Добавляем пути
sys.path.insert(0, '/root/mirai-agent/app/trader')
sys.path.insert(0, '/root/mirai-agent/app')
sys.path.insert(0, '/root/mirai-agent')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/mirai-agent/logs/services/trader.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('mirai_trader')

class SimpleTradingAgent:
    """Упрощенный торговый агент для демонстрации"""
    
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.running = True
        logger.info(f"🤖 Mirai Trading Agent initialized (dry_run={dry_run})")
    
    async def run(self):
        """Основной цикл агента"""
        logger.info("🚀 Starting trading agent loop...")
        
        cycle = 0
        while self.running:
            try:
                cycle += 1
                
                # Симуляция работы агента
                await self.process_market_data()
                await self.check_positions()
                await self.evaluate_signals()
                
                logger.info(f"📊 Trading cycle {cycle} completed")
                
                # Пауза между циклами
                await asyncio.sleep(10)
                
            except KeyboardInterrupt:
                logger.info("🛑 Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"❌ Error in trading cycle: {e}")
                await asyncio.sleep(5)
        
        logger.info("🏁 Trading agent stopped")
    
    async def process_market_data(self):
        """Обработка рыночных данных"""
        # Симуляция получения данных
        await asyncio.sleep(0.1)
        if self.dry_run:
            logger.debug("📈 Market data processed (simulated)")
    
    async def check_positions(self):
        """Проверка позиций"""
        await asyncio.sleep(0.1)
        if self.dry_run:
            logger.debug("📋 Positions checked (simulated)")
    
    async def evaluate_signals(self):
        """Оценка торговых сигналов"""
        await asyncio.sleep(0.1)
        if self.dry_run:
            logger.debug("🎯 Signals evaluated (simulated)")

async def main():
    """Основная функция"""
    try:
        agent = SimpleTradingAgent(dry_run=True)
        await agent.run()
    except Exception as e:
        logger.error(f"❌ Failed to start trading agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Создаем директорию для логов
    os.makedirs('/root/mirai-agent/logs/services', exist_ok=True)
    
    # Запускаем агента
    asyncio.run(main())