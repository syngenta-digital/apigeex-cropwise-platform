"""
Configuration Loader

Provides utilities for loading and validating configuration files.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv


class ConfigLoader:
    """Loads and validates configuration from files and environment."""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize the configuration loader.
        
        Args:
            base_dir: Base directory for configuration files.
                     Defaults to the project root.
        """
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Assume we're in scripts/utils, go up two levels
            self.base_dir = Path(__file__).parent.parent.parent
        
        self.config_dir = self.base_dir / "config"
        
        # Load environment variables from .env file
        env_file = self.base_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    
    def load_environments(self) -> Dict[str, Any]:
        """Load environment configurations."""
        config_file = self.config_dir / "environments.json"
        return self._load_json(config_file)
    
    def load_policies(self) -> Dict[str, Any]:
        """Load policy configurations."""
        config_file = self.config_dir / "policies.json"
        return self._load_json(config_file)
    
    def load_endpoints(self) -> Dict[str, Any]:
        """Load endpoint configurations."""
        config_file = self.config_dir / "endpoints.json"
        return self._load_json(config_file)
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a JSON file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def get_env_config(self, env: str) -> Dict[str, Any]:
        """
        Get configuration for a specific environment.
        
        Args:
            env: Environment name (dev, qa, prod)
            
        Returns:
            Environment-specific configuration dictionary
        """
        environments = self.load_environments()
        env_config = environments.get("environments", {}).get(env)
        
        if not env_config:
            raise ValueError(f"Environment '{env}' not found in configuration")
        
        # Override with environment variables if present
        env_overrides = {
            'apigee_org': os.getenv('APIGEE_ORG'),
            'apigee_env': os.getenv('APIGEE_ENV'),
        }
        
        for key, value in env_overrides.items():
            if value:
                env_config[key] = value
        
        return env_config
    
    def validate_config(self, env: str) -> bool:
        """
        Validate configuration for an environment.
        
        Args:
            env: Environment name to validate
            
        Returns:
            True if valid, raises exception otherwise
        """
        errors = []
        
        try:
            env_config = self.get_env_config(env)
            
            # Check required fields
            required_fields = [
                'name',
                'apigee_org',
                'apigee_env',
                'backend_host',
                'base_path'
            ]
            
            for field in required_fields:
                if not env_config.get(field):
                    errors.append(f"Missing required field: {field}")
            
            # Validate backend URL
            if env_config.get('backend_host'):
                host = env_config['backend_host']
                if not host or host == 'your-backend-host':
                    errors.append("Backend host not properly configured")
            
        except FileNotFoundError as e:
            errors.append(str(e))
        except ValueError as e:
            errors.append(str(e))
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
        
        return True
    
    def get_credentials_path(self) -> Optional[str]:
        """Get the path to Google Cloud credentials."""
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if creds_path and Path(creds_path).exists():
            return creds_path
        
        return None
    
    def get_backend_host(self, env: str) -> str:
        """Get the backend host for an environment."""
        # Check environment variable first
        env_var = f"BACKEND_HOST_{env.upper()}"
        host = os.getenv(env_var)
        
        if host:
            return host
        
        # Fall back to config file
        env_config = self.get_env_config(env)
        return env_config.get('backend_host', '')
