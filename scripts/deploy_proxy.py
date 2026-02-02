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
