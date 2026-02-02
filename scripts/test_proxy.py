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
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

import requests
import jwt
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
