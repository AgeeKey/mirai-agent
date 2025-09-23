"""
Notifications Service API Endpoints - Comprehensive Multi-Channel Notification System
"""

from notifications import (
    app, notification_service, manager, NotificationRequest, NotificationStatus, 
    NotificationChannel, NotificationTemplate, NotificationRule, NotificationAnalytics
)
from fastapi import HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import telegram
from jinja2 import Template

logger = logging.getLogger(__name__)

# Request/Response Models
class SendNotificationRequest(BaseModel):
    title: str
    message: str
    priority: str = "INFO"
    category: str = "general"
    channels: List[str] = []
    recipients: Dict[str, List[str]] = {}
    template_id: Optional[str] = None
    template_variables: Dict[str, Any] = {}
    schedule_time: Optional[datetime] = None

class BulkNotificationRequest(BaseModel):
    notifications: List[SendNotificationRequest]
    batch_id: Optional[str] = None

class ChannelConfigRequest(BaseModel):
    channel_type: str
    enabled: bool = True
    config: Dict[str, Any] = {}
    priority_threshold: str = "INFO"
    rate_limit: int = 60

class TemplateRequest(BaseModel):
    template_id: str
    name: str
    channel_type: str
    subject_template: str
    body_template: str
    format_type: str = "text"
    variables: List[str] = []

class RuleRequest(BaseModel):
    rule_id: str
    name: str
    enabled: bool = True
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    priority: int = 100

# Health Check
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        if notification_service.redis_client:
            notification_service.redis_client.ping()
        
        # Check channel status
        active_channels = len([c for c in notification_service.channels.values() if c.enabled])
        
        return {
            "status": "healthy",
            "service": "notifications",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "active_channels": active_channels,
                "total_templates": len(notification_service.templates),
                "pending_notifications": len(notification_service.pending_notifications),
                "is_processing": notification_service.is_processing
            }
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Core Notification Endpoints
@app.post("/send", response_model=NotificationStatus)
async def send_notification(
    request: SendNotificationRequest,
    background_tasks: BackgroundTasks
):
    """
    Send notification through specified channels
    
    Supports:
    - Multiple delivery channels (Telegram, Discord, Email, Webhook)
    - Template-based messages with variable substitution
    - Priority-based routing and rate limiting
    - Scheduled delivery and expiry times
    - Real-time delivery tracking
    """
    try:
        # Generate notification ID
        notification_id = request.notification_id if hasattr(request, 'notification_id') and request.notification_id else str(uuid.uuid4())
        
        logger.info(f"📤 Sending notification: {notification_id}")
        
        # Create notification request
        notification_req = NotificationRequest(
            notification_id=notification_id,
            title=request.title,
            message=request.message,
            priority=request.priority,
            category=request.category,
            channels=request.channels or ["telegram"],  # Default to telegram
            recipients=request.recipients,
            template_id=request.template_id,
            template_variables=request.template_variables,
            schedule_time=request.schedule_time
        )
        
        # Create notification status
        status = NotificationStatus(
            notification_id=notification_id,
            status="pending",
            created_at=datetime.now(),
            total_recipients=sum(len(recipients) for recipients in request.recipients.values())
        )
        
        # Store in service
        notification_service.pending_notifications[notification_id] = notification_req
        notification_service.notification_status[notification_id] = status
        
        # Schedule delivery
        if request.schedule_time and request.schedule_time > datetime.now():
            # Scheduled delivery
            background_tasks.add_task(
                notification_service._schedule_notification,
                notification_id
            )
            status.status = "scheduled"
        else:
            # Immediate delivery
            background_tasks.add_task(
                notification_service._process_notification,
                notification_id
            )
        
        # Broadcast to WebSocket clients
        await manager.broadcast_notification({
            "notification_id": notification_id,
            "status": status.status,
            "title": request.title,
            "priority": request.priority
        })
        
        logger.info(f"✅ Notification queued: {notification_id}")
        return status
        
    except Exception as e:
        logger.error(f"❌ Send notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Send notification failed: {str(e)}")

@app.post("/send/bulk", response_model=List[NotificationStatus])
async def send_bulk_notifications(
    request: BulkNotificationRequest,
    background_tasks: BackgroundTasks
):
    """Send multiple notifications in batch"""
    try:
        batch_id = request.batch_id or str(uuid.uuid4())
        logger.info(f"📤 Sending bulk notifications: {batch_id} ({len(request.notifications)} notifications)")
        
        results = []
        
        for i, notification in enumerate(request.notifications):
            notification_id = f"{batch_id}_{i}"
            
            # Create individual notification
            individual_request = SendNotificationRequest(
                title=notification.title,
                message=notification.message,
                priority=notification.priority,
                category=notification.category,
                channels=notification.channels,
                recipients=notification.recipients,
                template_id=notification.template_id,
                template_variables=notification.template_variables,
                schedule_time=notification.schedule_time
            )
            
            # Process through send_notification
            status = await send_notification(individual_request, background_tasks)
            status.notification_id = notification_id
            results.append(status)
        
        logger.info(f"✅ Bulk notifications queued: {batch_id}")
        return results
        
    except Exception as e:
        logger.error(f"❌ Bulk send failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk send failed: {str(e)}")

@app.get("/status/{notification_id}", response_model=NotificationStatus)
async def get_notification_status(notification_id: str):
    """Get delivery status of a specific notification"""
    try:
        if notification_id not in notification_service.notification_status:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return notification_service.notification_status[notification_id]
        
    except Exception as e:
        logger.error(f"❌ Get status failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get status failed: {str(e)}")

@app.get("/status", response_model=List[NotificationStatus])
async def get_all_notifications_status(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100
):
    """Get status of all notifications with filtering"""
    try:
        statuses = list(notification_service.notification_status.values())
        
        # Apply filters
        if status:
            statuses = [s for s in statuses if s.status == status]
        if priority:
            # Need to get priority from original request
            statuses = [s for s in statuses if s.notification_id in notification_service.pending_notifications and 
                       notification_service.pending_notifications[s.notification_id].priority == priority]
        if category:
            statuses = [s for s in statuses if s.notification_id in notification_service.pending_notifications and 
                       notification_service.pending_notifications[s.notification_id].category == category]
        
        # Sort by creation time (newest first) and limit
        statuses.sort(key=lambda x: x.created_at, reverse=True)
        return statuses[:limit]
        
    except Exception as e:
        logger.error(f"❌ Get all statuses failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get all statuses failed: {str(e)}")

# Channel Management Endpoints
@app.get("/channels", response_model=List[NotificationChannel])
async def get_channels():
    """Get all configured notification channels"""
    return list(notification_service.channels.values())

@app.post("/channels", response_model=NotificationChannel)
async def add_channel(request: ChannelConfigRequest):
    """Add or update a notification channel"""
    try:
        logger.info(f"⚙️ Configuring channel: {request.channel_type}")
        
        channel = NotificationChannel(
            channel_type=request.channel_type,
            enabled=request.enabled,
            config=request.config,
            priority_threshold=request.priority_threshold,
            rate_limit=request.rate_limit
        )
        
        notification_service.channels[request.channel_type] = channel
        
        # Cache configuration
        if notification_service.redis_client:
            try:
                notification_service.redis_client.setex(
                    f"channel_config:{request.channel_type}",
                    3600,
                    json.dumps(channel.dict())
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to cache channel config: {e}")
        
        logger.info(f"✅ Channel configured: {request.channel_type}")
        return channel
        
    except Exception as e:
        logger.error(f"❌ Add channel failed: {e}")
        raise HTTPException(status_code=500, detail=f"Add channel failed: {str(e)}")

@app.delete("/channels/{channel_type}")
async def remove_channel(channel_type: str):
    """Remove a notification channel"""
    try:
        if channel_type not in notification_service.channels:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        del notification_service.channels[channel_type]
        
        return {"status": "removed", "channel_type": channel_type}
        
    except Exception as e:
        logger.error(f"❌ Remove channel failed: {e}")
        raise HTTPException(status_code=500, detail=f"Remove channel failed: {str(e)}")

# Template Management Endpoints
@app.get("/templates", response_model=List[NotificationTemplate])
async def get_templates():
    """Get all notification templates"""
    return list(notification_service.templates.values())

@app.post("/templates", response_model=NotificationTemplate)
async def create_template(request: TemplateRequest):
    """Create a new notification template"""
    try:
        logger.info(f"📝 Creating template: {request.template_id}")
        
        template = NotificationTemplate(
            template_id=request.template_id,
            name=request.name,
            channel_type=request.channel_type,
            subject_template=request.subject_template,
            body_template=request.body_template,
            format_type=request.format_type,
            variables=request.variables
        )
        
        notification_service.templates[request.template_id] = template
        
        logger.info(f"✅ Template created: {request.template_id}")
        return template
        
    except Exception as e:
        logger.error(f"❌ Create template failed: {e}")
        raise HTTPException(status_code=500, detail=f"Create template failed: {str(e)}")

@app.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """Delete a notification template"""
    try:
        if template_id not in notification_service.templates:
            raise HTTPException(status_code=404, detail="Template not found")
        
        del notification_service.templates[template_id]
        
        return {"status": "deleted", "template_id": template_id}
        
    except Exception as e:
        logger.error(f"❌ Delete template failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete template failed: {str(e)}")

# Rule Management Endpoints
@app.get("/rules", response_model=List[NotificationRule])
async def get_rules():
    """Get all notification rules"""
    return list(notification_service.notification_rules.values())

@app.post("/rules", response_model=NotificationRule)
async def create_rule(request: RuleRequest):
    """Create a new notification rule"""
    try:
        logger.info(f"📋 Creating rule: {request.rule_id}")
        
        rule = NotificationRule(
            rule_id=request.rule_id,
            name=request.name,
            enabled=request.enabled,
            conditions=request.conditions,
            actions=request.actions,
            priority=request.priority
        )
        
        notification_service.notification_rules[request.rule_id] = rule
        
        logger.info(f"✅ Rule created: {request.rule_id}")
        return rule
        
    except Exception as e:
        logger.error(f"❌ Create rule failed: {e}")
        raise HTTPException(status_code=500, detail=f"Create rule failed: {str(e)}")

# Analytics Endpoints
@app.get("/analytics", response_model=NotificationAnalytics)
async def get_analytics(
    period_hours: int = 24,
    include_channel_stats: bool = True
):
    """Get notification analytics for specified period"""
    try:
        period_start = datetime.now() - timedelta(hours=period_hours)
        period_end = datetime.now()
        
        # Calculate analytics from notification status data
        relevant_statuses = [
            status for status in notification_service.notification_status.values()
            if status.created_at >= period_start
        ]
        
        total_notifications = len(relevant_statuses)
        successful_notifications = len([s for s in relevant_statuses if s.status == "sent"])
        success_rate = (successful_notifications / total_notifications) if total_notifications > 0 else 0.0
        
        # Priority distribution
        priority_dist = {}
        for notification_id, status in notification_service.notification_status.items():
            if notification_id in notification_service.pending_notifications:
                priority = notification_service.pending_notifications[notification_id].priority
                priority_dist[priority] = priority_dist.get(priority, 0) + 1
        
        # Category distribution
        category_dist = {}
        for notification_id, status in notification_service.notification_status.items():
            if notification_id in notification_service.pending_notifications:
                category = notification_service.pending_notifications[notification_id].category
                category_dist[category] = category_dist.get(category, 0) + 1
        
        analytics = NotificationAnalytics(
            period_start=period_start,
            period_end=period_end,
            total_notifications=total_notifications,
            success_rate=success_rate,
            priority_distribution=priority_dist,
            category_distribution=category_dist
        )
        
        return analytics
        
    except Exception as e:
        logger.error(f"❌ Get analytics failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get analytics failed: {str(e)}")

# Testing Endpoints
@app.post("/test/{channel_type}")
async def test_channel(
    channel_type: str,
    test_message: str = "Test notification from Mirai Notifications Service"
):
    """Test a specific notification channel"""
    try:
        if channel_type not in notification_service.channels:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # Send test notification
        test_request = SendNotificationRequest(
            title="🧪 Channel Test",
            message=test_message,
            priority="INFO",
            category="test",
            channels=[channel_type]
        )
        
        background_tasks = BackgroundTasks()
        status = await send_notification(test_request, background_tasks)
        
        return {
            "status": "test_sent",
            "channel_type": channel_type,
            "notification_id": status.notification_id
        }
        
    except Exception as e:
        logger.error(f"❌ Test channel failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test channel failed: {str(e)}")

# WebSocket for real-time notification updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time notification updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic status updates
            await asyncio.sleep(10)
            
            try:
                # Get current statistics
                stats = {
                    "type": "notification_stats",
                    "data": {
                        "total_notifications": len(notification_service.notification_status),
                        "pending_notifications": len([s for s in notification_service.notification_status.values() if s.status == "pending"]),
                        "failed_notifications": len([s for s in notification_service.notification_status.values() if s.status == "failed"]),
                        "active_channels": len([c for c in notification_service.channels.values() if c.enabled]),
                        "is_processing": notification_service.is_processing
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send_text(json.dumps(stats))
                
            except Exception as e:
                logger.error(f"❌ WebSocket update failed: {e}")
                break
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)