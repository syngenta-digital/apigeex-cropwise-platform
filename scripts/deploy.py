#!/usr/bin/env python3
"""
Cropwise Unified Platform - Apigee X Deployment Script

This script creates a proxy bundle and deploys it to Apigee X environments.
Works on Mac, Linux, and Windows.

Usage:
    # Deploy to dev environment
    python scripts/deploy.py --env dev

    # Deploy with custom organization
    python scripts/deploy.py --env dev --org your-org-name

    # Dry run (no actual deployment)
    python scripts/deploy.py --env dev --dry-run

    # Skip deployment, only create bundle
    python scripts/deploy.py --env dev --bundle-only

Requirements:
    - Python 3.7+
    - gcloud CLI installed and authenticated
    - requests library: pip install requests
"""

import os
import sys
import json
import time
import zipfile
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

try:
    import requests
except ImportError:
    print("❌ Error: 'requests' library not found")
    print("Install with: pip install requests")
    sys.exit(1)


# ANSI Colors
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_success(text: str):
    """Print success message in green"""
    print(f"{Colors.GREEN}{text}{Colors.RESET}")


def print_error(text: str):
    """Print error message in red"""
    print(f"{Colors.RED}{text}{Colors.RESET}")


def print_warning(text: str):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}{text}{Colors.RESET}")


def print_info(text: str):
    """Print info message in cyan"""
    print(f"{Colors.CYAN}{text}{Colors.RESET}")


def print_header(text: str):
    """Print header"""
    print(f"\n{Colors.BLUE}{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}{Colors.RESET}\n")


class ApigeeDeployer:
    """Handles Apigee X proxy deployment"""
    
    PROXY_NAME = "cropwise-unified-platform"
    BASE_URL = "https://apigee.googleapis.com/v1"
    DEFAULT_ORG = "711137019957"  # use1-non-prod-apigeex-service
    DEFAULT_PROJECT = "use1-apigeex"
    
    # Environment mapping
    ENV_MAP = {
        'dev': 'default-dev',
        'qa': 'default-qa',
        'prod': 'default-prod'
    }
    
    def __init__(self, env: str, organization: str = None, token: str = None):
        self.env = env
        self.apigee_env = self.ENV_MAP.get(env, 'default-dev')  # Map to actual Apigee env
        self.organization = organization or self.DEFAULT_ORG
        self.token = token
        self.base_dir = Path(__file__).parent.parent
        self.apiproxy_dir = self.base_dir / "apiproxy"
        self.dist_dir = self.base_dir / "dist"
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Ensure dist directory exists
        self.dist_dir.mkdir(exist_ok=True)
    
    def check_prerequisites(self) -> bool:
        """Check if required tools are available"""
        print_info("Checking prerequisites...")
        
        gcloud_available = False
        
        # Check gcloud CLI (optional if token and org provided)
        try:
            result = subprocess.run(
                ["gcloud", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print_success("  ✓ gcloud CLI found")
                gcloud_available = True
            else:
                print_warning("  ⚠ gcloud CLI not working properly")
        except FileNotFoundError:
            print_warning("  ⚠ gcloud CLI not found")
            if not self.token or not self.organization:
                print_error("    Install from: https://cloud.google.com/sdk/docs/install")
                print_error("    OR provide --token and --org parameters")
        except Exception as e:
            print_warning(f"  ⚠ Error checking gcloud: {e}")
        
        # Get access token if not provided
        if not self.token:
            if gcloud_available:
                print_info("  Getting access token from gcloud...")
                try:
                    result = subprocess.run(
                        ["gcloud", "auth", "print-access-token"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        self.token = result.stdout.strip()
                        print_success("  ✓ Access token obtained")
                    else:
                        print_error("  ✗ Failed to get access token")
                        print_error("    Run: gcloud auth login")
                        return False
                except Exception as e:
                    print_error(f"  ✗ Error getting token: {e}")
                    return False
            else:
                print_error("  ✗ Access token not provided and gcloud not available")
                print_error("    Provide with: --token YOUR_ACCESS_TOKEN")
                return False
        else:
            print_success("  ✓ Using provided access token")
        
        # Get organization if not provided
        if not self.organization:
            if gcloud_available:
                print_info("  Getting Apigee organization...")
                try:
                    result = subprocess.run(
                        ["gcloud", "config", "get-value", "project"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        project = result.stdout.strip()
                        # Use default org if project matches
                        if project == self.DEFAULT_PROJECT:
                            self.organization = self.DEFAULT_ORG
                            print_success(f"  ✓ Using organization: {self.organization} ({project})")
                        else:
                            self.organization = project
                            print_success(f"  ✓ Using organization: {self.organization}")
                    else:
                        print_warning(f"  ⚠ Could not determine organization, using default: {self.DEFAULT_ORG}")
                        self.organization = self.DEFAULT_ORG
                except Exception as e:
                    print_warning(f"  ⚠ Error getting organization: {e}, using default: {self.DEFAULT_ORG}")
                    self.organization = self.DEFAULT_ORG
            else:
                print_info(f"  Using default organization: {self.DEFAULT_ORG}")
                self.organization = self.DEFAULT_ORG
        else:
            print_success(f"  ✓ Using organization: {self.organization}")
        
        return True
    
    def create_bundle(self) -> Path:
        """Create ZIP bundle from apiproxy directory"""
        print_info("Creating proxy bundle...")
        
        # Check if apiproxy directory exists
        if not self.apiproxy_dir.exists():
            raise FileNotFoundError(f"apiproxy directory not found: {self.apiproxy_dir}")
        
        # Create bundle file path
        bundle_file = self.dist_dir / f"{self.PROXY_NAME}-{self.timestamp}.zip"
        
        print_info(f"  Bundle: {bundle_file}")
        
        # Create ZIP file
        with zipfile.ZipFile(bundle_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through apiproxy directory
            for root, dirs, files in os.walk(self.apiproxy_dir):
                for file in files:
                    file_path = Path(root) / file
                    # Calculate relative path from apiproxy parent
                    arcname = file_path.relative_to(self.base_dir)
                    zipf.write(file_path, arcname)
        
        # Get bundle size
        bundle_size = bundle_file.stat().st_size / 1024  # KB
        print_success(f"  ✓ Bundle created: {bundle_size:.2f} KB")
        
        return bundle_file
    
    def upload_bundle(self, bundle_file: Path) -> str:
        """Upload proxy bundle to Apigee X"""
        print_info("Uploading proxy bundle to Apigee X...")
        
        url = (
            f"{self.BASE_URL}/organizations/{self.organization}/apis"
            f"?action=import&name={self.PROXY_NAME}"
        )
        
        print_info(f"  URL: {url}")
        
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        with open(bundle_file, 'rb') as f:
            files = {
                'file': (bundle_file.name, f, 'application/zip')
            }
            
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    files=files,
                    timeout=60
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    revision = data.get('revision', 'unknown')
                    print_success(f"  ✓ Upload successful - Revision: {revision}")
                    return revision
                else:
                    print_error(f"  ✗ Upload failed: {response.status_code}")
                    print_error(f"  Response: {response.text}")
                    raise RuntimeError(f"Upload failed: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print_error(f"  ✗ Upload error: {e}")
                raise
    
    def deploy_revision(self, revision: str, override: bool = False) -> bool:
        """Deploy proxy revision to environment"""
        print_info(f"Deploying revision {revision} to {self.apigee_env}...")
        
        url = (
            f"{self.BASE_URL}/organizations/{self.organization}/"
            f"environments/{self.apigee_env}/apis/{self.PROXY_NAME}/"
            f"revisions/{revision}/deployments"
        )
        if override:
            url += "?override=true"
        
        print_info(f"  URL: {url}")
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                timeout=60
            )
            
            if response.status_code in [200, 201]:
                print_success("  ✓ Deployment initiated")
                return True
            else:
                print_error(f"  ✗ Deployment failed: {response.status_code}")
                print_error(f"  Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print_error(f"  ✗ Deployment error: {e}")
            return False
    
    def check_deployment_status(self, revision: str, timeout: int = 120) -> bool:
        """Check if deployment is ready"""
        print_info("Checking deployment status...")
        
        url = (
            f"{self.BASE_URL}/organizations/{self.organization}/"
            f"environments/{self.apigee_env}/apis/{self.PROXY_NAME}/"
            f"revisions/{revision}/deployments"
        )
        
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        start_time = time.time()
        attempt = 0
        max_attempts = timeout // 2  # Check every 2 seconds
        
        while attempt < max_attempts:
            time.sleep(2)
            attempt += 1
            elapsed = int(time.time() - start_time)
            
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    state = data.get('state', 'unknown')
                    
                    if state == 'deployed':
                        print_success("  ✓ Deployment is READY!")
                        return True
                    elif state in ['error', 'failed']:
                        print_error(f"  ✗ Deployment FAILED with state: {state}")
                        return False
                    else:
                        print_info(f"  ⏳ Waiting... ({elapsed}s) - State: {state}")
                else:
                    print_info(f"  ⏳ Waiting... ({elapsed}s) - Attempt {attempt}/{max_attempts}")
                    
            except requests.exceptions.RequestException:
                print_info(f"  ⏳ Waiting... ({elapsed}s) - Attempt {attempt}/{max_attempts}")
        
        print_warning(f"  ⚠ Deployment status check timed out after {timeout}s")
        print_info("  Check Apigee console for deployment status")
        return False
    
    def get_current_deployment(self) -> Optional[Dict[str, Any]]:
        """Get current deployment information"""
        url = (
            f"{self.BASE_URL}/organizations/{self.organization}/"
            f"environments/{self.apigee_env}/apis/{self.PROXY_NAME}/deployments"
        )
        
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def full_deploy(self, wait: bool = True, bundle_only: bool = False, override: bool = False) -> Dict[str, Any]:
        """Execute full deployment workflow"""
        result = {
            'proxy_name': self.PROXY_NAME,
            'environment': self.env,
            'apigee_environment': self.apigee_env,
            'organization': self.organization,
            'timestamp': self.timestamp,
            'success': False
        }
        
        try:
            # Step 1: Create bundle
            bundle_file = self.create_bundle()
            result['bundle_file'] = str(bundle_file)
            
            if bundle_only:
                print_success("\n✓ Bundle created successfully!")
                print_info(f"Bundle: {bundle_file}")
                result['success'] = True
                return result
            
            print()
            
            # Step 2: Upload bundle
            revision = self.upload_bundle(bundle_file)
            result['revision'] = revision
            
            print()
            
            # Step 3: Deploy
            deploy_success = self.deploy_revision(revision, override=override)
            if not deploy_success:
                raise RuntimeError("Deployment initiation failed")
            
            print()
            
            # Step 4: Wait for deployment
            if wait:
                ready = self.check_deployment_status(revision)
                result['ready'] = ready
                result['success'] = ready
            else:
                result['success'] = True
            
            # Save result
            self._save_result(result)
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            self._save_result(result)
            raise
    
    def _save_result(self, result: Dict[str, Any]):
        """Save deployment result to JSON file"""
        output_file = self.dist_dir / f"deployment-{self.env}-{self.timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print_info(f"\n📄 Deployment result saved: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Deploy Cropwise Unified Platform proxy to Apigee X',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy to dev environment
  python scripts/deploy.py --env dev

  # Deploy with custom organization
  python scripts/deploy.py --env dev --org my-org

  # Create bundle only (no deployment)
  python scripts/deploy.py --env dev --bundle-only

  # Dry run (check prerequisites only)
  python scripts/deploy.py --env dev --dry-run

  # Deploy without waiting for status
  python scripts/deploy.py --env dev --no-wait
        """
    )
    
    parser.add_argument(
        '--env', '-e',
        required=True,
        choices=['dev', 'qa', 'prod'],
        help='Target environment'
    )
    
    parser.add_argument(
        '--org', '-o',
        help='Apigee organization name (default: from gcloud config)'
    )
    
    parser.add_argument(
        '--token', '-t',
        help='Access token (default: from gcloud auth print-access-token)'
    )
    
    parser.add_argument(
        '--bundle-only',
        action='store_true',
        help='Create bundle only, do not deploy'
    )
    
    parser.add_argument(
        '--no-wait',
        action='store_true',
        help='Do not wait for deployment to be ready'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Check prerequisites and show deployment plan, but do not deploy'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=120,
        help='Deployment timeout in seconds (default: 120)'
    )
    
    parser.add_argument(
        '--override',
        action='store_true',
        help='Override existing deployment'
    )
    
    args = parser.parse_args()
    
    # Print header
    print_header("Apigee X Deployment Script")
    print(f"Proxy Name: {ApigeeDeployer.PROXY_NAME}")
    print(f"Environment: {args.env}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Initialize deployer
        deployer = ApigeeDeployer(
            env=args.env,
            organization=args.org,
            token=args.token
        )
        
        # Check prerequisites
        if not deployer.check_prerequisites():
            print_error("\n❌ Prerequisites check failed")
            sys.exit(1)
        
        print()
        
        # Dry run mode
        if args.dry_run:
            print_warning("DRY RUN MODE - No actual deployment will occur")
            print()
            print_info("Would deploy:")
            print(f"  Organization: {deployer.organization}")
            print(f"  Proxy: {deployer.PROXY_NAME}")
            print(f"  Environment: {args.env}")
            print(f"  Bundle: {deployer.dist_dir}/{deployer.PROXY_NAME}-{deployer.timestamp}.zip")
            print()
            sys.exit(0)
        
        # Execute deployment
        result = deployer.full_deploy(
            wait=not args.no_wait,
            bundle_only=args.bundle_only,
            override=args.override
        )
        
        # Print summary
        if not args.bundle_only:
            print()
            print_header("Deployment Summary")
            print(f"Proxy: {result['proxy_name']}")
            print(f"Revision: {result.get('revision', 'N/A')}")
            print(f"Environment: {result['environment']} → {result['apigee_environment']}")
            print(f"Organization: {result['organization']}")
            print(f"Bundle: {result['bundle_file']}")
            print(f"Status: {'DEPLOYED' if result['success'] else 'FAILED'}")
            print()
            
            if result['success']:
                print_success("✓ Deployment completed successfully!")
                print()
                
                # Show API endpoint and test commands
                api_endpoint = f"https://api.cropwise.com/{deployer.PROXY_NAME}/accounts/me"
                print_info(f"API Endpoint: {api_endpoint}")
                print()
                print_info("Test with performance headers:")
                print(f"  curl -H 'Authorization: Bearer YOUR_TOKEN' \\")
                print(f"       -H 'X-Debug-Performance: true' \\")
                print(f"       {api_endpoint}")
                print()
                print_info("Or run the EC2 performance test:")
                print(f"  export BEARER_TOKEN='your_token'")
                print(f"  python tests/ec2-performance-test.py")
                print()
            else:
                print_error("✗ Deployment failed")
                sys.exit(1)
        
    except KeyboardInterrupt:
        print()
        print_warning("\n⚠ Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
