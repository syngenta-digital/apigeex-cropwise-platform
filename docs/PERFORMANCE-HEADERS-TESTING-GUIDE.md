# Performance Headers Testing Guide

## Overview

Performance headers have been implemented to provide real-time latency visibility for the Cropwise Platform API proxy. This allows developers to quickly identify performance bottlenecks without accessing debug logs or analytics dashboards.

---

## Implementation Details

### Files Created:

1. **Timing Capture Policies**:
   - `apiproxy/policies/AM-Timestamp-JWT-Start.xml`
   - `apiproxy/policies/AM-Timestamp-JWT-End.xml`
   - `apiproxy/policies/AM-Timestamp-KVM-Start.xml`
   - `apiproxy/policies/AM-Timestamp-KVM-End.xml`
   - `apiproxy/policies/AM-Timestamp-RateLimit-Start.xml`
   - `apiproxy/policies/AM-Timestamp-RateLimit-End.xml`

2. **Performance Headers Policy**:
   - `apiproxy/policies/AM-Add-Performance-Headers.xml`

3. **Test Script**:
   - `tests/test-performance-headers.py`

### Proxy Configuration Updated:

- `apiproxy/proxies/default.xml` - Added timestamp policies and performance header output

---

## How It Works

### 1. Request Flow:

```
Client sends request with X-Debug-Performance: true header
  ↓
Timestamp policies capture start/end times for:
  - JWT processing
  - KVM lookup
  - Rate limiting
  ↓
Response includes X-Apigee-* headers with timing data
```

### 2. Security:

- Performance headers **ONLY** appear when `X-Debug-Performance: true` is present
- Normal requests (without debug header) have no overhead
- Safe for production deployment (headers won't leak without debug header)

---

## Testing

### Prerequisites:

```powershell
# Set bearer token
$env:BEARER_TOKEN = "your_jwt_token_here"
```

### Method 1: Using Python Test Script

```powershell
# Run test script
python tests/test-performance-headers.py
```

**Expected Output**:
```
================================================================================
PERFORMANCE HEADERS TEST
================================================================================

Test 1: WITH X-Debug-Performance header
--------------------------------------------------------------------------------
Status Code: 200

✓ Found 15 performance headers:

  X-Apigee-Environment: default-dev
  X-Apigee-JWT-Time: 12ms
  X-Apigee-KVM-Time: 8ms
  X-Apigee-Message-ID: abc123-def456
  X-Apigee-Network-ClientToProxy: 40ms
  X-Apigee-Network-ProxyToTarget: 15ms
  X-Apigee-Proxy-Name: cropwise-unified-platform
  X-Apigee-Proxy-Time: 138ms
  X-Apigee-RateLimit-Time: 45ms
  X-Apigee-Request-Processing: 90ms
  X-Apigee-Response-Processing: 10ms
  X-Apigee-Revision: 4
  X-Apigee-Target-Time: 1ms
  X-Apigee-Total-Time: 139ms

Timing Summary:
  Total Request Time: 139ms
  Proxy Processing: 138ms
  Backend Time: 1ms

Policy Execution Times:
  JWT Processing: 12ms
  KVM Lookup: 8ms
  Rate Limiting: 45ms

Latency Breakdown:
  Proxy Overhead: 99.3%
  Backend Time: 0.7%

Test 2: WITHOUT X-Debug-Performance header (normal request)
--------------------------------------------------------------------------------
Status Code: 200
✓ No performance headers (as expected)
```

### Method 2: Using curl

```bash
# With performance headers
curl -H "Authorization: Bearer $TOKEN" \
     -H "X-Debug-Performance: true" \
     https://dev.api.cropwise.com/cropwise-unified-platform/accounts/me \
     -v

# Without performance headers (normal request)
curl -H "Authorization: Bearer $TOKEN" \
     https://dev.api.cropwise.com/cropwise-unified-platform/accounts/me \
     -v
```

### Method 3: Using EC2 Test (with performance headers)

Modify `tests/ec2-latency-test.py` to add the debug header:

```python
headers = {
    "Authorization": f"Bearer {token}",
    "X-Debug-Performance": "true"  # Add this line
}
```

---

## Performance Headers Reference

### Timing Headers:

| Header | Description | Example |
|--------|-------------|---------|
| `X-Apigee-Total-Time` | End-to-end request time | `139ms` |
| `X-Apigee-Proxy-Time` | Total proxy processing time | `138ms` |
| `X-Apigee-Target-Time` | Backend response time | `1ms` |
| `X-Apigee-Request-Processing` | Time before target call | `90ms` |
| `X-Apigee-Response-Processing` | Time after target response | `10ms` |

### Policy-Specific Headers:

| Header | Description | Example |
|--------|-------------|---------|
| `X-Apigee-JWT-Time` | JWT extraction & parsing | `12ms` |
| `X-Apigee-KVM-Time` | KVM lookup duration | `8ms` |
| `X-Apigee-RateLimit-Time` | Rate limiting policies | `45ms` |

### Network Latency Headers:

| Header | Description | Example |
|--------|-------------|---------|
| `X-Apigee-Network-ClientToProxy` | Estimated client → proxy latency | `40ms` |
| `X-Apigee-Network-ProxyToTarget` | Proxy → backend network time | `15ms` |

### Metadata Headers:

| Header | Description | Example |
|--------|-------------|---------|
| `X-Apigee-Message-ID` | Unique request identifier | `abc123-def456` |
| `X-Apigee-Proxy-Name` | API proxy name | `cropwise-unified-platform` |
| `X-Apigee-Revision` | Proxy revision number | `4` |
| `X-Apigee-Environment` | Apigee environment | `default-dev` |

---

## Interpreting Results

### Example Analysis:

```
X-Apigee-Total-Time: 139ms
X-Apigee-Proxy-Time: 138ms
X-Apigee-Target-Time: 1ms
X-Apigee-JWT-Time: 12ms
X-Apigee-KVM-Time: 8ms
X-Apigee-RateLimit-Time: 45ms
```

**Analysis**:
- **Total Request**: 139ms
- **Backend**: 1ms (excellent! <1% of total)
- **Proxy Overhead**: 138ms (99% of total)
  - JWT Processing: 12ms (9%)
  - KVM Lookup: 8ms (6%)
  - Rate Limiting: 45ms (32%) ⚠️ **Optimization target**
  - Other processing: 73ms (53%)

**Conclusion**: Rate limiting policies are the slowest component (45ms). Consider:
1. Caching rate limit lookups
2. Consolidating multiple rate limit policies
3. Optimizing KVM structure

---

## Troubleshooting

### Issue: No performance headers in response

**Possible Causes**:
1. Missing `X-Debug-Performance: true` header in request
2. Policy not deployed yet (need to deploy proxy revision)
3. Policy execution being skipped due to conditions

**Solution**:
```bash
# Verify header is sent
curl -H "Authorization: Bearer $TOKEN" \
     -H "X-Debug-Performance: true" \
     https://dev.api.cropwise.com/cropwise-unified-platform/accounts/me \
     -v 2>&1 | grep -i "x-debug"
```

### Issue: Some timing headers show no value

**Cause**: Variables not set (policy may not have executed)

**Example**:
```
X-Apigee-JWT-Time: (no value)
```

**Explanation**: JWT policy may have been skipped due to condition not met

---

## Performance Impact

### Overhead Analysis:

| Scenario | Overhead | Notes |
|----------|----------|-------|
| **Normal Request** (no debug header) | **0ms** | No timing policies execute |
| **Debug Request** (with header) | **2-3ms** | 6 timestamp captures + header assignment |

### Best Practices:

1. ✅ **Development/Testing**: Always use debug header
2. ✅ **Production**: Use sparingly for troubleshooting
3. ⚠️ **Load Testing**: Disable debug header (adds overhead)
4. ⚠️ **Monitoring**: Use Apigee Analytics instead (no overhead)

---

## Next Steps

### Immediate:

1. **Test Implementation**:
   ```powershell
   $env:BEARER_TOKEN = "your_token"
   python tests/test-performance-headers.py
   ```

2. **Deploy to Apigee**:
   - Upload proxy bundle
   - Deploy revision
   - Test with curl

### Short-term:

1. **Optimize Slow Policies**:
   - If rate limiting > 30ms, optimize
   - If KVM lookup > 10ms, consider caching
   - If JWT parsing > 15ms, investigate

2. **Add More Timing Markers**:
   - ServiceCallout policies
   - Custom JavaScript callouts
   - External API calls

### Long-term:

1. **Transition to Production Monitoring**:
   - Enable Google Cloud Trace
   - Set up Apigee Analytics dashboards
   - Create alerts for slow requests (>150ms)

2. **Remove Debug Headers**:
   - Once production monitoring is in place
   - Keep code in repository for future use

---

## Security Considerations

### Safe for Production:

✅ Headers only appear when debug header is present  
✅ No sensitive information exposed (only timing data)  
✅ Minimal overhead when not in use  
✅ Conditional execution prevents accidental exposure

### Recommendations:

1. **Limit Access**: Consider IP whitelisting for debug header usage
2. **Monitor Usage**: Log when debug header is used
3. **Rotate Tokens**: Use separate tokens for testing
4. **Remove in Production**: Once proper monitoring is set up

---

## Example Use Cases

### 1. Identify Slow Policy

```bash
curl -H "Authorization: Bearer $TOKEN" \
     -H "X-Debug-Performance: true" \
     https://dev.api.cropwise.com/cropwise-unified-platform/accounts/me \
     -v 2>&1 | grep "X-Apigee-.*-Time"
```

**Look for**: Headers with high values (>20ms)

### 2. Compare with Direct Backend

```bash
# Via proxy (with debug)
time curl -H "Authorization: Bearer $TOKEN" \
          -H "X-Debug-Performance: true" \
          https://dev.api.cropwise.com/cropwise-unified-platform/accounts/me

# Direct to backend
time curl -H "Authorization: Bearer $TOKEN" \
          https://api.staging.base.cropwise.com/v2/accounts/me
```

### 3. Monitor Performance Over Time

```python
# Run 20 requests and track timing
import requests
import statistics

timings = []
for i in range(20):
    r = requests.get(url, headers={"Authorization": f"Bearer {token}", "X-Debug-Performance": "true"})
    total_time = int(r.headers.get("X-Apigee-Total-Time", 0))
    timings.append(total_time)

print(f"Average: {statistics.mean(timings)}ms")
print(f"Min: {min(timings)}ms")
print(f"Max: {max(timings)}ms")
print(f"Stdev: {statistics.stdev(timings):.2f}ms")
```

---

## Summary

✅ **Implementation Complete**  
✅ **Ready for Testing**  
✅ **Safe for Production** (conditional execution)  
✅ **Immediate Visibility** (no log analysis needed)

**Next Action**: Run `python tests/test-performance-headers.py` to verify implementation!

---

*Document Version: 1.0*  
*Last Updated: February 2, 2026*  
*Author: Cropwise Platform Team*
