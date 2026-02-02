#!/usr/bin/env python3
"""
network-latency-test.py

Comprehensive network latency test comparing:
1. Local Network → Proxy
2. Local Network → Target
3. EC2 US-East → Proxy
4. EC2 US-East → Target

Usage:
    # Run locally
    python network-latency-test.py --mode local
    
    # Run on EC2 (after deployment)
    python network-latency-test.py --mode ec2
    
    # Run full test (local + EC2 via SSH)
    python network-latency-test.py --mode full
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple

try:
    import requests
except ImportError:
    print("Error: requests module not installed")
    print("Install with: pip install requests")
    sys.exit(1)

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # Define dummy color codes
    class Fore:
        GREEN = RED = YELLOW = CYAN = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""


# Test Configuration
PROXY_URL = "https://dev.api.cropwise.com/cropwise-unified-platform"
TARGET_URL = "https://api.staging.base.cropwise.com"
PROXY_ENDPOINT = "/accounts/me"
TARGET_ENDPOINT = "/v2/accounts/me"
NUM_REQUESTS = 20  # Increased for better statistics
TIMEOUT = 30

# EC2 Configuration
EC2_HOST = "ec2-107-20-114-33.compute-1.amazonaws.com"
EC2_USER = "ec2-user"
EC2_KEY_PATH = r"C:\apigeex-cropwise-platform\keys\dssat-testing-use1.pem"
EC2_REGION = "US-East (Virginia)"

# Bearer Token (read from environment or prompt)
BEARER_TOKEN = os.environ.get("BEARER_TOKEN", "")


def get_bearer_token():
    """Get Bearer token from environment or user input"""
    global BEARER_TOKEN
    if not BEARER_TOKEN:
        print(f"{Fore.YELLOW}Bearer token required for authentication.")
        BEARER_TOKEN = input("Enter Bearer token: ").strip()
    return BEARER_TOKEN


def test_endpoint(url: str, name: str, location: str) -> Dict:
    """
    Test a single endpoint and return latency statistics
    
    Args:
        url: Full URL to test
        name: Descriptive name (Proxy/Target)
        location: Test location (Local/EC2)
    
    Returns:
        Dictionary with test results
    """
    token = get_bearer_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "User-Agent": "NetworkLatencyTest/1.0"
    }
    
    latencies = []
    success_count = 0
    errors = []
    
    print(f"\n{Fore.CYAN}[{location.upper()}] Testing {name}...")
    print(f"{Fore.WHITE}URL: {url}")
    print(f"{Fore.WHITE}Requests: {NUM_REQUESTS}")
    
    for i in range(NUM_REQUESTS):
        try:
            start = time.time()
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
            latency = (time.time() - start) * 1000  # Convert to ms
            
            if response.status_code == 200:
                latencies.append(latency)
                success_count += 1
                status_color = Fore.GREEN
                status_symbol = "✓"
            else:
                status_color = Fore.RED
                status_symbol = "✗"
                errors.append(f"Request {i+1}: HTTP {response.status_code}")
            
            print(f"  Request {i+1}/{NUM_REQUESTS}... {status_color}{status_symbol} {response.status_code} - {latency:.2f}ms")
            
        except requests.exceptions.Timeout:
            print(f"  Request {i+1}/{NUM_REQUESTS}... {Fore.RED}✗ TIMEOUT (>{TIMEOUT}s)")
            errors.append(f"Request {i+1}: Timeout")
        except requests.exceptions.RequestException as e:
            print(f"  Request {i+1}/{NUM_REQUESTS}... {Fore.RED}✗ ERROR - {str(e)}")
            errors.append(f"Request {i+1}: {str(e)}")
        
        # Small delay between requests
        if i < NUM_REQUESTS - 1:
            time.sleep(0.1)
    
    # Calculate statistics
    if latencies:
        result = {
            "name": name,
            "location": location,
            "url": url,
            "total_requests": NUM_REQUESTS,
            "successful_requests": success_count,
            "failed_requests": NUM_REQUESTS - success_count,
            "success_rate": (success_count / NUM_REQUESTS) * 100,
            "latency": {
                "min": min(latencies),
                "max": max(latencies),
                "avg": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "stdev": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
                "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
            },
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
    else:
        result = {
            "name": name,
            "location": location,
            "url": url,
            "total_requests": NUM_REQUESTS,
            "successful_requests": 0,
            "failed_requests": NUM_REQUESTS,
            "success_rate": 0,
            "latency": None,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
    
    return result


def get_location_info() -> str:
    """Get current location information"""
    try:
        # Try to get public IP
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        public_ip = response.json().get("ip", "unknown")
        
        # Try to get location from IP
        response = requests.get(f"https://ipapi.co/{public_ip}/json/", timeout=5)
        location_data = response.json()
        
        return {
            "ip": public_ip,
            "city": location_data.get("city", "unknown"),
            "region": location_data.get("region", "unknown"),
            "country": location_data.get("country_name", "unknown"),
            "isp": location_data.get("org", "unknown")
        }
    except:
        return {
            "ip": "unknown",
            "city": "unknown",
            "region": "unknown",
            "country": "unknown",
            "isp": "unknown"
        }


def run_local_tests() -> List[Dict]:
    """Run tests from local network"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}LOCAL NETWORK TESTS")
    print(f"{Fore.CYAN}{'='*60}")
    
    location = get_location_info()
    print(f"\n{Fore.WHITE}Location: {location['city']}, {location['region']}, {location['country']}")
    print(f"{Fore.WHITE}ISP: {location['isp']}")
    print(f"{Fore.WHITE}Public IP: {location['ip']}")
    
    results = []
    
    # Test 1: Local → Proxy
    proxy_result = test_endpoint(
        f"{PROXY_URL}{PROXY_ENDPOINT}",
        "Apigee Proxy",
        "Local"
    )
    proxy_result["location_info"] = location
    results.append(proxy_result)
    
    # Test 2: Local → Target
    target_result = test_endpoint(
        f"{TARGET_URL}{TARGET_ENDPOINT}",
        "Direct Target",
        "Local"
    )
    target_result["location_info"] = location
    results.append(target_result)
    
    return results


def deploy_to_ec2() -> bool:
    """Deploy test script to EC2 instance"""
    print(f"\n{Fore.CYAN}Deploying test script to EC2...")
    
    try:
        # Check if SSH key exists
        if not os.path.exists(EC2_KEY_PATH):
            print(f"{Fore.RED}ERROR: SSH key not found at {EC2_KEY_PATH}")
            return False
        
        # Create remote script
        remote_script = f"""#!/usr/bin/env python3
import requests
import json
import statistics
import time
from datetime import datetime

PROXY_URL = "{PROXY_URL}"
TARGET_URL = "{TARGET_URL}"
PROXY_ENDPOINT = "{PROXY_ENDPOINT}"
TARGET_ENDPOINT = "{TARGET_ENDPOINT}"
NUM_REQUESTS = {NUM_REQUESTS}
TIMEOUT = {TIMEOUT}
BEARER_TOKEN = "{get_bearer_token()}"

def test_endpoint(url, name):
    headers = {{
        "Authorization": f"Bearer {{BEARER_TOKEN}}",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "User-Agent": "NetworkLatencyTest/1.0-EC2"
    }}
    
    latencies = []
    success_count = 0
    errors = []
    
    for i in range(NUM_REQUESTS):
        try:
            start = time.time()
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                latencies.append(latency)
                success_count += 1
            else:
                errors.append(f"Request {{i+1}}: HTTP {{response.status_code}}")
        except Exception as e:
            errors.append(f"Request {{i+1}}: {{str(e)}}")
    
    if latencies:
        return {{
            "name": name,
            "location": "EC2",
            "url": url,
            "total_requests": NUM_REQUESTS,
            "successful_requests": success_count,
            "failed_requests": NUM_REQUESTS - success_count,
            "success_rate": (success_count / NUM_REQUESTS) * 100,
            "latency": {{
                "min": min(latencies),
                "max": max(latencies),
                "avg": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "stdev": statistics.stdev(latencies) if len(latencies) > 1 else 0
            }},
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }}
    return None

# Get EC2 location info
try:
    response = requests.get("http://169.254.169.254/latest/meta-data/placement/region", timeout=2)
    region = response.text
    response = requests.get("http://169.254.169.254/latest/meta-data/public-ipv4", timeout=2)
    public_ip = response.text
    location_info = {{"region": region, "ip": public_ip}}
except:
    location_info = {{"region": "unknown", "ip": "unknown"}}

results = []

# Test Proxy
proxy_result = test_endpoint(f"{{PROXY_URL}}{{PROXY_ENDPOINT}}", "Apigee Proxy")
if proxy_result:
    proxy_result["location_info"] = location_info
    results.append(proxy_result)

# Test Target
target_result = test_endpoint(f"{{TARGET_URL}}{{TARGET_ENDPOINT}}", "Direct Target")
if target_result:
    target_result["location_info"] = location_info
    results.append(target_result)

print(json.dumps(results, indent=2))
"""
        
        # Write to temp file
        temp_script = "network_test_ec2.py"
        with open(temp_script, "w") as f:
            f.write(remote_script)
        
        # Copy to EC2
        scp_cmd = [
            "scp",
            "-i", EC2_KEY_PATH,
            "-o", "StrictHostKeyChecking=no",
            temp_script,
            f"{EC2_USER}@{EC2_HOST}:~/"
        ]
        
        result = subprocess.run(scp_cmd, capture_output=True, text=True)
        
        # Clean up temp file
        os.remove(temp_script)
        
        if result.returncode != 0:
            print(f"{Fore.RED}ERROR: Failed to copy script to EC2")
            print(result.stderr)
            return False
        
        print(f"{Fore.GREEN}✓ Script deployed to EC2")
        return True
        
    except Exception as e:
        print(f"{Fore.RED}ERROR: {str(e)}")
        return False


def run_ec2_tests() -> List[Dict]:
    """Run tests from EC2 instance"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}EC2 US-EAST TESTS")
    print(f"{Fore.CYAN}{'='*60}")
    
    if not deploy_to_ec2():
        return []
    
    print(f"\n{Fore.CYAN}Running tests on EC2...")
    
    # Execute on EC2
    ssh_cmd = [
        "ssh",
        "-i", EC2_KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        f"{EC2_USER}@{EC2_HOST}",
        "python3 network_test_ec2.py"
    ]
    
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"{Fore.RED}ERROR: EC2 test failed")
            print(result.stderr)
            return []
        
        # Parse JSON output
        results = json.loads(result.stdout)
        
        # Display results
        for res in results:
            print(f"\n{Fore.GREEN}✓ {res['name']} test completed")
            if res.get('latency'):
                print(f"  Avg Latency: {res['latency']['avg']:.2f}ms")
                print(f"  Success Rate: {res['success_rate']:.1f}%")
        
        return results
        
    except subprocess.TimeoutExpired:
        print(f"{Fore.RED}ERROR: EC2 test timed out")
        return []
    except json.JSONDecodeError:
        print(f"{Fore.RED}ERROR: Failed to parse EC2 test results")
        print(result.stdout)
        return []
    except Exception as e:
        print(f"{Fore.RED}ERROR: {str(e)}")
        return []


def generate_report(all_results: List[Dict]) -> str:
    """Generate comprehensive comparison report"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_file = f"latency-test/network-latency-report-{timestamp}.md"
    
    os.makedirs("latency-test", exist_ok=True)
    
    with open(report_file, "w") as f:
        f.write("# Network Latency Analysis Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        f.write("## Executive Summary\n\n")
        
        # Create comparison table
        f.write("### Latency Comparison\n\n")
        f.write("| Test | Location | Endpoint | Avg Latency | Min | Max | P95 | Success Rate |\n")
        f.write("|------|----------|----------|-------------|-----|-----|-----|-------------|\n")
        
        for result in all_results:
            if result.get('latency'):
                lat = result['latency']
                f.write(f"| {result['name']} | {result['location']} | ")
                f.write(f"{result['url']} | ")
                f.write(f"{lat['avg']:.2f}ms | ")
                f.write(f"{lat['min']:.2f}ms | ")
                f.write(f"{lat['max']:.2f}ms | ")
                f.write(f"{lat.get('p95', 0):.2f}ms | ")
                f.write(f"{result['success_rate']:.1f}% |\n")
        
        f.write("\n---\n\n")
        
        # Detailed results for each test
        f.write("## Detailed Results\n\n")
        
        for result in all_results:
            f.write(f"### {result['location']} → {result['name']}\n\n")
            f.write(f"**URL**: `{result['url']}`\n\n")
            
            if result.get('location_info'):
                loc = result['location_info']
                if isinstance(loc, dict):
                    if 'region' in loc:
                        f.write(f"**Region**: {loc.get('region', 'N/A')}\n")
                    if 'city' in loc:
                        f.write(f"**Location**: {loc.get('city', 'N/A')}, {loc.get('region', 'N/A')}, {loc.get('country', 'N/A')}\n")
                    if 'ip' in loc:
                        f.write(f"**IP**: {loc['ip']}\n")
                    if 'isp' in loc:
                        f.write(f"**ISP**: {loc.get('isp', 'N/A')}\n")
                f.write("\n")
            
            f.write(f"**Requests**: {result['total_requests']} ")
            f.write(f"({result['successful_requests']} succeeded, {result['failed_requests']} failed)\n\n")
            
            if result.get('latency'):
                lat = result['latency']
                f.write("**Latency Statistics**:\n")
                f.write(f"- Minimum: {lat['min']:.2f}ms\n")
                f.write(f"- Maximum: {lat['max']:.2f}ms\n")
                f.write(f"- Average: {lat['avg']:.2f}ms\n")
                f.write(f"- Median: {lat['median']:.2f}ms\n")
                f.write(f"- Std Dev: {lat['stdev']:.2f}ms\n")
                if 'p95' in lat:
                    f.write(f"- 95th Percentile: {lat['p95']:.2f}ms\n")
                if 'p99' in lat:
                    f.write(f"- 99th Percentile: {lat['p99']:.2f}ms\n")
            else:
                f.write("**Status**: All requests failed\n")
            
            if result.get('errors'):
                f.write(f"\n**Errors** ({len(result['errors'])}):\n")
                for error in result['errors'][:10]:  # Show first 10 errors
                    f.write(f"- {error}\n")
                if len(result['errors']) > 10:
                    f.write(f"- ... and {len(result['errors']) - 10} more\n")
            
            f.write("\n---\n\n")
        
        # Analysis
        f.write("## Analysis\n\n")
        
        # Compare proxy vs target from same location
        local_results = [r for r in all_results if r['location'] == 'Local']
        ec2_results = [r for r in all_results if r['location'] == 'EC2']
        
        if len(local_results) == 2:
            proxy_local = next((r for r in local_results if 'Proxy' in r['name']), None)
            target_local = next((r for r in local_results if 'Target' in r['name']), None)
            
            if proxy_local and target_local and proxy_local.get('latency') and target_local.get('latency'):
                diff = proxy_local['latency']['avg'] - target_local['latency']['avg']
                pct = (diff / target_local['latency']['avg']) * 100
                
                f.write("### Local Network: Proxy vs Direct Target\n\n")
                f.write(f"- Proxy Avg: {proxy_local['latency']['avg']:.2f}ms\n")
                f.write(f"- Target Avg: {target_local['latency']['avg']:.2f}ms\n")
                f.write(f"- Difference: {diff:+.2f}ms ({pct:+.1f}%)\n\n")
                
                if diff < 0:
                    f.write(f"✅ **Proxy is {abs(diff):.2f}ms faster** than direct target\n\n")
                elif diff < 50:
                    f.write(f"✅ **Proxy overhead is minimal** ({diff:.2f}ms)\n\n")
                else:
                    f.write(f"⚠️ **Proxy adds {diff:.2f}ms overhead**\n\n")
        
        if len(ec2_results) == 2:
            proxy_ec2 = next((r for r in ec2_results if 'Proxy' in r['name']), None)
            target_ec2 = next((r for r in ec2_results if 'Target' in r['name']), None)
            
            if proxy_ec2 and target_ec2 and proxy_ec2.get('latency') and target_ec2.get('latency'):
                diff = proxy_ec2['latency']['avg'] - target_ec2['latency']['avg']
                pct = (diff / target_ec2['latency']['avg']) * 100
                
                f.write("### EC2 US-East: Proxy vs Direct Target\n\n")
                f.write(f"- Proxy Avg: {proxy_ec2['latency']['avg']:.2f}ms\n")
                f.write(f"- Target Avg: {target_ec2['latency']['avg']:.2f}ms\n")
                f.write(f"- Difference: {diff:+.2f}ms ({pct:+.1f}%)\n\n")
                
                if diff < 0:
                    f.write(f"✅ **Proxy is {abs(diff):.2f}ms faster** than direct target\n\n")
                elif diff < 50:
                    f.write(f"✅ **Proxy overhead is minimal** ({diff:.2f}ms)\n\n")
                else:
                    f.write(f"⚠️ **Proxy adds {diff:.2f}ms overhead**\n\n")
        
        # Compare same endpoint from different locations
        if local_results and ec2_results:
            f.write("### Geographic Latency Comparison\n\n")
            
            for endpoint_type in ['Proxy', 'Target']:
                local_ep = next((r for r in local_results if endpoint_type in r['name']), None)
                ec2_ep = next((r for r in ec2_results if endpoint_type in r['name']), None)
                
                if local_ep and ec2_ep and local_ep.get('latency') and ec2_ep.get('latency'):
                    diff = abs(local_ep['latency']['avg'] - ec2_ep['latency']['avg'])
                    f.write(f"**{endpoint_type}**:\n")
                    f.write(f"- Local: {local_ep['latency']['avg']:.2f}ms\n")
                    f.write(f"- EC2: {ec2_ep['latency']['avg']:.2f}ms\n")
                    f.write(f"- Geographic Difference: {diff:.2f}ms\n\n")
        
        f.write("---\n\n")
        f.write("*Report generated by Network Latency Test Tool*\n")
    
    return report_file


def print_summary(all_results: List[Dict]):
    """Print summary to console"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}TEST SUMMARY")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    # Table header
    print(f"{Fore.WHITE}{'Test':<30} {'Location':<10} {'Avg Latency':<15} {'Success Rate'}")
    print(f"{Fore.WHITE}{'-'*70}")
    
    for result in all_results:
        name = f"{result['location']} → {result['name']}"
        if result.get('latency'):
            lat_str = f"{result['latency']['avg']:.2f}ms"
            success_str = f"{result['success_rate']:.1f}%"
            color = Fore.GREEN if result['success_rate'] > 95 else Fore.YELLOW
        else:
            lat_str = "FAILED"
            success_str = "0%"
            color = Fore.RED
        
        print(f"{color}{name:<30} {result['location']:<10} {lat_str:<15} {success_str}")
    
    print(f"{Fore.WHITE}{'-'*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Network Latency Test Tool")
    parser.add_argument(
        "--mode",
        choices=["local", "ec2", "full"],
        default="full",
        help="Test mode: local (run local tests only), ec2 (run EC2 tests only), full (run both)"
    )
    parser.add_argument(
        "--output",
        help="Output report file path (default: auto-generated)"
    )
    
    args = parser.parse_args()
    
    print(f"{Fore.CYAN}{Style.BRIGHT}")
    print("="*60)
    print("NETWORK LATENCY TEST")
    print("="*60)
    print(f"{Style.RESET_ALL}")
    print(f"Proxy: {PROXY_URL}")
    print(f"Target: {TARGET_URL}")
    print(f"Requests per test: {NUM_REQUESTS}")
    print(f"Mode: {args.mode.upper()}")
    
    all_results = []
    
    try:
        if args.mode in ["local", "full"]:
            local_results = run_local_tests()
            all_results.extend(local_results)
        
        if args.mode in ["ec2", "full"]:
            ec2_results = run_ec2_tests()
            all_results.extend(ec2_results)
        
        if all_results:
            # Print summary
            print_summary(all_results)
            
            # Generate report
            report_file = generate_report(all_results)
            print(f"\n{Fore.GREEN}✓ Report saved to: {report_file}")
            
            # Save JSON results
            json_file = report_file.replace(".md", ".json")
            with open(json_file, "w") as f:
                json.dump(all_results, f, indent=2)
            print(f"{Fore.GREEN}✓ JSON results saved to: {json_file}")
        else:
            print(f"\n{Fore.RED}No test results collected")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
