"""
Apigee X API Client

Provides a Python client for interacting with Apigee X Management APIs.
"""

import requests
from pathlib import Path
from typing import Dict, Any, Optional

from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2 import service_account


class ApigeeClient:
    """Client for interacting with Apigee X Management APIs."""
    
    BASE_URL = "https://apigee.googleapis.com/v1"
    
    def __init__(self, org: str, credentials_path: str = None):
        """
        Initialize the Apigee client.
        
        Args:
            org: The Apigee X organization name
            credentials_path: Optional path to service account JSON file
        """
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
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> requests.Response:
        """Make authenticated request to Apigee API."""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = self._get_auth_header()
        headers.update(kwargs.pop('headers', {}))
        
        response = self.session.request(method, url, headers=headers, **kwargs)
        return response
    
    def list_apis(self) -> Dict[str, Any]:
        """List all API proxies in the organization."""
        endpoint = f"organizations/{self.org}/apis"
        response = self._make_request('GET', endpoint)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError(
                f"Failed to list APIs: {response.status_code} - {response.text}"
            )
    
    def get_api(self, api_name: str) -> Dict[str, Any]:
        """Get details of a specific API proxy."""
        endpoint = f"organizations/{self.org}/apis/{api_name}"
        response = self._make_request('GET', endpoint)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise RuntimeError(
                f"Failed to get API: {response.status_code} - {response.text}"
            )
    
    def upload_api(self, api_name: str, bundle_path: str) -> Dict[str, Any]:
        """Upload an API proxy bundle."""
        endpoint = f"organizations/{self.org}/apis"
        
        with open(bundle_path, 'rb') as f:
            files = {'file': (Path(bundle_path).name, f, 'application/zip')}
            params = {'name': api_name, 'action': 'import'}
            
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
                f"Failed to upload API: {response.status_code} - {response.text}"
            )
    
    def deploy_api(
        self,
        api_name: str,
        revision: str,
        env: str
    ) -> Dict[str, Any]:
        """Deploy an API proxy revision to an environment."""
        endpoint = (
            f"organizations/{self.org}/environments/{env}/"
            f"apis/{api_name}/revisions/{revision}/deployments"
        )
        
        response = self._make_request('POST', endpoint)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise RuntimeError(
                f"Failed to deploy API: {response.status_code} - {response.text}"
            )
    
    def undeploy_api(
        self,
        api_name: str,
        revision: str,
        env: str
    ) -> bool:
        """Undeploy an API proxy revision from an environment."""
        endpoint = (
            f"organizations/{self.org}/environments/{env}/"
            f"apis/{api_name}/revisions/{revision}/deployments"
        )
        
        response = self._make_request('DELETE', endpoint)
        return response.status_code in [200, 204]
    
    def get_deployment_status(
        self,
        api_name: str,
        env: str
    ) -> Dict[str, Any]:
        """Get deployment status for an API in an environment."""
        endpoint = (
            f"organizations/{self.org}/environments/{env}/"
            f"apis/{api_name}/deployments"
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
    
    def list_environments(self) -> list:
        """List all environments in the organization."""
        endpoint = f"organizations/{self.org}/environments"
        response = self._make_request('GET', endpoint)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError(
                f"Failed to list environments: {response.status_code} - {response.text}"
            )
    
    def get_kvm(self, env: str, kvm_name: str) -> Dict[str, Any]:
        """Get a Key Value Map from an environment."""
        endpoint = f"organizations/{self.org}/environments/{env}/keyvaluemaps/{kvm_name}"
        response = self._make_request('GET', endpoint)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise RuntimeError(
                f"Failed to get KVM: {response.status_code} - {response.text}"
            )
    
    def create_kvm(
        self,
        env: str,
        kvm_name: str,
        encrypted: bool = False
    ) -> Dict[str, Any]:
        """Create a Key Value Map in an environment."""
        endpoint = f"organizations/{self.org}/environments/{env}/keyvaluemaps"
        
        data = {
            "name": kvm_name,
            "encrypted": encrypted
        }
        
        response = self._make_request(
            'POST',
            endpoint,
            json=data
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise RuntimeError(
                f"Failed to create KVM: {response.status_code} - {response.text}"
            )
