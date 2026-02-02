# Apigee X Payload & Response Size Limits

## Overview

This document outlines the payload and response size limits enforced by Apigee X API Gateway, along with configuration guidelines for handling large payloads in the Cropwise Platform proxy.

---

## Official Apigee X Size Limits

### Message Size Limits

| Limit Type | Maximum Size | Enforced | Notes |
|------------|--------------|----------|-------|
| **Request/Response (Buffered)** | **30 MB** | ✅ Yes | Standard non-streaming requests |
| **Request/Response (Streamed)** | **10 MB** recommended | ⚠️ No | Performance implications above 10 MB |
| **Request Header Size** | 60 KB | ✅ Yes | Total size of all request headers |
| **Response Header Size** | 60 KB | ✅ Yes | Total size of all response headers |
| **API Proxy Request URL Size** | 10 KB | ✅ Yes | Full URL including query parameters |
| **Message Logging Payload** | 11 MB | Planned | For MessageLogging policy |
| **Debug Payload** | No limit | - | Per transaction in debug sessions |
| **Debug Data Size** | 10 KB | ✅ Yes | Truncated in debug view |

### Related Limits

| Limit Type | Maximum Size | Notes |
|------------|--------------|-------|
| **API Proxy Bundle Size** | 15 MB | ZIP file containing proxy configuration |
| **Resource Files Size** | 15 MB | XSL, JavaScript, Python, JAR files |
| **Cache Value Size** | 256 KB | Per cache entry |
| **KVM Value Size** | 10 KB | Key Value Map entry size |
| **TLS/DTLS Handshake Message** | 128 KB | SSL handshake limit |

---

## Buffered vs Streaming Mode

### Buffered Mode (Default)

In buffered mode, Apigee stores the entire request/response in memory before processing or forwarding.

**Characteristics:**
- ✅ Supports payload transformation (JavaScript, XSLT, etc.)
- ✅ Supports payload validation
- ✅ Supports payload logging
- ❌ Limited to 30 MB maximum
- ❌ Higher memory consumption
- ❌ Higher latency for large payloads

**Use Cases:**
- JSON/XML transformation
- Request/Response validation
- Content-based routing
- Payload logging

### Streaming Mode

In streaming mode, Apigee forwards data as it's received without buffering the entire payload.

**Characteristics:**
- ✅ Supports payloads larger than 10 MB
- ✅ Lower memory consumption
- ✅ Lower latency for large payloads
- ❌ Cannot transform payload
- ❌ Cannot validate payload content
- ❌ Limited policy support

**Use Cases:**
- File uploads/downloads
- Large data exports
- Binary content transfer
- Video/audio streaming

---

## Enabling Large Payloads (> 10 MB)

### Option 1: Enable Streaming on Target Endpoint

To handle payloads larger than 10 MB, enable streaming on the target endpoint:

**File:** `apiproxy/targets/default.xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<TargetEndpoint name="default">
    <HTTPTargetConnection>
        <URL>https://backend.example.com</URL>
        <Properties>
            <!-- Enable request streaming -->
            <Property name="request.streaming.enabled">true</Property>
            <!-- Enable response streaming -->
            <Property name="response.streaming.enabled">true</Property>
        </Properties>
    </HTTPTargetConnection>
</TargetEndpoint>
```

### Option 2: Enable Streaming on Proxy Endpoint

Enable streaming on the proxy endpoint for incoming requests:

**File:** `apiproxy/proxies/default.xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ProxyEndpoint name="default">
    <HTTPProxyConnection>
        <BasePath>/cropwise-unified-platform</BasePath>
        <Properties>
            <!-- Enable request streaming -->
            <Property name="request.streaming.enabled">true</Property>
            <!-- Enable response streaming -->
            <Property name="response.streaming.enabled">true</Property>
        </Properties>
    </HTTPProxyConnection>
</ProxyEndpoint>
```

### Option 3: Conditional Streaming Policy

Use the `AM-Enable-Streaming` policy for conditional streaming based on content type or path:

**File:** `apiproxy/policies/AM-Enable-Streaming.xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<AssignMessage name="AM-Enable-Streaming">
    <DisplayName>AM-Enable-Streaming</DisplayName>
    <AssignVariable>
        <Name>request.streaming.enabled</Name>
        <Value>true</Value>
    </AssignVariable>
    <AssignVariable>
        <Name>response.streaming.enabled</Name>
        <Value>true</Value>
    </AssignVariable>
</AssignMessage>
```

**Apply conditionally in proxy flow:**

```xml
<Flow name="large-file-upload">
    <Request>
        <Step>
            <Name>AM-Enable-Streaming</Name>
            <Condition>(request.header.Content-Type = "application/octet-stream") or (request.header.Content-Length > 10000000)</Condition>
        </Step>
    </Request>
    <Condition>(proxy.pathsuffix MatchesPath "/files/**") or (proxy.pathsuffix MatchesPath "/exports/**")</Condition>
</Flow>
```

---

## Policy Limitations with Streaming

When streaming is enabled, certain policies cannot access or modify the payload:

### ❌ Policies NOT Supported with Streaming

| Policy Type | Reason |
|-------------|--------|
| **JavaScript** | Cannot access `request.content` or `response.content` |
| **Python** | Cannot access message content |
| **XSL Transform** | Requires full payload in memory |
| **JSONToXML / XMLToJSON** | Requires payload transformation |
| **JSONThreatProtection** | Requires payload parsing |
| **XMLThreatProtection** | Requires payload parsing |
| **SOAPMessageValidation** | Requires full SOAP envelope |
| **RegularExpressionProtection** | Requires payload scanning |
| **MessageLogging** (with content) | Cannot log payload content |

### ✅ Policies Supported with Streaming

| Policy Type | Notes |
|-------------|-------|
| **AssignMessage** | Header manipulation only |
| **ExtractVariables** | Headers and path only |
| **RaiseFault** | Error responses |
| **FlowCallout** | Shared flow calls |
| **ServiceCallout** | Side-effect calls |
| **KeyValueMapOperations** | KVM access |
| **LookupCache / PopulateCache** | Caching operations |
| **SpikeArrest / Quota** | Rate limiting |
| **VerifyAPIKey / OAuthV2** | Authentication |
| **MessageLogging** (headers only) | Log without content |

---

## Size Limit Enforcement Policy

To proactively reject requests that exceed size limits, use the following policy:

**File:** `apiproxy/policies/RF-PayloadTooLarge.xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<RaiseFault name="RF-PayloadTooLarge">
    <DisplayName>RF-PayloadTooLarge</DisplayName>
    <FaultResponse>
        <Set>
            <StatusCode>413</StatusCode>
            <ReasonPhrase>Payload Too Large</ReasonPhrase>
            <Payload contentType="application/json">
                {
                    "error": "payload_too_large",
                    "message": "Request payload exceeds maximum allowed size",
                    "max_size_bytes": 31457280,
                    "max_size_mb": 30,
                    "requestId": "{messageid}",
                    "documentation": "https://docs.cropwise.com/api/limits"
                }
            </Payload>
        </Set>
    </FaultResponse>
    <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
</RaiseFault>
```

**Apply in PreFlow with condition:**

```xml
<PreFlow>
    <Request>
        <Step>
            <Name>RF-PayloadTooLarge</Name>
            <Condition>(request.header.Content-Length > 31457280)</Condition>
        </Step>
    </Request>
</PreFlow>
```

---

## Best Practices

### 1. For Standard API Requests (< 10 MB)

- Use default buffered mode
- Apply full policy processing (validation, transformation, logging)
- Monitor payload sizes via analytics

### 2. For Large File Transfers (10-30 MB)

- Enable streaming on specific endpoints
- Limit policy processing to headers only
- Consider chunked transfer encoding
- Monitor performance metrics

### 3. For Very Large Files (> 30 MB)

- Use signed URLs for direct cloud storage access
- Implement client-side chunking
- Consider resumable upload protocols
- Bypass Apigee for direct upload/download

### 4. Monitoring & Alerts

Set up monitoring for:
- Requests approaching size limits
- Streaming mode usage
- Timeout errors on large transfers
- Memory consumption in Apigee instances

---

## Cropwise Platform Recommendations

### Current Configuration

| Endpoint Pattern | Mode | Max Size | Reason |
|------------------|------|----------|--------|
| `/accounts/**` | Buffered | 30 MB | Standard JSON responses |
| `/v1/users/**` | Buffered | 30 MB | Small payloads |
| `/health` | Buffered | 30 MB | Health checks |
| `/remote-sensing/**` | **Streaming** | Unlimited* | Imagery data |
| `/files/**` | **Streaming** | Unlimited* | File uploads |
| `/exports/**` | **Streaming** | Unlimited* | Data exports |

*Unlimited within backend and network capabilities; performance may degrade.

### Recommended Flow Configuration

```xml
<Flows>
    <!-- Enable streaming for file operations -->
    <Flow name="file-operations">
        <Request>
            <Step>
                <Name>AM-Enable-Streaming</Name>
            </Step>
        </Request>
        <Condition>(proxy.pathsuffix MatchesPath "/files/**") or 
                   (proxy.pathsuffix MatchesPath "/exports/**") or
                   (proxy.pathsuffix MatchesPath "/remote-sensing/download/**")</Condition>
    </Flow>
    
    <!-- Standard buffered processing for API requests -->
    <Flow name="standard-api">
        <Request/>
        <Response/>
        <Condition>true</Condition>
    </Flow>
</Flows>
```

---

## Error Handling

### Common Size-Related Errors

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `413 Request Entity Too Large` | 413 | Request > 30 MB (buffered) | Enable streaming or reduce payload |
| `502 Bad Gateway` | 502 | Response too large | Enable response streaming |
| `504 Gateway Timeout` | 504 | Large payload timeout | Increase I/O timeout |
| `503 Service Unavailable` | 503 | Memory exhaustion | Enable streaming |

### Custom Error Response

```json
{
    "error": "payload_too_large",
    "message": "Request payload exceeds maximum allowed size of 30 MB",
    "max_size_bytes": 31457280,
    "your_size_bytes": 45000000,
    "suggestions": [
        "Enable streaming for this endpoint",
        "Use chunked upload for large files",
        "Use signed URLs for direct storage access"
    ],
    "requestId": "abc123-def456",
    "documentation": "https://docs.cropwise.com/api/limits"
}
```

---

## References

- [Apigee X Limits Documentation](https://cloud.google.com/apigee/docs/api-platform/reference/limits)
- [Streaming in Apigee](https://cloud.google.com/apigee/docs/api-platform/develop/enabling-streaming)
- [Best Practices for Large Payloads](https://cloud.google.com/apigee/docs/api-platform/fundamentals/best-practices-api-proxy-design-and-development)

---

*Document Version: 1.0*  
*Last Updated: February 2, 2026*  
*Author: Cropwise Platform Team*
