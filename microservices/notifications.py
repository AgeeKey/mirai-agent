"""
Notifications Service - Multi-Channel Notification System with Smart Routing
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr, validator
import asyncio
import logging
import os
import json
import smtplib
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import redis
import aiohttp
import discord
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import telegram
from telegram.ext import Application
from dataclasses import dataclass
from jinja2 import Template
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mirai Notifications Service",
    description="🔔 Multi-Channel Notification System with Smart Routing & Analytics",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True,
        socket_timeout=5
    )
    redis_client.ping()
    logger.info("✅ Redis connection established")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}")
    redis_client = None

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
WEBHOOK_ENDPOINTS = os.getenv('WEBHOOK_ENDPOINTS', '').split(',') if os.getenv('WEBHOOK_ENDPOINTS') else []

# Enhanced Data Models
class NotificationChannel(BaseModel):
    channel_type: str = Field(..., description="telegram, discord, email, webhook, sms")
    enabled: bool = Field(True, description="Channel enabled status")
    config: Dict[str, Any] = Field(default_factory=dict, description="Channel-specific configuration")
    priority_threshold: str = Field("INFO", description="Minimum priority level")
    rate_limit: int = Field(60, description="Max notifications per hour")
    retry_count: int = Field(3, description="Number of retry attempts")
    retry_delay: int = Field(300, description="Retry delay in seconds")

class NotificationTemplate(BaseModel):
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    channel_type: str = Field(..., description="Target channel type")
    subject_template: str = Field(..., description="Subject/title template")
    body_template: str = Field(..., description="Message body template")
    format_type: str = Field("text", description="text, html, markdown")
    variables: List[str] = Field(default_factory=list, description="Template variables")
    created_at: datetime = Field(default_factory=datetime.now)

class NotificationRequest(BaseModel):
    notification_id: Optional[str] = Field(None, description="Unique notification ID")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    priority: str = Field("INFO", description="DEBUG, INFO, WARNING, ERROR, CRITICAL")
    category: str = Field("general", description="Notification category")
    channels: List[str] = Field(default_factory=list, description="Target channels")
    recipients: Dict[str, List[str]] = Field(default_factory=dict, description="Channel-specific recipients")
    template_id: Optional[str] = Field(None, description="Template to use")
    template_variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    attachments: List[str] = Field(default_factory=list, description="File attachments")
    schedule_time: Optional[datetime] = Field(None, description="Scheduled delivery time")
    expiry_time: Optional[datetime] = Field(None, description="Message expiry time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class NotificationStatus(BaseModel):
    notification_id: str = Field(..., description="Notification identifier")
    status: str = Field(..., description="pending, sent, failed, expired, cancelled")
    created_at: datetime = Field(..., description="Creation timestamp")
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    delivery_status: Dict[str, str] = Field(default_factory=dict, description="Per-channel delivery status")
    error_details: Dict[str, str] = Field(default_factory=dict, description="Error details per channel")
    retry_count: Dict[str, int] = Field(default_factory=dict, description="Retry count per channel")
    recipients_reached: int = Field(0, description="Number of recipients reached")
    total_recipients: int = Field(0, description="Total number of recipients")

class NotificationRule(BaseModel):
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Rule name")
    enabled: bool = Field(True, description="Rule enabled status")
    conditions: Dict[str, Any] = Field(..., description="Rule conditions")
    actions: List[Dict[str, Any]] = Field(..., description="Rule actions")
    priority: int = Field(100, description="Rule priority (lower = higher priority)")
    created_at: datetime = Field(default_factory=datetime.now)

class NotificationAnalytics(BaseModel):
    period_start: datetime = Field(..., description="Analytics period start")
    period_end: datetime = Field(..., description="Analytics period end")
    total_notifications: int = Field(0, description="Total notifications sent")
    success_rate: float = Field(0.0, description="Overall success rate")
    channel_statistics: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Per-channel stats")
    priority_distribution: Dict[str, int] = Field(default_factory=dict, description="Priority distribution")
    category_distribution: Dict[str, int] = Field(default_factory=dict, description="Category distribution")
    delivery_times: Dict[str, float] = Field(default_factory=dict, description="Average delivery times")
    error_summary: Dict[str, int] = Field(default_factory=dict, description="Error summary")

# Notification Service
class NotificationService:
    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
        self.templates: Dict[str, NotificationTemplate] = {}
        self.pending_notifications: Dict[str, NotificationRequest] = {}
        self.notification_status: Dict[str, NotificationStatus] = {}
        self.notification_rules: Dict[str, NotificationRule] = {}
        self.delivery_queue = asyncio.Queue()
        self.is_processing = False
        
        # Initialize default channels
        self._initialize_default_channels()
        self._initialize_default_templates()
        
    def _initialize_default_channels(self):
        """Initialize default notification channels"""
        
        # Telegram channel
        if TELEGRAM_BOT_TOKEN:
            self.channels['telegram'] = NotificationChannel(
                channel_type='telegram',
                config={
                    'bot_token': TELEGRAM_BOT_TOKEN,
                    'parse_mode': 'HTML'
                },
                priority_threshold='INFO'
            )
        
        # Discord channel
        if DISCORD_BOT_TOKEN:
            self.channels['discord'] = NotificationChannel(
                channel_type='discord',
                config={
                    'bot_token': DISCORD_BOT_TOKEN,
                    'embed_color': 0x00ff00
                },
                priority_threshold='INFO'
            )
        
        # Email channel
        if EMAIL_USER and EMAIL_PASS:
            self.channels['email'] = NotificationChannel(
                channel_type='email',
                config={
                    'smtp_host': EMAIL_HOST,
                    'smtp_port': EMAIL_PORT,
                    'username': EMAIL_USER,
                    'password': EMAIL_PASS,
                    'use_tls': True
                },
                priority_threshold='WARNING'
            )
        
        # Webhook channel
        if WEBHOOK_ENDPOINTS:
            self.channels['webhook'] = NotificationChannel(
                channel_type='webhook',
                config={
                    'endpoints': WEBHOOK_ENDPOINTS,
                    'timeout': 30,
                    'verify_ssl': True
                },
                priority_threshold='ERROR'
            )
    
    def _initialize_default_templates(self):
        """Initialize default notification templates"""
        
        # Trading alert template
        self.templates['trading_alert'] = NotificationTemplate(
            template_id='trading_alert',
            name='Trading Alert',
            channel_type='telegram',
            subject_template='🚨 Trading Alert: {{symbol}}',
            body_template='''
🚨 <b>Trading Alert</b>

📊 <b>Symbol:</b> {{symbol}}
📈 <b>Action:</b> {{action}}
💰 <b>Price:</b> ${{price}}
📊 <b>Quantity:</b> {{quantity}}
⚡ <b>Priority:</b> {{priority}}

📝 <b>Details:</b> {{message}}

🕐 {{timestamp}}
            ''',
            format_type='html',
            variables=['symbol', 'action', 'price', 'quantity', 'priority', 'message', 'timestamp']
        )
        
        # Risk alert template
        self.templates['risk_alert'] = NotificationTemplate(
            template_id='risk_alert',
            name='Risk Alert',
            channel_type='telegram',
            subject_template='⚠️ Risk Alert: {{alert_type}}',
            body_template='''
⚠️ <b>Risk Alert</b>

🎯 <b>Type:</b> {{alert_type}}
📊 <b>Severity:</b> {{severity}}
💼 <b>Portfolio:</b> {{portfolio_id}}
📈 <b>Symbol:</b> {{symbol}}

📊 <b>Current Value:</b> {{current_value}}
🚨 <b>Threshold:</b> {{threshold_value}}

💡 <b>Recommendation:</b> {{recommended_action}}

📝 {{message}}

🕐 {{timestamp}}
            ''',
            format_type='html',
            variables=['alert_type', 'severity', 'portfolio_id', 'symbol', 'current_value', 'threshold_value', 'recommended_action', 'message', 'timestamp']
        )
        
        # Performance report template
        self.templates['performance_report'] = NotificationTemplate(
            template_id='performance_report',
            name='Performance Report',
            channel_type='email',
            subject_template='📊 Daily Performance Report - {{date}}',
            body_template='''
            <html>
            <body>
                <h2>📊 Daily Performance Report</h2>
                <h3>Date: {{date}}</h3>
                
                <h4>Portfolio Summary</h4>
                <ul>
                    <li><strong>Total Value:</strong> ${{total_value}}</li>
                    <li><strong>Daily P&L:</strong> {{daily_pnl}}%</li>
                    <li><strong>Total Return:</strong> {{total_return}}%</li>
                    <li><strong>Sharpe Ratio:</strong> {{sharpe_ratio}}</li>
                </ul>
                
                <h4>Top Performing Assets</h4>
                <ul>
                {{#top_performers}}
                    <li>{{symbol}}: {{performance}}%</li>
                {{/top_performers}}
                </ul>
                
                <h4>Risk Metrics</h4>
                <ul>
                    <li><strong>VaR (1d):</strong> {{var_1d}}%</li>
                    <li><strong>Max Drawdown:</strong> {{max_drawdown}}%</li>
                    <li><strong>Risk Exposure:</strong> {{risk_exposure}}%</li>
                </ul>
                
                <p>Generated at {{timestamp}}</p>
            </body>
            </html>
            ''',
            format_type='html',
            variables=['date', 'total_value', 'daily_pnl', 'total_return', 'sharpe_ratio', 'top_performers', 'var_1d', 'max_drawdown', 'risk_exposure', 'timestamp']
        )

# Initialize service
notification_service = NotificationService()

# WebSocket connection manager
class NotificationConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔌 Notification WebSocket client connected. Total: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"❌ Notification WebSocket client disconnected. Total: {len(self.active_connections)}")
        
    async def broadcast_notification(self, notification: Dict[str, Any]):
        """Broadcast notification to all connected clients"""
        if self.active_connections:
            message = {
                "type": "notification_update",
                "data": notification,
                "timestamp": datetime.now().isoformat()
            }
            dead_connections = []
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    dead_connections.append(connection)
            
            # Remove dead connections
            for dead_conn in dead_connections:
                self.disconnect(dead_conn)

manager = NotificationConnectionManager()

@app.get("/notifications", response_model=List[Notification])
async def get_notifications(limit: int = 50):
    return notifications[-limit:] if notifications else []

@app.post("/notify")
async def send_notification(
    type: str,
    title: str,
    message: str,
    channel: str = "web"
):
    notification = Notification(
        id=f"notif_{datetime.now().timestamp()}",
        type=type,
        title=title,
        message=message,
        timestamp=datetime.now(),
        channel=channel
    )
    
    notifications.append(notification)
    if len(notifications) > 1000:
        notifications.pop(0)
    
    # Store in Redis
    try:
        redis_client.lpush("notifications", json.dumps(notification.dict(), default=str))
        redis_client.ltrim("notifications", 0, 999)  # Keep last 1000
    except:
        pass
    
    return {"message": "Notification sent", "notification": notification}

@app.post("/notify/trade")
async def notify_trade(
    symbol: str,
    action: str,
    quantity: float,
    price: float,
    status: str = "EXECUTED"
):
    title = f"Trade {status}: {action} {symbol}"
    message = f"{action} {quantity} {symbol} at {price}"
    
    return await send_notification("TRADE", title, message)

@app.post("/notify/alert")
async def notify_alert(
    symbol: str,
    alert_type: str,
    message: str
):
    title = f"{alert_type} Alert: {symbol}"
    
    return await send_notification("WARNING", title, message)

@app.get("/config", response_model=AlertConfig)
async def get_alert_config():
    return alert_config

@app.post("/config")
async def update_alert_config(config: AlertConfig):
    global alert_config
    alert_config = config
    return {"message": "Alert configuration updated"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
