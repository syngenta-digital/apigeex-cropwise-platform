# Network Latency Testing

This directory contains tools for testing network latency between different locations and the Cropwise Platform API.

## Files

- **network-latency-test.py** - Comprehensive network latency testing tool
- **workspace.py** - Simple latency comparison tool (Proxy vs Target)
- **latency-test/** - Output directory for latency test results
- **debug-logs/** - Apigee X debug session logs

## Network Latency Test

The `network-latency-test.py` script performs comprehensive latency testing from multiple locations:

1. **Local Network → Apigee Proxy**
2. **Local Network → Direct Target**
3. **EC2 US-East → Apigee Proxy**
4. **EC2 US-East → Direct Target**

### Prerequisites

```bash
pip install requests colorama
```

### Configuration

Set your Bearer token as an environment variable:

```bash
# Windows
set BEARER_TOKEN=your_jwt_token_here

# Linux/Mac
export BEARER_TOKEN=your_jwt_token_here
```

Or the script will prompt you for it.

### Usage

#### Run Full Test (Local + EC2)

```bash
python network-latency-test.py --mode full
```

#### Run Local Tests Only

```bash
python network-latency-test.py --mode local
```

#### Run EC2 Tests Only

```bash
python network-latency-test.py --mode ec2
```

### EC2 Configuration

- **Instance**: ec2-107-20-114-33.compute-1.amazonaws.com
- **Region**: US-East (Virginia)
- **User**: ec2-user
- **SSH Key**: `C:\apigeex-cropwise-platform\keys\dssat-testing-use1.pem`

### Output

The tool generates:

1. **Markdown Report**: `latency-test/network-latency-report-YYYYMMDD-HHMMSS.md`
   - Executive summary with comparison tables
   - Detailed results for each test
   - Analysis and recommendations

2. **JSON Results**: `latency-test/network-latency-report-YYYYMMDD-HHMMSS.json`
   - Raw data for further analysis
   - All latency statistics and metadata

### Example Output

```
========================================
LOCAL NETWORK TESTS
========================================

Location: New York, NY, United States
ISP: Verizon Fios
Public IP: 49.37.219.182

[LOCAL] Testing Apigee Proxy...
URL: https://dev.api.cropwise.com/cropwise-unified-platform/accounts/me
Requests: 20
  Request 1/20... ✓ 200 - 842.09ms
  Request 2/20... ✓ 200 - 723.93ms
  ...

========================================
EC2 US-EAST TESTS
========================================

Deploying test script to EC2...
✓ Script deployed to EC2

Running tests on EC2...

✓ Apigee Proxy test completed
  Avg Latency: 125.43ms
  Success Rate: 100.0%

✓ Direct Target test completed
  Avg Latency: 198.76ms
  Success Rate: 100.0%

========================================
TEST SUMMARY
========================================

Test                           Location   Avg Latency     Success Rate
----------------------------------------------------------------------
Local → Apigee Proxy          Local      805.86ms        100.0%
Local → Direct Target         Local      1309.04ms       100.0%
EC2 → Apigee Proxy           EC2        125.43ms        100.0%
EC2 → Direct Target          EC2        198.76ms        100.0%
----------------------------------------------------------------------

✓ Report saved to: latency-test/network-latency-report-20260202-203045.md
✓ JSON results saved to: latency-test/network-latency-report-20260202-203045.json
```

### Interpreting Results

#### Proxy Overhead

Compare proxy vs target from the same location to measure Apigee overhead:

- **< 0ms**: Proxy is faster (caching or optimized routing)
- **< 50ms**: Excellent - minimal overhead
- **50-100ms**: Good - acceptable overhead
- **> 100ms**: Investigate - may need optimization

#### Geographic Latency

Compare same endpoint from different locations:

- Shows impact of physical distance on latency
- Helps identify optimal deployment regions
- Useful for CDN and edge strategy planning

### Troubleshooting

#### SSH Connection Issues

If EC2 tests fail, verify:

1. SSH key permissions:
   ```bash
   icacls "C:\apigeex-cropwise-platform\keys\dssat-testing-use1.pem" /inheritance:r /grant:r "%USERNAME%:R"
   ```

2. EC2 instance is running:
   ```bash
   ssh -i keys/dssat-testing-use1.pem ec2-user@ec2-107-20-114-33.compute-1.amazonaws.com
   ```

3. Security group allows SSH (port 22) from your IP

#### Authentication Errors

If you get 401 errors:

1. Verify Bearer token is valid and not expired
2. Check token has correct permissions for `/accounts/me` endpoint
3. Ensure token is properly formatted (starts with "eyJ...")

#### Python Dependencies

If imports fail:

```bash
pip install --upgrade requests colorama
```

## Simple Latency Test

The `workspace.py` script is a simpler tool for quick proxy vs target comparison:

```bash
python workspace.py
```

This runs 10 requests to both endpoints and compares the latency.

## Debug Logs

Apigee X debug session logs can be stored in `debug-logs/` for analysis. Use the companion analysis tool to parse debug logs:

```bash
python -c "import json; print(json.dumps(json.load(open('debug-logs/debug-XXXXX.json')), indent=2))"
```

## Security Notes

⚠️ **Never commit sensitive data**:

- Bearer tokens should be in environment variables only
- SSH keys are excluded via `.gitignore`
- Debug logs may contain sensitive headers (masked by default)
- Test results may contain IP addresses and location data

## Contributing

When adding new test scripts:

1. Follow the existing code structure
2. Include proper error handling
3. Generate both markdown and JSON output
4. Add documentation to this README
5. Exclude test results from git (add to `.gitignore`)
