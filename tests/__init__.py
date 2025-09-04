"""
Test configuration for mirai-agent
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "app"))

# Set test environment variables
os.environ["DRY_RUN"] = "true"
os.environ["TESTNET"] = "true"
