# Latency Test Analysis Report

**Test Date:** February 2, 2026, 19:05:46  
**Test Duration:** 10 requests per endpoint  
**Report Generated:** February 2, 2026

---

## Executive Summary

This report analyzes the latency performance comparison between the Apigee X proxy gateway and the direct backend target for the Cropwise Unified Platform. The test results show **unexpected performance characteristics** where the proxy demonstrates **lower latency** than direct backend access.

### Key Findings

- ✅ **100% Success Rate** on both proxy and target endpoints
- 🚀 **Proxy Performance:** Average 705.62ms (28.06% faster than target)
- 📊 **Target Performance:** Average 980.79ms
- ⚡ **Negative Overhead:** -275.17ms (proxy is faster than direct backend)
- 📈 **Proxy Stability:** Lower standard deviation (73.01ms vs 274.87ms)

---

## Test Configuration

| Parameter | Value |
|-----------|-------|
| **Proxy URL** | `https://dev.api.cropwise.com/cropwise-unified-platform` |
| **Target URL** | `https://api.staging.base.cropwise.com` |
| **Proxy Endpoint** | `/accounts/me` |
| **Target Endpoint** | `/v2/accounts/me` |
| **Test Method** | HTTP GET with JWT authentication |
| **Number of Requests** | 10 per endpoint |
| **Authentication** | Bearer Token + Session Cookie |

### Full Request URLs
- **Proxy:** `https://dev.api.cropwise.com/cropwise-unified-platform/accounts/me`
- **Target:** `https://api.staging.base.cropwise.com/v2/accounts/me`

---

## Performance Metrics

### Apigee Proxy Statistics

| Metric | Value | Status |
|--------|-------|--------|
| **Total Requests** | 10 | ✅ All Successful |
| **Success Rate** | 100.0% | ✅ Excellent |
| **Minimum Latency** | 610.14ms | 🟢 Best case |
| **Maximum Latency** | 803.96ms | 🟢 Worst case |
| **Average Latency** | 705.62ms | 🟢 Good |
| **Median Latency** | 689.57ms | 🟢 Consistent |
| **Standard Deviation** | 73.01ms | 🟢 Low variance |

#### Proxy Request Distribution
```
Request 1:  801.75ms  ███████████████████▌
Request 2:  713.37ms  █████████████████▍
Request 3:  626.75ms  ███████████████▎
Request 4:  705.64ms  █████████████████▏
Request 5:  655.82ms  ████████████████
Request 6:  666.68ms  ████████████████▎
Request 7:  673.51ms  ████████████████▍
Request 8:  803.96ms  ███████████████████▌ (MAX)
Request 9:  610.14ms  ██████████████▊ (MIN)
Request 10: 798.59ms  ███████████████████▍
```

### Direct Backend Target Statistics

| Metric | Value | Status |
|--------|-------|--------|
| **Total Requests** | 10 | ✅ All Successful |
| **Success Rate** | 100.0% | ✅ Excellent |
| **Minimum Latency** | 771.69ms | 🟡 Slower than proxy |
| **Maximum Latency** | 1,722.85ms | 🔴 Significant spike |
| **Average Latency** | 980.79ms | 🟡 28% slower |
| **Median Latency** | 919.73ms | 🟡 Higher baseline |
| **Standard Deviation** | 274.87ms | 🔴 High variance |

#### Target Request Distribution
```
Request 1:  1,009.78ms  ████████████████████▍
Request 2:    985.41ms  ███████████████████▉
Request 3:    798.69ms  ████████████████▏
Request 4:    993.55ms  ████████████████████▏
Request 5:  1,722.85ms  ██████████████████████████████████▉ (MAX - OUTLIER)
Request 6:    771.69ms  ████████████████▋ (MIN)
Request 7:    973.13ms  ███████████████████▋
Request 8:    857.20ms  █████████████████▍
Request 9:    866.33ms  █████████████████▌
Request 10:   829.27ms  ████████████████▊
```

---

## Comparative Analysis

### Latency Overhead

| Comparison Metric | Value | Assessment |
|-------------------|-------|------------|
| **Proxy vs Target Overhead** | **-275.17ms** | ⚡ **Proxy is FASTER** |
| **Overhead Percentage** | **-28.06%** | 🚀 Significant advantage |
| **Latency Reduction** | 275.17ms saved per request | 💰 Cost effective |

### Performance Interpretation

The **negative overhead** indicates that the Apigee proxy is responding **faster** than the direct backend. This unusual result suggests one of the following scenarios:

#### Possible Explanations:

1. **✅ Caching Mechanism**
   - Apigee proxy may have response caching enabled for the `/accounts/me` endpoint
   - Cached responses eliminate backend processing time
   - **Recommendation:** Review proxy cache policies

2. **🌐 Network Routing Optimization**
   - Proxy may have better network routes or CDN integration
   - Geographic proximity to test client
   - **Recommendation:** Test from multiple geographic locations

3. **⚙️ Backend Processing Overhead**
   - Direct backend may perform additional processing not present in cached proxy responses
   - Database queries, authentication validation, or business logic execution
   - **Recommendation:** Profile backend application performance

4. **🔄 Request Transformation**
   - Proxy may be simplifying or transforming requests
   - Path rewriting from `/accounts/me` → `/v2/accounts/me` on backend
   - **Recommendation:** Verify data consistency between proxy and target responses

---

## Stability Analysis

### Variance Comparison

| Endpoint | Std Dev | Variance Ratio | Stability |
|----------|---------|----------------|-----------|
| **Proxy** | 73.01ms | 1.0x | 🟢 **Very Stable** |
| **Target** | 274.87ms | 3.76x | 🔴 **Unstable** |

**Analysis:** The proxy demonstrates **3.76x better stability** than the direct backend, with significantly lower standard deviation. This indicates:

- ✅ More predictable response times through the proxy
- ⚠️ Backend has high variability (outlier spike of 1,722.85ms)
- 💡 Proxy provides consistent user experience

### Reliability Score

| Aspect | Proxy | Target |
|--------|-------|--------|
| **Success Rate** | 100% ✅ | 100% ✅ |
| **Consistency** | High (73ms σ) ✅ | Low (274ms σ) ⚠️ |
| **Outlier Count** | 0 | 1 (Request #5) |
| **Overall Reliability** | **Excellent** | **Good** |

---

## Request-by-Request Analysis

### Latency Delta Per Request

| Request # | Proxy (ms) | Target (ms) | Delta (ms) | Winner |
|-----------|------------|-------------|------------|--------|
| 1 | 801.75 | 1,009.78 | -208.03 | 🟢 Proxy |
| 2 | 713.37 | 985.41 | -272.04 | 🟢 Proxy |
| 3 | 626.75 | 798.69 | -171.94 | 🟢 Proxy |
| 4 | 705.64 | 993.55 | -287.91 | 🟢 Proxy |
| 5 | 655.82 | 1,722.85 | -1,067.03 | 🟢 Proxy (huge gap) |
| 6 | 666.68 | 771.69 | -105.01 | 🟢 Proxy |
| 7 | 673.51 | 973.13 | -299.62 | 🟢 Proxy |
| 8 | 803.96 | 857.20 | -53.24 | 🟢 Proxy |
| 9 | 610.14 | 866.33 | -256.19 | 🟢 Proxy |
| 10 | 798.59 | 829.27 | -30.68 | 🟢 Proxy |

**Result:** Proxy won all 10 requests with lower latency

---

## Performance Percentiles

### Proxy Latency Distribution

| Percentile | Latency (ms) | Status |
|------------|--------------|--------|
| P10 (Best 10%) | 610.14 | 🟢 Excellent |
| P25 | 655.82 | 🟢 Good |
| **P50 (Median)** | **689.57** | 🟢 Good |
| P75 | 713.37 | 🟢 Good |
| P90 | 801.75 | 🟢 Good |
| P95 | 803.96 | 🟢 Good |
| P99 (Worst 1%) | 803.96 | 🟢 Good |

### Target Latency Distribution

| Percentile | Latency (ms) | Status |
|------------|--------------|--------|
| P10 (Best 10%) | 771.69 | 🟡 Acceptable |
| P25 | 829.27 | 🟡 Acceptable |
| **P50 (Median)** | **919.73** | 🟡 Acceptable |
| P75 | 993.55 | 🟡 Acceptable |
| P90 | 1,009.78 | 🟡 Acceptable |
| P95 | 1,722.85 | 🔴 High |
| P99 (Worst 1%) | 1,722.85 | 🔴 High |

---

## Anomaly Detection

### Identified Anomalies

1. **🔴 Target Request #5 Spike**
   - **Latency:** 1,722.85ms (75.7% above average)
   - **Impact:** Significantly skewed target statistics
   - **Possible Causes:**
     - Cold start / lazy initialization
     - Database connection pool exhaustion
     - Garbage collection pause
     - Network congestion
   - **Recommendation:** Monitor backend metrics during testing

2. **⚡ Consistent Proxy Performance Advantage**
   - All 10 requests showed proxy faster than target
   - **Probability:** This pattern is unlikely without caching
   - **Recommendation:** Verify cache configuration in Apigee

---

## Recommendations

### Immediate Actions

1. **🔍 Investigate Caching**
   - Review Apigee proxy cache policies for `/accounts/me` endpoint
   - Verify cache TTL and invalidation strategies
   - Ensure cached data is fresh and accurate

2. **📊 Backend Performance Profiling**
   - Identify cause of 1,722.85ms spike in target
   - Monitor database query performance
   - Check for resource contention during peak loads

3. **🧪 Expand Testing Scope**
   - Test with cache-bypass headers
   - Test from multiple geographic locations
   - Increase sample size to 100+ requests for statistical significance
   - Test different endpoints (not just `/accounts/me`)

### Long-Term Optimizations

4. **⚙️ Backend Optimization**
   - Reduce P95 latency on direct backend
   - Implement connection pooling and query optimization
   - Add database indexes for account lookups

5. **📈 Monitoring & Alerting**
   - Set up latency SLOs (Service Level Objectives)
   - Alert on P95 latency > 1,000ms
   - Track cache hit ratios in Apigee

6. **🔄 Load Testing**
   - Perform load testing with concurrent users
   - Test cache eviction under high traffic
   - Validate performance under stress conditions

---

## Conclusions

### Summary

The Apigee proxy demonstrates **superior performance** compared to direct backend access for the `/accounts/me` endpoint:

- ✅ **28.06% faster** average response time
- ✅ **3.76x more stable** with lower variance
- ✅ **100% success rate** maintained
- ⚠️ **Potential caching** requires validation

### Final Verdict

| Category | Rating | Notes |
|----------|--------|-------|
| **Proxy Performance** | ⭐⭐⭐⭐⭐ Excellent | Fast and consistent |
| **Target Performance** | ⭐⭐⭐ Good | Acceptable but variable |
| **Cache Strategy** | ⚠️ Unknown | Requires investigation |
| **Overall System Health** | ✅ Healthy | Both endpoints operational |

### Next Steps

1. ✅ Validate proxy cache configuration
2. ✅ Investigate backend performance spike
3. ✅ Expand testing to additional endpoints
4. ✅ Implement continuous latency monitoring
5. ✅ Document cache policies and TTLs

---

## Appendix

### Test Environment Details

- **Client Location:** Unknown (not captured)
- **Network Conditions:** Unknown (not captured)
- **Test Tool:** Python requests library
- **Concurrency:** Sequential requests (no parallel load)
- **Authentication:** JWT Bearer Token + Session Cookie
- **HTTP Method:** GET
- **Response Validation:** Status code only (200 OK)

### Data Files

- **Raw Results:** `latency-results-20260202-190546.json`
- **Summary CSV:** `latency-summary.csv` (if generated)
- **Test Script:** `workspace.py`

### Related Documentation

- Apigee Proxy Configuration: `apiproxy/proxies/default.xml`
- Endpoint Configuration: `config/endpoints.json`
- Deployment Guide: `docs/DEPLOYMENT-GUIDE.md`

---

*This analysis was generated based on test results from February 2, 2026. Performance characteristics may vary under different load conditions, network environments, and time periods.*
