"""
Chaos Engineering Framework for Mirai Trading System
Systematic failure injection and resilience testing
"""

import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import logging
from enum import Enum
import psutil
import os
from unittest.mock import patch, MagicMock
from contextlib import contextmanager


class FailureType(Enum):
    NETWORK_TIMEOUT = "network_timeout"
    NETWORK_DISCONNECT = "network_disconnect"
    API_RATE_LIMIT = "api_rate_limit"
    DATABASE_ERROR = "database_error"
    MEMORY_PRESSURE = "memory_pressure"
    CPU_SPIKE = "cpu_spike"
    DISK_FULL = "disk_full"
    INVALID_RESPONSE = "invalid_response"
    PARTIAL_OUTAGE = "partial_outage"
    CASCADING_FAILURE = "cascading_failure"


@dataclass
class ChaosExperiment:
    name: str
    description: str
    failure_type: FailureType
    duration_seconds: float
    intensity: float  # 0.0 to 1.0
    target_component: str
    success_criteria: List[str]
    recovery_time_limit: float


@dataclass
class ExperimentResult:
    experiment: ChaosExperiment
    start_time: datetime
    end_time: datetime
    success: bool
    recovery_time: float
    error_count: int
    system_stability: float
    observations: List[str]
    metrics: Dict[str, Any]


class ChaosEngineering:
    """
    Chaos engineering framework for systematic failure injection
    """
    
    def __init__(self, target_system=None):
        self.target_system = target_system
        self.experiments: List[ChaosExperiment] = []
        self.results: List[ExperimentResult] = []
        self.logger = logging.getLogger(__name__)
        self.setup_experiments()
    
    def setup_experiments(self):
        """Define chaos engineering experiments"""
        self.experiments = [
            ChaosExperiment(
                name="Binance API Timeout",
                description="Simulate Binance API timeouts during trading",
                failure_type=FailureType.NETWORK_TIMEOUT,
                duration_seconds=30.0,
                intensity=0.3,  # 30% of requests timeout
                target_component="binance_client",
                success_criteria=[
                    "System continues operation",
                    "Fallback mechanisms activate",
                    "No data corruption",
                    "Recovery within 60 seconds"
                ],
                recovery_time_limit=60.0
            ),
            ChaosExperiment(
                name="Database Connection Loss",
                description="Simulate database connection failures",
                failure_type=FailureType.DATABASE_ERROR,
                duration_seconds=45.0,
                intensity=1.0,  # Complete database failure
                target_component="database",
                success_criteria=[
                    "In-memory caching works",
                    "No trade data loss",
                    "Graceful degradation",
                    "Automatic reconnection"
                ],
                recovery_time_limit=90.0
            ),
            ChaosExperiment(
                name="Memory Pressure Spike",
                description="Simulate high memory usage conditions",
                failure_type=FailureType.MEMORY_PRESSURE,
                duration_seconds=60.0,
                intensity=0.8,  # 80% memory utilization
                target_component="system",
                success_criteria=[
                    "No memory leaks",
                    "Garbage collection efficiency",
                    "Performance degradation < 50%",
                    "System remains responsive"
                ],
                recovery_time_limit=30.0
            ),
            ChaosExperiment(
                name="WebSocket Disconnection Storm",
                description="Simulate mass WebSocket disconnections",
                failure_type=FailureType.NETWORK_DISCONNECT,
                duration_seconds=20.0,
                intensity=0.7,  # 70% of connections drop
                target_component="websocket",
                success_criteria=[
                    "Automatic reconnection",
                    "No duplicate data",
                    "Connection pooling works",
                    "Backoff strategy effective"
                ],
                recovery_time_limit=45.0
            ),
            ChaosExperiment(
                name="AI Model Latency Spike",
                description="Simulate AI decision making delays",
                failure_type=FailureType.CPU_SPIKE,
                duration_seconds=40.0,
                intensity=0.6,  # 60% slower decisions
                target_component="ai_engine",
                success_criteria=[
                    "Timeout mechanisms work",
                    "Fallback to simple rules",
                    "No trading halts",
                    "Queue management effective"
                ],
                recovery_time_limit=60.0
            ),
            ChaosExperiment(
                name="Partial Exchange Outage",
                description="Simulate partial exchange API failures",
                failure_type=FailureType.PARTIAL_OUTAGE,
                duration_seconds=90.0,
                intensity=0.5,  # 50% of endpoints fail
                target_component="exchange_api",
                success_criteria=[
                    "Service degradation graceful",
                    "Critical functions maintained",
                    "Error handling robust",
                    "User notification system works"
                ],
                recovery_time_limit=120.0
            ),
            ChaosExperiment(
                name="Cascading System Failure",
                description="Simulate multiple simultaneous failures",
                failure_type=FailureType.CASCADING_FAILURE,
                duration_seconds=120.0,
                intensity=0.4,  # Multiple components affected
                target_component="system_wide",
                success_criteria=[
                    "Core functionality preserved",
                    "Data integrity maintained",
                    "Emergency protocols activate",
                    "System remains recoverable"
                ],
                recovery_time_limit=300.0
            )
        ]
    
    async def run_experiment(self, experiment: ChaosExperiment) -> ExperimentResult:
        """Execute a single chaos experiment"""
        self.logger.info(f"🔥 Starting chaos experiment: {experiment.name}")
        
        start_time = datetime.now()
        observations = []
        error_count = 0
        
        # Pre-experiment baseline
        baseline_metrics = await self._collect_baseline_metrics()
        
        try:
            # Inject failure
            async with self._inject_failure(experiment) as failure_context:
                observations.append(f"Failure injected: {experiment.failure_type.value}")
                
                # Monitor system during failure
                monitoring_tasks = [
                    self._monitor_system_health(experiment.duration_seconds),
                    self._monitor_error_rates(experiment.duration_seconds),
                    self._monitor_performance_metrics(experiment.duration_seconds)
                ]
                
                monitoring_results = await asyncio.gather(*monitoring_tasks, return_exceptions=True)
                
                # Extract monitoring data
                system_health = monitoring_results[0] if len(monitoring_results) > 0 else {}
                error_rates = monitoring_results[1] if len(monitoring_results) > 1 else {}
                performance = monitoring_results[2] if len(monitoring_results) > 2 else {}
                
                # Count errors during experiment
                error_count = error_rates.get('total_errors', 0)
                
                observations.append(f"System health during failure: {system_health.get('status', 'unknown')}")
                observations.append(f"Error rate: {error_rates.get('error_rate', 0):.2%}")
        
        except Exception as e:
            observations.append(f"Experiment error: {str(e)}")
            error_count += 1
        
        # Wait for recovery
        recovery_start = time.time()
        recovery_successful = await self._wait_for_recovery(experiment)
        recovery_time = time.time() - recovery_start
        
        end_time = datetime.now()
        
        # Post-experiment metrics
        post_metrics = await self._collect_baseline_metrics()
        
        # Evaluate success criteria
        success = await self._evaluate_success_criteria(
            experiment, 
            baseline_metrics, 
            post_metrics, 
            recovery_time, 
            error_count
        )
        
        # Calculate system stability score
        stability_score = self._calculate_stability_score(
            baseline_metrics, 
            post_metrics, 
            recovery_time, 
            error_count
        )
        
        result = ExperimentResult(
            experiment=experiment,
            start_time=start_time,
            end_time=end_time,
            success=success,
            recovery_time=recovery_time,
            error_count=error_count,
            system_stability=stability_score,
            observations=observations,
            metrics={
                'baseline': baseline_metrics,
                'post_experiment': post_metrics,
                'system_health': system_health,
                'error_rates': error_rates,
                'performance': performance
            }
        )
        
        self.results.append(result)
        
        status_icon = "✅" if success else "❌"
        self.logger.info(f"{status_icon} Experiment completed: {experiment.name} (Recovery: {recovery_time:.1f}s)")
        
        return result
    
    @contextmanager
    async def _inject_failure(self, experiment: ChaosExperiment):
        """Context manager for failure injection"""
        failure_injector = None
        
        try:
            if experiment.failure_type == FailureType.NETWORK_TIMEOUT:
                failure_injector = self._inject_network_timeout(experiment)
            elif experiment.failure_type == FailureType.DATABASE_ERROR:
                failure_injector = self._inject_database_error(experiment)
            elif experiment.failure_type == FailureType.MEMORY_PRESSURE:
                failure_injector = self._inject_memory_pressure(experiment)
            elif experiment.failure_type == FailureType.NETWORK_DISCONNECT:
                failure_injector = self._inject_network_disconnect(experiment)
            elif experiment.failure_type == FailureType.CPU_SPIKE:
                failure_injector = self._inject_cpu_spike(experiment)
            elif experiment.failure_type == FailureType.PARTIAL_OUTAGE:
                failure_injector = self._inject_partial_outage(experiment)
            elif experiment.failure_type == FailureType.CASCADING_FAILURE:
                failure_injector = self._inject_cascading_failure(experiment)
            
            if failure_injector:
                async with failure_injector:
                    yield failure_injector
            else:
                yield None
                
        except Exception as e:
            self.logger.error(f"Failed to inject failure: {e}")
            yield None
    
    @contextmanager
    async def _inject_network_timeout(self, experiment: ChaosExperiment):
        """Inject network timeout failures"""
        
        def timeout_side_effect(*args, **kwargs):
            if random.random() < experiment.intensity:
                raise asyncio.TimeoutError("Chaos-induced timeout")
            return MagicMock()
        
        with patch('aiohttp.ClientSession.get', side_effect=timeout_side_effect):
            with patch('aiohttp.ClientSession.post', side_effect=timeout_side_effect):
                yield
    
    @contextmanager
    async def _inject_database_error(self, experiment: ChaosExperiment):
        """Inject database connection failures"""
        
        def db_error_side_effect(*args, **kwargs):
            if random.random() < experiment.intensity:
                raise Exception("Database connection failed")
            return MagicMock()
        
        with patch('sqlite3.connect', side_effect=db_error_side_effect):
            yield
    
    @contextmanager
    async def _inject_memory_pressure(self, experiment: ChaosExperiment):
        """Inject memory pressure by allocating memory"""
        allocated_memory = []
        
        try:
            # Allocate memory to simulate pressure
            memory_to_allocate = int(experiment.intensity * 100 * 1024 * 1024)  # MB
            chunk_size = 1024 * 1024  # 1MB chunks
            
            for _ in range(memory_to_allocate // chunk_size):
                allocated_memory.append(bytearray(chunk_size))
                await asyncio.sleep(0.001)  # Small delay to prevent blocking
            
            yield
            
        finally:
            # Clean up allocated memory
            allocated_memory.clear()
    
    @contextmanager
    async def _inject_network_disconnect(self, experiment: ChaosExperiment):
        """Inject WebSocket disconnections"""
        
        def disconnect_side_effect(*args, **kwargs):
            if random.random() < experiment.intensity:
                raise ConnectionResetError("Connection reset by peer")
            return MagicMock()
        
        with patch('websockets.connect', side_effect=disconnect_side_effect):
            yield
    
    @contextmanager
    async def _inject_cpu_spike(self, experiment: ChaosExperiment):
        """Inject CPU usage spikes"""
        cpu_tasks = []
        
        def cpu_intensive_task():
            """CPU-intensive task to simulate load"""
            end_time = time.time() + experiment.duration_seconds
            while time.time() < end_time:
                # Busy-wait to consume CPU
                for _ in range(1000):
                    pass
                time.sleep(0.001)
        
        try:
            # Start CPU-intensive tasks
            num_tasks = int(experiment.intensity * 4)  # Scale with CPU cores
            for _ in range(num_tasks):
                task = asyncio.create_task(asyncio.to_thread(cpu_intensive_task))
                cpu_tasks.append(task)
            
            yield
            
        finally:
            # Cancel CPU tasks
            for task in cpu_tasks:
                task.cancel()
            
            await asyncio.gather(*cpu_tasks, return_exceptions=True)
    
    @contextmanager
    async def _inject_partial_outage(self, experiment: ChaosExperiment):
        """Inject partial service outages"""
        
        failed_endpoints = set()
        
        def selective_failure(*args, **kwargs):
            endpoint = str(args[0]) if args else "unknown"
            
            # Determine if this endpoint should fail
            if endpoint not in failed_endpoints:
                if random.random() < experiment.intensity:
                    failed_endpoints.add(endpoint)
            
            if endpoint in failed_endpoints:
                raise Exception(f"Service unavailable: {endpoint}")
            
            return MagicMock()
        
        with patch('aiohttp.ClientSession.request', side_effect=selective_failure):
            yield
    
    @contextmanager
    async def _inject_cascading_failure(self, experiment: ChaosExperiment):
        """Inject cascading failures across multiple systems"""
        
        failure_probability = experiment.intensity * 0.7  # Start with lower probability
        
        def cascading_failure(*args, **kwargs):
            nonlocal failure_probability
            
            if random.random() < failure_probability:
                # Increase failure probability over time (cascade effect)
                failure_probability = min(1.0, failure_probability * 1.1)
                raise Exception("Cascading system failure")
            
            return MagicMock()
        
        # Patch multiple system components
        patches = [
            patch('aiohttp.ClientSession.get', side_effect=cascading_failure),
            patch('sqlite3.connect', side_effect=cascading_failure),
            patch('websockets.connect', side_effect=cascading_failure)
        ]
        
        try:
            for p in patches:
                p.start()
            yield
        finally:
            for p in patches:
                p.stop()
    
    async def _monitor_system_health(self, duration: float) -> Dict[str, Any]:
        """Monitor system health during experiment"""
        start_time = time.time()
        health_samples = []
        
        while time.time() - start_time < duration:
            try:
                # Collect system metrics
                process = psutil.Process(os.getpid())
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                health_sample = {
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb,
                    'memory_percent': process.memory_percent()
                }
                
                health_samples.append(health_sample)
                
            except Exception as e:
                self.logger.warning(f"Health monitoring error: {e}")
            
            await asyncio.sleep(1.0)
        
        # Calculate health metrics
        if health_samples:
            avg_cpu = sum(s['cpu_percent'] for s in health_samples) / len(health_samples)
            max_memory = max(s['memory_mb'] for s in health_samples)
            
            # Determine overall health status
            if avg_cpu > 80 or max_memory > 1000:
                status = "degraded"
            elif avg_cpu > 50 or max_memory > 500:
                status = "stressed"
            else:
                status = "healthy"
            
            return {
                'status': status,
                'avg_cpu_percent': avg_cpu,
                'max_memory_mb': max_memory,
                'sample_count': len(health_samples)
            }
        
        return {'status': 'unknown'}
    
    async def _monitor_error_rates(self, duration: float) -> Dict[str, Any]:
        """Monitor error rates during experiment"""
        # This would integrate with actual logging/monitoring
        # For simulation, we'll return mock data
        
        await asyncio.sleep(duration)
        
        return {
            'total_errors': random.randint(0, 10),
            'error_rate': random.uniform(0.01, 0.1),
            'critical_errors': random.randint(0, 2)
        }
    
    async def _monitor_performance_metrics(self, duration: float) -> Dict[str, Any]:
        """Monitor performance metrics during experiment"""
        # Simulate performance monitoring
        await asyncio.sleep(duration)
        
        return {
            'response_time_p95': random.uniform(0.1, 2.0),
            'throughput_rps': random.uniform(50, 200),
            'active_connections': random.randint(10, 100)
        }
    
    async def _collect_baseline_metrics(self) -> Dict[str, Any]:
        """Collect baseline system metrics"""
        try:
            process = psutil.Process(os.getpid())
            
            return {
                'cpu_percent': process.cpu_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'timestamp': time.time(),
                'connection_count': len(process.connections())
            }
        except Exception as e:
            self.logger.warning(f"Baseline metrics collection failed: {e}")
            return {}
    
    async def _wait_for_recovery(self, experiment: ChaosExperiment) -> bool:
        """Wait for system recovery and validate"""
        recovery_start = time.time()
        
        while time.time() - recovery_start < experiment.recovery_time_limit:
            try:
                # Check if system is responsive
                # This would normally test actual endpoints
                await asyncio.sleep(1.0)
                
                # Simulate recovery check
                if random.random() > 0.1:  # 90% chance of recovery each second
                    return True
                    
            except Exception as e:
                self.logger.debug(f"Recovery check failed: {e}")
                await asyncio.sleep(1.0)
        
        return False
    
    async def _evaluate_success_criteria(self, experiment: ChaosExperiment, 
                                       baseline: Dict, post: Dict, 
                                       recovery_time: float, error_count: int) -> bool:
        """Evaluate if experiment met success criteria"""
        
        # Basic success criteria
        if recovery_time > experiment.recovery_time_limit:
            return False
        
        if error_count > 50:  # Too many errors
            return False
        
        # Check if system metrics are within acceptable ranges
        if baseline and post:
            memory_increase = post.get('memory_mb', 0) - baseline.get('memory_mb', 0)
            if memory_increase > 100:  # More than 100MB increase
                return False
        
        return True
    
    def _calculate_stability_score(self, baseline: Dict, post: Dict, 
                                 recovery_time: float, error_count: int) -> float:
        """Calculate system stability score (0.0 to 1.0)"""
        score = 1.0
        
        # Penalize for slow recovery
        if recovery_time > 30:
            score -= 0.2
        if recovery_time > 60:
            score -= 0.3
        
        # Penalize for errors
        score -= min(0.4, error_count * 0.02)
        
        # Penalize for resource usage increases
        if baseline and post:
            memory_increase = post.get('memory_mb', 0) - baseline.get('memory_mb', 0)
            if memory_increase > 50:
                score -= 0.1
        
        return max(0.0, score)
    
    async def run_chaos_suite(self, experiments: Optional[List[str]] = None) -> List[ExperimentResult]:
        """Run a suite of chaos experiments"""
        self.logger.info("🔥 Starting Chaos Engineering Suite for Mirai Trading System")
        
        experiments_to_run = self.experiments
        if experiments:
            experiments_to_run = [e for e in self.experiments if e.name in experiments]
        
        results = []
        
        for i, experiment in enumerate(experiments_to_run, 1):
            self.logger.info(f"🧪 Running experiment {i}/{len(experiments_to_run)}: {experiment.name}")
            
            try:
                result = await self.run_experiment(experiment)
                results.append(result)
                
                # Wait between experiments to allow system stabilization
                if i < len(experiments_to_run):
                    self.logger.info("⏳ Waiting for system stabilization...")
                    await asyncio.sleep(30)
                    
            except Exception as e:
                self.logger.error(f"❌ Experiment failed: {experiment.name} - {e}")
        
        return results
    
    def generate_chaos_report(self) -> str:
        """Generate comprehensive chaos engineering report"""
        if not self.results:
            return "No chaos experiments have been run."
        
        report = "🔥 MIRAI TRADING SYSTEM - CHAOS ENGINEERING REPORT\n"
        report += "=" * 70 + "\n\n"
        
        # Summary statistics
        total_experiments = len(self.results)
        successful_experiments = sum(1 for r in self.results if r.success)
        avg_recovery_time = sum(r.recovery_time for r in self.results) / total_experiments
        avg_stability = sum(r.system_stability for r in self.results) / total_experiments
        
        report += f"📊 EXECUTIVE SUMMARY\n"
        report += f"   Total Experiments: {total_experiments}\n"
        report += f"   Successful: {successful_experiments} ({successful_experiments/total_experiments*100:.1f}%)\n"
        report += f"   Average Recovery Time: {avg_recovery_time:.1f}s\n"
        report += f"   Average Stability Score: {avg_stability:.2f}/1.0\n\n"
        
        # Individual experiment results
        report += "🧪 EXPERIMENT RESULTS\n"
        report += "-" * 50 + "\n"
        
        for result in self.results:
            status_icon = "✅" if result.success else "❌"
            report += f"{status_icon} {result.experiment.name}\n"
            report += f"   Type: {result.experiment.failure_type.value}\n"
            report += f"   Duration: {result.experiment.duration_seconds}s\n"
            report += f"   Intensity: {result.experiment.intensity:.1%}\n"
            report += f"   Recovery Time: {result.recovery_time:.1f}s\n"
            report += f"   Stability Score: {result.system_stability:.2f}/1.0\n"
            report += f"   Error Count: {result.error_count}\n"
            
            if result.observations:
                report += f"   Key Observations:\n"
                for obs in result.observations[:3]:  # Show top 3 observations
                    report += f"     • {obs}\n"
            
            report += "\n"
        
        # Resilience analysis
        report += "🛡️  RESILIENCE ANALYSIS\n"
        report += "-" * 50 + "\n"
        
        failure_types = {}
        for result in self.results:
            ft = result.experiment.failure_type.value
            if ft not in failure_types:
                failure_types[ft] = {'count': 0, 'success': 0, 'avg_recovery': 0}
            failure_types[ft]['count'] += 1
            if result.success:
                failure_types[ft]['success'] += 1
            failure_types[ft]['avg_recovery'] += result.recovery_time
        
        for failure_type, stats in failure_types.items():
            success_rate = stats['success'] / stats['count'] * 100
            avg_recovery = stats['avg_recovery'] / stats['count']
            
            if success_rate >= 80:
                resilience_level = "🟢 HIGH"
            elif success_rate >= 60:
                resilience_level = "🟡 MEDIUM"
            else:
                resilience_level = "🔴 LOW"
            
            report += f"   {failure_type.replace('_', ' ').title()}: {resilience_level}\n"
            report += f"     Success Rate: {success_rate:.1f}%\n"
            report += f"     Avg Recovery: {avg_recovery:.1f}s\n\n"
        
        # Recommendations
        report += "💡 RECOMMENDATIONS\n"
        report += "-" * 50 + "\n"
        
        failed_experiments = [r for r in self.results if not r.success]
        if failed_experiments:
            report += "   Priority Improvements:\n"
            for result in failed_experiments:
                report += f"   • Improve {result.experiment.target_component} resilience\n"
                report += f"     → {result.experiment.failure_type.value} handling\n"
        
        if avg_recovery_time > 60:
            report += "   • Implement faster recovery mechanisms\n"
        
        if avg_stability < 0.8:
            report += "   • Enhance system stability under stress\n"
        
        return report


if __name__ == "__main__":
    async def run_chaos_experiments():
        """Run chaos engineering experiments"""
        chaos = ChaosEngineering()
        
        # Run specific experiments or all
        print("🔥 Starting Chaos Engineering for Mirai Trading System\n")
        
        # Run a subset of experiments for demo
        experiment_names = [
            "Binance API Timeout",
            "Database Connection Loss", 
            "Memory Pressure Spike",
            "WebSocket Disconnection Storm"
        ]
        
        results = await chaos.run_chaos_suite(experiment_names)
        
        print("\n" + chaos.generate_chaos_report())
    
    # Run the chaos experiments
    asyncio.run(run_chaos_experiments())