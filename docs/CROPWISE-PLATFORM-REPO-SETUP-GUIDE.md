# Cropwise Unified Platform - Apigee X Proxy Repository Setup Guide

**Project:** Cropwise Unified Platform API Proxy  
**Date:** February 2, 2026  
**Version:** 1.0  
**Team:** CropwisePlatform Team

---

## Table of Contents

1. [Overview](#overview)
2. [Repository Structure](#repository-structure)
3. [Prerequisites](#prerequisites)
4. [Step 1: Repository Setup](#step-1-repository-setup)
5. [Step 2: Proxy Generation Script](#step-2-proxy-generation-script)
6. [Step 3: Deployment Script](#step-3-deployment-script)
7. [Step 4: Testing Script](#step-4-testing-script)
8. [Step 5: Configuration Guide](#step-5-configuration-guide)
9. [Policy Customization Reference](#policy-customization-reference)
10. [CI/CD Integration](#cicd-integration)
11. [Troubleshooting](#troubleshooting)

---

## Overview

This document provides step-by-step instructions for the CropwisePlatform team to:
- Set up a dedicated repository for the cropwise-unified-platform Apigee X proxy
- Generate, deploy, and test proxies using Python scripts
- Customize policies and configurations for their platform needs

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CropwisePlatform Repository                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │   apiproxy/ │   │   scripts/  │   │   tests/    │           │
│  │  (Policies) │   │  (Python)   │   │  (Python)   │           │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘           │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              generate_proxy.py                           │   │
│  │              deploy_proxy.py                             │   │
│  │              test_proxy.py                               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Apigee X      │
                    │   (dev/qa/prod) │
                    └─────────────────┘
```

---

## Repository Structure

```
cropwise-unified-platform-proxy/
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── config/
│   ├── environments.json          # Environment configurations
│   ├── policies.json              # Policy customization settings
│   └── endpoints.json             # Target endpoint mappings
├── apiproxy/
│   ├── cropwise-unified-platform-proxy.xml
│   ├── policies/
│   │   ├── AM-SetTarget.xml
│   │   ├── AM-InvalidAPIKey.xml
│   │   ├── AM-Apply-ReadOnly-Prefix.xml
│   │   ├── AM-Protector-Alerts-Special-Case.xml
│   │   ├── AM-Rewrite-OAuth-Token-URI.xml
│   │   ├── AM-Rewrite-Remote-Sensing-URI.xml
│   │   ├── AM-Set-Default-Rate-Limit.xml
│   │   ├── AM-Set-High-Rate-Header.xml
│   │   ├── AM-Set-Low-Rate-Header.xml
│   │   ├── AM-Set-Medium-Rate-Header.xml
│   │   ├── AM-Set-Rate-Limit-Headers.xml
│   │   ├── EV-Extract-JWT-Token.xml
│   │   ├── FC-Syng-ErrorHandling.xml
│   │   ├── FC-Syng-Logging.xml
│   │   ├── FC-Syng-Preflow.xml
│   │   ├── JS-Handle-ReadOnly-Routes.xml
│   │   ├── JS-Parse-JWT-Token.xml
│   │   ├── KVM-Get-User-Rate-Limit.xml
│   │   └── RF-APINotFound.xml
│   ├── proxies/
│   │   └── default.xml
│   ├── resources/
│   │   └── jsc/
│   │       ├── handle-readonly-routes.js
│   │       └── parse-jwt-token.js
│   └── targets/
│       └── default.xml
├── scripts/
│   ├── generate_proxy.py          # Proxy bundle generation
│   ├── deploy_proxy.py            # Deployment to Apigee X
│   ├── test_proxy.py              # API testing
│   └── utils/
│       ├── __init__.py
│       ├── apigee_client.py       # Apigee API client
│       └── config_loader.py       # Configuration loader
├── tests/
│   ├── __init__.py
│   ├── test_endpoints.py
│   ├── test_policies.py
│   └── fixtures/
│       └── test_tokens.json
└── docs/
    ├── DEPLOYMENT-GUIDE.md
    ├── POLICY-REFERENCE.md
    └── TROUBLESHOOTING.md
```

---

## Prerequisites

### 1. Software Requirements

- Python 3.9+
- Git
- Google Cloud SDK (gcloud CLI)
- Access to Apigee X organization

### 2. Access Requirements

- Apigee X organization admin or deployer role
- Service account with Apigee API access
- Access to target backend services

### 3. Python Dependencies

```txt
# requirements.txt
google-auth==2.23.0
google-auth-oauthlib==1.1.0
google-api-python-client==2.100.0
requests==2.31.0
pyyaml==6.0.1
python-dotenv==1.0.0
pytest==7.4.2
pytest-asyncio==0.21.1
httpx==0.25.0
colorama==0.4.6
```

---

## Step 1: Repository Setup

### 1.1 Create New Repository

```bash
# Create repository directory
mkdir cropwise-unified-platform-proxy
cd cropwise-unified-platform-proxy

# Initialize git
git init

# Create branch structure
git checkout -b main
git checkout -b develop
git checkout -b feature/initial-setup
```

### 1.2 Create .gitignore

```gitignore
# .gitignore
*.pyc
__pycache__/
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache/
.hypothesis/

# Environment files
.env
.env.local
*.env

# IDE
.idea/
.vscode/
*.swp
*.swo

# Build artifacts
*.zip
dist/
build/
*.egg-info/

# Apigee bundles
*.bundle.zip
deployment-*.json
```

### 1.3 Create Environment Configuration

```bash
# .env.example
APIGEE_ORG=your-apigee-org
APIGEE_ENV=dev
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
BACKEND_HOST_DEV=dev.api.insights.cropwise.com
BACKEND_HOST_QA=qa.api.insights.cropwise.com
BACKEND_HOST_PROD=api.insights.cropwise.com
```

### 1.4 Create environments.json

```json
{
    "environments": {
        "dev": {
            "name": "dev",
            "apigee_org": "your-apigee-org",
            "apigee_env": "dev",
            "backend_host": "dev.api.insights.cropwise.com",
            "backend_port": 443,
            "backend_protocol": "https",
            "virtual_hosts": ["default", "secure"],
            "base_path": "/cropwise-unified-platform",
            "syslog_host": "syslog-dev.internal.com",
            "syslog_port": 514
        },
        "qa": {
            "name": "qa",
            "apigee_org": "your-apigee-org",
            "apigee_env": "qa",
            "backend_host": "qa.api.insights.cropwise.com",
            "backend_port": 443,
            "backend_protocol": "https",
            "virtual_hosts": ["default", "secure"],
            "base_path": "/cropwise-unified-platform",
            "syslog_host": "syslog-qa.internal.com",
            "syslog_port": 514
        },
        "prod": {
            "name": "prod",
            "apigee_org": "your-apigee-org",
            "apigee_env": "prod",
            "backend_host": "api.insights.cropwise.com",
            "backend_port": 443,
            "backend_protocol": "https",
            "virtual_hosts": ["default", "secure"],
            "base_path": "/cropwise-unified-platform",
            "syslog_host": "syslog.internal.com",
            "syslog_port": 514
        }
    }
}
```

---

## Step 2: Proxy Generation Script

### 2.1 Create generate_proxy.py

```python
#!/usr/bin/env python3
"""
Cropwise Unified Platform - Proxy Bundle Generator

This script generates an Apigee X proxy bundle with environment-specific
configurations for the cropwise-unified-platform proxy.

Usage:
    python scripts/generate_proxy.py --env dev
    python scripts/generate_proxy.py --env qa --output ./dist
    python scripts/generate_proxy.py --env prod --validate
"""

import os
import sys
import json
import shutil
import zipfile
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class ProxyGenerator:
    """Generates Apigee X proxy bundles with environment-specific configurations."""
    
    def __init__(self, base_dir: str, env: str, config_path: str = None):
        self.base_dir = Path(base_dir)
        self.env = env
        self.config_path = config_path or self.base_dir / "config" / "environments.json"
        self.apiproxy_dir = self.base_dir / "apiproxy"
        self.config = self._load_config()
        self.env_config = self.config["environments"].get(env)
        
        if not self.env_config:
            raise ValueError(f"Environment '{env}' not found in configuration")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load environment configuration from JSON file."""
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def _update_target_endpoint(self, target_file: Path, temp_dir: Path) -> None:
        """Update target endpoint with environment-specific backend settings."""
        tree = ET.parse(target_file)
        root = tree.getroot()
        
        # Update HTTPTargetConnection
        http_target = root.find('.//HTTPTargetConnection')
        if http_target is not None:
            # Update URL
            url_elem = http_target.find('URL')
            if url_elem is not None:
                protocol = self.env_config.get('backend_protocol', 'https')
                host = self.env_config['backend_host']
                port = self.env_config.get('backend_port', 443)
                url_elem.text = f"{protocol}://{host}:{port}"
            
            # Update SSLInfo if exists
            ssl_info = http_target.find('SSLInfo')
            if ssl_info is None and self.env_config.get('backend_protocol') == 'https':
                ssl_info = ET.SubElement(http_target, 'SSLInfo')
                enabled = ET.SubElement(ssl_info, 'Enabled')
                enabled.text = 'true'
        
        # Write updated file
        output_file = temp_dir / "targets" / target_file.name
        output_file.parent.mkdir(parents=True, exist_ok=True)
        tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    
    def _update_proxy_endpoint(self, proxy_file: Path, temp_dir: Path) -> None:
        """Update proxy endpoint with environment-specific settings."""
        tree = ET.parse(proxy_file)
        root = tree.getroot()
        
        # Update VirtualHosts
        http_proxy = root.find('.//HTTPProxyConnection')
        if http_proxy is not None:
            # Remove existing VirtualHost elements
            for vh in http_proxy.findall('VirtualHost'):
                http_proxy.remove(vh)
            
            # Add environment-specific VirtualHosts
            for vh_name in self.env_config.get('virtual_hosts', ['default', 'secure']):
                vh_elem = ET.SubElement(http_proxy, 'VirtualHost')
                vh_elem.text = vh_name
            
            # Update BasePath if specified
            base_path = http_proxy.find('BasePath')
            if base_path is not None and self.env_config.get('base_path'):
                base_path.text = self.env_config['base_path']
        
        # Write updated file
        output_file = temp_dir / "proxies" / proxy_file.name
        output_file.parent.mkdir(parents=True, exist_ok=True)
        tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    
    def _update_logging_policy(self, policy_file: Path, temp_dir: Path) -> None:
        """Update logging policy with environment-specific syslog settings."""
        tree = ET.parse(policy_file)
        root = tree.getroot()
        
        # Update Syslog settings
        syslog = root.find('.//Syslog')
        if syslog is not None:
            host = syslog.find('Host')
            if host is not None:
                host.text = self.env_config.get('syslog_host', 'localhost')
            
            port = syslog.find('Port')
            if port is not None:
                port.text = str(self.env_config.get('syslog_port', 514))
        
        # Write updated file
        output_file = temp_dir / "policies" / policy_file.name
        output_file.parent.mkdir(parents=True, exist_ok=True)
        tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    
    def _copy_and_update_policies(self, temp_dir: Path) -> None:
        """Copy and update all policy files."""
        policies_dir = self.apiproxy_dir / "policies"
        output_policies_dir = temp_dir / "policies"
        output_policies_dir.mkdir(parents=True, exist_ok=True)
        
        for policy_file in policies_dir.glob("*.xml"):
            if policy_file.name == "FC-Syng-Logging.xml":
                self._update_logging_policy(policy_file, temp_dir)
            else:
                shutil.copy2(policy_file, output_policies_dir / policy_file.name)
    
    def _copy_resources(self, temp_dir: Path) -> None:
        """Copy JavaScript and other resource files."""
        resources_dir = self.apiproxy_dir / "resources"
        if resources_dir.exists():
            output_resources_dir = temp_dir / "resources"
            shutil.copytree(resources_dir, output_resources_dir)
    
    def _copy_proxy_descriptor(self, temp_dir: Path) -> None:
        """Copy and update the main proxy descriptor XML."""
        for xml_file in self.apiproxy_dir.glob("*.xml"):
            if xml_file.is_file():
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Update revision if needed
                revision = root.get('revision')
                if revision:
                    # Increment revision for new deployment
                    root.set('revision', str(int(revision) + 1))
                
                # Add deployment timestamp as description
                desc = root.find('Description')
                if desc is not None:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    desc.text = f"{desc.text} | Deployed: {timestamp} | Env: {self.env}"
                
                tree.write(temp_dir / xml_file.name, encoding='UTF-8', xml_declaration=True)
    
    def validate(self) -> bool:
        """Validate the proxy structure and configuration."""
        errors = []
        
        # Check required directories
        required_dirs = ['policies', 'proxies', 'targets']
        for dir_name in required_dirs:
            dir_path = self.apiproxy_dir / dir_name
            if not dir_path.exists():
                errors.append(f"Missing required directory: {dir_name}")
        
        # Check required policies
        required_policies = [
            'AM-SetTarget.xml',
            'FC-Syng-Preflow.xml',
            'FC-Syng-ErrorHandling.xml',
            'FC-Syng-Logging.xml',
            'RF-APINotFound.xml'
        ]
        policies_dir = self.apiproxy_dir / "policies"
        for policy in required_policies:
            if not (policies_dir / policy).exists():
                errors.append(f"Missing required policy: {policy}")
        
        # Validate XML syntax
        for xml_file in self.apiproxy_dir.rglob("*.xml"):
            try:
                ET.parse(xml_file)
            except ET.ParseError as e:
                errors.append(f"Invalid XML in {xml_file.name}: {e}")
        
        if errors:
            print("Validation Errors:")
            for error in errors:
                print(f"  ❌ {error}")
            return False
        
        print("✅ Validation passed!")
        return True
    
    def generate(self, output_dir: str = None) -> str:
        """Generate the proxy bundle ZIP file."""
        output_path = Path(output_dir) if output_dir else self.base_dir / "dist"
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        bundle_name = f"cropwise-unified-platform-{self.env}-{timestamp}"
        temp_dir = output_path / bundle_name / "apiproxy"
        
        try:
            # Create temp directory structure
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Process all components
            print(f"Generating proxy bundle for environment: {self.env}")
            
            # Copy and update proxy descriptor
            print("  → Processing proxy descriptor...")
            self._copy_proxy_descriptor(temp_dir)
            
            # Process proxy endpoints
            print("  → Processing proxy endpoints...")
            for proxy_file in (self.apiproxy_dir / "proxies").glob("*.xml"):
                self._update_proxy_endpoint(proxy_file, temp_dir)
            
            # Process target endpoints
            print("  → Processing target endpoints...")
            for target_file in (self.apiproxy_dir / "targets").glob("*.xml"):
                self._update_target_endpoint(target_file, temp_dir)
            
            # Copy and update policies
            print("  → Processing policies...")
            self._copy_and_update_policies(temp_dir)
            
            # Copy resources
            print("  → Copying resources...")
            self._copy_resources(temp_dir)
            
            # Create ZIP bundle
            zip_path = output_path / f"{bundle_name}.zip"
            print(f"  → Creating bundle: {zip_path}")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_dir.parent)
                        zipf.write(file_path, arcname)
            
            # Cleanup temp directory
            shutil.rmtree(temp_dir.parent)
            
            print(f"\n✅ Bundle generated successfully: {zip_path}")
            return str(zip_path)
            
        except Exception as e:
            # Cleanup on error
            if temp_dir.parent.exists():
                shutil.rmtree(temp_dir.parent)
            raise RuntimeError(f"Failed to generate bundle: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate Apigee X proxy bundle for Cropwise Unified Platform'
    )
    parser.add_argument(
        '--env', '-e',
        required=True,
        choices=['dev', 'qa', 'prod'],
        help='Target environment'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output directory for the bundle'
    )
    parser.add_argument(
        '--validate', '-v',
        action='store_true',
        help='Validate proxy structure before generating'
    )
    parser.add_argument(
        '--config', '-c',
        default=None,
        help='Path to environments.json configuration file'
    )
    
    args = parser.parse_args()
    
    # Determine base directory
    base_dir = Path(__file__).parent.parent
    
    try:
        generator = ProxyGenerator(
            base_dir=str(base_dir),
            env=args.env,
            config_path=args.config
        )
        
        if args.validate:
            if not generator.validate():
                sys.exit(1)
        
        bundle_path = generator.generate(args.output)
        print(f"\nBundle ready for deployment: {bundle_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## Step 3: Deployment Script

### 3.1 Create deploy_proxy.py

```python
#!/usr/bin/env python3
"""
Cropwise Unified Platform - Apigee X Deployment Script

This script deploys the proxy bundle to Apigee X environments.

Usage:
    python scripts/deploy_proxy.py --env dev --bundle ./dist/bundle.zip
    python scripts/deploy_proxy.py --env qa --bundle ./dist/bundle.zip --deploy
    python scripts/deploy_proxy.py --env prod --bundle ./dist/bundle.zip --deploy --wait
"""

import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2 import service_account


class ApigeeXClient:
    """Client for interacting with Apigee X Management APIs."""
    
    BASE_URL = "https://apigee.googleapis.com/v1"
    
    def __init__(self, org: str, credentials_path: str = None):
        self.org = org
        self.credentials = self._get_credentials(credentials_path)
        self.session = requests.Session()
    
    def _get_credentials(self, credentials_path: str = None):
        """Get Google Cloud credentials."""
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
        else:
            credentials, _ = default(
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
        return credentials
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Get authorization header with fresh token."""
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return {"Authorization": f"Bearer {self.credentials.token}"}
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated request to Apigee API."""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = self._get_auth_header()
        headers.update(kwargs.pop('headers', {}))
        
        response = self.session.request(method, url, headers=headers, **kwargs)
        return response
    
    def upload_proxy(self, proxy_name: str, bundle_path: str) -> Dict[str, Any]:
        """Upload proxy bundle to Apigee X."""
        endpoint = f"organizations/{self.org}/apis"
        
        with open(bundle_path, 'rb') as f:
            files = {'file': (Path(bundle_path).name, f, 'application/zip')}
            params = {'name': proxy_name, 'action': 'import'}
            
            response = self._make_request(
                'POST',
                endpoint,
                params=params,
                files=files
            )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise RuntimeError(
                f"Failed to upload proxy: {response.status_code} - {response.text}"
            )
    
    def get_proxy_revisions(self, proxy_name: str) -> list:
        """Get all revisions of a proxy."""
        endpoint = f"organizations/{self.org}/apis/{proxy_name}/revisions"
        response = self._make_request('GET', endpoint)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return []
        else:
            raise RuntimeError(
                f"Failed to get revisions: {response.status_code} - {response.text}"
            )
    
    def deploy_proxy(self, proxy_name: str, revision: str, env: str) -> Dict[str, Any]:
        """Deploy a proxy revision to an environment."""
        endpoint = (
            f"organizations/{self.org}/environments/{env}/"
            f"apis/{proxy_name}/revisions/{revision}/deployments"
        )
        
        response = self._make_request('POST', endpoint)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise RuntimeError(
                f"Failed to deploy proxy: {response.status_code} - {response.text}"
            )
    
    def get_deployment_status(self, proxy_name: str, env: str) -> Dict[str, Any]:
        """Get deployment status for a proxy in an environment."""
        endpoint = (
            f"organizations/{self.org}/environments/{env}/"
            f"apis/{proxy_name}/deployments"
        )
        
        response = self._make_request('GET', endpoint)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"deployments": []}
        else:
            raise RuntimeError(
                f"Failed to get deployment status: {response.status_code} - {response.text}"
            )
    
    def undeploy_proxy(self, proxy_name: str, revision: str, env: str) -> bool:
        """Undeploy a proxy revision from an environment."""
        endpoint = (
            f"organizations/{self.org}/environments/{env}/"
            f"apis/{proxy_name}/revisions/{revision}/deployments"
        )
        
        response = self._make_request('DELETE', endpoint)
        return response.status_code in [200, 204]
    
    def wait_for_deployment(
        self,
        proxy_name: str,
        revision: str,
        env: str,
        timeout: int = 120,
        interval: int = 5
    ) -> bool:
        """Wait for deployment to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_deployment_status(proxy_name, env)
            deployments = status.get('deployments', [])
            
            for deployment in deployments:
                if deployment.get('revision') == revision:
                    state = deployment.get('state', '')
                    if state == 'READY':
                        return True
                    elif state in ['ERROR', 'FAILED']:
                        raise RuntimeError(
                            f"Deployment failed with state: {state}"
                        )
            
            print(f"  ⏳ Waiting for deployment... ({int(time.time() - start_time)}s)")
            time.sleep(interval)
        
        raise TimeoutError(f"Deployment did not complete within {timeout} seconds")


class ProxyDeployer:
    """Handles the deployment of Apigee X proxies."""
    
    PROXY_NAME = "cropwise-unified-platform"
    
    def __init__(self, env: str, config_path: str = None, credentials_path: str = None):
        self.env = env
        self.config = self._load_config(config_path)
        self.env_config = self.config["environments"].get(env)
        
        if not self.env_config:
            raise ValueError(f"Environment '{env}' not found in configuration")
        
        self.client = ApigeeXClient(
            org=self.env_config['apigee_org'],
            credentials_path=credentials_path
        )
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file."""
        path = Path(config_path) if config_path else (
            Path(__file__).parent.parent / "config" / "environments.json"
        )
        with open(path, 'r') as f:
            return json.load(f)
    
    def upload(self, bundle_path: str) -> Tuple[str, str]:
        """Upload the proxy bundle."""
        print(f"\n📦 Uploading proxy bundle: {bundle_path}")
        
        result = self.client.upload_proxy(self.PROXY_NAME, bundle_path)
        revision = result.get('revision', 'unknown')
        
        print(f"  ✅ Uploaded successfully - Revision: {revision}")
        return self.PROXY_NAME, revision
    
    def deploy(self, revision: str, undeploy_existing: bool = True) -> Dict[str, Any]:
        """Deploy the proxy revision to the environment."""
        env = self.env_config['apigee_env']
        
        print(f"\n🚀 Deploying revision {revision} to {env}...")
        
        # Check for existing deployments
        if undeploy_existing:
            status = self.client.get_deployment_status(self.PROXY_NAME, env)
            for deployment in status.get('deployments', []):
                existing_rev = deployment.get('revision')
                if existing_rev and existing_rev != revision:
                    print(f"  ⏸️  Undeploying existing revision: {existing_rev}")
                    self.client.undeploy_proxy(self.PROXY_NAME, existing_rev, env)
        
        # Deploy new revision
        result = self.client.deploy_proxy(self.PROXY_NAME, revision, env)
        print(f"  ✅ Deployment initiated")
        
        return result
    
    def wait_for_ready(self, revision: str, timeout: int = 120) -> bool:
        """Wait for deployment to be ready."""
        env = self.env_config['apigee_env']
        
        print(f"\n⏳ Waiting for deployment to be ready...")
        
        try:
            self.client.wait_for_deployment(
                self.PROXY_NAME,
                revision,
                env,
                timeout=timeout
            )
            print(f"  ✅ Deployment is READY!")
            return True
        except (TimeoutError, RuntimeError) as e:
            print(f"  ❌ {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current deployment status."""
        env = self.env_config['apigee_env']
        return self.client.get_deployment_status(self.PROXY_NAME, env)
    
    def full_deploy(
        self,
        bundle_path: str,
        wait: bool = True,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """Perform full deployment: upload, deploy, and optionally wait."""
        
        result = {
            'proxy_name': self.PROXY_NAME,
            'environment': self.env,
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            # Upload
            _, revision = self.upload(bundle_path)
            result['revision'] = revision
            
            # Deploy
            deploy_result = self.deploy(revision)
            result['deploy_response'] = deploy_result
            
            # Wait
            if wait:
                ready = self.wait_for_ready(revision, timeout)
                result['ready'] = ready
                result['success'] = ready
            else:
                result['success'] = True
            
            # Save deployment result
            self._save_result(result)
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            self._save_result(result)
            raise
    
    def _save_result(self, result: Dict[str, Any]) -> None:
        """Save deployment result to file."""
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        output_dir = Path(__file__).parent.parent / "dist"
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"deployment-{self.env}-{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n📄 Deployment result saved: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Deploy Cropwise Unified Platform proxy to Apigee X'
    )
    parser.add_argument(
        '--env', '-e',
        required=True,
        choices=['dev', 'qa', 'prod'],
        help='Target environment'
    )
    parser.add_argument(
        '--bundle', '-b',
        required=True,
        help='Path to the proxy bundle ZIP file'
    )
    parser.add_argument(
        '--deploy', '-d',
        action='store_true',
        help='Deploy after uploading (default: upload only)'
    )
    parser.add_argument(
        '--wait', '-w',
        action='store_true',
        help='Wait for deployment to be ready'
    )
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=120,
        help='Deployment timeout in seconds (default: 120)'
    )
    parser.add_argument(
        '--config', '-c',
        default=None,
        help='Path to environments.json configuration file'
    )
    parser.add_argument(
        '--credentials',
        default=None,
        help='Path to service account credentials JSON'
    )
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show current deployment status and exit'
    )
    
    args = parser.parse_args()
    
    # Validate bundle exists
    bundle_path = Path(args.bundle)
    if not args.status and not bundle_path.exists():
        print(f"❌ Bundle file not found: {bundle_path}")
        sys.exit(1)
    
    try:
        deployer = ProxyDeployer(
            env=args.env,
            config_path=args.config,
            credentials_path=args.credentials
        )
        
        if args.status:
            status = deployer.get_status()
            print(json.dumps(status, indent=2))
            return
        
        if args.deploy:
            result = deployer.full_deploy(
                bundle_path=str(bundle_path),
                wait=args.wait,
                timeout=args.timeout
            )
            
            if result.get('success'):
                print("\n✅ Deployment completed successfully!")
            else:
                print("\n⚠️  Deployment completed with warnings")
                sys.exit(1)
        else:
            # Upload only
            _, revision = deployer.upload(str(bundle_path))
            print(f"\n✅ Upload complete. Revision: {revision}")
            print(f"   Run with --deploy flag to deploy this revision")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## Step 4: Testing Script

### 4.1 Create test_proxy.py

```python
#!/usr/bin/env python3
"""
Cropwise Unified Platform - Proxy Testing Script

This script tests the deployed proxy endpoints to verify functionality.

Usage:
    python scripts/test_proxy.py --env dev
    python scripts/test_proxy.py --env qa --verbose
    python scripts/test_proxy.py --env prod --test-suite smoke
"""

import os
import sys
import json
import time
import argparse
import base64
import jwt
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

import requests
from colorama import init, Fore, Style

# Initialize colorama for Windows
init()


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    duration_ms: float
    message: str = ""
    response_code: int = 0
    response_body: str = ""


class JWTGenerator:
    """Generates test JWT tokens."""
    
    def __init__(self, secret: str = "test-secret-key"):
        self.secret = secret
    
    def generate_token(
        self,
        username: str,
        client_id: str = "test-client",
        expires_in: int = 3600,
        custom_claims: Dict[str, Any] = None
    ) -> str:
        """Generate a JWT token for testing."""
        now = datetime.utcnow()
        payload = {
            "sub": username,
            "username": username,
            "client_id": client_id,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
            "iss": "cropwise-test"
        }
        
        if custom_claims:
            payload.update(custom_claims)
        
        return jwt.encode(payload, self.secret, algorithm="HS256")


class ProxyTester:
    """Tests Apigee X proxy endpoints."""
    
    def __init__(self, env: str, config_path: str = None, verbose: bool = False):
        self.env = env
        self.verbose = verbose
        self.config = self._load_config(config_path)
        self.env_config = self.config["environments"].get(env)
        
        if not self.env_config:
            raise ValueError(f"Environment '{env}' not found in configuration")
        
        self.base_url = self._get_base_url()
        self.jwt_generator = JWTGenerator()
        self.results: List[TestResult] = []
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file."""
        path = Path(config_path) if config_path else (
            Path(__file__).parent.parent / "config" / "environments.json"
        )
        with open(path, 'r') as f:
            return json.load(f)
    
    def _get_base_url(self) -> str:
        """Construct the base URL for testing."""
        # This should be updated based on your Apigee X hostname configuration
        org = self.env_config['apigee_org']
        env = self.env_config['apigee_env']
        base_path = self.env_config['base_path']
        
        # Default Apigee X hostname pattern
        return f"https://{org}-{env}.apigee.net{base_path}"
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log message with color."""
        colors = {
            "INFO": Fore.CYAN,
            "SUCCESS": Fore.GREEN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED
        }
        color = colors.get(level, Fore.WHITE)
        print(f"{color}{message}{Style.RESET_ALL}")
    
    def _make_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str] = None,
        data: Any = None,
        timeout: int = 30
    ) -> requests.Response:
        """Make HTTP request to the proxy."""
        url = f"{self.base_url}{path}"
        
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if headers:
            default_headers.update(headers)
        
        if self.verbose:
            self._log(f"  → {method} {url}", "INFO")
        
        response = requests.request(
            method=method,
            url=url,
            headers=default_headers,
            json=data if data else None,
            timeout=timeout,
            verify=True
        )
        
        if self.verbose:
            self._log(f"  ← {response.status_code} ({response.elapsed.total_seconds()*1000:.0f}ms)", "INFO")
        
        return response
    
    def run_test(
        self,
        name: str,
        method: str,
        path: str,
        headers: Dict[str, str] = None,
        data: Any = None,
        expected_status: int = 200,
        validate_response: callable = None
    ) -> TestResult:
        """Run a single test case."""
        start_time = time.time()
        
        try:
            response = self._make_request(method, path, headers, data)
            duration_ms = (time.time() - start_time) * 1000
            
            # Check status code
            if response.status_code != expected_status:
                return TestResult(
                    name=name,
                    status=TestStatus.FAILED,
                    duration_ms=duration_ms,
                    message=f"Expected {expected_status}, got {response.status_code}",
                    response_code=response.status_code,
                    response_body=response.text[:500]
                )
            
            # Custom validation
            if validate_response:
                validation_result = validate_response(response)
                if not validation_result[0]:
                    return TestResult(
                        name=name,
                        status=TestStatus.FAILED,
                        duration_ms=duration_ms,
                        message=validation_result[1],
                        response_code=response.status_code,
                        response_body=response.text[:500]
                    )
            
            return TestResult(
                name=name,
                status=TestStatus.PASSED,
                duration_ms=duration_ms,
                response_code=response.status_code
            )
            
        except requests.exceptions.Timeout:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                name=name,
                status=TestStatus.ERROR,
                duration_ms=duration_ms,
                message="Request timed out"
            )
        except requests.exceptions.ConnectionError as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                name=name,
                status=TestStatus.ERROR,
                duration_ms=duration_ms,
                message=f"Connection error: {str(e)}"
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                name=name,
                status=TestStatus.ERROR,
                duration_ms=duration_ms,
                message=f"Unexpected error: {str(e)}"
            )
    
    # ============== Test Cases ==============
    
    def test_health_check(self) -> TestResult:
        """Test basic connectivity to the proxy."""
        return self.run_test(
            name="Health Check",
            method="GET",
            path="/health",
            expected_status=200
        )
    
    def test_unauthorized_request(self) -> TestResult:
        """Test that requests without auth are handled correctly."""
        return self.run_test(
            name="Unauthorized Request",
            method="GET",
            path="/v1/users",
            expected_status=401
        )
    
    def test_authorized_request(self) -> TestResult:
        """Test request with valid JWT token."""
        token = self.jwt_generator.generate_token(
            username="test.user@syngenta.com",
            client_id="strider-ui"
        )
        
        return self.run_test(
            name="Authorized Request",
            method="GET",
            path="/v1/users",
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200
        )
    
    def test_invalid_path(self) -> TestResult:
        """Test that invalid paths return 404."""
        return self.run_test(
            name="Invalid Path Returns 404",
            method="GET",
            path="/invalid/path/that/does/not/exist",
            expected_status=404
        )
    
    def test_request_id_header(self) -> TestResult:
        """Test that x-request-id header is added to response."""
        token = self.jwt_generator.generate_token(username="test.user@syngenta.com")
        
        def validate_request_id(response):
            if 'x-request-id' in response.headers:
                return (True, "")
            return (False, "x-request-id header not found in response")
        
        return self.run_test(
            name="Request ID Header Present",
            method="GET",
            path="/v1/users",
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200,
            validate_response=validate_request_id
        )
    
    def test_rate_limit_headers(self) -> TestResult:
        """Test that rate limit headers are present for authenticated users."""
        token = self.jwt_generator.generate_token(
            username="test.user@syngenta.com",
            client_id="test-client"
        )
        
        def validate_rate_limit(response):
            headers = response.headers
            required = ['x-ratelimit-type']
            missing = [h for h in required if h.lower() not in [k.lower() for k in headers.keys()]]
            
            if missing:
                return (False, f"Missing rate limit headers: {missing}")
            return (True, "")
        
        return self.run_test(
            name="Rate Limit Headers Present",
            method="GET",
            path="/v1/users",
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200,
            validate_response=validate_rate_limit
        )
    
    def test_remote_sensing_rewrite(self) -> TestResult:
        """Test remote sensing URI rewrite."""
        token = self.jwt_generator.generate_token(username="test.user@syngenta.com")
        
        return self.run_test(
            name="Remote Sensing URI Rewrite",
            method="GET",
            path="/remote-sensing/v1/imagery",
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200
        )
    
    def test_protector_alerts_special_case(self) -> TestResult:
        """Test protector alerts special case handling."""
        token = self.jwt_generator.generate_token(
            username="protector.alerts.account@syngenta.com",
            client_id="strider-ui"
        )
        
        return self.run_test(
            name="Protector Alerts Special Case",
            method="GET",
            path="/v2/accounts/ids",
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200
        )
    
    def test_content_type_passthrough(self) -> TestResult:
        """Test that Content-Type header is passed through."""
        token = self.jwt_generator.generate_token(username="test.user@syngenta.com")
        
        return self.run_test(
            name="Content-Type Passthrough",
            method="POST",
            path="/v1/data",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            data={"test": "data"},
            expected_status=200
        )
    
    def test_error_response_format(self) -> TestResult:
        """Test that error responses have correct JSON format."""
        def validate_error_format(response):
            try:
                body = response.json()
                if 'message' in body or 'error' in body:
                    return (True, "")
                return (False, "Error response missing required fields")
            except:
                return (False, "Error response is not valid JSON")
        
        return self.run_test(
            name="Error Response Format",
            method="GET",
            path="/nonexistent",
            expected_status=404,
            validate_response=validate_error_format
        )
    
    # ============== Test Suites ==============
    
    def run_smoke_tests(self) -> List[TestResult]:
        """Run smoke test suite (quick validation)."""
        self._log("\n🔥 Running Smoke Tests...\n", "INFO")
        
        tests = [
            self.test_health_check,
            self.test_unauthorized_request,
            self.test_invalid_path,
        ]
        
        return self._run_tests(tests)
    
    def run_functional_tests(self) -> List[TestResult]:
        """Run functional test suite (comprehensive)."""
        self._log("\n🧪 Running Functional Tests...\n", "INFO")
        
        tests = [
            self.test_health_check,
            self.test_unauthorized_request,
            self.test_authorized_request,
            self.test_invalid_path,
            self.test_request_id_header,
            self.test_rate_limit_headers,
            self.test_error_response_format,
        ]
        
        return self._run_tests(tests)
    
    def run_integration_tests(self) -> List[TestResult]:
        """Run integration test suite (includes backend interactions)."""
        self._log("\n🔗 Running Integration Tests...\n", "INFO")
        
        tests = [
            self.test_health_check,
            self.test_authorized_request,
            self.test_remote_sensing_rewrite,
            self.test_protector_alerts_special_case,
            self.test_content_type_passthrough,
        ]
        
        return self._run_tests(tests)
    
    def run_all_tests(self) -> List[TestResult]:
        """Run all test suites."""
        self._log("\n🚀 Running All Tests...\n", "INFO")
        
        tests = [
            self.test_health_check,
            self.test_unauthorized_request,
            self.test_authorized_request,
            self.test_invalid_path,
            self.test_request_id_header,
            self.test_rate_limit_headers,
            self.test_remote_sensing_rewrite,
            self.test_protector_alerts_special_case,
            self.test_content_type_passthrough,
            self.test_error_response_format,
        ]
        
        return self._run_tests(tests)
    
    def _run_tests(self, tests: List[callable]) -> List[TestResult]:
        """Run a list of test functions."""
        results = []
        
        for test_func in tests:
            result = test_func()
            results.append(result)
            self._print_result(result)
        
        self.results = results
        return results
    
    def _print_result(self, result: TestResult) -> None:
        """Print a single test result."""
        status_colors = {
            TestStatus.PASSED: Fore.GREEN,
            TestStatus.FAILED: Fore.RED,
            TestStatus.SKIPPED: Fore.YELLOW,
            TestStatus.ERROR: Fore.RED
        }
        
        status_icons = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.SKIPPED: "⏭️",
            TestStatus.ERROR: "💥"
        }
        
        color = status_colors.get(result.status, Fore.WHITE)
        icon = status_icons.get(result.status, "❓")
        
        print(f"  {icon} {result.name}: {color}{result.status.value}{Style.RESET_ALL} ({result.duration_ms:.0f}ms)")
        
        if result.message and result.status != TestStatus.PASSED:
            print(f"     └─ {Fore.YELLOW}{result.message}{Style.RESET_ALL}")
    
    def print_summary(self) -> None:
        """Print test summary."""
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        total = len(self.results)
        total_time = sum(r.duration_ms for r in self.results)
        
        print("\n" + "=" * 60)
        print(f"📊 Test Summary for {self.env.upper()} environment")
        print("=" * 60)
        print(f"  Total:   {total}")
        print(f"  {Fore.GREEN}Passed:  {passed}{Style.RESET_ALL}")
        print(f"  {Fore.RED}Failed:  {failed}{Style.RESET_ALL}")
        print(f"  {Fore.RED}Errors:  {errors}{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}Skipped: {skipped}{Style.RESET_ALL}")
        print(f"  Time:    {total_time:.0f}ms")
        print("=" * 60)
        
        if failed == 0 and errors == 0:
            print(f"\n{Fore.GREEN}✅ All tests passed!{Style.RESET_ALL}\n")
        else:
            print(f"\n{Fore.RED}❌ Some tests failed!{Style.RESET_ALL}\n")
    
    def save_results(self, output_dir: str = None) -> str:
        """Save test results to JSON file."""
        output_path = Path(output_dir) if output_dir else (
            Path(__file__).parent.parent / "dist"
        )
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f"test-results-{self.env}-{timestamp}.json"
        output_file = output_path / filename
        
        results_data = {
            "environment": self.env,
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.status == TestStatus.PASSED),
                "failed": sum(1 for r in self.results if r.status == TestStatus.FAILED),
                "errors": sum(1 for r in self.results if r.status == TestStatus.ERROR),
                "skipped": sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
            },
            "tests": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "duration_ms": r.duration_ms,
                    "message": r.message,
                    "response_code": r.response_code
                }
                for r in self.results
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"📄 Results saved: {output_file}")
        return str(output_file)


def main():
    parser = argparse.ArgumentParser(
        description='Test Cropwise Unified Platform proxy endpoints'
    )
    parser.add_argument(
        '--env', '-e',
        required=True,
        choices=['dev', 'qa', 'prod'],
        help='Target environment'
    )
    parser.add_argument(
        '--test-suite', '-t',
        choices=['smoke', 'functional', 'integration', 'all'],
        default='all',
        help='Test suite to run (default: all)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--config', '-c',
        default=None,
        help='Path to environments.json configuration file'
    )
    parser.add_argument(
        '--save-results', '-s',
        action='store_true',
        help='Save results to JSON file'
    )
    parser.add_argument(
        '--base-url', '-u',
        default=None,
        help='Override base URL for testing'
    )
    
    args = parser.parse_args()
    
    try:
        tester = ProxyTester(
            env=args.env,
            config_path=args.config,
            verbose=args.verbose
        )
        
        # Override base URL if provided
        if args.base_url:
            tester.base_url = args.base_url
        
        print(f"\n🎯 Testing proxy at: {tester.base_url}")
        
        # Run selected test suite
        suite_runners = {
            'smoke': tester.run_smoke_tests,
            'functional': tester.run_functional_tests,
            'integration': tester.run_integration_tests,
            'all': tester.run_all_tests
        }
        
        suite_runners[args.test_suite]()
        
        # Print summary
        tester.print_summary()
        
        # Save results if requested
        if args.save_results:
            tester.save_results()
        
        # Exit with appropriate code
        failed = sum(1 for r in tester.results if r.status in [TestStatus.FAILED, TestStatus.ERROR])
        sys.exit(1 if failed > 0 else 0)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## Step 5: Configuration Guide

### 5.1 Create config/policies.json

```json
{
    "policies": {
        "AM-SetTarget": {
            "description": "Copies Authorization and Content-Type headers to backend",
            "customizable_fields": {
                "headers": ["Authorization", "Content-Type"]
            },
            "notes": "Add additional headers if your backend requires them"
        },
        "FC-Syng-Preflow": {
            "description": "Initializes request tracking variables",
            "customizable_fields": {
                "request_id_header": "x-request-id",
                "timestamp_variable": "request.received.time"
            },
            "notes": "Change header name if your tracing system uses different conventions"
        },
        "FC-Syng-Logging": {
            "description": "Logs API transactions to Syslog",
            "customizable_fields": {
                "syslog_host": "ENVIRONMENT_SPECIFIC",
                "syslog_port": 514,
                "protocol": "TCP",
                "message_format": "Custom log format string"
            },
            "notes": "Update syslog_host per environment in environments.json"
        },
        "FC-Syng-ErrorHandling": {
            "description": "Standardized error handling for 500 errors",
            "customizable_fields": {
                "error_payload_fields": ["code", "message", "requestId"],
                "include_trace": false
            },
            "notes": "Modify error payload structure as needed"
        },
        "RF-APINotFound": {
            "description": "Returns 404 for undefined routes",
            "customizable_fields": {
                "support_contact": "Slack channel or email",
                "error_message": "Custom 404 message"
            },
            "notes": "Update support contact for your team"
        },
        "AM-InvalidAPIKey": {
            "description": "Returns 401 for invalid API keys (future use)",
            "customizable_fields": {
                "error_message": "Custom unauthorized message"
            },
            "notes": "Enable when API key validation is implemented"
        },
        "KVM-Get-User-Rate-Limit": {
            "description": "Looks up user rate limits from Key Value Map",
            "customizable_fields": {
                "kvm_name": "user-rate-limits",
                "default_rate_type": "medium-rate"
            },
            "notes": "Create KVM in Apigee with user rate limit mappings"
        },
        "JS-Parse-JWT-Token": {
            "description": "Parses JWT and extracts claims",
            "customizable_fields": {
                "required_claims": ["sub", "username", "client_id"],
                "optional_claims": ["scope", "roles"]
            },
            "notes": "Modify parse-jwt-token.js to extract additional claims"
        }
    }
}
```

---

## Policy Customization Reference

### What to Change for Your Platform

| Policy | Field to Change | Location | Description |
|--------|----------------|----------|-------------|
| **FC-Syng-Logging** | `<Host>` | `policies/FC-Syng-Logging.xml` | Your Syslog server hostname |
| **FC-Syng-Logging** | `<Port>` | `policies/FC-Syng-Logging.xml` | Syslog port (default: 514) |
| **FC-Syng-Logging** | `<Message>` | `policies/FC-Syng-Logging.xml` | Log message format |
| **RF-APINotFound** | `support contact` | `policies/RF-APINotFound.xml` | Your team's Slack channel |
| **AM-SetTarget** | `<Header>` elements | `policies/AM-SetTarget.xml` | Additional headers to copy |
| **KVM-Get-User-Rate-Limit** | `<MapIdentifier>` | `policies/KVM-Get-User-Rate-Limit.xml` | KVM name in Apigee |
| **JS-Parse-JWT-Token** | Claims extraction | `resources/jsc/parse-jwt-token.js` | JWT claims to extract |
| **Target Endpoint** | `<URL>` | `targets/default.xml` | Backend service URL |
| **Proxy Endpoint** | `<BasePath>` | `proxies/default.xml` | API base path |

### Example: Updating Support Contact

```xml
<!-- Before -->
<Payload contentType="application/json">
    {
        "support contact" : "If issue persists, please connect with Syngenta Digital DevOps support via slack- #devops-help"
    }
</Payload>

<!-- After -->
<Payload contentType="application/json">
    {
        "support contact" : "Contact CropwisePlatform team via slack- #cropwise-platform-support"
    }
</Payload>
```

### Example: Adding Custom Headers to Copy

```xml
<!-- policies/AM-SetTarget.xml -->
<AssignMessage async="false" continueOnError="false" enabled="true" name="AM-SetTarget">
    <DisplayName>AM-SetTarget</DisplayName>
    <Copy source="request">
        <Headers>
            <Header name="Authorization"/>
            <Header name="Content-Type"/>
            <!-- Add your custom headers below -->
            <Header name="X-Correlation-Id"/>
            <Header name="X-Tenant-Id"/>
        </Headers>
    </Copy>
    <AssignTo createNew="false" transport="http" type="request"/>
</AssignMessage>
```

### Example: Customizing Log Format

```xml
<!-- policies/FC-Syng-Logging.xml -->
<MessageLogging async="true" continueOnError="true" enabled="true" name="FC-Syng-Logging">
    <DisplayName>FC-Syng-Logging</DisplayName>
    <Syslog>
        <Message>[CropwisePlatform][{environment.name}] RequestId={messageid} User={jwt.username} ClientIP={client.ip} Method={request.verb} Path={request.uri} Status={response.status.code} Latency={client.sent.end.timestamp - client.received.start.timestamp}ms</Message>
        <Host>your-syslog-server.company.com</Host>
        <Port>514</Port>
        <Protocol>TCP</Protocol>
    </Syslog>
</MessageLogging>
```

---

## CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Cropwise Unified Platform Proxy

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - qa
          - prod

env:
  PYTHON_VERSION: '3.9'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Validate proxy structure
        run: |
          python scripts/generate_proxy.py --env dev --validate

  build-and-deploy:
    needs: validate
    runs-on: ubuntu-latest
    if: github.event_name != 'pull_request'
    
    strategy:
      matrix:
        include:
          - branch: develop
            environment: dev
          - branch: main
            environment: qa
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SERVICE_ACCOUNT_KEY }}
      
      - name: Determine environment
        id: env
        run: |
          if [ "${{ github.event_name }}" == "workflow_dispatch" ]; then
            echo "environment=${{ github.event.inputs.environment }}" >> $GITHUB_OUTPUT
          elif [ "${{ github.ref }}" == "refs/heads/main" ]; then
            echo "environment=qa" >> $GITHUB_OUTPUT
          else
            echo "environment=dev" >> $GITHUB_OUTPUT
          fi
      
      - name: Generate proxy bundle
        run: |
          python scripts/generate_proxy.py \
            --env ${{ steps.env.outputs.environment }} \
            --output ./dist
      
      - name: Deploy to Apigee X
        run: |
          BUNDLE=$(ls -t ./dist/*.zip | head -1)
          python scripts/deploy_proxy.py \
            --env ${{ steps.env.outputs.environment }} \
            --bundle "$BUNDLE" \
            --deploy \
            --wait
      
      - name: Run smoke tests
        run: |
          python scripts/test_proxy.py \
            --env ${{ steps.env.outputs.environment }} \
            --test-suite smoke \
            --save-results
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results-${{ steps.env.outputs.environment }}
          path: dist/test-results-*.json

  deploy-prod:
    needs: build-and-deploy
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_PROD_SERVICE_ACCOUNT_KEY }}
      
      - name: Generate and deploy to production
        run: |
          python scripts/generate_proxy.py --env prod --output ./dist
          BUNDLE=$(ls -t ./dist/*.zip | head -1)
          python scripts/deploy_proxy.py \
            --env prod \
            --bundle "$BUNDLE" \
            --deploy \
            --wait \
            --timeout 180
      
      - name: Run production smoke tests
        run: |
          python scripts/test_proxy.py \
            --env prod \
            --test-suite smoke \
            --save-results
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Authentication failed | Invalid or expired credentials | Run `gcloud auth application-default login` |
| Bundle upload failed | Invalid XML syntax | Run `python scripts/generate_proxy.py --validate` |
| Deployment stuck | Resource conflicts | Check Apigee console for stuck deployments |
| 404 on all requests | Wrong base path | Verify `<BasePath>` in `proxies/default.xml` |
| 502 Bad Gateway | Backend unreachable | Check target endpoint URL and network |
| Tests failing | Wrong test URL | Use `--base-url` to specify correct hostname |

### Debug Commands

```bash
# Check deployment status
python scripts/deploy_proxy.py --env dev --status

# Test with verbose output
python scripts/test_proxy.py --env dev --verbose

# Validate proxy structure
python scripts/generate_proxy.py --env dev --validate

# Check Apigee API connectivity
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://apigee.googleapis.com/v1/organizations/YOUR_ORG/apis"
```

### Getting Help

- **Internal:** Slack #cropwise-platform-support
- **Apigee Documentation:** https://cloud.google.com/apigee/docs
- **API Reference:** https://cloud.google.com/apigee/docs/reference/apis/apigee/rest

---

## Quick Start Commands

```bash
# 1. Clone repository
git clone https://github.com/your-org/cropwise-unified-platform-proxy.git
cd cropwise-unified-platform-proxy

# 2. Set up Python environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your values

# 4. Authenticate
gcloud auth application-default login

# 5. Validate proxy
python scripts/generate_proxy.py --env dev --validate

# 6. Generate bundle
python scripts/generate_proxy.py --env dev --output ./dist

# 7. Deploy
python scripts/deploy_proxy.py --env dev --bundle ./dist/cropwise-*.zip --deploy --wait

# 8. Test
python scripts/test_proxy.py --env dev --test-suite all
```

---

**Document Version:** 1.0  
**Last Updated:** February 2, 2026  
**Owner:** CropwisePlatform Team
