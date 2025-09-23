"""
Enterprise Security Framework for Mirai Trading System
Advanced security features: secrets rotation, audit logging, encryption
"""

import os
import json
import logging
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiofiles
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import sqlite3
import threading
from contextlib import contextmanager


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    TRADE_EXECUTED = "trade_executed"
    TRADE_CANCELLED = "trade_cancelled"
    API_KEY_USED = "api_key_used"
    CONFIG_CHANGED = "config_changed"
    ERROR_OCCURRED = "error_occurred"
    SECURITY_VIOLATION = "security_violation"
    DATA_ACCESS = "data_access"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"


@dataclass
class AuditEvent:
    event_id: str
    timestamp: datetime
    event_type: EventType
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource: str
    action: str
    details: Dict[str, Any]
    security_level: SecurityLevel
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'resource': self.resource,
            'action': self.action,
            'details': self.details,
            'security_level': self.security_level.value,
            'success': self.success,
            'error_message': self.error_message
        }


class EncryptionManager:
    """
    Advanced encryption for sensitive data at rest and in transit
    """
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or self._generate_master_key()
        self.fernet = self._create_fernet_instance()
        self.logger = logging.getLogger(__name__)
    
    def _generate_master_key(self) -> str:
        """Generate a new master encryption key"""
        return Fernet.generate_key().decode()
    
    def _create_fernet_instance(self) -> Fernet:
        """Create Fernet encryption instance"""
        if isinstance(self.master_key, str):
            key_bytes = self.master_key.encode()
        else:
            key_bytes = self.master_key
            
        return Fernet(key_bytes)
    
    def encrypt_data(self, data: Union[str, Dict, List]) -> str:
        """Encrypt sensitive data"""
        try:
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data)
            else:
                data_str = str(data)
            
            encrypted = self.fernet.encrypt(data_str.encode())
            return base64.b64encode(encrypted).decode()
        
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> Union[str, Dict, List]:
        """Decrypt sensitive data"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            data_str = decrypted.decode()
            
            # Try to parse as JSON
            try:
                return json.loads(data_str)
            except json.JSONDecodeError:
                return data_str
        
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """Encrypt a file"""
        output_path = output_path or f"{file_path}.encrypted"
        
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            encrypted_data = self.fernet.encrypt(file_data)
            
            with open(output_path, 'wb') as encrypted_file:
                encrypted_file.write(encrypted_data)
            
            return output_path
        
        except Exception as e:
            self.logger.error(f"File encryption failed: {e}")
            raise
    
    def decrypt_file(self, encrypted_file_path: str, output_path: Optional[str] = None) -> str:
        """Decrypt a file"""
        output_path = output_path or encrypted_file_path.replace('.encrypted', '')
        
        try:
            with open(encrypted_file_path, 'rb') as encrypted_file:
                encrypted_data = encrypted_file.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as file:
                file.write(decrypted_data)
            
            return output_path
        
        except Exception as e:
            self.logger.error(f"File decryption failed: {e}")
            raise


class SecretsManager:
    """
    Advanced secrets management with rotation and versioning
    """
    
    def __init__(self, storage_path: str = "state/secrets.db"):
        self.storage_path = storage_path
        self.encryption = EncryptionManager()
        self.logger = logging.getLogger(__name__)
        self._init_storage()
        self._rotation_schedule: Dict[str, timedelta] = {}
    
    def _init_storage(self):
        """Initialize secure storage for secrets"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        with sqlite3.connect(self.storage_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS secrets (
                    id TEXT PRIMARY KEY,
                    encrypted_value TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    rotation_interval INTEGER,
                    last_rotated_at TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS secret_history (
                    id TEXT,
                    version INTEGER,
                    encrypted_value TEXT,
                    created_at TIMESTAMP,
                    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id, version)
                )
            """)
    
    def store_secret(self, secret_id: str, secret_value: str, 
                    rotation_interval: Optional[timedelta] = None,
                    metadata: Optional[Dict] = None) -> bool:
        """Store a secret with encryption and versioning"""
        try:
            encrypted_value = self.encryption.encrypt_data(secret_value)
            
            with sqlite3.connect(self.storage_path) as conn:
                # Get current version
                cursor = conn.execute(
                    "SELECT version FROM secrets WHERE id = ?", (secret_id,)
                )
                result = cursor.fetchone()
                new_version = (result[0] + 1) if result else 1
                
                # Store old version in history if exists
                if result:
                    conn.execute("""
                        INSERT INTO secret_history (id, version, encrypted_value, created_at)
                        SELECT id, version, encrypted_value, created_at 
                        FROM secrets WHERE id = ?
                    """, (secret_id,))
                
                # Calculate expiration
                expires_at = None
                if rotation_interval:
                    expires_at = datetime.now() + rotation_interval
                
                # Store new version
                conn.execute("""
                    INSERT OR REPLACE INTO secrets 
                    (id, encrypted_value, version, expires_at, rotation_interval, 
                     last_rotated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    secret_id, encrypted_value, new_version, expires_at,
                    rotation_interval.total_seconds() if rotation_interval else None,
                    datetime.now(), json.dumps(metadata or {})
                ))
            
            self.logger.info(f"Secret stored: {secret_id} (version {new_version})")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to store secret {secret_id}: {e}")
            return False
    
    def get_secret(self, secret_id: str, version: Optional[int] = None) -> Optional[str]:
        """Retrieve and decrypt a secret"""
        try:
            with sqlite3.connect(self.storage_path) as conn:
                if version:
                    # Get specific version from history
                    cursor = conn.execute(
                        "SELECT encrypted_value FROM secret_history WHERE id = ? AND version = ?",
                        (secret_id, version)
                    )
                else:
                    # Get current version
                    cursor = conn.execute(
                        "SELECT encrypted_value FROM secrets WHERE id = ?",
                        (secret_id,)
                    )
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                decrypted_value = self.encryption.decrypt_data(result[0])
                return decrypted_value
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve secret {secret_id}: {e}")
            return None
    
    def rotate_secret(self, secret_id: str, new_value: str) -> bool:
        """Rotate a secret to a new value"""
        try:
            # Get current secret metadata
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.execute(
                    "SELECT rotation_interval, metadata FROM secrets WHERE id = ?",
                    (secret_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    self.logger.warning(f"Secret {secret_id} not found for rotation")
                    return False
                
                rotation_interval_seconds, metadata_json = result
                rotation_interval = timedelta(seconds=rotation_interval_seconds) if rotation_interval_seconds else None
                metadata = json.loads(metadata_json) if metadata_json else {}
            
            # Store new version
            return self.store_secret(secret_id, new_value, rotation_interval, metadata)
        
        except Exception as e:
            self.logger.error(f"Failed to rotate secret {secret_id}: {e}")
            return False
    
    def check_expiring_secrets(self) -> List[str]:
        """Check for secrets that need rotation"""
        try:
            expiring_secrets = []
            
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.execute("""
                    SELECT id, expires_at FROM secrets 
                    WHERE expires_at IS NOT NULL AND expires_at <= ?
                """, (datetime.now(),))
                
                for secret_id, expires_at in cursor.fetchall():
                    expiring_secrets.append(secret_id)
            
            return expiring_secrets
        
        except Exception as e:
            self.logger.error(f"Failed to check expiring secrets: {e}")
            return []
    
    async def auto_rotate_secrets(self):
        """Automatically rotate expired secrets"""
        expiring_secrets = self.check_expiring_secrets()
        
        for secret_id in expiring_secrets:
            try:
                # Generate new value (this would be customized per secret type)
                new_value = self._generate_new_secret_value(secret_id)
                
                if new_value:
                    success = self.rotate_secret(secret_id, new_value)
                    if success:
                        self.logger.info(f"Auto-rotated secret: {secret_id}")
                    else:
                        self.logger.error(f"Failed to auto-rotate secret: {secret_id}")
            
            except Exception as e:
                self.logger.error(f"Auto-rotation failed for {secret_id}: {e}")
    
    def _generate_new_secret_value(self, secret_id: str) -> Optional[str]:
        """Generate new secret value based on secret type"""
        # This would be customized based on the type of secret
        if 'api_key' in secret_id.lower():
            return secrets.token_urlsafe(32)
        elif 'password' in secret_id.lower():
            return secrets.token_urlsafe(16)
        elif 'token' in secret_id.lower():
            return secrets.token_hex(32)
        else:
            return secrets.token_urlsafe(24)


class AuditLogger:
    """
    Comprehensive audit logging for compliance and security
    """
    
    def __init__(self, log_file: str = "logs/audit.log", 
                 db_file: str = "state/audit.db"):
        self.log_file = log_file
        self.db_file = db_file
        self.encryption = EncryptionManager()
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._init_storage()
    
    def _init_storage(self):
        """Initialize audit log storage"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TIMESTAMP,
                    event_type TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    resource TEXT,
                    action TEXT,
                    encrypted_details TEXT,
                    security_level TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    hash_chain TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                ON audit_events(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_user 
                ON audit_events(user_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_event_type 
                ON audit_events(event_type)
            """)
    
    def log_event(self, event: AuditEvent) -> bool:
        """Log an audit event with encryption and integrity protection"""
        try:
            with self._lock:
                # Encrypt sensitive details
                encrypted_details = self.encryption.encrypt_data(event.details)
                
                # Calculate hash chain for integrity
                hash_chain = self._calculate_hash_chain(event)
                
                # Store in database
                with sqlite3.connect(self.db_file) as conn:
                    conn.execute("""
                        INSERT INTO audit_events 
                        (event_id, timestamp, event_type, user_id, session_id, 
                         ip_address, user_agent, resource, action, encrypted_details,
                         security_level, success, error_message, hash_chain)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event.event_id, event.timestamp, event.event_type.value,
                        event.user_id, event.session_id, event.ip_address,
                        event.user_agent, event.resource, event.action,
                        encrypted_details, event.security_level.value,
                        event.success, event.error_message, hash_chain
                    ))
                
                # Also write to log file
                self._write_to_log_file(event)
                
                return True
        
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
            return False
    
    def _calculate_hash_chain(self, event: AuditEvent) -> str:
        """Calculate hash chain for audit event integrity"""
        try:
            # Get last hash from database
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.execute(
                    "SELECT hash_chain FROM audit_events ORDER BY timestamp DESC LIMIT 1"
                )
                result = cursor.fetchone()
                previous_hash = result[0] if result else "genesis"
            
            # Create hash of current event + previous hash
            event_data = f"{event.event_id}{event.timestamp}{event.event_type.value}{previous_hash}"
            return hashlib.sha256(event_data.encode()).hexdigest()
        
        except Exception as e:
            self.logger.error(f"Hash chain calculation failed: {e}")
            return "error"
    
    def _write_to_log_file(self, event: AuditEvent):
        """Write audit event to log file"""
        try:
            log_entry = {
                'timestamp': event.timestamp.isoformat(),
                'event_id': event.event_id,
                'type': event.event_type.value,
                'user': event.user_id,
                'resource': event.resource,
                'action': event.action,
                'success': event.success,
                'security_level': event.security_level.value
            }
            
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        
        except Exception as e:
            self.logger.error(f"Failed to write to log file: {e}")
    
    def query_events(self, start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None,
                    event_type: Optional[EventType] = None,
                    user_id: Optional[str] = None,
                    limit: int = 100) -> List[AuditEvent]:
        """Query audit events with filters"""
        try:
            query = "SELECT * FROM audit_events WHERE 1=1"
            params = []
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type.value)
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            events = []
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.execute(query, params)
                
                for row in cursor.fetchall():
                    # Decrypt details
                    try:
                        details = self.encryption.decrypt_data(row[9])
                    except:
                        details = {}
                    
                    event = AuditEvent(
                        event_id=row[0],
                        timestamp=datetime.fromisoformat(row[1]),
                        event_type=EventType(row[2]),
                        user_id=row[3],
                        session_id=row[4],
                        ip_address=row[5],
                        user_agent=row[6],
                        resource=row[7],
                        action=row[8],
                        details=details,
                        security_level=SecurityLevel(row[10]),
                        success=bool(row[11]),
                        error_message=row[12]
                    )
                    events.append(event)
            
            return events
        
        except Exception as e:
            self.logger.error(f"Failed to query audit events: {e}")
            return []
    
    def verify_integrity(self, start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> bool:
        """Verify audit log integrity using hash chain"""
        try:
            query = "SELECT event_id, timestamp, event_type, hash_chain FROM audit_events"
            params = []
            
            if start_time:
                query += " WHERE timestamp >= ?"
                params.append(start_time)
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time)
            elif end_time:
                query += " WHERE timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp ASC"
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.execute(query, params)
                
                previous_hash = "genesis"
                for row in cursor.fetchall():
                    event_id, timestamp, event_type, stored_hash = row
                    
                    # Recalculate expected hash
                    event_data = f"{event_id}{timestamp}{event_type}{previous_hash}"
                    expected_hash = hashlib.sha256(event_data.encode()).hexdigest()
                    
                    if stored_hash != expected_hash and stored_hash != "error":
                        self.logger.warning(f"Integrity violation detected at event {event_id}")
                        return False
                    
                    previous_hash = stored_hash
            
            return True
        
        except Exception as e:
            self.logger.error(f"Integrity verification failed: {e}")
            return False


class SecurityManager:
    """
    Main security manager coordinating all security components
    """
    
    def __init__(self):
        self.secrets_manager = SecretsManager()
        self.audit_logger = AuditLogger()
        self.encryption_manager = EncryptionManager()
        self.logger = logging.getLogger(__name__)
        self._security_checks_enabled = True
    
    async def initialize_security(self):
        """Initialize security system"""
        # Log system start
        await self.log_security_event(
            event_type=EventType.SYSTEM_START,
            resource="security_manager",
            action="initialize",
            details={"component": "security_manager"},
            security_level=SecurityLevel.HIGH
        )
        
        # Start automated security tasks
        asyncio.create_task(self._automated_security_tasks())
    
    async def log_security_event(self, event_type: EventType, resource: str, 
                                action: str, details: Dict[str, Any],
                                security_level: SecurityLevel = SecurityLevel.MEDIUM,
                                user_id: Optional[str] = None,
                                session_id: Optional[str] = None,
                                success: bool = True,
                                error_message: Optional[str] = None):
        """Log a security event"""
        event = AuditEvent(
            event_id=secrets.token_hex(16),
            timestamp=datetime.now(),
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=None,  # Would be extracted from request
            user_agent=None,  # Would be extracted from request
            resource=resource,
            action=action,
            details=details,
            security_level=security_level,
            success=success,
            error_message=error_message
        )
        
        return self.audit_logger.log_event(event)
    
    async def rotate_trading_secrets(self):
        """Rotate trading-related secrets"""
        trading_secrets = [
            "binance_api_key",
            "binance_api_secret", 
            "jwt_secret",
            "telegram_bot_token"
        ]
        
        for secret_id in trading_secrets:
            try:
                # Check if secret needs rotation
                expiring = self.secrets_manager.check_expiring_secrets()
                if secret_id in expiring:
                    await self.secrets_manager.auto_rotate_secrets()
                    
                    await self.log_security_event(
                        event_type=EventType.CONFIG_CHANGED,
                        resource="secrets_manager",
                        action="secret_rotated",
                        details={"secret_id": secret_id},
                        security_level=SecurityLevel.HIGH
                    )
            
            except Exception as e:
                await self.log_security_event(
                    event_type=EventType.ERROR_OCCURRED,
                    resource="secrets_manager",
                    action="secret_rotation_failed",
                    details={"secret_id": secret_id, "error": str(e)},
                    security_level=SecurityLevel.HIGH,
                    success=False,
                    error_message=str(e)
                )
    
    async def _automated_security_tasks(self):
        """Run automated security tasks"""
        while self._security_checks_enabled:
            try:
                # Check for expiring secrets every hour
                await self.rotate_trading_secrets()
                
                # Verify audit log integrity daily
                if datetime.now().hour == 0:  # Run at midnight
                    integrity_ok = self.audit_logger.verify_integrity(
                        start_time=datetime.now() - timedelta(days=1)
                    )
                    
                    if not integrity_ok:
                        await self.log_security_event(
                            event_type=EventType.SECURITY_VIOLATION,
                            resource="audit_logger",
                            action="integrity_check_failed",
                            details={"check_date": datetime.now().isoformat()},
                            security_level=SecurityLevel.CRITICAL,
                            success=False
                        )
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                self.logger.error(f"Automated security task failed: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes on error
    
    def encrypt_sensitive_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive configuration values"""
        sensitive_keys = [
            'api_key', 'api_secret', 'password', 'token', 
            'private_key', 'secret', 'credential'
        ]
        
        encrypted_config = config.copy()
        
        for key, value in config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                encrypted_config[key] = self.encryption_manager.encrypt_data(str(value))
                encrypted_config[f"{key}_encrypted"] = True
        
        return encrypted_config
    
    def decrypt_sensitive_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive configuration values"""
        decrypted_config = config.copy()
        
        for key, value in config.items():
            if key.endswith('_encrypted') and value:
                original_key = key.replace('_encrypted', '')
                if original_key in config:
                    try:
                        decrypted_config[original_key] = self.encryption_manager.decrypt_data(config[original_key])
                        del decrypted_config[key]  # Remove encryption flag
                    except Exception as e:
                        self.logger.error(f"Failed to decrypt {original_key}: {e}")
        
        return decrypted_config
    
    async def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        try:
            # Get recent security events
            recent_events = self.audit_logger.query_events(
                start_time=datetime.now() - timedelta(days=7),
                limit=1000
            )
            
            # Analyze security metrics
            total_events = len(recent_events)
            security_violations = len([e for e in recent_events if e.event_type == EventType.SECURITY_VIOLATION])
            failed_events = len([e for e in recent_events if not e.success])
            
            # Check secret rotation status
            expiring_secrets = self.secrets_manager.check_expiring_secrets()
            
            # Verify audit integrity
            integrity_ok = self.audit_logger.verify_integrity(
                start_time=datetime.now() - timedelta(days=7)
            )
            
            report = {
                'report_generated': datetime.now().isoformat(),
                'audit_events': {
                    'total': total_events,
                    'security_violations': security_violations,
                    'failed_events': failed_events,
                    'integrity_verified': integrity_ok
                },
                'secrets_management': {
                    'expiring_secrets_count': len(expiring_secrets),
                    'expiring_secrets': expiring_secrets
                },
                'security_score': self._calculate_security_score(
                    total_events, security_violations, failed_events, 
                    len(expiring_secrets), integrity_ok
                ),
                'recommendations': self._generate_security_recommendations(
                    security_violations, failed_events, expiring_secrets, integrity_ok
                )
            }
            
            return report
        
        except Exception as e:
            self.logger.error(f"Failed to generate security report: {e}")
            return {'error': str(e)}
    
    def _calculate_security_score(self, total_events: int, violations: int, 
                                failures: int, expiring_secrets: int, 
                                integrity_ok: bool) -> float:
        """Calculate overall security score (0.0 to 1.0)"""
        score = 1.0
        
        # Penalize for violations
        if total_events > 0:
            violation_rate = violations / total_events
            score -= violation_rate * 0.4
            
            failure_rate = failures / total_events
            score -= failure_rate * 0.2
        
        # Penalize for expiring secrets
        if expiring_secrets > 0:
            score -= min(0.3, expiring_secrets * 0.1)
        
        # Penalize for integrity issues
        if not integrity_ok:
            score -= 0.5
        
        return max(0.0, score)
    
    def _generate_security_recommendations(self, violations: int, failures: int,
                                         expiring_secrets: int, integrity_ok: bool) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if violations > 0:
            recommendations.append(f"Investigate {violations} security violations")
        
        if failures > 10:
            recommendations.append(f"High failure rate detected ({failures} failures)")
        
        if expiring_secrets > 0:
            recommendations.append(f"Rotate {expiring_secrets} expiring secrets")
        
        if not integrity_ok:
            recommendations.append("Audit log integrity compromised - investigate immediately")
        
        if not recommendations:
            recommendations.append("Security posture looks good")
        
        return recommendations


# Global security manager instance
security_manager = SecurityManager()


async def initialize_security():
    """Initialize the security system"""
    await security_manager.initialize_security()


async def log_trade_execution(symbol: str, side: str, size: float, 
                            price: float, success: bool, 
                            user_id: Optional[str] = None):
    """Log trade execution event"""
    await security_manager.log_security_event(
        event_type=EventType.TRADE_EXECUTED,
        resource=f"trading/{symbol}",
        action=f"{side.lower()}_order",
        details={
            "symbol": symbol,
            "side": side,
            "size": size,
            "price": price
        },
        security_level=SecurityLevel.HIGH,
        user_id=user_id,
        success=success
    )


async def get_security_report() -> Dict[str, Any]:
    """Get comprehensive security report"""
    return await security_manager.generate_security_report()


def encrypt_sensitive_data(data: Union[str, Dict, List]) -> str:
    """Encrypt sensitive data"""
    return security_manager.encryption_manager.encrypt_data(data)


def decrypt_sensitive_data(encrypted_data: str) -> Union[str, Dict, List]:
    """Decrypt sensitive data"""
    return security_manager.encryption_manager.decrypt_data(encrypted_data)