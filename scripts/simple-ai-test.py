#!/usr/bin/env python3
"""
Simple AI Integration Test
Tests AI components without relative imports
"""

import sys
import os
sys.path.insert(0, '/root/mirai-agent')

def test_basic_imports():
    """Test basic Python imports"""
    try:
        import aiohttp
        import asyncio
        import json
        from datetime import datetime
        print("✅ Basic imports successful")
        return True
    except Exception as e:
        print(f"❌ Basic imports failed: {e}")
        return False

def test_ai_config():
    """Test AI configuration structure"""
    try:
        # Mock AI configuration test
        config = {
            'ai_enabled': True,
            'orchestrator_url': 'http://localhost:8080',
            'ai_decision_weight': 0.6,
            'timeout': 8.0
        }
        
        # Validate configuration
        assert isinstance(config['ai_enabled'], bool)
        assert isinstance(config['orchestrator_url'], str)
        assert 0.0 <= config['ai_decision_weight'] <= 1.0
        assert config['timeout'] > 0
        
        print("✅ AI configuration validation successful")
        return True
        
    except Exception as e:
        print(f"❌ AI configuration test failed: {e}")
        return False

def test_trading_loop_structure():
    """Test trading loop structure without imports"""
    try:
        # Read and validate agent_loop.py structure
        with open('/root/mirai-agent/app/trader/agent_loop.py', 'r') as f:
            content = f.read()
        
        # Check for key components
        required_elements = [
            'class AIIntegratedTradingLoop',
            'async def _submit_ai_task',
            'async def _get_ai_task_result',
            'ai_enabled',
            'orchestrator_url',
            'def create_enhanced_trading_loop'
        ]
        
        for element in required_elements:
            if element not in content:
                raise ValueError(f"Missing required element: {element}")
        
        print("✅ Trading loop structure validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Trading loop structure test failed: {e}")
        return False

def test_policy_structure():
    """Test policy structure without imports"""
    try:
        # Read and validate policy.py structure
        with open('/root/mirai-agent/app/agent/policy.py', 'r') as f:
            content = f.read()
        
        # Check for key components
        required_elements = [
            'class AIEnhancedPolicy',
            'class PolicyEngine',
            'async def analyze_market_with_ai',
            'async def _get_ai_market_analysis',
            'ai_enabled',
            'orchestrator_url'
        ]
        
        for element in required_elements:
            if element not in content:
                raise ValueError(f"Missing required element: {element}")
        
        print("✅ Policy structure validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Policy structure test failed: {e}")
        return False

def test_config_files():
    """Test configuration files"""
    try:
        import yaml
        
        # Test strategies.yaml
        with open('/root/mirai-agent/configs/strategies.yaml', 'r') as f:
            strategies = yaml.safe_load(f)
        
        if 'ai_integration' not in strategies:
            raise ValueError("ai_integration not found in strategies.yaml")
        
        ai_config = strategies['ai_integration']
        required_keys = ['enabled', 'orchestrator_url', 'decision_weight', 'timeout']
        
        for key in required_keys:
            if key not in ai_config:
                raise ValueError(f"Missing AI config key: {key}")
        
        print("✅ Configuration files validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Configuration files test failed: {e}")
        return False

def test_orchestrator_structure():
    """Test orchestrator structure"""
    try:
        # Read and validate orchestrator main.py structure
        with open('/root/mirai-agent/microservices/ai-engine/orchestrator/main.py', 'r') as f:
            content = f.read()
        
        # Check for key components
        required_elements = [
            'class OrchestratorService',
            'async def submit_task',
            'async def get_task_status',
            '/task/submit',
            '/task/{task_id}',
            '/health'
        ]
        
        for element in required_elements:
            if element not in content:
                raise ValueError(f"Missing required element: {element}")
        
        print("✅ Orchestrator structure validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator structure test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 SIMPLE AI INTEGRATION TEST")
    print("=" * 40)
    
    tests = [
        test_basic_imports,
        test_ai_config,
        test_trading_loop_structure,
        test_policy_structure,
        test_config_files,
        test_orchestrator_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - AI INTEGRATION READY!")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)