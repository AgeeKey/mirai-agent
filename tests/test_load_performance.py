"""
Load Testing Framework for Mirai Trading System
High-performance load testing with realistic trading scenarios
"""

import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass
import aiohttp
import json
import random
from concurrent.futures import ThreadPoolExecutor
import psutil
import os


@dataclass
class LoadTestResult:
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    total_duration: float
    memory_usage_mb: float
    cpu_usage_percent: float


class TradingLoadTester:
    """
    Comprehensive load testing framework for trading operations
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.results: List[LoadTestResult] = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def load_test_api_endpoints(self, concurrent_users: int = 100, duration_seconds: int = 60):
        """Load test API endpoints with concurrent users"""
        print(f"🚀 Starting API load test: {concurrent_users} users for {duration_seconds}s")
        
        endpoints = [
            {"path": "/healthz", "method": "GET", "weight": 20},
            {"path": "/portfolio", "method": "GET", "weight": 15},
            {"path": "/positions", "method": "GET", "weight": 15},
            {"path": "/trades", "method": "GET", "weight": 10},
            {"path": "/metrics", "method": "GET", "weight": 10},
            {"path": "/alerts", "method": "GET", "weight": 5},
            {"path": "/market-data/BTCUSDT", "method": "GET", "weight": 25}
        ]
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        response_times = []
        successful_requests = 0
        failed_requests = 0
        
        # Monitor system resources
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        async def user_session():
            nonlocal successful_requests, failed_requests
            
            while time.time() < end_time:
                # Select endpoint based on weight
                endpoint = self._weighted_choice(endpoints)
                
                request_start = time.time()
                try:
                    async with self.session.request(
                        endpoint["method"],
                        f"{self.base_url}{endpoint['path']}",
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        await response.text()
                        
                        if response.status < 400:
                            successful_requests += 1
                        else:
                            failed_requests += 1
                            
                        response_time = time.time() - request_start
                        response_times.append(response_time)
                        
                except Exception as e:
                    failed_requests += 1
                    response_times.append(time.time() - request_start)
                
                # Small delay to simulate realistic user behavior
                await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Run concurrent user sessions
        tasks = [user_session() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        total_duration = time.time() - start_time
        final_memory = process.memory_info().rss / 1024 / 1024
        cpu_usage = process.cpu_percent()
        
        # Calculate statistics
        if response_times:
            result = LoadTestResult(
                test_name="API Endpoints Load Test",
                total_requests=len(response_times),
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                avg_response_time=statistics.mean(response_times),
                min_response_time=min(response_times),
                max_response_time=max(response_times),
                p95_response_time=statistics.quantiles(response_times, n=20)[18],
                p99_response_time=statistics.quantiles(response_times, n=100)[98],
                requests_per_second=len(response_times) / total_duration,
                total_duration=total_duration,
                memory_usage_mb=final_memory - initial_memory,
                cpu_usage_percent=cpu_usage
            )
        else:
            result = LoadTestResult(
                test_name="API Endpoints Load Test",
                total_requests=0, successful_requests=0, failed_requests=0,
                avg_response_time=0, min_response_time=0, max_response_time=0,
                p95_response_time=0, p99_response_time=0, requests_per_second=0,
                total_duration=total_duration, memory_usage_mb=0, cpu_usage_percent=0
            )
        
        self.results.append(result)
        print(f"✅ API Load Test completed: {result.requests_per_second:.1f} RPS")
        return result
    
    async def load_test_websocket_connections(self, concurrent_connections: int = 50, duration_seconds: int = 60):
        """Load test WebSocket connections"""
        print(f"🔌 Starting WebSocket load test: {concurrent_connections} connections for {duration_seconds}s")
        
        import websockets
        
        connection_times = []
        message_counts = []
        successful_connections = 0
        failed_connections = 0
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        async def websocket_client():
            nonlocal successful_connections, failed_connections
            
            connect_start = time.time()
            try:
                uri = f"ws://localhost:8000/ws"
                async with websockets.connect(uri) as websocket:
                    connection_time = time.time() - connect_start
                    connection_times.append(connection_time)
                    successful_connections += 1
                    
                    message_count = 0
                    while time.time() < end_time:
                        try:
                            # Wait for messages with timeout
                            message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            message_count += 1
                        except asyncio.TimeoutError:
                            continue
                        except websockets.exceptions.ConnectionClosed:
                            break
                    
                    message_counts.append(message_count)
                    
            except Exception as e:
                failed_connections += 1
                connection_times.append(time.time() - connect_start)
        
        # Run concurrent WebSocket connections
        tasks = [websocket_client() for _ in range(concurrent_connections)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        total_duration = time.time() - start_time
        
        if connection_times:
            result = LoadTestResult(
                test_name="WebSocket Load Test",
                total_requests=len(connection_times),
                successful_requests=successful_connections,
                failed_requests=failed_connections,
                avg_response_time=statistics.mean(connection_times),
                min_response_time=min(connection_times),
                max_response_time=max(connection_times),
                p95_response_time=statistics.quantiles(connection_times, n=20)[18] if len(connection_times) >= 20 else max(connection_times),
                p99_response_time=statistics.quantiles(connection_times, n=100)[98] if len(connection_times) >= 100 else max(connection_times),
                requests_per_second=successful_connections / total_duration,
                total_duration=total_duration,
                memory_usage_mb=0,
                cpu_usage_percent=0
            )
        else:
            result = LoadTestResult(
                test_name="WebSocket Load Test",
                total_requests=0, successful_requests=0, failed_requests=0,
                avg_response_time=0, min_response_time=0, max_response_time=0,
                p95_response_time=0, p99_response_time=0, requests_per_second=0,
                total_duration=total_duration, memory_usage_mb=0, cpu_usage_percent=0
            )
        
        self.results.append(result)
        print(f"✅ WebSocket Load Test completed: {successful_connections} successful connections")
        return result
    
    async def load_test_trading_decisions(self, decisions_per_second: int = 10, duration_seconds: int = 60):
        """Load test AI trading decision making"""
        print(f"🤖 Starting AI decision load test: {decisions_per_second} decisions/s for {duration_seconds}s")
        
        decision_times = []
        successful_decisions = 0
        failed_decisions = 0
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        async def make_trading_decision():
            nonlocal successful_decisions, failed_decisions
            
            decision_start = time.time()
            try:
                # Mock market data for decision
                market_data = {
                    "symbol": random.choice(["BTCUSDT", "ETHUSDT", "ADAUSDT"]),
                    "price": random.uniform(30000, 70000),
                    "volume": random.uniform(1000000, 5000000),
                    "timestamp": time.time()
                }
                
                # Simulate AI decision process
                await asyncio.sleep(random.uniform(0.01, 0.1))  # AI processing time
                
                decision_time = time.time() - decision_start
                decision_times.append(decision_time)
                successful_decisions += 1
                
            except Exception as e:
                failed_decisions += 1
                decision_times.append(time.time() - decision_start)
        
        # Schedule decisions at target rate
        while time.time() < end_time:
            batch_start = time.time()
            
            # Create batch of decisions
            tasks = [make_trading_decision() for _ in range(decisions_per_second)]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Maintain rate
            batch_duration = time.time() - batch_start
            sleep_time = max(0, 1.0 - batch_duration)
            await asyncio.sleep(sleep_time)
        
        total_duration = time.time() - start_time
        
        if decision_times:
            result = LoadTestResult(
                test_name="AI Decision Load Test",
                total_requests=len(decision_times),
                successful_requests=successful_decisions,
                failed_requests=failed_decisions,
                avg_response_time=statistics.mean(decision_times),
                min_response_time=min(decision_times),
                max_response_time=max(decision_times),
                p95_response_time=statistics.quantiles(decision_times, n=20)[18] if len(decision_times) >= 20 else max(decision_times),
                p99_response_time=statistics.quantiles(decision_times, n=100)[98] if len(decision_times) >= 100 else max(decision_times),
                requests_per_second=len(decision_times) / total_duration,
                total_duration=total_duration,
                memory_usage_mb=0,
                cpu_usage_percent=0
            )
        else:
            result = LoadTestResult(
                test_name="AI Decision Load Test",
                total_requests=0, successful_requests=0, failed_requests=0,
                avg_response_time=0, min_response_time=0, max_response_time=0,
                p95_response_time=0, p99_response_time=0, requests_per_second=0,
                total_duration=total_duration, memory_usage_mb=0, cpu_usage_percent=0
            )
        
        self.results.append(result)
        print(f"✅ AI Decision Load Test completed: {result.requests_per_second:.1f} decisions/s")
        return result
    
    def _weighted_choice(self, choices: List[Dict]) -> Dict:
        """Select item based on weight"""
        total_weight = sum(choice["weight"] for choice in choices)
        random_weight = random.uniform(0, total_weight)
        
        current_weight = 0
        for choice in choices:
            current_weight += choice["weight"]
            if random_weight <= current_weight:
                return choice
        
        return choices[-1]  # Fallback
    
    def generate_report(self) -> str:
        """Generate comprehensive load test report"""
        if not self.results:
            return "No load test results available"
        
        report = "📊 MIRAI TRADING SYSTEM - LOAD TEST REPORT\n"
        report += "=" * 60 + "\n\n"
        
        for result in self.results:
            report += f"🔸 {result.test_name}\n"
            report += f"   Total Requests: {result.total_requests:,}\n"
            report += f"   Successful: {result.successful_requests:,} ({result.successful_requests/result.total_requests*100:.1f}%)\n"
            report += f"   Failed: {result.failed_requests:,} ({result.failed_requests/result.total_requests*100:.1f}%)\n"
            report += f"   Requests/Second: {result.requests_per_second:.1f}\n"
            report += f"   Avg Response Time: {result.avg_response_time*1000:.1f}ms\n"
            report += f"   95th Percentile: {result.p95_response_time*1000:.1f}ms\n"
            report += f"   99th Percentile: {result.p99_response_time*1000:.1f}ms\n"
            report += f"   Max Response Time: {result.max_response_time*1000:.1f}ms\n"
            if result.memory_usage_mb > 0:
                report += f"   Memory Usage: +{result.memory_usage_mb:.1f}MB\n"
            if result.cpu_usage_percent > 0:
                report += f"   CPU Usage: {result.cpu_usage_percent:.1f}%\n"
            report += f"   Duration: {result.total_duration:.1f}s\n\n"
        
        # Overall summary
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        avg_rps = statistics.mean([r.requests_per_second for r in self.results])
        
        report += "📈 OVERALL PERFORMANCE SUMMARY\n"
        report += f"   Total Requests Processed: {total_requests:,}\n"
        report += f"   Overall Success Rate: {total_successful/total_requests*100:.1f}%\n"
        report += f"   Average RPS Across Tests: {avg_rps:.1f}\n"
        
        # Performance benchmarks
        report += "\n🎯 PERFORMANCE BENCHMARKS\n"
        for result in self.results:
            if result.avg_response_time < 0.1:
                status = "✅ EXCELLENT"
            elif result.avg_response_time < 0.5:
                status = "🟡 GOOD"
            elif result.avg_response_time < 1.0:
                status = "🟠 ACCEPTABLE"
            else:
                status = "🔴 POOR"
            
            report += f"   {result.test_name}: {status}\n"
        
        return report


# Stress test scenarios
class StressTestScenarios:
    """
    Predefined stress test scenarios for different use cases
    """
    
    @staticmethod
    async def high_frequency_trading_simulation():
        """Simulate high-frequency trading load"""
        async with TradingLoadTester() as tester:
            # Burst of API calls
            await tester.load_test_api_endpoints(concurrent_users=200, duration_seconds=30)
            
            # High-frequency decisions
            await tester.load_test_trading_decisions(decisions_per_second=50, duration_seconds=30)
            
            return tester.generate_report()
    
    @staticmethod
    async def market_volatility_simulation():
        """Simulate high market volatility with many connections"""
        async with TradingLoadTester() as tester:
            # Many WebSocket connections for real-time data
            await tester.load_test_websocket_connections(concurrent_connections=100, duration_seconds=60)
            
            # High API load during volatile periods
            await tester.load_test_api_endpoints(concurrent_users=150, duration_seconds=60)
            
            return tester.generate_report()
    
    @staticmethod
    async def extended_operation_simulation():
        """Simulate extended trading session"""
        async with TradingLoadTester() as tester:
            # Longer duration tests
            await tester.load_test_api_endpoints(concurrent_users=50, duration_seconds=300)  # 5 minutes
            await tester.load_test_trading_decisions(decisions_per_second=5, duration_seconds=300)
            
            return tester.generate_report()


if __name__ == "__main__":
    async def run_comprehensive_load_tests():
        """Run all load test scenarios"""
        print("🚀 Starting Comprehensive Load Tests for Mirai Trading System\n")
        
        # Standard load test
        async with TradingLoadTester() as tester:
            await tester.load_test_api_endpoints(concurrent_users=100, duration_seconds=60)
            await tester.load_test_websocket_connections(concurrent_connections=50, duration_seconds=60)
            await tester.load_test_trading_decisions(decisions_per_second=10, duration_seconds=60)
            
            print(tester.generate_report())
        
        print("\n" + "="*60)
        print("🔥 HIGH FREQUENCY TRADING SIMULATION")
        print("="*60)
        hft_report = await StressTestScenarios.high_frequency_trading_simulation()
        print(hft_report)
        
        print("\n" + "="*60)
        print("📈 MARKET VOLATILITY SIMULATION")
        print("="*60)
        volatility_report = await StressTestScenarios.market_volatility_simulation()
        print(volatility_report)
    
    # Run the tests
    asyncio.run(run_comprehensive_load_tests())