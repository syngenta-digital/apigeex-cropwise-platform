"""
Test Endpoints

Unit tests for endpoint configuration and routing logic.
"""

import pytest
import json
from pathlib import Path


class TestEndpointConfiguration:
    """Tests for endpoint configuration."""
    
    @pytest.fixture
    def config_dir(self):
        """Get the config directory path."""
        return Path(__file__).parent.parent / "config"
    
    @pytest.fixture
    def endpoints_config(self, config_dir):
        """Load endpoints configuration."""
        with open(config_dir / "endpoints.json", 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def environments_config(self, config_dir):
        """Load environments configuration."""
        with open(config_dir / "environments.json", 'r') as f:
            return json.load(f)
    
    def test_endpoints_config_exists(self, config_dir):
        """Test that endpoints.json exists."""
        assert (config_dir / "endpoints.json").exists()
    
    def test_endpoints_has_default(self, endpoints_config):
        """Test that default endpoint is configured."""
        assert "endpoints" in endpoints_config
        assert "default" in endpoints_config["endpoints"]
    
    def test_path_mappings_exist(self, endpoints_config):
        """Test that path mappings are defined."""
        assert "path_mappings" in endpoints_config
        assert len(endpoints_config["path_mappings"]) > 0
    
    def test_health_endpoint_no_auth(self, endpoints_config):
        """Test that health endpoint doesn't require auth."""
        mappings = endpoints_config.get("path_mappings", {})
        health = mappings.get("/health", {})
        assert health.get("auth_required") is False
    
    def test_environments_have_backend_host(self, environments_config):
        """Test that all environments have backend hosts configured."""
        envs = environments_config.get("environments", {})
        
        for env_name, env_config in envs.items():
            assert "backend_host" in env_config, f"{env_name} missing backend_host"
            assert env_config["backend_host"], f"{env_name} has empty backend_host"
    
    def test_environments_have_base_path(self, environments_config):
        """Test that all environments have base path configured."""
        envs = environments_config.get("environments", {})
        
        for env_name, env_config in envs.items():
            assert "base_path" in env_config, f"{env_name} missing base_path"
            assert env_config["base_path"].startswith("/"), \
                f"{env_name} base_path should start with /"
    
    def test_all_required_environments_exist(self, environments_config):
        """Test that dev, qa, and prod environments are defined."""
        envs = environments_config.get("environments", {})
        required = ["dev", "qa", "prod"]
        
        for env in required:
            assert env in envs, f"Missing required environment: {env}"


class TestEndpointRouting:
    """Tests for endpoint routing logic."""
    
    def test_remote_sensing_path_pattern(self):
        """Test remote sensing path matching."""
        import re
        pattern = r"^/remote-sensing/.*"
        
        assert re.match(pattern, "/remote-sensing/v1/imagery")
        assert re.match(pattern, "/remote-sensing/v2/data")
        assert not re.match(pattern, "/v1/users")
    
    def test_accounts_path_pattern(self):
        """Test accounts path matching."""
        import re
        pattern = r"^/v2/accounts/.*"
        
        assert re.match(pattern, "/v2/accounts/ids")
        assert re.match(pattern, "/v2/accounts/123")
        assert not re.match(pattern, "/v1/accounts")
    
    def test_health_path_pattern(self):
        """Test health endpoint path matching."""
        import re
        pattern = r"^/health$"
        
        assert re.match(pattern, "/health")
        assert not re.match(pattern, "/health/check")
        assert not re.match(pattern, "/healthcheck")
