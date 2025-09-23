"""
Performance Optimization Framework for Mirai Trading System
Advanced performance enhancements: connection pooling, caching, async optimization
"""

import asyncio
import aiohttp
import aioredis
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
import weakref
from contextlib import asynccontextmanager
import hashlib
import pickle
import psutil
import os
from functools import wraps, lru_cache


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    timestamp: datetime
    operation: str
    duration: float
    memory_usage: float
    cpu_usage: float
    cache_hit_rate: float = 0.0
    connection_pool_size: int = 0
    active_connections: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'operation': self.operation,
            'duration': self.duration,
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage,
            'cache_hit_rate': self.cache_hit_rate,
            'connection_pool_size': self.connection_pool_size,
            'active_connections': self.active_connections
        }


class ConnectionPoolManager:
    """
    Advanced connection pooling for external APIs and databases
    """
    
    def __init__(self, max_connections: int = 100, max_keepalive_connections: int = 20):
        self.max_connections = max_connections
        self.max_keepalive_connections = max_keepalive_connections
        self.logger = logging.getLogger(__name__)
        
        # HTTP connection pools
        self.http_pools: Dict[str, aiohttp.ClientSession] = {}
        self.pool_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'active_connections': 0,
            'total_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'created_at': datetime.now()
        })
        
        # Database connection pools
        self.db_pools: Dict[str, List[Any]] = defaultdict(list)
        self.db_pool_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        
        # Redis connection pool
        self.redis_pool: Optional[aioredis.ConnectionPool] = None
        
        # WebSocket connection pool
        self.websocket_pools: Dict[str, List[Any]] = defaultdict(list)
        
        self._monitor_task: Optional[asyncio.Task] = None
        self._start_monitoring()
    
    async def get_http_session(self, pool_name: str = "default") -> aiohttp.ClientSession:
        """Get or create HTTP session with connection pooling"""
        if pool_name not in self.http_pools:
            # Create new session with optimized settings
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=20,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
                use_dns_cache=True,
                ttl_dns_cache=300
            )
            
            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'Mirai-Trading-Bot/1.0'}
            )
            
            self.http_pools[pool_name] = session
            self.pool_stats[pool_name]['created_at'] = datetime.now()
            
            self.logger.info(f"Created HTTP pool: {pool_name}")
        
        return self.http_pools[pool_name]
    
    async def make_http_request(self, method: str, url: str, 
                              pool_name: str = "default", **kwargs) -> aiohttp.ClientResponse:
        """Make HTTP request with connection pooling and performance tracking"""
        start_time = time.time()
        session = await self.get_http_session(pool_name)
        
        try:
            self.pool_stats[pool_name]['active_connections'] += 1
            
            async with session.request(method, url, **kwargs) as response:
                self.pool_stats[pool_name]['total_requests'] += 1
                
                duration = time.time() - start_time
                
                # Update average response time
                current_avg = self.pool_stats[pool_name]['avg_response_time']
                total_requests = self.pool_stats[pool_name]['total_requests']
                self.pool_stats[pool_name]['avg_response_time'] = (
                    (current_avg * (total_requests - 1) + duration) / total_requests
                )
                
                return response
        
        except Exception as e:
            self.pool_stats[pool_name]['failed_requests'] += 1
            raise
        finally:
            self.pool_stats[pool_name]['active_connections'] -= 1
    
    async def get_redis_connection(self) -> aioredis.Redis:
        """Get Redis connection from pool"""
        if not self.redis_pool:
            self.redis_pool = aioredis.ConnectionPool.from_url(
                "redis://localhost:6379",
                max_connections=20,
                retry_on_timeout=True,
                decode_responses=True
            )
        
        return aioredis.Redis(connection_pool=self.redis_pool)
    
    @asynccontextmanager
    async def get_db_connection(self, db_name: str = "default"):
        """Get database connection from pool"""
        async with self.db_pool_locks[db_name]:
            if self.db_pools[db_name]:
                # Reuse existing connection
                connection = self.db_pools[db_name].pop()
            else:
                # Create new connection (mock for now)
                connection = {"created_at": datetime.now(), "id": id(object())}
            
            try:
                yield connection
            finally:
                # Return connection to pool
                if len(self.db_pools[db_name]) < self.max_keepalive_connections:
                    self.db_pools[db_name].append(connection)
    
    def _start_monitoring(self):
        """Start background monitoring of connection pools"""
        async def monitor():
            while True:
                try:
                    await self._monitor_pools()
                    await asyncio.sleep(60)  # Monitor every minute
                except Exception as e:
                    self.logger.error(f"Pool monitoring failed: {e}")
                    await asyncio.sleep(60)
        
        self._monitor_task = asyncio.create_task(monitor())
    
    async def _monitor_pools(self):
        """Monitor pool health and performance"""
        for pool_name, stats in self.pool_stats.items():
            failure_rate = 0
            if stats['total_requests'] > 0:
                failure_rate = stats['failed_requests'] / stats['total_requests']
            
            # Log warnings for high failure rates
            if failure_rate > 0.1:  # 10% failure rate
                self.logger.warning(
                    f"High failure rate in pool {pool_name}: {failure_rate:.2%}"
                )
            
            # Log slow average response times
            if stats['avg_response_time'] > 5.0:  # 5 seconds
                self.logger.warning(
                    f"Slow response times in pool {pool_name}: {stats['avg_response_time']:.2f}s"
                )
    
    async def close_all_pools(self):
        """Close all connection pools"""
        # Close HTTP sessions
        for pool_name, session in self.http_pools.items():
            await session.close()
            self.logger.info(f"Closed HTTP pool: {pool_name}")
        
        # Close Redis pool
        if self.redis_pool:
            await self.redis_pool.disconnect()
        
        # Cancel monitoring
        if self._monitor_task:
            self._monitor_task.cancel()
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            'http_pools': dict(self.pool_stats),
            'db_pools': {name: len(pool) for name, pool in self.db_pools.items()},
            'redis_pool_size': self.redis_pool.max_connections if self.redis_pool else 0
        }


class AdvancedCache:
    """
    Multi-level caching system with TTL, LRU, and intelligent invalidation
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.logger = logging.getLogger(__name__)
        
        # In-memory cache (L1)
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'memory_usage': 0
        }
        
        # Cache configuration
        self.max_memory_items = 10000
        self.default_ttl = 300  # 5 minutes
        
        # Redis connection
        self.redis: Optional[aioredis.Redis] = None
        
        # Cache invalidation tracking
        self.invalidation_patterns: Dict[str, List[str]] = defaultdict(list)
        
        # Performance tracking
        self.access_times: deque = deque(maxlen=1000)
    
    async def _get_redis(self) -> aioredis.Redis:
        """Get Redis connection"""
        if not self.redis:
            self.redis = await aioredis.from_url(self.redis_url)
        return self.redis
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # Hash complex objects
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
        
        # Add keyword arguments
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        return ":".join(key_parts)
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache (L1 memory -> L2 Redis)"""
        start_time = time.time()
        
        # Try L1 cache (memory)
        if key in self.memory_cache:
            cache_entry = self.memory_cache[key]
            if cache_entry['expires_at'] > datetime.now():
                self.cache_stats['hits'] += 1
                self.access_times.append(time.time() - start_time)
                return cache_entry['value']
            else:
                # Expired, remove from memory
                del self.memory_cache[key]
        
        # Try L2 cache (Redis)
        try:
            redis = await self._get_redis()
            cached_data = await redis.get(key)
            
            if cached_data:
                value = pickle.loads(cached_data)
                
                # Store in L1 cache for faster access
                await self._store_memory_cache(key, value, self.default_ttl)
                
                self.cache_stats['hits'] += 1
                self.access_times.append(time.time() - start_time)
                return value
        
        except Exception as e:
            self.logger.warning(f"Redis cache get failed: {e}")
        
        # Cache miss
        self.cache_stats['misses'] += 1
        self.access_times.append(time.time() - start_time)
        return default
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache (both L1 and L2)"""
        ttl = ttl or self.default_ttl
        
        try:
            # Store in L1 cache (memory)
            await self._store_memory_cache(key, value, ttl)
            
            # Store in L2 cache (Redis)
            redis = await self._get_redis()
            serialized_value = pickle.dumps(value)
            await redis.setex(key, ttl, serialized_value)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Cache set failed: {e}")
            return False
    
    async def _store_memory_cache(self, key: str, value: Any, ttl: int):
        """Store value in L1 memory cache"""
        # Check memory limits
        if len(self.memory_cache) >= self.max_memory_items:
            await self._evict_memory_cache()
        
        self.memory_cache[key] = {
            'value': value,
            'expires_at': datetime.now() + timedelta(seconds=ttl),
            'created_at': datetime.now()
        }
    
    async def _evict_memory_cache(self):
        """Evict old items from memory cache (LRU)"""
        # Sort by creation time and remove oldest 10%
        items_to_remove = len(self.memory_cache) // 10
        
        sorted_items = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1]['created_at']
        )
        
        for key, _ in sorted_items[:items_to_remove]:
            del self.memory_cache[key]
            self.cache_stats['evictions'] += 1
    
    async def invalidate(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        try:
            # Invalidate memory cache
            keys_to_remove = [
                key for key in self.memory_cache.keys() 
                if pattern in key
            ]
            
            for key in keys_to_remove:
                del self.memory_cache[key]
            
            # Invalidate Redis cache
            redis = await self._get_redis()
            keys = await redis.keys(f"*{pattern}*")
            if keys:
                await redis.delete(*keys)
            
            self.logger.info(f"Invalidated {len(keys_to_remove)} memory + {len(keys)} Redis keys")
        
        except Exception as e:
            self.logger.error(f"Cache invalidation failed: {e}")
    
    def register_invalidation_pattern(self, cache_key_pattern: str, invalidation_triggers: List[str]):
        """Register automatic cache invalidation patterns"""
        self.invalidation_patterns[cache_key_pattern] = invalidation_triggers
    
    async def trigger_invalidation(self, trigger: str):
        """Trigger cache invalidation based on registered patterns"""
        for pattern, triggers in self.invalidation_patterns.items():
            if trigger in triggers:
                await self.invalidate(pattern)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0
        
        avg_access_time = sum(self.access_times) / len(self.access_times) if self.access_times else 0
        
        return {
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions'],
            'memory_items': len(self.memory_cache),
            'avg_access_time_ms': avg_access_time * 1000
        }


def cached(ttl: int = 300, cache_key_prefix: str = None):
    """
    Decorator for caching function results
    """
    def decorator(func: Callable) -> Callable:
        cache_prefix = cache_key_prefix or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = advanced_cache._generate_cache_key(cache_prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await advanced_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await advanced_cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


class AsyncTaskManager:
    """
    Advanced async task management with priority queues and resource limits
    """
    
    def __init__(self, max_concurrent_tasks: int = 100):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.logger = logging.getLogger(__name__)
        
        # Task queues by priority
        self.high_priority_queue: asyncio.Queue = asyncio.Queue()
        self.normal_priority_queue: asyncio.Queue = asyncio.Queue()
        self.low_priority_queue: asyncio.Queue = asyncio.Queue()
        
        # Task tracking
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: deque = deque(maxlen=1000)
        self.failed_tasks: deque = deque(maxlen=100)
        
        # Resource tracking
        self.task_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        
        # Performance metrics
        self.task_metrics: Dict[str, List[float]] = defaultdict(list)
        
        # Start task processor
        self._processor_task = asyncio.create_task(self._process_tasks())
    
    async def submit_task(self, coro, priority: str = "normal", 
                         task_id: Optional[str] = None) -> str:
        """Submit async task with priority"""
        task_id = task_id or f"task_{int(time.time() * 1000000)}"
        
        task_item = {
            'id': task_id,
            'coro': coro,
            'submitted_at': time.time(),
            'priority': priority
        }
        
        if priority == "high":
            await self.high_priority_queue.put(task_item)
        elif priority == "low":
            await self.low_priority_queue.put(task_item)
        else:
            await self.normal_priority_queue.put(task_item)
        
        self.logger.debug(f"Submitted task {task_id} with priority {priority}")
        return task_id
    
    async def _process_tasks(self):
        """Process tasks from priority queues"""
        while True:
            try:
                # Get next task (prioritized)
                task_item = await self._get_next_task()
                
                if task_item:
                    # Wait for semaphore (rate limiting)
                    await self.task_semaphore.acquire()
                    
                    # Execute task
                    task = asyncio.create_task(
                        self._execute_task_with_tracking(task_item)
                    )
                    
                    self.active_tasks[task_item['id']] = task
            
            except Exception as e:
                self.logger.error(f"Task processor error: {e}")
                await asyncio.sleep(1)
    
    async def _get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get next task from priority queues"""
        # Try high priority first
        try:
            return self.high_priority_queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        
        # Try normal priority
        try:
            return self.normal_priority_queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        
        # Try low priority
        try:
            return self.low_priority_queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        
        # Wait for any task
        done, _ = await asyncio.wait([
            asyncio.create_task(self.high_priority_queue.get()),
            asyncio.create_task(self.normal_priority_queue.get()),
            asyncio.create_task(self.low_priority_queue.get())
        ], return_when=asyncio.FIRST_COMPLETED)
        
        for task in done:
            return task.result()
        
        return None
    
    async def _execute_task_with_tracking(self, task_item: Dict[str, Any]):
        """Execute task with performance tracking"""
        task_id = task_item['id']
        start_time = time.time()
        
        try:
            # Execute the coroutine
            result = await task_item['coro']
            
            # Track success
            duration = time.time() - start_time
            self.task_metrics[task_item['priority']].append(duration)
            
            self.completed_tasks.append({
                'id': task_id,
                'duration': duration,
                'completed_at': time.time(),
                'success': True
            })
            
            self.logger.debug(f"Task {task_id} completed in {duration:.3f}s")
            
        except Exception as e:
            # Track failure
            duration = time.time() - start_time
            
            self.failed_tasks.append({
                'id': task_id,
                'duration': duration,
                'failed_at': time.time(),
                'error': str(e)
            })
            
            self.logger.error(f"Task {task_id} failed after {duration:.3f}s: {e}")
        
        finally:
            # Clean up
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            self.task_semaphore.release()
    
    def get_task_stats(self) -> Dict[str, Any]:
        """Get task management statistics"""
        total_completed = len(self.completed_tasks)
        total_failed = len(self.failed_tasks)
        
        # Calculate average durations by priority
        avg_durations = {}
        for priority, durations in self.task_metrics.items():
            if durations:
                avg_durations[priority] = sum(durations) / len(durations)
        
        return {
            'active_tasks': len(self.active_tasks),
            'completed_tasks': total_completed,
            'failed_tasks': total_failed,
            'success_rate': total_completed / (total_completed + total_failed) if (total_completed + total_failed) > 0 else 1.0,
            'avg_duration_by_priority': avg_durations,
            'queue_sizes': {
                'high': self.high_priority_queue.qsize(),
                'normal': self.normal_priority_queue.qsize(),
                'low': self.low_priority_queue.qsize()
            }
        }


class PerformanceProfiler:
    """
    Advanced performance profiling and optimization recommendations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_history: deque = deque(maxlen=10000)
        self.slow_operations: deque = deque(maxlen=100)
        self.memory_snapshots: deque = deque(maxlen=1000)
        
        # Start background monitoring
        self._monitor_task = asyncio.create_task(self._background_monitoring())
    
    def profile_function(self, operation_name: str):
        """Decorator for profiling function performance"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await self._profile_execution(operation_name, func, *args, **kwargs)
            return wrapper
        return decorator
    
    async def _profile_execution(self, operation_name: str, func: Callable, *args, **kwargs):
        """Profile function execution"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        start_cpu = psutil.cpu_percent()
        
        try:
            result = await func(*args, **kwargs)
            
            duration = time.time() - start_time
            end_memory = self._get_memory_usage()
            end_cpu = psutil.cpu_percent()
            
            # Record metrics
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                operation=operation_name,
                duration=duration,
                memory_usage=end_memory - start_memory,
                cpu_usage=end_cpu - start_cpu
            )
            
            self.metrics_history.append(metrics)
            
            # Track slow operations
            if duration > 1.0:  # Operations taking more than 1 second
                self.slow_operations.append({
                    'operation': operation_name,
                    'duration': duration,
                    'timestamp': datetime.now(),
                    'args_summary': str(args)[:100] if args else None
                })
            
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Profiled operation {operation_name} failed after {duration:.3f}s: {e}")
            raise
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    async def _background_monitoring(self):
        """Background monitoring of system performance"""
        while True:
            try:
                # Take memory snapshot
                memory_usage = self._get_memory_usage()
                cpu_usage = psutil.cpu_percent(interval=1)
                
                self.memory_snapshots.append({
                    'timestamp': datetime.now(),
                    'memory_mb': memory_usage,
                    'cpu_percent': cpu_usage
                })
                
                # Check for memory leaks
                if len(self.memory_snapshots) > 100:
                    await self._check_memory_trends()
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
            
            except Exception as e:
                self.logger.error(f"Background monitoring failed: {e}")
                await asyncio.sleep(60)
    
    async def _check_memory_trends(self):
        """Check for memory usage trends and leaks"""
        if len(self.memory_snapshots) < 50:
            return
        
        recent_snapshots = list(self.memory_snapshots)[-50:]
        memory_values = [s['memory_mb'] for s in recent_snapshots]
        
        # Simple trend analysis
        first_half = memory_values[:25]
        second_half = memory_values[25:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        memory_increase = avg_second - avg_first
        
        if memory_increase > 50:  # More than 50MB increase
            self.logger.warning(f"Potential memory leak detected: {memory_increase:.1f}MB increase")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.metrics_history:
            return {"error": "No performance data available"}
        
        # Analyze metrics
        durations = [m.duration for m in self.metrics_history]
        memory_usages = [m.memory_usage for m in self.metrics_history]
        
        # Group by operation
        operation_stats = defaultdict(list)
        for metric in self.metrics_history:
            operation_stats[metric.operation].append(metric.duration)
        
        # Calculate statistics
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        p95_duration = sorted(durations)[int(len(durations) * 0.95)] if durations else 0
        
        avg_memory = sum(memory_usages) / len(memory_usages)
        
        # Operation-specific stats
        operation_summary = {}
        for operation, times in operation_stats.items():
            operation_summary[operation] = {
                'count': len(times),
                'avg_duration': sum(times) / len(times),
                'max_duration': max(times),
                'min_duration': min(times)
            }
        
        # Recent slow operations
        recent_slow = list(self.slow_operations)[-10:]
        
        report = {
            'overall_stats': {
                'avg_duration': avg_duration,
                'max_duration': max_duration,
                'p95_duration': p95_duration,
                'avg_memory_usage': avg_memory,
                'total_operations': len(self.metrics_history)
            },
            'operation_breakdown': operation_summary,
            'recent_slow_operations': recent_slow,
            'recommendations': self._generate_recommendations(operation_summary, recent_slow)
        }
        
        return report
    
    def _generate_recommendations(self, operation_stats: Dict, slow_ops: List) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Check for consistently slow operations
        for operation, stats in operation_stats.items():
            if stats['avg_duration'] > 2.0:
                recommendations.append(f"Optimize {operation}: avg {stats['avg_duration']:.2f}s")
        
        # Check for frequent slow operations
        slow_operations_count = defaultdict(int)
        for slow_op in slow_ops:
            slow_operations_count[slow_op['operation']] += 1
        
        for operation, count in slow_operations_count.items():
            if count > 3:
                recommendations.append(f"Frequent slow operation: {operation} ({count} times)")
        
        # Memory recommendations
        if len(self.memory_snapshots) > 10:
            recent_memory = [s['memory_mb'] for s in list(self.memory_snapshots)[-10:]]
            if max(recent_memory) > 500:
                recommendations.append("High memory usage detected - consider optimization")
        
        if not recommendations:
            recommendations.append("Performance looks good!")
        
        return recommendations


# Global instances
connection_pool_manager = ConnectionPoolManager()
advanced_cache = AdvancedCache()
task_manager = AsyncTaskManager()
performance_profiler = PerformanceProfiler()


# Convenience decorators and functions
def performance_optimized(operation_name: str, cache_ttl: int = 300):
    """
    Decorator combining caching and performance profiling
    """
    def decorator(func: Callable) -> Callable:
        # Apply profiling
        profiled_func = performance_profiler.profile_function(operation_name)(func)
        # Apply caching
        cached_func = cached(ttl=cache_ttl, cache_key_prefix=operation_name)(profiled_func)
        return cached_func
    return decorator


async def get_performance_summary() -> Dict[str, Any]:
    """Get comprehensive performance summary"""
    return {
        'connection_pools': connection_pool_manager.get_pool_stats(),
        'cache_performance': advanced_cache.get_cache_stats(),
        'task_management': task_manager.get_task_stats(),
        'profiling_report': performance_profiler.get_performance_report()
    }


async def initialize_performance_system():
    """Initialize performance optimization system"""
    # Setup cache invalidation patterns
    advanced_cache.register_invalidation_pattern(
        "market_data", ["price_update", "market_close"]
    )
    advanced_cache.register_invalidation_pattern(
        "portfolio", ["trade_executed", "position_update"]
    )
    
    # Create HTTP pools for different services
    await connection_pool_manager.get_http_session("binance_api")
    await connection_pool_manager.get_http_session("market_data")
    await connection_pool_manager.get_http_session("external_api")
    
    logging.getLogger(__name__).info("Performance optimization system initialized")


async def cleanup_performance_system():
    """Cleanup performance system resources"""
    await connection_pool_manager.close_all_pools()
    
    if advanced_cache.redis:
        await advanced_cache.redis.close()
    
    if task_manager._processor_task:
        task_manager._processor_task.cancel()
    
    if performance_profiler._monitor_task:
        performance_profiler._monitor_task.cancel()


# Example usage patterns
@performance_optimized("fetch_market_data", cache_ttl=60)
async def fetch_market_data_optimized(symbol: str):
    """Example optimized market data fetching"""
    session = await connection_pool_manager.get_http_session("market_data")
    async with session.get(f"https://api.example.com/ticker/{symbol}") as response:
        return await response.json()


@cached(ttl=300, cache_key_prefix="portfolio_summary")
async def get_portfolio_summary_cached(user_id: str):
    """Example cached portfolio summary"""
    # Expensive portfolio calculation here
    return {"user_id": user_id, "total_value": 10000, "positions": []}


async def submit_background_task(task_func, priority: str = "normal"):
    """Submit background task with priority"""
    return await task_manager.submit_task(task_func(), priority=priority)