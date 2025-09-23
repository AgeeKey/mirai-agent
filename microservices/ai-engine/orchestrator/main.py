"""
Mirai AI Orchestrator - Исправленная версия
Координатор AI агентов с правильной интеграцией SuperAGI/AutoGPT
"""
import os
import sys
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, WebSocket, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Setup logging - Updated for non-Docker environment
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
logs_dir = os.path.join(project_root, "logs")
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'orchestrator.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mirai AI Orchestrator", 
    version="2.0.0",
    description="Координатор AI агентов для автономной торговли"
)

# CORS для взаимодействия с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class AgentTask(BaseModel):
    type: str = Field(..., description="Тип задачи: analysis, trading, reporting")
    goal: str = Field(..., description="Цель задачи")
    context: Dict[str, Any] = Field(default_factory=dict, description="Контекст")
    priority: int = Field(default=5, description="Приоритет (1-10)")
    timeout: int = Field(default=300, description="Таймаут в секундах")
    agent_preference: Optional[str] = Field(default=None, description="Предпочтительный агент")

class TaskStatus(BaseModel):
    task_id: str
    status: str  # "pending", "running", "completed", "failed", "timeout"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    agent_used: Optional[str] = None

class MemoryEntry(BaseModel):
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    importance: float = 0.5

class OrchestratorService:
    def __init__(self):
        self.active_tasks: Dict[str, TaskStatus] = {}
        self.task_counter = 0
        self.memory_entries: List[MemoryEntry] = []
        
        # URLs сервисов из environment
        self.superagi_url = os.getenv("SUPERAGI_URL", "http://superagi:3000")
        self.autogpt_url = os.getenv("AUTOGPT_URL", "http://autogpt-runner:8090")
        self.chromadb_url = os.getenv("CHROMADB_URL", "http://chromadb:8000")
        self.api_url = os.getenv("API_URL", "http://host.docker.internal:8001")
        self.trader_url = os.getenv("TRADER_URL", "http://host.docker.internal:8002")
        
        # Настройки
        self.max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
        self.task_timeout = int(os.getenv("TASK_TIMEOUT", "300"))
        
        # Clients
        self.http_timeout = httpx.Timeout(30.0)
        
        # Ensure directories exist
        # Setup paths for non-Docker environment
        shared_dir = os.path.join(project_root, "shared")
        os.makedirs(os.path.join(shared_dir, "data"), exist_ok=True)
        os.makedirs(os.path.join(shared_dir, "reports"), exist_ok=True)
        os.makedirs(os.path.join(shared_dir, "knowledge"), exist_ok=True)
        os.makedirs("/app/logs", exist_ok=True)
        
        logger.info("Orchestrator service initialized")
        
    async def submit_task(self, task: AgentTask) -> str:
        """Submit task to appropriate AI service"""
        self.task_counter += 1
        task_id = f"task_{self.task_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Check concurrent tasks limit
        active_count = len([t for t in self.active_tasks.values() if t.status in ["pending", "running"]])
        if active_count >= self.max_concurrent_tasks:
            raise HTTPException(
                status_code=429, 
                detail=f"Too many active tasks ({active_count}/{self.max_concurrent_tasks})"
            )
        
        # Create task status
        status = TaskStatus(
            task_id=task_id,
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.active_tasks[task_id] = status
        
        # Start async execution
        asyncio.create_task(self._execute_task_with_timeout(task_id, task))
        
        logger.info(f"Task {task_id} submitted: {task.type} - {task.goal[:50]}...")
        return task_id
    
    async def _execute_task_with_timeout(self, task_id: str, task: AgentTask):
        """Execute task with timeout handling"""
        try:
            await asyncio.wait_for(
                self._execute_task(task_id, task), 
                timeout=task.timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Task {task_id} timed out after {task.timeout}s")
            self.active_tasks[task_id].status = "timeout"
            self.active_tasks[task_id].error = f"Task timed out after {task.timeout} seconds"
            self.active_tasks[task_id].updated_at = datetime.now()
    
    async def _execute_task(self, task_id: str, task: AgentTask):
        """Execute task based on type and route to appropriate agent"""
        try:
            self.active_tasks[task_id].status = "running"
            self.active_tasks[task_id].started_at = datetime.now()
            self.active_tasks[task_id].updated_at = datetime.now()
            
            # Determine best agent for task
            agent_to_use = await self._select_best_agent(task)
            self.active_tasks[task_id].agent_used = agent_to_use
            
            # Execute based on task type and selected agent
            if task.type == "analysis":
                result = await self._run_market_analysis(task, agent_to_use)
            elif task.type == "trading":
                result = await self._run_trading_decision(task, agent_to_use)
            elif task.type == "reporting":
                result = await self._run_reporting(task, agent_to_use)
            elif task.type == "learning":
                result = await self._run_learning_task(task, agent_to_use)
            else:
                raise ValueError(f"Unknown task type: {task.type}")
            
            # Store result and complete
            self.active_tasks[task_id].status = "completed"
            self.active_tasks[task_id].result = result
            self.active_tasks[task_id].completed_at = datetime.now()
            self.active_tasks[task_id].updated_at = datetime.now()
            self.active_tasks[task_id].progress = 1.0
            
            # Store in memory for learning
            await self._store_task_memory(task, result)
            
            logger.info(f"Task {task_id} completed successfully with {agent_to_use}")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            self.active_tasks[task_id].status = "failed"
            self.active_tasks[task_id].error = str(e)
            self.active_tasks[task_id].updated_at = datetime.now()
    
    async def _select_best_agent(self, task: AgentTask) -> str:
        """Select best agent based on task requirements and agent availability"""
        
        # Check agent preference
        if task.agent_preference:
            if await self._check_agent_health(task.agent_preference):
                return task.agent_preference
        
        # Default routing based on task type
        if task.type == "analysis":
            # SuperAGI better for research and analysis
            if await self._check_agent_health("superagi"):
                return "superagi"
            elif await self._check_agent_health("autogpt"):
                return "autogpt"
        elif task.type == "trading":
            # AutoGPT better for autonomous execution
            if await self._check_agent_health("autogpt"):
                return "autogpt"
            elif await self._check_agent_health("superagi"):
                return "superagi"
        elif task.type == "reporting":
            # SuperAGI better for structured reporting
            if await self._check_agent_health("superagi"):
                return "superagi"
            elif await self._check_agent_health("autogpt"):
                return "autogpt"
        
        # Fallback to local processing
        return "local"
    
    async def _check_agent_health(self, agent: str) -> bool:
        """Check if agent is available and healthy"""
        try:
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                if agent == "superagi":
                    response = await client.get(f"{self.superagi_url}/api/health")
                elif agent == "autogpt":
                    response = await client.get(f"{self.autogpt_url}/health")
                else:
                    return False
                
                return response.status_code == 200
        except:
            return False
    
    async def _run_market_analysis(self, task: AgentTask, agent: str) -> Dict[str, Any]:
        """Run market analysis using selected agent"""
        
        if agent == "superagi":
            return await self._superagi_analysis(task)
        elif agent == "autogpt":
            return await self._autogpt_analysis(task)
        else:
            return await self._local_analysis(task)
    
    async def _superagi_analysis(self, task: AgentTask) -> Dict[str, Any]:
        """Execute analysis via SuperAGI"""
        try:
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                # Create SuperAGI agent run
                agent_config = {
                    "name": "MarketAnalyzer",
                    "description": task.goal,
                    "goals": [task.goal],
                    "tools": ["web_search", "file_reader", "code_writer"],
                    "model": "gpt-4",
                    "max_iterations": 5,
                    "user_timezone": "UTC",
                    "permission_type": "RESTRICTED",
                    "LTM_DB": "Pinecone"
                }
                
                # Submit to SuperAGI
                response = await client.post(
                    f"{self.superagi_url}/api/agent/create_and_run",
                    json=agent_config
                )
                
                if response.status_code == 200:
                    run_data = response.json()
                    run_id = run_data.get("run_id")
                    
                    # Poll for completion
                    result = await self._poll_superagi_completion(run_id)
                    return result
                else:
                    logger.error(f"SuperAGI request failed: {response.status_code}")
                    return await self._local_analysis(task)
                    
        except Exception as e:
            logger.error(f"SuperAGI analysis failed: {e}")
            return await self._local_analysis(task)
    
    async def _autogpt_analysis(self, task: AgentTask) -> Dict[str, Any]:
        """Execute analysis via AutoGPT"""
        try:
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                agent_config = {
                    "agent_id": f"analyzer_{int(datetime.now().timestamp())}",
                    "name": "Market Analyzer",
                    "role": "Market analysis expert",
                    "goals": [task.goal],
                    "max_iterations": 10,
                    "model": "gpt-4"
                }
                
                response = await client.post(
                    f"{self.autogpt_url}/api/agents",
                    json=agent_config
                )
                
                if response.status_code == 200:
                    agent_data = response.json()
                    agent_id = agent_data.get("agent_id")
                    
                    # Start execution
                    exec_response = await client.post(
                        f"{self.autogpt_url}/api/agents/{agent_id}/execute"
                    )
                    
                    if exec_response.status_code == 200:
                        # Poll for results
                        result = await self._poll_autogpt_completion(agent_id)
                        return result
                
                return await self._local_analysis(task)
                
        except Exception as e:
            logger.error(f"AutoGPT analysis failed: {e}")
            return await self._local_analysis(task)
    
    async def _local_analysis(self, task: AgentTask) -> Dict[str, Any]:
        """Fallback local analysis"""
        await asyncio.sleep(2)  # Simulate processing
        
        symbols = task.context.get("symbols", ["BTC/USDT"])
        
        # Basic analysis result
        return {
            "analysis_type": "market",
            "agent": "local",
            "symbols": symbols,
            "recommendations": [
                {
                    "symbol": symbol,
                    "action": "hold",
                    "confidence": 0.6,
                    "reasoning": "Waiting for clearer market signals"
                } for symbol in symbols
            ],
            "market_conditions": {
                "volatility": "medium",
                "trend": "sideways",
                "sentiment": "neutral"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _run_trading_decision(self, task: AgentTask, agent: str) -> Dict[str, Any]:
        """Execute trading decision with risk checks"""
        
        # Always check risk first
        risk_approved = await self._check_risk_management()
        
        if not risk_approved:
            return {
                "decision": "rejected",
                "reason": "Risk management blocked the trade",
                "risk_approved": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get market data
        market_data = await self._get_current_market_data()
        
        if agent == "autogpt":
            decision = await self._autogpt_trading_decision(task, market_data)
        elif agent == "superagi":
            decision = await self._superagi_trading_decision(task, market_data)
        else:
            decision = await self._local_trading_decision(task, market_data)
        
        decision["risk_approved"] = risk_approved
        return decision
    
    async def _check_risk_management(self) -> bool:
        """Check with Mirai risk management system"""
        try:
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                response = await client.get(f"{self.trader_url}/risk/status")
                if response.status_code == 200:
                    risk_data = response.json()
                    return risk_data.get("can_trade", False)
        except:
            logger.warning("Could not connect to risk management, defaulting to safe mode")
        
        return False  # Default to safe
    
    async def _get_current_market_data(self) -> Dict[str, Any]:
        """Get current market data from Mirai API"""
        try:
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                response = await client.get(f"{self.api_url}/market/snapshot")
                if response.status_code == 200:
                    return response.json()
        except:
            logger.warning("Could not get market data from API")
        
        return {"status": "unavailable"}
    
    async def _local_trading_decision(self, task: AgentTask, market_data: Dict) -> Dict[str, Any]:
        """Local trading decision logic"""
        await asyncio.sleep(1)
        
        return {
            "decision": "wait",
            "symbol": task.context.get("symbol", "BTC/USDT"),
            "reasoning": "Insufficient data for trading decision",
            "confidence": 0.3,
            "agent": "local",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _run_reporting(self, task: AgentTask, agent: str) -> Dict[str, Any]:
        """Generate comprehensive reports"""
        
        report_type = task.context.get("type", "performance")
        period = task.context.get("period", "24h")
        
        # Gather data for report
        report_data = await self._gather_report_data(period)
        
        # Generate report file
        report_path = os.path.join(project_root, "shared", "reports", f"report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        report_content = {
            "type": report_type,
            "period": period,
            "generated_at": datetime.now().isoformat(),
            "agent": agent,
            "data": report_data,
            "summary": {
                "total_tasks": len(self.active_tasks),
                "completed_tasks": len([t for t in self.active_tasks.values() if t.status == "completed"]),
                "success_rate": self._calculate_success_rate()
            }
        }
        
        # Save report
        with open(report_path, 'w') as f:
            json.dump(report_content, f, indent=2, default=str)
        
        return {
            "report_path": report_path,
            "status": "generated",
            "summary": report_content["summary"]
        }
    
    async def _gather_report_data(self, period: str) -> Dict[str, Any]:
        """Gather data for reports from various sources"""
        
        # Calculate time range
        if period == "1h":
            since = datetime.now() - timedelta(hours=1)
        elif period == "24h":
            since = datetime.now() - timedelta(days=1)
        elif period == "7d":
            since = datetime.now() - timedelta(days=7)
        else:
            since = datetime.now() - timedelta(hours=1)
        
        # Filter tasks by time period
        recent_tasks = [
            t for t in self.active_tasks.values() 
            if t.created_at >= since
        ]
        
        return {
            "period_start": since.isoformat(),
            "period_end": datetime.now().isoformat(),
            "task_count": len(recent_tasks),
            "task_types": self._count_task_types(recent_tasks),
            "agent_usage": self._count_agent_usage(recent_tasks),
            "performance_metrics": self._calculate_performance_metrics(recent_tasks)
        }
    
    def _count_task_types(self, tasks: List[TaskStatus]) -> Dict[str, int]:
        """Count tasks by type"""
        counts = {}
        for task in tasks:
            # Extract task type from task_id or other identifier
            # This is a simplified version
            task_type = "unknown"
            counts[task_type] = counts.get(task_type, 0) + 1
        return counts
    
    def _count_agent_usage(self, tasks: List[TaskStatus]) -> Dict[str, int]:
        """Count usage by agent"""
        counts = {}
        for task in tasks:
            agent = task.agent_used or "unknown"
            counts[agent] = counts.get(agent, 0) + 1
        return counts
    
    def _calculate_performance_metrics(self, tasks: List[TaskStatus]) -> Dict[str, float]:
        """Calculate performance metrics"""
        if not tasks:
            return {"avg_duration": 0, "success_rate": 0}
        
        completed_tasks = [t for t in tasks if t.completed_at and t.started_at]
        
        if completed_tasks:
            durations = [
                (t.completed_at - t.started_at).total_seconds() 
                for t in completed_tasks
            ]
            avg_duration = sum(durations) / len(durations)
        else:
            avg_duration = 0
        
        success_rate = len([t for t in tasks if t.status == "completed"]) / len(tasks)
        
        return {
            "avg_duration": avg_duration,
            "success_rate": success_rate,
            "total_tasks": len(tasks)
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        if not self.active_tasks:
            return 0.0
        
        completed = len([t for t in self.active_tasks.values() if t.status == "completed"])
        total = len(self.active_tasks)
        return completed / total
    
    async def _run_learning_task(self, task: AgentTask, agent: str) -> Dict[str, Any]:
        """Execute learning/training tasks"""
        
        learning_type = task.context.get("learning_type", "pattern_analysis")
        
        if learning_type == "pattern_analysis":
            return await self._analyze_patterns()
        elif learning_type == "performance_optimization":
            return await self._optimize_performance()
        else:
            return {"status": "unknown_learning_type", "type": learning_type}
    
    async def _analyze_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in historical data"""
        
        # Get completed tasks for pattern analysis
        completed_tasks = [
            t for t in self.active_tasks.values() 
            if t.status == "completed" and t.result
        ]
        
        patterns = {
            "successful_task_patterns": [],
            "timing_patterns": [],
            "context_patterns": []
        }
        
        # Simple pattern detection (can be enhanced with ML)
        if len(completed_tasks) > 5:
            # Analyze timing patterns
            completion_times = [
                t.completed_at.hour for t in completed_tasks 
                if t.completed_at
            ]
            
            if completion_times:
                most_successful_hour = max(set(completion_times), key=completion_times.count)
                patterns["timing_patterns"].append({
                    "pattern": "peak_performance_hour",
                    "value": most_successful_hour,
                    "confidence": completion_times.count(most_successful_hour) / len(completion_times)
                })
        
        return {
            "learning_type": "pattern_analysis",
            "patterns_found": len([p for p in patterns.values() if p]),
            "patterns": patterns,
            "recommendations": self._generate_learning_recommendations(patterns)
        }
    
    def _generate_learning_recommendations(self, patterns: Dict) -> List[str]:
        """Generate recommendations based on learned patterns"""
        recommendations = []
        
        for pattern_type, pattern_list in patterns.items():
            if pattern_list:
                if pattern_type == "timing_patterns":
                    recommendations.append("Schedule high-priority tasks during peak performance hours")
                elif pattern_type == "successful_task_patterns":
                    recommendations.append("Replicate successful task configurations")
        
        return recommendations
    
    async def _store_task_memory(self, task: AgentTask, result: Dict[str, Any]):
        """Store task results in memory for learning"""
        
        memory_entry = MemoryEntry(
            content=f"Task: {task.goal} | Result: {json.dumps(result, default=str)[:200]}",
            metadata={
                "task_type": task.type,
                "success": result.get("status") != "failed",
                "context_keys": list(task.context.keys()),
                "result_keys": list(result.keys())
            },
            timestamp=datetime.now(),
            importance=task.priority / 10.0
        )
        
        self.memory_entries.append(memory_entry)
        
        # Keep only recent entries (memory limit)
        if len(self.memory_entries) > 1000:
            # Remove oldest low-importance entries
            self.memory_entries.sort(key=lambda x: (x.importance, x.timestamp))
            self.memory_entries = self.memory_entries[-800:]  # Keep 800 most important/recent
    
    async def get_task_status(self, task_id: str) -> TaskStatus:
        """Get detailed task status"""
        if task_id not in self.active_tasks:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        return self.active_tasks[task_id]
    
    async def list_active_tasks(self) -> List[TaskStatus]:
        """List all active tasks"""
        return [
            task for task in self.active_tasks.values()
            if task.status in ["pending", "running"]
        ]
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            "total_tasks": len(self.active_tasks),
            "active_tasks": len(await self.list_active_tasks()),
            "completed_tasks": len([t for t in self.active_tasks.values() if t.status == "completed"]),
            "failed_tasks": len([t for t in self.active_tasks.values() if t.status == "failed"]),
            "success_rate": self._calculate_success_rate(),
            "memory_entries": len(self.memory_entries),
            "uptime": "system_uptime_placeholder",  # Can be enhanced
            "agent_health": {
                "superagi": await self._check_agent_health("superagi"),
                "autogpt": await self._check_agent_health("autogpt")
            }
        }
    
    # Polling methods for agent completion
    async def _poll_superagi_completion(self, run_id: str, max_polls: int = 60) -> Dict[str, Any]:
        """Poll SuperAGI for completion"""
        for _ in range(max_polls):
            try:
                async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                    response = await client.get(f"{self.superagi_url}/api/agent/run/{run_id}")
                    if response.status_code == 200:
                        run_data = response.json()
                        if run_data.get("status") in ["COMPLETED", "FAILED"]:
                            return {
                                "status": run_data.get("status"),
                                "result": run_data.get("output", {}),
                                "agent": "superagi"
                            }
                await asyncio.sleep(5)
            except:
                await asyncio.sleep(5)
        
        return {"status": "TIMEOUT", "agent": "superagi"}
    
    async def _poll_autogpt_completion(self, agent_id: str, max_polls: int = 60) -> Dict[str, Any]:
        """Poll AutoGPT for completion"""
        for _ in range(max_polls):
            try:
                async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                    response = await client.get(f"{self.autogpt_url}/api/agents/{agent_id}/status")
                    if response.status_code == 200:
                        status_data = response.json()
                        if status_data.get("status") in ["completed", "failed"]:
                            # Get results
                            result_response = await client.get(f"{self.autogpt_url}/api/agents/{agent_id}/output")
                            result = result_response.json() if result_response.status_code == 200 else {}
                            
                            return {
                                "status": status_data.get("status"),
                                "result": result,
                                "agent": "autogpt"
                            }
                await asyncio.sleep(5)
            except:
                await asyncio.sleep(5)
        
        return {"status": "timeout", "agent": "autogpt"}

# Initialize service
orchestrator = OrchestratorService()

@app.on_event("startup")
async def startup():
    """Startup tasks"""
    logger.info("Mirai AI Orchestrator starting up...")
    
    # Test connections to agents
    superagi_ok = await orchestrator._check_agent_health("superagi")
    autogpt_ok = await orchestrator._check_agent_health("autogpt")
    
    logger.info(f"Agent health check - SuperAGI: {'✅' if superagi_ok else '❌'}, AutoGPT: {'✅' if autogpt_ok else '❌'}")

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    stats = await orchestrator.get_system_stats()
    
    return {
        "status": "healthy",
        "service": "orchestrator",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "stats": stats
    }

@app.get("/status")
async def status_check():
    """System status and metrics"""
    stats = await orchestrator.get_system_stats()
    
    return {
        "status": "operational",
        "service": "mirai-ai-orchestrator",
        "version": "2.0.0",
        "uptime": datetime.now().isoformat(),
        "active_tasks": len(orchestrator.active_tasks),
        "completed_tasks": stats.get("total_completed", 0),
        "ai_enabled": True,
        "agents_available": ["superagi", "autogpt"],
        "system_health": "excellent"
    }

@app.post("/task/submit")
async def submit_task(task: AgentTask):
    """Submit new task to orchestrator"""
    task_id = await orchestrator.submit_task(task)
    return {"task_id": task_id, "status": "submitted"}

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get detailed task status"""
    status = await orchestrator.get_task_status(task_id)
    return status.dict()

@app.get("/tasks/active")
async def list_active_tasks():
    """List all active tasks"""
    tasks = await orchestrator.list_active_tasks()
    return {
        "count": len(tasks),
        "tasks": [task.dict() for task in tasks]
    }

@app.get("/tasks/history")
async def get_task_history(limit: int = 50):
    """Get task history"""
    all_tasks = list(orchestrator.active_tasks.values())
    all_tasks.sort(key=lambda x: x.created_at, reverse=True)
    
    return {
        "count": len(all_tasks),
        "tasks": [task.dict() for task in all_tasks[:limit]]
    }

@app.get("/stats")
async def get_system_statistics():
    """Get comprehensive system statistics"""
    return await orchestrator.get_system_stats()

@app.post("/learn")
async def trigger_learning():
    """Manually trigger learning/pattern analysis"""
    learning_task = AgentTask(
        type="learning",
        goal="Analyze patterns and optimize performance",
        context={"learning_type": "pattern_analysis"},
        priority=3
    )
    
    task_id = await orchestrator.submit_task(learning_task)
    return {"message": "Learning task submitted", "task_id": task_id}

@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel active task"""
    if task_id not in orchestrator.active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = orchestrator.active_tasks[task_id]
    if task.status in ["pending", "running"]:
        task.status = "cancelled"
        task.updated_at = datetime.now()
        return {"message": f"Task {task_id} cancelled"}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot cancel task in status: {task.status}")

# WebSocket для real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket for real-time task updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send current stats every 5 seconds
            stats = await orchestrator.get_system_stats()
            await websocket.send_json(stats)
            await asyncio.sleep(5)
    except:
        pass

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8080,
        log_level="info",
        access_log=True
    )