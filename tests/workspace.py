#!/usr/bin/env python3
"""
Cropwise Platform Latency Test

Measures latency between calling the Apigee proxy and direct backend target.
Records statistics and saves results to latency-test directory.

Usage:
    python workspace.curl --requests 10
    python workspace.curl --requests 20 --endpoint /v2/accounts/me
"""

import os
import sys
import time
import json
import statistics
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

import requests
from colorama import init, Fore, Style

# Initialize colorama for Windows
init()

# Configuration
# Proxy URL includes the base path /cropwise-unified-platform
# Endpoints should match the proxy's expected path structure
PROXY_BASE_URL = "https://dev.api.cropwise.com/cropwise-unified-platform"
TARGET_BASE_URL = "https://api.staging.base.cropwise.com"

# Default endpoint - proxy expects /accounts/me, target expects /v2/accounts/me
DEFAULT_ENDPOINT = "/accounts/me"
DEFAULT_NUM_REQUESTS = 10

# Alternative endpoints to test:
# "/health" - Health check endpoint (no auth required)
# "/v1/users" - Users endpoint
# "/remote-sensing/v1/imagery" - Remote sensing endpoint (uses URI rewrite)

# JWT Token from the curl commands
JWT_TOKEN = "eyJ0eXAiOiJKV1QiLCJraWQiOiJjcm9wd2lzZS1iYXNlLXRva2VuLXB1Yi1rZXkiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI2M2QyZTg5Yy02MDRlLTQ2NWEtYTNiZC1kNzRmNjdlMzdhZjUiLCJpc191c2luZ19yYmFjIjp0cnVlLCJhdWQiOlsic3RyaWRlci1iYXNlIl0sInVzZXJfbmFtZSI6ImJhc2Uuc2VydmljZS5hY2NvdW50QHN5bmdlbnRhLmNvbSIsInNjb3BlIjoicmVhZCB3cml0ZSIsImlzcyI6ImNyb3B3aXNlLWJhc2Utc3RyaXgiLCJleHAiOjE3NzIyNjA2NTIsImp0aSI6Ijg4MmVmN2Y0LTk3MDgtNGIzYi1hMmY5LThlYWU2Yzc0N2Y0NyIsImNsaWVudF9pZCI6InN0cml4LXVpIn0.SuVIQuHogbLLsGXZk9wHfBuGii8pU1hzIqdGhskKexVNnbBJhdMV3HQiLwnr8KQjcZM20q-7eWpM7jklv1lVTAfow8EfWUVoc0rIFnqroMB1YfMNdI6-ZZR4f_zxmnC28ptIZHISqJNXEOGtv0mmUmIDqdsLblial4-5vQ0VTBAmWfQmNaxtTknpwAK7wD8DsnOYjLlrVDNbiOqO7VQdbIv2OUFnB5B6KFSuN7Cu9N3OJ_DsWwpuAru-hQo06y4r3rm3OEX8FzWLp3ahlqIxJxfcfMm42-R4ZZss1sFE8nhmyEEoa3wGURVlxNQdZ4F7Ya-MzQbJN0bXDBC7GxQjOg"

# Cookie from the curl commands
COOKIE_SESSION = "Y2RmN2IwODYtYTQ0Ni00ZmJlLWJjN2ItYTVjN2JiZjcwNWEz"


class LatencyResult:
    """Represents a single latency test result."""
    
    def __init__(self, success: bool, status_code: int, latency_ms: float, error: str = None):
        self.success = success
        self.status_code = status_code
        self.latency_ms = latency_ms
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status_code": self.status_code,
            "latency_ms": self.latency_ms,
            "error": self.error
        }


class LatencyTester:
    """Tests and measures latency between proxy and target."""
    
    def __init__(self, proxy_url: str, target_url: str, endpoint: str, num_requests: int, target_endpoint: str = None):
        self.proxy_url = proxy_url
        self.target_url = target_url
        self.endpoint = endpoint
        self.target_endpoint = target_endpoint or endpoint  # Use different endpoint for target if specified
        self.num_requests = num_requests
        self.proxy_results: List[LatencyResult] = []
        self.target_results: List[LatencyResult] = []
    
    def _make_request(self, url: str) -> LatencyResult:
        """Make a single HTTP request and measure latency."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JWT_TOKEN}",
            "Cookie": f"SESSION={COOKIE_SESSION}",
            "User-Agent": "CropwisePlatform-LatencyTest/1.0"
        }
        
        try:
            start_time = time.perf_counter()
            response = requests.get(url, headers=headers, timeout=30)
            end_time = time.perf_counter()
            
            latency_ms = (end_time - start_time) * 1000
            
            return LatencyResult(
                success=True,
                status_code=response.status_code,
                latency_ms=latency_ms
            )
        except requests.exceptions.Timeout as e:
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            return LatencyResult(
                success=False,
                status_code=0,
                latency_ms=latency_ms,
                error="Request timeout"
            )
        except requests.exceptions.RequestException as e:
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            return LatencyResult(
                success=False,
                status_code=0,
                latency_ms=latency_ms,
                error=str(e)
            )
    
    def test_proxy(self):
        """Test latency through the Apigee proxy."""
        print(f"\n{Fore.CYAN}[PROXY TEST]{Style.RESET_ALL} Testing Apigee proxy...")
        print(f"{Fore.LIGHTBLACK_EX}URL: {self.proxy_url}{self.endpoint}{Style.RESET_ALL}\n")
        
        for i in range(1, self.num_requests + 1):
            print(f"  Request {i}/{self.num_requests}...", end="")
            
            url = f"{self.proxy_url}{self.endpoint}"
            result = self._make_request(url)
            self.proxy_results.append(result)
            
            if result.success:
                print(f" {Fore.GREEN}✓ {result.status_code} - {result.latency_ms:.2f}ms{Style.RESET_ALL}")
            else:
                print(f" {Fore.RED}✗ Error - {result.latency_ms:.2f}ms{Style.RESET_ALL}")
                if result.error:
                    print(f"{Fore.RED}    Error: {result.error}{Style.RESET_ALL}")
            
            time.sleep(0.1)  # Small delay between requests
    
    def test_target(self):
        """Test latency to direct backend target."""
        print(f"\n{Fore.CYAN}[TARGET TEST]{Style.RESET_ALL} Testing direct backend...")
        print(f"{Fore.LIGHTBLACK_EX}URL: {self.target_url}{self.target_endpoint}{Style.RESET_ALL}\n")
        
        for i in range(1, self.num_requests + 1):
            print(f"  Request {i}/{self.num_requests}...", end="")
            
            url = f"{self.target_url}{self.target_endpoint}"
            result = self._make_request(url)
            self.target_results.append(result)
            
            if result.success:
                print(f" {Fore.GREEN}✓ {result.status_code} - {result.latency_ms:.2f}ms{Style.RESET_ALL}")
            else:
                print(f" {Fore.RED}✗ Error - {result.latency_ms:.2f}ms{Style.RESET_ALL}")
                if result.error:
                    print(f"{Fore.RED}    Error: {result.error}{Style.RESET_ALL}")
            
            time.sleep(0.1)  # Small delay between requests
    
    def _calculate_stats(self, results: List[LatencyResult]) -> Dict[str, Any]:
        """Calculate statistics from results."""
        successful = [r for r in results if r.success]
        latencies = [r.latency_ms for r in successful]
        
        if not latencies:
            return {
                "count": len(results),
                "success_rate": 0.0,
                "min": 0.0,
                "max": 0.0,
                "average": 0.0,
                "median": 0.0,
                "std_dev": 0.0
            }
        
        return {
            "count": len(results),
            "success_rate": round((len(successful) / len(results)) * 100, 2),
            "min": round(min(latencies), 2),
            "max": round(max(latencies), 2),
            "average": round(statistics.mean(latencies), 2),
            "median": round(statistics.median(latencies), 2),
            "std_dev": round(statistics.stdev(latencies), 2) if len(latencies) > 1 else 0.0
        }
    
    def print_results(self) -> Dict[str, Any]:
        """Print and return test results."""
        proxy_stats = self._calculate_stats(self.proxy_results)
        target_stats = self._calculate_stats(self.target_results)
        
        print(f"\n{Fore.CYAN}========================================")
        print("LATENCY TEST RESULTS")
        print(f"========================================{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}[PROXY] Apigee Proxy Statistics:{Style.RESET_ALL}")
        print(f"  Requests:     {proxy_stats['count']}")
        print(f"  Success Rate: {proxy_stats['success_rate']}%")
        print(f"  Min Latency:  {proxy_stats['min']}ms")
        print(f"  Max Latency:  {proxy_stats['max']}ms")
        print(f"  Avg Latency:  {proxy_stats['average']}ms")
        print(f"  Med Latency:  {proxy_stats['median']}ms")
        print(f"  Std Dev:      {proxy_stats['std_dev']}ms")
        
        print(f"\n{Fore.YELLOW}[TARGET] Direct Backend Statistics:{Style.RESET_ALL}")
        print(f"  Requests:     {target_stats['count']}")
        print(f"  Success Rate: {target_stats['success_rate']}%")
        print(f"  Min Latency:  {target_stats['min']}ms")
        print(f"  Max Latency:  {target_stats['max']}ms")
        print(f"  Avg Latency:  {target_stats['average']}ms")
        print(f"  Med Latency:  {target_stats['median']}ms")
        print(f"  Std Dev:      {target_stats['std_dev']}ms")
        
        # Calculate overhead
        overhead = proxy_stats['average'] - target_stats['average']
        overhead_percent = (overhead / target_stats['average'] * 100) if target_stats['average'] > 0 else 0
        
        print(f"\n{Fore.YELLOW}[COMPARISON] Proxy Overhead:{Style.RESET_ALL}")
        print(f"  Additional Latency: {overhead:.2f}ms (+{overhead_percent:.2f}%)")
        
        if overhead < 50:
            print(f"  Status: {Fore.GREEN}✓ Excellent (< 50ms overhead){Style.RESET_ALL}")
        elif overhead < 100:
            print(f"  Status: {Fore.YELLOW}⚠ Acceptable (50-100ms overhead){Style.RESET_ALL}")
        else:
            print(f"  Status: {Fore.RED}✗ High (> 100ms overhead){Style.RESET_ALL}")
        
        return {
            "proxy": proxy_stats,
            "target": target_stats,
            "comparison": {
                "overhead_ms": round(overhead, 2),
                "overhead_percent": round(overhead_percent, 2)
            }
        }
    
    def save_results(self, output_dir: Path) -> str:
        """Save detailed results to JSON file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        results_file = output_dir / f"latency-results-{timestamp}.json"
        
        stats = self.print_results()
        
        results = {
            "timestamp": timestamp,
            "configuration": {
                "proxy_url": self.proxy_url,
                "target_url": self.target_url,
                "proxy_endpoint": self.endpoint,
                "target_endpoint": self.target_endpoint,
                "num_requests": self.num_requests
            },
            "proxy": {
                "statistics": stats["proxy"],
                "results": [r.to_dict() for r in self.proxy_results]
            },
            "target": {
                "statistics": stats["target"],
                "results": [r.to_dict() for r in self.target_results]
            },
            "comparison": stats["comparison"]
        }
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{Fore.CYAN}========================================")
        print(f"{Fore.GREEN}Results saved to:")
        print(f"{Style.RESET_ALL}{results_file}")
        print(f"{Fore.CYAN}========================================{Style.RESET_ALL}\n")
        
        # Also save to CSV summary
        self._save_csv_summary(output_dir, timestamp, stats)
        
        return str(results_file)
    
    def _save_csv_summary(self, output_dir: Path, timestamp: str, stats: Dict[str, Any]):
        """Append summary to CSV file."""
        import csv
        
        csv_file = output_dir / "latency-summary.csv"
        file_exists = csv_file.exists()
        
        with open(csv_file, 'a', newline='') as f:
            fieldnames = [
                'timestamp', 'endpoint', 'proxy_requests', 'proxy_success_rate',
                'proxy_avg_latency', 'proxy_median_latency', 'target_avg_latency',
                'target_median_latency', 'overhead_ms', 'overhead_percent'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'timestamp': timestamp,
                'endpoint': self.endpoint,
                'proxy_requests': stats['proxy']['count'],
                'proxy_success_rate': stats['proxy']['success_rate'],
                'proxy_avg_latency': stats['proxy']['average'],
                'proxy_median_latency': stats['proxy']['median'],
                'target_avg_latency': stats['target']['average'],
                'target_median_latency': stats['target']['median'],
                'overhead_ms': stats['comparison']['overhead_ms'],
                'overhead_percent': stats['comparison']['overhead_percent']
            })
        
        print(f"{Fore.LIGHTBLACK_EX}Summary appended to: {csv_file}{Style.RESET_ALL}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Measure latency between Apigee proxy and direct backend'
    )
    parser.add_argument(
        '--requests', '-n',
        type=int,
        default=DEFAULT_NUM_REQUESTS,
        help=f'Number of requests to make (default: {DEFAULT_NUM_REQUESTS})'
    )
    parser.add_argument(
        '--endpoint', '-e',
        default=DEFAULT_ENDPOINT,
        help=f'API endpoint to test (default: {DEFAULT_ENDPOINT})'
    )
    parser.add_argument(
        '--proxy-url',
        default=PROXY_BASE_URL,
        help='Proxy base URL'
    )
    parser.add_argument(
        '--target-url',
        default=TARGET_BASE_URL,
        help='Target base URL'
    )
    
    args = parser.parse_args()
    
    print(f"\n{Fore.CYAN}========================================")
    print("Cropwise Platform Latency Test")
    print(f"========================================{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Proxy URL:{Style.RESET_ALL} {args.proxy_url}")
    print(f"{Fore.YELLOW}Target URL:{Style.RESET_ALL} {args.target_url}")
    print(f"{Fore.YELLOW}Proxy Endpoint:{Style.RESET_ALL} {args.endpoint}")
    print(f"{Fore.YELLOW}Target Endpoint:{Style.RESET_ALL} /v2{args.endpoint}")
    print(f"{Fore.YELLOW}Number of Requests:{Style.RESET_ALL} {args.requests}")
    print(f"{Fore.CYAN}========================================{Style.RESET_ALL}\n")
    
    # Create tester and run tests
    # Proxy uses /accounts/me, target uses /v2/accounts/me
    tester = LatencyTester(
        proxy_url=args.proxy_url,
        target_url=args.target_url,
        endpoint=args.endpoint,
        num_requests=args.requests,
        target_endpoint=f"/v2{args.endpoint}"  # Target needs /v2 prefix
    )
    
    tester.test_proxy()
    tester.test_target()
    
    # Save results
    output_dir = Path(__file__).parent / "latency-test"
    tester.save_results(output_dir)


if __name__ == "__main__":
    main()