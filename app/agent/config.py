"""
Configuration utilities for loading advisor and risk settings
"""
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def load_advisor_config(config_path: str = "configs/risk.yaml") -> Dict[str, Any]:
    """
    Load advisor configuration from YAML file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary with advisor configuration
    """
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Config file {config_path} not found, using defaults")
            return get_default_advisor_config()
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            
        advisor_config = config.get('advisor', {})
        
        # Ensure all required keys exist with defaults
        defaults = get_default_advisor_config()
        for key, default_value in defaults.items():
            if key not in advisor_config:
                advisor_config[key] = default_value
                logger.warning(f"Missing advisor config key '{key}', using default: {default_value}")
        
        return advisor_config
        
    except Exception as e:
        logger.error(f"Failed to load advisor config: {e}")
        return get_default_advisor_config()


def get_default_advisor_config() -> Dict[str, Any]:
    """Get default advisor configuration"""
    return {
        'ADVISOR_THRESHOLD': 0.70,
        'RECOVERY_THRESHOLD': 0.80,
        'RECOVERY_MAX_TRIES': 3
    }