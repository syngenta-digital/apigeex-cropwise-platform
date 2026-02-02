"""
Test Policies

Unit tests for Apigee policy configurations.
"""

import pytest
import json
import xml.etree.ElementTree as ET
from pathlib import Path


class TestPolicyConfiguration:
    """Tests for policy configuration."""
    
    @pytest.fixture
    def apiproxy_dir(self):
        """Get the apiproxy directory path."""
        return Path(__file__).parent.parent / "apiproxy"
    
    @pytest.fixture
    def policies_dir(self, apiproxy_dir):
        """Get the policies directory path."""
        return apiproxy_dir / "policies"
    
    @pytest.fixture
    def policies_config(self):
        """Load policies configuration."""
        config_path = Path(__file__).parent.parent / "config" / "policies.json"
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def test_policies_directory_exists(self, policies_dir):
        """Test that policies directory exists."""
        assert policies_dir.exists()
        assert policies_dir.is_dir()
    
    def test_required_policies_exist(self, policies_dir):
        """Test that required policies exist."""
        required_policies = [
            "AM-SetTarget.xml",
            "FC-Syng-Preflow.xml",
            "FC-Syng-ErrorHandling.xml",
            "FC-Syng-Logging.xml",
            "RF-APINotFound.xml",
            "EV-Extract-JWT-Token.xml",
            "JS-Parse-JWT-Token.xml"
        ]
        
        for policy in required_policies:
            assert (policies_dir / policy).exists(), f"Missing policy: {policy}"
    
    def test_all_policies_valid_xml(self, policies_dir):
        """Test that all policy files are valid XML."""
        for policy_file in policies_dir.glob("*.xml"):
            try:
                ET.parse(policy_file)
            except ET.ParseError as e:
                pytest.fail(f"Invalid XML in {policy_file.name}: {e}")
    
    def test_policies_have_display_name(self, policies_dir):
        """Test that all policies have DisplayName element."""
        for policy_file in policies_dir.glob("*.xml"):
            tree = ET.parse(policy_file)
            root = tree.getroot()
            
            display_name = root.find("DisplayName")
            assert display_name is not None, \
                f"{policy_file.name} missing DisplayName"
            assert display_name.text, \
                f"{policy_file.name} has empty DisplayName"
    
    def test_policies_have_name_attribute(self, policies_dir):
        """Test that all policies have name attribute."""
        for policy_file in policies_dir.glob("*.xml"):
            tree = ET.parse(policy_file)
            root = tree.getroot()
            
            name = root.get("name")
            assert name, f"{policy_file.name} missing name attribute"
            
            # Name should match filename (without .xml)
            expected_name = policy_file.stem
            assert name == expected_name, \
                f"{policy_file.name} name mismatch: {name} != {expected_name}"


class TestAMSetTarget:
    """Tests for AM-SetTarget policy."""
    
    @pytest.fixture
    def policy_path(self):
        """Get the policy file path."""
        return Path(__file__).parent.parent / "apiproxy" / "policies" / "AM-SetTarget.xml"
    
    def test_policy_exists(self, policy_path):
        """Test that policy file exists."""
        assert policy_path.exists()
    
    def test_copies_authorization_header(self, policy_path):
        """Test that Authorization header is copied."""
        tree = ET.parse(policy_path)
        root = tree.getroot()
        
        headers = root.findall(".//Header[@name='Authorization']")
        assert len(headers) > 0, "Authorization header not configured"
    
    def test_copies_content_type_header(self, policy_path):
        """Test that Content-Type header is copied."""
        tree = ET.parse(policy_path)
        root = tree.getroot()
        
        headers = root.findall(".//Header[@name='Content-Type']")
        assert len(headers) > 0, "Content-Type header not configured"


class TestFCSyngLogging:
    """Tests for FC-Syng-Logging policy."""
    
    @pytest.fixture
    def policy_path(self):
        """Get the policy file path."""
        return Path(__file__).parent.parent / "apiproxy" / "policies" / "FC-Syng-Logging.xml"
    
    def test_policy_exists(self, policy_path):
        """Test that policy file exists."""
        assert policy_path.exists()
    
    def test_has_syslog_configuration(self, policy_path):
        """Test that Syslog is configured."""
        tree = ET.parse(policy_path)
        root = tree.getroot()
        
        syslog = root.find(".//Syslog")
        assert syslog is not None, "Syslog not configured"
    
    def test_has_message_format(self, policy_path):
        """Test that message format is defined."""
        tree = ET.parse(policy_path)
        root = tree.getroot()
        
        message = root.find(".//Message")
        assert message is not None, "Message format not defined"
        assert message.text, "Message format is empty"
    
    def test_async_enabled(self, policy_path):
        """Test that async is enabled for logging."""
        tree = ET.parse(policy_path)
        root = tree.getroot()
        
        async_attr = root.get("async")
        assert async_attr == "true", "Logging should be async"


class TestRFAPINotFound:
    """Tests for RF-APINotFound policy."""
    
    @pytest.fixture
    def policy_path(self):
        """Get the policy file path."""
        return Path(__file__).parent.parent / "apiproxy" / "policies" / "RF-APINotFound.xml"
    
    def test_policy_exists(self, policy_path):
        """Test that policy file exists."""
        assert policy_path.exists()
    
    def test_returns_404_status(self, policy_path):
        """Test that 404 status code is returned."""
        tree = ET.parse(policy_path)
        root = tree.getroot()
        
        status_code = root.find(".//StatusCode")
        assert status_code is not None, "StatusCode not defined"
        assert status_code.text == "404", f"Expected 404, got {status_code.text}"
    
    def test_has_json_payload(self, policy_path):
        """Test that JSON payload is configured."""
        tree = ET.parse(policy_path)
        root = tree.getroot()
        
        payload = root.find(".//Payload")
        assert payload is not None, "Payload not defined"
        
        content_type = payload.get("contentType")
        assert content_type == "application/json", \
            f"Expected application/json, got {content_type}"
