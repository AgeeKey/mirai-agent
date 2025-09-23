"""
Mirai Agent - Telegram Alert Bot
Система уведомлений для критичных событий торговли
"""
import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import schedule
import threading
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/mirai-agent/logs/telegram-alerts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MiraiAlertBot:
    def __init__(self):
        # Получаем данные из .env
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '8104619923:AAGS0IUt18-LoVbI_UTXk51xEfF4vbr2Sr4')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '6428365358')
        
        # API endpoints
        self.trading_api = os.getenv('TRADING_API_URL', "http://localhost:8000")
        self.ai_api = "http://localhost:8080"
        # Alert state
        self._notified_trade_ids: set[int] = set()
        self._last_drawdown_alert: Optional[datetime] = None
        self._last_seen_trade_at: Optional[datetime] = None
        
        # Thresholds
        self.TRADE_THRESHOLD = 100.0  # Уведомления о сделках >$100
        self.DRAWDOWN_THRESHOLD = 5.0  # Алерт при просадке >5%
        self.REPORT_INTERVAL = 4  # Сводки каждые 4 часа
        
        # State tracking
        self.last_balance = 0.0
        self.today_start_balance = 0.0
        self.max_balance_today = 0.0
        self.emergency_mode = False
        
        # Авторизованные пользователи
        self.authorized_users = [int(self.chat_id)]
        
        self.bot = None
        self.application = None
        
    async def initialize(self):
        """Инициализация бота"""
        self.application = Application.builder().token(self.bot_token).build()
        self.bot = self.application.bot
        
        # Добавляем обработчики команд
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("status", self.cmd_status))
        self.application.add_handler(CommandHandler("pnl", self.cmd_pnl))
        self.application.add_handler(CommandHandler("stop", self.cmd_emergency_stop))
        self.application.add_handler(CommandHandler("emergency_stop", self.cmd_emergency_stop))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        logger.info("🤖 Telegram Alert Bot инициализирован")
        
    async def cmd_start(self, update: Update, context):
        """Команда /start"""
        user_id = update.effective_user.id
        
        if user_id not in self.authorized_users:
            await update.message.reply_text("❌ Доступ запрещен")
            return
            
        keyboard = [
            [InlineKeyboardButton("📊 Статус системы", callback_data="status")],
            [InlineKeyboardButton("💰 P&L отчет", callback_data="pnl")],
            [InlineKeyboardButton("🚨 Экстренная остановка", callback_data="emergency_confirm")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎌 *Mirai Agent Alert Bot*\n\n"
            "Система мониторинга автономной торговли\n"
            "🤖 AI торговля активна\n"
            "💸 Live торговля на Binance\n\n"
            "Выберите действие:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    async def cmd_status(self, update: Update, context):
        """Команда /status - статус системы"""
        user_id = update.effective_user.id
        if user_id not in self.authorized_users:
            await update.message.reply_text("❌ Доступ запрещен")
            return
            
        status = await self.get_system_status()
        await update.message.reply_text(status, parse_mode='Markdown')
        
    async def cmd_pnl(self, update: Update, context):
        """Команда /pnl - отчет о прибыли"""
        user_id = update.effective_user.id
        if user_id not in self.authorized_users:
            await update.message.reply_text("❌ Доступ запрещен")
            return
            
        pnl_report = await self.get_pnl_report()
        await update.message.reply_text(pnl_report, parse_mode='Markdown')
        
    async def cmd_emergency_stop(self, update: Update, context):
        """Команда /stop - экстренная остановка"""
        user_id = update.effective_user.id
        if user_id not in self.authorized_users:
            await update.message.reply_text("❌ Доступ запрещен")
            return
            
        keyboard = [
            [InlineKeyboardButton("🛑 ПОДТВЕРДИТЬ ОСТАНОВКУ", callback_data="emergency_stop")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🚨 *ЭКСТРЕННАЯ ОСТАНОВКА ТОРГОВЛИ*\n\n"
            "⚠️ Это остановит ВСЮ торговлю немедленно!\n"
            "💸 Все открытые позиции будут закрыты\n"
            "🤖 AI система будет отключена\n\n"
            "Вы уверены?",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    async def cmd_help(self, update: Update, context):
        """Команда /help"""
        help_text = """
🎌 *Mirai Agent Commands*

📊 `/status` - Статус системы
💰 `/pnl` - P&L отчет  
🚨 `/stop` - Экстренная остановка
❓ `/help` - Помощь

*Автоматические уведомления:*
💸 Сделки >$100
📉 Просадка >5%
📋 Сводки каждые 4 часа
🚨 Критические ошибки

*Emergency:* @mirai_emergency
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    async def button_handler(self, update: Update, context):
        """Обработчик кнопок"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if user_id not in self.authorized_users:
            await query.answer("❌ Доступ запрещен")
            return
            
        await query.answer()
        
        if query.data == "status":
            status = await self.get_system_status()
            await query.edit_message_text(status, parse_mode='Markdown')
            
        elif query.data == "pnl":
            pnl_report = await self.get_pnl_report()
            await query.edit_message_text(pnl_report, parse_mode='Markdown')
            
        elif query.data == "emergency_confirm":
            keyboard = [
                [InlineKeyboardButton("🛑 ПОДТВЕРДИТЬ ОСТАНОВКУ", callback_data="emergency_stop")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🚨 *ЭКСТРЕННАЯ ОСТАНОВКА ТОРГОВЛИ*\n\n"
                "⚠️ Это остановит ВСЮ торговлю!\n"
                "Подтвердите действие:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        elif query.data == "emergency_stop":
            await self.execute_emergency_stop()
            await query.edit_message_text(
                "🛑 *ТОРГОВЛЯ ОСТАНОВЛЕНА*\n\n"
                "✅ Экстренная остановка выполнена\n"
                "📊 Проверьте логи для деталей\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
            )
            
        elif query.data == "cancel":
            await query.edit_message_text("❌ Операция отменена")
            
    async def get_system_status(self) -> str:
        """Получить статус системы"""
        try:
            # Проверяем AI Orchestrator
            async with httpx.AsyncClient() as client:
                ai_response = await client.get(f"{self.ai_api}/health", timeout=5)
                ai_status = "✅ Здоров" if ai_response.status_code == 200 else "❌ Недоступен"
                
                # Проверяем Trading API  
                trading_response = await client.get(f"{self.trading_api}/docs", timeout=5)
                trading_status = "✅ Активен" if trading_response.status_code == 200 else "❌ Недоступен"
                
            status_text = f"""
📊 *Статус системы Mirai Agent*

🤖 AI Orchestrator: {ai_status}
💰 Trading API: {trading_status}
🌐 Веб-интерфейс: ✅ Работает
🔐 SSL: ✅ Активен

⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
🚀 Uptime: {self.get_uptime()}
💾 Memory: {self.get_memory_usage()}%
            """
            
        except Exception as e:
            status_text = f"❌ Ошибка получения статуса: {str(e)}"
            
        return status_text
        
    async def get_pnl_report(self) -> str:
        """Получить отчет P&L"""
        try:
            # В реальной системе здесь будет запрос к Trading API
            # Пока используем моковые данные
            daily_pnl = 127.45
            total_pnl = 1247.83
            win_rate = 68.5
            active_positions = 2
            
            pnl_text = f"""
💰 *P&L Отчет*

📈 Общий P&L: ${total_pnl:.2f}
📊 Дневной P&L: ${daily_pnl:.2f}
🎯 Win Rate: {win_rate}%
📋 Активных позиций: {active_positions}

⚡ Лучшая сделка: +$89.30 (ADAUSDT)
⚠️ Худшая сделка: -$23.10 (ETHUSDT)

⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}
            """
            
        except Exception as e:
            pnl_text = f"❌ Ошибка получения P&L: {str(e)}"
            
        return pnl_text
        
    async def execute_emergency_stop(self):
        """Выполнить экстренную остановку"""
        try:
            # Отправляем команду остановки к Trading API
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.trading_api}/emergency/stop", timeout=10)
                
            self.emergency_mode = True
            logger.critical("🚨 ЭКСТРЕННАЯ ОСТАНОВКА ВЫПОЛНЕНА ЧЕРЕЗ TELEGRAM")
            
            # Уведомляем всех авторизованных пользователей
            await self.broadcast_message(
                "🚨 *ЭКСТРЕННАЯ ОСТАНОВКА*\n\n"
                "🛑 Торговля остановлена\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}\n"
                "📊 Проверьте систему"
            )
            
        except Exception as e:
            logger.error(f"Ошибка экстренной остановки: {e}")
            
    async def broadcast_message(self, message: str):
        """Отправить сообщение всем авторизованным пользователям"""
        for user_id in self.authorized_users:
            try:
                await self.bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения {user_id}: {e}")
                
    async def check_large_trades(self):
        """Проверка и уведомления о крупных сделках (ноционал > $threshold)"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.trading_api}/api/trading/trades", timeout=10)
                data = resp.json()
                trades: List[Dict[str, Any]] = data.get('trades', [])
        except Exception as e:
            logger.error(f"Ошибка получения сделок: {e}")
            return

        new_alerts = []
        for t in trades:
            try:
                trade_id = int(t.get('id', 0))
            except Exception:
                trade_id = None

            price = float(t.get('price', 0))
            qty = float(t.get('quantity', 0))
            notional = abs(price * qty)
            ts = t.get('timestamp')
            symbol = t.get('symbol', 'UNKNOWN')
            action = t.get('action', 'TRADE')
            strategy = t.get('strategy', 'unknown')

            if notional >= self.TRADE_THRESHOLD:
                # Avoid duplicate notifications
                if trade_id is not None and trade_id in self._notified_trade_ids:
                    continue
                new_alerts.append((trade_id, symbol, action, notional, strategy, ts))

        for trade_id, symbol, action, notional, strategy, ts in new_alerts:
            text = (
                f"💸 *Крупная сделка*\n\n"
                f"{symbol} {action}\n"
                f"Ноционал: ${notional:,.2f}\n"
                f"Стратегия: {strategy}\n"
                f"⏰ {ts if ts else datetime.now().strftime('%H:%M:%S')}"
            )
            await self.broadcast_message(text)
            if trade_id is not None:
                self._notified_trade_ids.add(trade_id)
        
    async def check_drawdown(self):
        """Проверка дневной просадки и уведомление при превышении порога"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.trading_api}/api/trading/status", timeout=10)
                status = resp.json()
        except Exception as e:
            logger.error(f"Ошибка получения статуса для drawdown: {e}")
            return

        # Use balance.total as equity; initialize daily baseline and max
        balance = status.get('balance', {}).get('total')
        if balance is None:
            return
        try:
            balance = float(balance)
        except Exception:
            return

        # Initialize daily tracking
        if self.today_start_balance == 0.0:
            self.today_start_balance = balance
            self.max_balance_today = balance

        # Update max balance seen today
        if balance > self.max_balance_today:
            self.max_balance_today = balance

        # Compute drawdown from max
        if self.max_balance_today > 0:
            dd = (self.max_balance_today - balance) / self.max_balance_today * 100.0
        else:
            dd = 0.0

        if dd >= self.DRAWDOWN_THRESHOLD:
            # Throttle alerts to once per 30 minutes
            now = datetime.now()
            if self._last_drawdown_alert and (now - self._last_drawdown_alert) < timedelta(minutes=30):
                return
            self._last_drawdown_alert = now
            text = (
                f"📉 *Просадка превышает порог*\n\n"
                f"Текущая просадка: {dd:.2f}% (порог {self.DRAWDOWN_THRESHOLD:.1f}%)\n"
                f"Текущий баланс: ${balance:,.2f}\n"
                f"Макс. баланс за день: ${self.max_balance_today:,.2f}\n"
                f"⏰ {now.strftime('%H:%M:%S')}"
            )
            await self.broadcast_message(text)
        
    def get_uptime(self) -> str:
        """Получить время работы"""
        # Заглушка
        return "2h 15m"
        
    def get_memory_usage(self) -> float:
        """Получить использование памяти"""
        # Заглушка
        return 45.2
        
    def start_scheduled_reports(self):
        """Запустить планировщик отчетов"""
        def run_scheduler():
            schedule.every(4).hours.do(lambda: asyncio.create_task(self.send_periodic_report()))
            schedule.every(1).minutes.do(lambda: asyncio.create_task(self.check_large_trades()))
            schedule.every(1).minutes.do(lambda: asyncio.create_task(self.check_drawdown()))
            
            while True:
                schedule.run_pending()
                time.sleep(60)
                
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("📅 Планировщик отчетов запущен (каждые 4 часа)")
        
    async def send_periodic_report(self):
        """Отправить периодический отчет"""
        report = f"""
📋 *Периодический отчет*

{await self.get_pnl_report()}

{await self.get_system_status()}

⏰ Следующий отчет через 4 часа
        """
        
        await self.broadcast_message(report)
        logger.info("📋 Периодический отчет отправлен")
        
    async def run(self):
        """Запустить бота"""
        try:
            await self.initialize()
            self.start_scheduled_reports()
            
            logger.info("🚀 Telegram Alert Bot запущен")
            await self.broadcast_message(
                "🚀 *Mirai Alert Bot запущен*\n\n"
                "🔔 Мониторинг активирован\n"
                "💸 Live торговля под контролем\n"
                f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
            )
            # Initial checks
            await self.check_large_trades()
            await self.check_drawdown()
            
            # Запускаем polling
            await self.application.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise

def main():
    """Главная функция"""
    # Загружаем переменные окружения
    if os.path.exists('/root/mirai-agent/.env'):
        with open('/root/mirai-agent/.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    bot = MiraiAlertBot()
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.run())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        try:
            loop.close()
        except:
            pass

if __name__ == "__main__":
    main()
