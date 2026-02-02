# Enabling Policy-Wise Latency and Network Latency Logging in Apigee X

**Document Version**: 1.0  
**Last Updated**: February 2, 2026  
**Author**: Cropwise Platform Team

---

## Overview

This guide provides methods to capture detailed policy-wise execution times and network latency metrics in Apigee X for performance analysis and optimization.

---

## Method 1: Apigee Analytics (Built-in)

### Description
Apigee X automatically captures policy execution metrics in the Analytics dashboard.

### Steps to Access:

1. **Navigate to Apigee Console**:
   ```
   https://apigee.google.com/
   ```

2. **Go to Analytics**:
   - Select your organization: `use1-apigeex`
   - Select environment: `default-dev`
   - Navigate to: **Analyze** → **API Proxy Performance**

3. **View Policy Performance**:
   - Select API: `cropwise-unified-platform`
   - Time range: Last 1 hour / 24 hours / Custom
   - Metrics available:
     - **Policy Execution Time**: Time spent in each policy
     - **Target Response Time**: Backend response time
     - **Total Response Time**: End-to-end latency

### Metrics Available:

| Metric | Description | Usage |
|--------|-------------|-------|
| `policy_execution_time` | Time spent executing each policy | Identify slow policies |
| `target_response_time` | Backend response time | Measure backend performance |
| `request_processing_latency` | Apigee processing time | Total proxy overhead |
| `total_response_time` | End-to-end latency | Overall performance |

### Advantages:
- ✅ Built-in, no configuration needed
- ✅ Historical data (retention based on plan)
- ✅ Dashboard visualization

### Limitations:
- ⚠️ Aggregated data (not per-request)
- ⚠️ Limited real-time visibility
- ⚠️ May not show sub-millisecond timings

---

## Method 2: Statistics Collector Policy (Recommended)

### Description
Add Statistics Collector policies before and after each critical policy to measure execution time.

### Implementation:

#### Step 1: Create Statistics Collector Policies

**File**: `apiproxy/policies/SC-Start-Timer.xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<StatisticsCollector name="SC-Start-Timer">
    <DisplayName>SC-Start-Timer</DisplayName>
    <Statistics>
        <Statistic name="request_start_time" ref="system.timestamp" type="long"/>
    </Statistics>
</StatisticsCollector>
```

**File**: `apiproxy/policies/SC-Policy-JWT-Start.xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<StatisticsCollector name="SC-Policy-JWT-Start">
    <DisplayName>SC-Policy-JWT-Start</DisplayName>
    <Statistics>
        <Statistic name="jwt_policy_start" ref="system.timestamp" type="long"/>
    </Statistics>
</StatisticsCollector>
```

**File**: `apiproxy/policies/SC-Policy-JWT-End.xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<StatisticsCollector name="SC-Policy-JWT-End">
    <DisplayName>SC-Policy-JWT-End</DisplayName>
    <Statistics>
        <Statistic name="jwt_policy_end" ref="system.timestamp" type="long"/>
        <Statistic name="jwt_policy_duration" ref="jwt_policy_end - jwt_policy_start" type="long"/>
    </Statistics>
</StatisticsCollector>
```

#### Step 2: Add to Proxy Flow

**File**: `apiproxy/proxies/default.xml`

```xml
<PreFlow name="PreFlow">
    <Request>
        <Step>
            <Name>SC-Start-Timer</Name>
        </Step>
        
        <Step>
            <Name>SC-Policy-JWT-Start</Name>
        </Step>
        <Step>
            <Name>EV-Extract-JWT-Token</Name>
        </Step>
        <Step>
            <Name>JS-Parse-JWT-Token</Name>
        </Step>
        <Step>
            <Name>SC-Policy-JWT-End</Name>
        </Step>
        
        <!-- Add similar wrappers for other policies -->
    </Request>
</PreFlow>
```

#### Step 3: Query Analytics

Access custom statistics via Apigee Analytics API or custom reports.

### Advantages:
- ✅ Per-policy timing
- ✅ Custom metrics
- ✅ Visible in Analytics dashboard

### Limitations:
- ⚠️ Adds slight overhead (~1-2ms per collector)
- ⚠️ Requires policy modifications

---

## Method 3: Custom Variables + MessageLogging (Detailed)

### Description
Use AssignMessage policies to capture timestamps and log them via MessageLogging.

### Implementation:

#### Step 1: Add Timestamp Variables

**File**: `apiproxy/policies/AM-Timestamp-JWT-Start.xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<AssignMessage name="AM-Timestamp-JWT-Start">
    <DisplayName>AM-Timestamp-JWT-Start</DisplayName>
    <AssignVariable>
        <Name>timing.jwt.start</Name>
        <Value>{system.timestamp}</Value>
    </AssignVariable>
</AssignMessage>
```

**File**: `apiproxy/policies/AM-Timestamp-JWT-End.xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<AssignMessage name="AM-Timestamp-JWT-End">
    <DisplayName>AM-Timestamp-JWT-End</DisplayName>
    <AssignVariable>
        <Name>timing.jwt.end</Name>
        <Value>{system.timestamp}</Value>
    </AssignVariable>
    <AssignVariable>
        <Name>timing.jwt.duration</Name>
        <Value>{timing.jwt.end - timing.jwt.start}</Value>
    </AssignVariable>
</AssignMessage>
```

#### Step 2: Create Enhanced MessageLogging Policy

**File**: `apiproxy/policies/ML-Performance-Metrics.xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<MessageLogging name="ML-Performance-Metrics">
    <DisplayName>ML-Performance-Metrics</DisplayName>
    <Syslog>
        <Message>[PERFORMANCE] requestId={messageid} | totalTime={client.received.end.timestamp - client.received.start.timestamp} | jwtDuration={timing.jwt.duration} | kvmDuration={timing.kvm.duration} | rateLimitDuration={timing.ratelimit.duration} | targetTime={target.received.end.timestamp - target.sent.start.timestamp} | clientIP={client.ip} | path={proxy.pathsuffix} | status={message.status.code}</Message>
        <Host>{syslog.host}</Host>
        <Port>{syslog.port}</Port>
        <Protocol>TCP</Protocol>
        <FormatMessage>true</FormatMessage>
    </Syslog>
</MessageLogging>
```

#### Step 3: Add to Response Flow

```xml
<PostFlow name="PostFlow">
    <Response>
        <Step>
            <Name>ML-Performance-Metrics</Name>
        </Step>
    </Response>
</PostFlow>
```

### Log Output Example:

```
[PERFORMANCE] requestId=abc123 | totalTime=139 | jwtDuration=12 | kvmDuration=8 | rateLimitDuration=45 | targetTime=1 | clientIP=49.37.219.182 | path=/accounts/me | status=200
```

### Advantages:
- ✅ Extremely detailed per-request logging
- ✅ Real-time analysis
- ✅ Can send to external log aggregators (Splunk, ELK, etc.)

### Limitations:
- ⚠️ Requires many policy additions
- ⚠️ Higher overhead (~5-10ms)
- ⚠️ Requires log analysis infrastructure

---

## Method 4: Response Headers (Quick Testing)

### Description
Add custom headers to responses showing policy execution times.

### Implementation:

**File**: `apiproxy/policies/AM-Add-Performance-Headers.xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<AssignMessage name="AM-Add-Performance-Headers">
    <DisplayName>AM-Add-Performance-Headers</DisplayName>
    <Set>
        <Headers>
            <!-- Total time -->
            <Header name="X-Apigee-Total-Time">{client.received.end.timestamp - client.received.start.timestamp}</Header>
            
            <!-- Target time -->
            <Header name="X-Apigee-Target-Time">{target.received.end.timestamp - target.sent.start.timestamp}</Header>
            
            <!-- Proxy overhead -->
            <Header name="X-Apigee-Proxy-Time">{(client.received.end.timestamp - client.received.start.timestamp) - (target.received.end.timestamp - target.sent.start.timestamp)}</Header>
            
            <!-- Individual policy times (if captured) -->
            <Header name="X-Apigee-JWT-Time">{timing.jwt.duration}</Header>
            <Header name="X-Apigee-KVM-Time">{timing.kvm.duration}</Header>
            <Header name="X-Apigee-RateLimit-Time">{timing.ratelimit.duration}</Header>
        </Headers>
    </Set>
</AssignMessage>
```

**Add to Response Flow**:

```xml
<PostFlow name="PostFlow">
    <Response>
        <Step>
            <Name>AM-Add-Performance-Headers</Name>
            <Condition>request.header.X-Debug-Performance = "true"</Condition>
        </Step>
    </Response>
</PostFlow>
```

### Usage:

```bash
curl -H "X-Debug-Performance: true" \
     -H "Authorization: Bearer $TOKEN" \
     https://dev.api.cropwise.com/cropwise-unified-platform/accounts/me \
     -v
```

### Response Headers:

```
X-Apigee-Total-Time: 139
X-Apigee-Target-Time: 1
X-Apigee-Proxy-Time: 138
X-Apigee-JWT-Time: 12
X-Apigee-KVM-Time: 8
X-Apigee-RateLimit-Time: 45
```

### Advantages:
- ✅ Instant visibility
- ✅ No log infrastructure needed
- ✅ Easy to test with curl

### Limitations:
- ⚠️ Only available per-request
- ⚠️ Exposes internal metrics (use conditional)
- ⚠️ Not suitable for production (security risk)

---

## Method 5: JavaScript Callout (Maximum Control)

### Description
Use JavaScript to calculate and log precise timings.

### Implementation:

**File**: `apiproxy/resources/jsc/performance-tracker.js`

```javascript
// Initialize timings object
var timings = context.getVariable("timings") || {};

// Capture current timestamp
var currentTime = Date.now();
var phase = context.getVariable("current.flow.name");

// Store timing
timings[phase] = {
    start: timings[phase] ? timings[phase].start : currentTime,
    end: currentTime,
    duration: timings[phase] ? (currentTime - timings[phase].start) : 0
};

// Save back to context
context.setVariable("timings", JSON.stringify(timings));

// Calculate total proxy time
if (phase === "PostFlow") {
    var totalTime = context.getVariable("client.received.end.timestamp") - 
                    context.getVariable("client.received.start.timestamp");
    var targetTime = context.getVariable("target.received.end.timestamp") - 
                     context.getVariable("target.sent.start.timestamp");
    var proxyTime = totalTime - targetTime;
    
    // Log performance metrics
    print("[PERFORMANCE] Total: " + totalTime + "ms, Proxy: " + proxyTime + "ms, Target: " + targetTime + "ms");
    print("[TIMINGS] " + JSON.stringify(timings));
    
    // Set as variables for MessageLogging
    context.setVariable("perf.total", totalTime);
    context.setVariable("perf.proxy", proxyTime);
    context.setVariable("perf.target", targetTime);
}
```

**Policy**: `apiproxy/policies/JS-Performance-Tracker.xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Javascript name="JS-Performance-Tracker" timeLimit="200">
    <DisplayName>JS-Performance-Tracker</DisplayName>
    <ResourceURL>jsc://performance-tracker.js</ResourceURL>
</Javascript>
```

### Advantages:
- ✅ Maximum flexibility
- ✅ Custom calculations
- ✅ Can aggregate multiple metrics

### Limitations:
- ⚠️ JavaScript execution overhead (~5-15ms)
- ⚠️ More complex to maintain

---

## Method 6: Third-Party APM Tools

### Description
Integrate with Application Performance Monitoring tools.

### Supported Tools:

1. **Apigee Sense** (Google Cloud):
   - Built-in anomaly detection
   - Automatic latency tracking
   - AI-powered insights

2. **New Relic**:
   - Use MessageLogging to send metrics
   - Real-time dashboards
   - Alert capabilities

3. **Datadog**:
   - Custom metrics via HTTP callout
   - Distributed tracing
   - APM integration

4. **Google Cloud Trace**:
   - Native integration with Apigee X
   - Distributed tracing
   - Performance bottleneck identification

### Example: Google Cloud Trace Integration

**Enable Cloud Trace**:

1. Navigate to Google Cloud Console
2. Enable Cloud Trace API
3. Apigee X automatically sends trace data
4. View traces in Cloud Console → Trace → Trace List

**Access Trace Data**:
```
https://console.cloud.google.com/traces/list?project=YOUR_PROJECT_ID
```

### Advantages:
- ✅ Professional-grade monitoring
- ✅ Advanced analytics
- ✅ Alerting and dashboards

### Limitations:
- ⚠️ Additional cost
- ⚠️ External dependency

---

## Recommended Implementation for Cropwise Platform

### Quick Start (Testing - Method 4):

1. Add performance headers for development/testing
2. Use conditional execution (X-Debug-Performance header)
3. Test with curl to verify timings

### Production (Method 2 + Enhanced MessageLogging):

1. **Add Statistics Collectors** around critical policies:
   - JWT parsing
   - KVM lookups
   - Rate limiting

2. **Enhanced MessageLogging** policy:
   ```xml
   <MessageLogging name="ML-Performance-Metrics">
       <Syslog>
           <Message>
           {
               "requestId": "{messageid}",
               "timestamp": "{system.timestamp}",
               "totalTime": {client.received.end.timestamp - client.received.start.timestamp},
               "proxyTime": {(client.received.end.timestamp - client.received.start.timestamp) - (target.received.end.timestamp - target.sent.start.timestamp)},
               "targetTime": {target.received.end.timestamp - target.sent.start.timestamp},
               "jwtDuration": {timing.jwt.duration},
               "kvmDuration": {timing.kvm.duration},
               "rateLimitDuration": {timing.ratelimit.duration},
               "clientIP": "{client.ip}",
               "path": "{proxy.pathsuffix}",
               "status": {message.status.code},
               "method": "{request.verb}",
               "userAgent": "{request.header.user-agent}"
           }
           </Message>
           <Host>{syslog.host}</Host>
           <Port>{syslog.port}</Port>
           <Protocol>TCP</Protocol>
           <FormatMessage>true</FormatMessage>
       </Syslog>
   </MessageLogging>
   ```

3. **Send to Google Cloud Logging**:
   - Configure syslog to send to Cloud Logging
   - Use BigQuery for analysis
   - Create dashboards in Looker Studio

---

## Network Latency Tracking

### Built-in Variables:

| Variable | Description |
|----------|-------------|
| `client.received.start.timestamp` | Request received from client |
| `target.sent.start.timestamp` | Request sent to target |
| `target.received.start.timestamp` | Response received from target |
| `client.received.end.timestamp` | Response sent to client |

### Calculate Network Latencies:

```javascript
// Client to Apigee
var clientToApigee = context.getVariable("client.received.start.timestamp") - 
                     context.getVariable("request.timestamp"); // Approximate

// Apigee to Target (request)
var apigeeToTarget = context.getVariable("target.sent.start.timestamp") - 
                     context.getVariable("client.received.start.timestamp");

// Target processing
var targetProcessing = context.getVariable("target.received.start.timestamp") - 
                       context.getVariable("target.sent.start.timestamp");

// Target to Apigee (response)
var targetToApigee = context.getVariable("target.received.end.timestamp") - 
                     context.getVariable("target.received.start.timestamp");

// Apigee to Client (response)
var apigeeToClient = context.getVariable("client.received.end.timestamp") - 
                     context.getVariable("target.received.end.timestamp");

print("Client→Apigee: " + clientToApigee + "ms");
print("Apigee→Target: " + apigeeToTarget + "ms");
print("Target Processing: " + targetProcessing + "ms");
print("Target→Apigee: " + targetToApigee + "ms");
print("Apigee→Client: " + apigeeToClient + "ms");
```

---

## Performance Impact Comparison

| Method | Overhead | Detail Level | Real-time | Production Ready |
|--------|----------|--------------|-----------|------------------|
| **Apigee Analytics** | None | Medium | No | ✅ Yes |
| **Statistics Collector** | ~1-2ms | High | No | ✅ Yes |
| **Custom Variables + MessageLogging** | ~5-10ms | Very High | Yes | ⚠️ Conditional |
| **Response Headers** | ~2-3ms | High | Yes | ⚠️ Testing only |
| **JavaScript Callout** | ~5-15ms | Maximum | Yes | ⚠️ Use sparingly |
| **APM Tools** | ~5-10ms | Maximum | Yes | ✅ Yes |

---

## Example: Complete Implementation

### Policy Files to Create:

1. `AM-Timestamp-JWT-Start.xml`
2. `AM-Timestamp-JWT-End.xml`
3. `AM-Timestamp-KVM-Start.xml`
4. `AM-Timestamp-KVM-End.xml`
5. `AM-Timestamp-RateLimit-Start.xml`
6. `AM-Timestamp-RateLimit-End.xml`
7. `ML-Performance-Metrics.xml`

### Update Proxy Flow:

```xml
<PreFlow name="PreFlow">
    <Request>
        <!-- JWT Parsing -->
        <Step><Name>AM-Timestamp-JWT-Start</Name></Step>
        <Step><Name>EV-Extract-JWT-Token</Name></Step>
        <Step><Name>JS-Parse-JWT-Token</Name></Step>
        <Step><Name>AM-Timestamp-JWT-End</Name></Step>
        
        <!-- KVM Lookup -->
        <Step><Name>AM-Timestamp-KVM-Start</Name></Step>
        <Step><Name>KVM-Get-User-Rate-Limit</Name></Step>
        <Step><Name>AM-Timestamp-KVM-End</Name></Step>
        
        <!-- Rate Limiting -->
        <Step><Name>AM-Timestamp-RateLimit-Start</Name></Step>
        <Step><Name>SA-User-Spike-Arrest</Name></Step>
        <Step><Name>Q-User-Rate-Limit</Name></Step>
        <Step><Name>AM-Timestamp-RateLimit-End</Name></Step>
    </Request>
</PreFlow>

<PostFlow name="PostFlow">
    <Response>
        <!-- Log performance metrics -->
        <Step><Name>ML-Performance-Metrics</Name></Step>
    </Response>
</PostFlow>
```

---

## Testing the Implementation

### 1. Make Test Request:

```bash
curl -H "Authorization: Bearer $TOKEN" \
     https://dev.api.cropwise.com/cropwise-unified-platform/accounts/me
```

### 2. Check Logs:

**Syslog Output**:
```json
{
  "requestId": "abc123-def456",
  "timestamp": 1738512000000,
  "totalTime": 139,
  "proxyTime": 138,
  "targetTime": 1,
  "jwtDuration": 12,
  "kvmDuration": 8,
  "rateLimitDuration": 45,
  "clientIP": "49.37.219.182",
  "path": "/accounts/me",
  "status": 200,
  "method": "GET"
}
```

### 3. Analyze Results:

- **JWT Duration**: 12ms → Acceptable
- **KVM Duration**: 8ms → Acceptable
- **Rate Limit Duration**: 45ms → ⚠️ **Optimization target**
- **Target Time**: 1ms → Excellent

---

## Next Steps

1. **Immediate**: Add response headers for testing (Method 4)
2. **Short-term**: Implement Statistics Collectors (Method 2)
3. **Long-term**: Integrate with Google Cloud Trace (Method 6)
4. **Monitoring**: Set up alerts for requests > 120ms

---

## References

- [Apigee Analytics Documentation](https://cloud.google.com/apigee/docs/api-platform/analytics/analytics-dashboards)
- [Statistics Collector Policy](https://cloud.google.com/apigee/docs/api-platform/reference/policies/statistics-collector-policy)
- [MessageLogging Policy](https://cloud.google.com/apigee/docs/api-platform/reference/policies/message-logging-policy)
- [Google Cloud Trace](https://cloud.google.com/trace/docs)

---

*Document Version: 1.0*  
*Last Updated: February 2, 2026*  
*Author: Cropwise Platform Team*
