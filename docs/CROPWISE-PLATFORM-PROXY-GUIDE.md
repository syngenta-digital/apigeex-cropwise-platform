# Cropwise Platform Service - API Proxy Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Proxy Configuration](#proxy-configuration)
4. [Request Flow](#request-flow)
5. [Policies Reference](#policies-reference)
6. [JavaScript Resources](#javascript-resources)
7. [Conditional Flows](#conditional-flows)
8. [Environment Configuration](#environment-configuration)
9. [Security Features](#security-features)
10. [Rate Limiting](#rate-limiting)
11. [Logging & Monitoring](#logging--monitoring)
12. [Troubleshooting](#troubleshooting)

---

## Overview

The **Cropwise Unified Platform Proxy** is an Apigee X API gateway that serves as the single entry point for all Cropwise Platform API requests. It provides authentication, authorization, rate limiting, logging, and intelligent routing to backend services.

### Key Features

| Feature | Description |
|---------|-------------|
| **JWT Authentication** | Extracts and parses JWT tokens from Authorization headers |
| **Rate Limiting** | User-based rate limiting with configurable tiers |
| **Request Routing** | Intelligent routing based on path patterns |
| **URI Rewriting** | Path transformation for backend compatibility |
| **Centralized Logging** | Syslog integration for request/response logging |
| **Error Handling** | Standardized error responses with request tracking |
| **Special Case Handling** | Custom logic for specific users/endpoints |

### Quick Stats

| Metric | Value |
|--------|-------|
| **Total Policies** | 19 |
| **JavaScript Resources** | 2 |
| **Conditional Flows** | 4 |
| **Supported Environments** | 3 (dev, qa, prod) |

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT APPLICATIONS                                │
│                    (Web Apps, Mobile Apps, Third-Party)                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          APIGEE X API GATEWAY                                │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      cropwise-unified-platform-proxy                    │ │
│  │                                                                         │ │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐               │ │
│  │  │   PreFlow    │──▶│  Conditional │──▶│   PostFlow   │               │ │
│  │  │              │   │    Flows     │   │              │               │ │
│  │  │ • JWT Parse  │   │              │   │ • Rate Limit │               │ │
│  │  │ • Extract    │   │ • Health     │   │   Headers    │               │ │
│  │  │   Variables  │   │ • Remote     │   │ • Logging    │               │ │
│  │  │ • Rate Limit │   │   Sensing    │   │              │               │ │
│  │  │   Lookup     │   │ • Protector  │   │              │               │ │
│  │  └──────────────┘   │   Alerts     │   └──────────────┘               │ │
│  │                     │ • Not Found  │                                    │ │
│  │                     └──────────────┘                                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND SERVICES                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                   Cropwise Backend API                                   ││
│  │                                                                          ││
│  │   dev:  https://dev.api.insights.cropwise.com:443                       ││
│  │   qa:   https://qa.api.insights.cropwise.com:443                        ││
│  │   prod: https://api.insights.cropwise.com:443                           ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Request Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              REQUEST FLOW                                     │
└──────────────────────────────────────────────────────────────────────────────┘

Client Request
      │
      ▼
┌─────────────────┐
│  PROXY ENDPOINT │
│    (PreFlow)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         │
┌─────────────────┐
│ FC-Syng-Preflow │ ──▶ Shared flow for common preprocessing
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ EV-Extract-JWT  │ ──▶ Extract Bearer token from Authorization header
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ JS-Parse-JWT    │ ──▶ Decode and validate JWT, extract claims
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ KVM-Get-Rate    │ ──▶ Lookup user's rate limit tier from KVM
│   Limit         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AM-Set-Default  │ ──▶ Apply default rate limit if user not found
│ Rate Limit      │     (Condition: user.rate.limit.type = null)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│           CONDITIONAL FLOWS                  │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │ health-check                         │   │
│  │ Path: /health                        │   │
│  │ Action: Pass-through (no policies)   │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │ remote-sensing                       │   │
│  │ Path: /remote-sensing/**            │   │
│  │ Action: AM-Rewrite-Remote-Sensing   │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │ protector-alerts                     │   │
│  │ Path: /v2/accounts/**               │   │
│  │ Condition: JWT user = protector...  │   │
│  │ Action: AM-Protector-Alerts-Special │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │ not-found (catch-all)               │   │
│  │ Condition: true                      │   │
│  │ Action: RF-APINotFound              │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ TARGET ENDPOINT │
│   (PreFlow)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AM-SetTarget    │ ──▶ Copy headers to target request
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Backend Server  │ ──▶ Forward request to Cropwise backend
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ TARGET ENDPOINT │
│   (PostFlow)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PROXY ENDPOINT  │
│   (PostFlow)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         │
┌─────────────────┐
│ AM-Set-Rate     │ ──▶ Add rate limit headers to response
│ Limit-Headers   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FC-Syng-Logging │ ──▶ Log request/response to Syslog
└────────┬────────┘
         │
         ▼
   Client Response
```

---

## Proxy Configuration

### Main Proxy Descriptor

**File:** `apiproxy/cropwise-unified-platform-proxy.xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<APIProxy revision="1" name="cropwise-unified-platform-proxy">
    <DisplayName>Cropwise Unified Platform Proxy</DisplayName>
    <Description>API Proxy for Cropwise Unified Platform</Description>
    <Basepaths>/cropwise-unified-platform</Basepaths>
    ...
</APIProxy>
```

### Proxy Endpoint Configuration

**File:** `apiproxy/proxies/default.xml`

| Setting | Value |
|---------|-------|
| **Base Path** | `/cropwise-unified-platform` |
| **Virtual Hosts** | `default`, `secure` |
| **Route Rule** | Routes all traffic to `default` target |

### Target Endpoint Configuration

**File:** `apiproxy/targets/default.xml`

| Setting | Value |
|---------|-------|
| **Target URL** | `https://dev.api.insights.cropwise.com:443` |
| **SSL Enabled** | `true` |
| **Connect Timeout** | `30,000ms` |
| **I/O Timeout** | `60,000ms` |

---

## Request Flow

### PreFlow (Proxy Endpoint)

The PreFlow executes on every incoming request:

| Step | Policy | Description | Condition |
|------|--------|-------------|-----------|
| 1 | `FC-Syng-Preflow` | Common preprocessing via shared flow | Always |
| 2 | `EV-Extract-JWT-Token` | Extract Bearer token from header | Always |
| 3 | `JS-Parse-JWT-Token` | Decode and validate JWT token | Always |
| 4 | `KVM-Get-User-Rate-Limit` | Lookup user's rate limit tier | Always |
| 5 | `AM-Set-Default-Rate-Limit` | Set default rate limit | `user.rate.limit.type = null` |

### PostFlow (Proxy Endpoint)

The PostFlow executes on every outgoing response:

| Step | Policy | Description |
|------|--------|-------------|
| 1 | `AM-Set-Rate-Limit-Headers` | Add rate limit info to response headers |
| 2 | `FC-Syng-Logging` | Log request/response metrics to Syslog |

### Fault Handling

All faults are handled by `FC-Syng-ErrorHandling` shared flow:

```xml
<DefaultFaultRule>
    <Step>
        <Name>FC-Syng-ErrorHandling</Name>
    </Step>
    <AlwaysEnforce>true</AlwaysEnforce>
</DefaultFaultRule>
```

---

## Policies Reference

### Policy Categories

| Category | Count | Purpose |
|----------|-------|---------|
| **AssignMessage (AM)** | 10 | Variable assignment, header manipulation |
| **ExtractVariables (EV)** | 1 | Extract data from request/response |
| **FlowCallout (FC)** | 3 | Call shared flows |
| **JavaScript (JS)** | 2 | Custom JavaScript logic |
| **KeyValueMapOperations (KVM)** | 1 | Read from key-value store |
| **RaiseFault (RF)** | 1 | Generate error responses |

---

### Policy Details

#### 1. AM-SetTarget

**Purpose:** Copy authorization headers to the target request.

```xml
<AssignMessage name="AM-SetTarget">
    <Copy source="request">
        <Headers>
            <Header name="Authorization"/>
            <Header name="Content-Type"/>
        </Headers>
    </Copy>
</AssignMessage>
```

| Property | Value |
|----------|-------|
| **Execution Point** | Target PreFlow |
| **Async** | `false` |
| **Continue on Error** | `false` |

---

#### 2. EV-Extract-JWT-Token

**Purpose:** Extract the JWT token from the Authorization Bearer header.

```xml
<ExtractVariables name="EV-Extract-JWT-Token">
    <Source>request</Source>
    <Header name="Authorization">
        <Pattern ignoreCase="true">Bearer {jwt.token}</Pattern>
    </Header>
    <VariablePrefix>extracted</VariablePrefix>
</ExtractVariables>
```

**Variables Set:**
| Variable | Description |
|----------|-------------|
| `extracted.jwt.token` | Raw JWT token string |

---

#### 3. JS-Parse-JWT-Token

**Purpose:** Parse and decode the JWT token, extract claims.

```xml
<Javascript name="JS-Parse-JWT-Token" timeLimit="200">
    <ResourceURL>jsc://parse-jwt-token.js</ResourceURL>
</Javascript>
```

**Variables Set:**
| Variable | Description |
|----------|-------------|
| `jwt.valid` | Boolean - token validity |
| `jwt.sub` | Subject claim |
| `jwt.username` | Username from token |
| `jwt.client_id` | OAuth client ID |
| `jwt.iss` | Token issuer |
| `jwt.exp` | Expiration timestamp |
| `jwt.iat` | Issued-at timestamp |
| `jwt.scope` | Token scopes |
| `jwt.roles` | User roles (JSON array) |
| `jwt.expired` | Boolean - token expiration status |
| `jwt.error` | Error message if parsing failed |

---

#### 4. KVM-Get-User-Rate-Limit

**Purpose:** Lookup user's rate limit tier from Key Value Map.

```xml
<KeyValueMapOperations name="KVM-Get-User-Rate-Limit" mapIdentifier="user-rate-limits">
    <Scope>environment</Scope>
    <Get assignTo="user.rate.limit.type">
        <Key>
            <Parameter ref="jwt.username"/>
        </Key>
    </Get>
</KeyValueMapOperations>
```

**KVM Structure:**
| Key (Username) | Value (Tier) |
|----------------|--------------|
| `user1@example.com` | `high` |
| `service.account@syngenta.com` | `high` |
| `partner@external.com` | `medium` |

---

#### 5. AM-Set-Default-Rate-Limit

**Purpose:** Apply default rate limit when user not found in KVM.

**Condition:** `user.rate.limit.type = null`

**Variables Set:**
| Variable | Value |
|----------|-------|
| `user.rate.limit.type` | `low` |
| `rate.limit.value` | `1000` |
| `rate.limit.interval` | `1h` |

---

#### 6. AM-Set-Rate-Limit-Headers

**Purpose:** Add rate limit information to response headers.

```xml
<AssignMessage name="AM-Set-Rate-Limit-Headers">
    <Set>
        <Headers>
            <Header name="x-ratelimit-limit">{rate.limit.value}</Header>
            <Header name="x-ratelimit-remaining">{rate.limit.remaining}</Header>
            <Header name="x-ratelimit-reset">{rate.limit.reset}</Header>
            <Header name="x-ratelimit-type">{rate.limit.type}</Header>
        </Headers>
    </Set>
</AssignMessage>
```

**Response Headers:**
| Header | Description | Example |
|--------|-------------|---------|
| `x-ratelimit-limit` | Maximum requests allowed | `10000` |
| `x-ratelimit-remaining` | Requests remaining | `9876` |
| `x-ratelimit-reset` | Reset timestamp (Unix epoch) | `1706918400` |
| `x-ratelimit-type` | Rate limit tier | `high` |

---

#### 7. AM-Rewrite-Remote-Sensing-URI

**Purpose:** Rewrite URI for remote sensing API requests.

```xml
<AssignMessage name="AM-Rewrite-Remote-Sensing-URI">
    <AssignVariable>
        <Name>target.copy.pathsuffix</Name>
        <Value>false</Value>
    </AssignVariable>
    <Set>
        <Path>/remote-sensing/api{proxy.pathsuffix}</Path>
    </Set>
</AssignMessage>
```

**Path Transformation:**
| Incoming Path | Outgoing Path |
|---------------|---------------|
| `/remote-sensing/v1/imagery` | `/remote-sensing/api/remote-sensing/v1/imagery` |

---

#### 8. AM-Protector-Alerts-Special-Case

**Purpose:** Handle special routing for Protector Alerts service account.

**Condition:** `jwt.username = "protector.alerts.account@syngenta.com"`

```xml
<AssignMessage name="AM-Protector-Alerts-Special-Case">
    <AssignVariable>
        <Name>is.protector.alerts.user</Name>
        <Value>true</Value>
    </AssignVariable>
    <Set>
        <Headers>
            <Header name="X-Protector-Alerts">true</Header>
        </Headers>
    </Set>
</AssignMessage>
```

---

#### 9. RF-APINotFound

**Purpose:** Return standardized 404 error for undefined routes.

```xml
<RaiseFault name="RF-APINotFound">
    <FaultResponse>
        <Set>
            <StatusCode>404</StatusCode>
            <ReasonPhrase>Not Found</ReasonPhrase>
            <Payload contentType="application/json">
                {
                    "error": "not_found",
                    "message": "The requested resource was not found",
                    "requestId": "{messageid}",
                    "path": "{request.uri}",
                    "support contact": "Contact CropwisePlatform team via slack- #cropwise-platform-support"
                }
            </Payload>
        </Set>
    </FaultResponse>
</RaiseFault>
```

**Error Response Format:**
```json
{
    "error": "not_found",
    "message": "The requested resource was not found",
    "requestId": "abc123-def456",
    "path": "/cropwise-unified-platform/invalid/path",
    "support contact": "Contact CropwisePlatform team via slack- #cropwise-platform-support"
}
```

---

#### 10. FC-Syng-Logging

**Purpose:** Log request/response metrics to Syslog server.

```xml
<MessageLogging name="FC-Syng-Logging" async="true">
    <Syslog>
        <Message>[CropwisePlatform][{environment.name}] RequestId={messageid} User={jwt.username} ClientIP={client.ip} Method={request.verb} Path={request.uri} Status={response.status.code} Latency={client.sent.end.timestamp - client.received.start.timestamp}ms</Message>
        <Host>syslog-dev.internal.com</Host>
        <Port>514</Port>
        <Protocol>TCP</Protocol>
        <FormatMessage>true</FormatMessage>
    </Syslog>
</MessageLogging>
```

**Log Message Format:**
```
[CropwisePlatform][dev] RequestId=abc123 User=user@example.com ClientIP=192.168.1.1 Method=GET Path=/cropwise-unified-platform/accounts/me Status=200 Latency=456ms
```

---

#### 11. FC-Syng-ErrorHandling

**Purpose:** Shared flow for centralized error handling.

```xml
<FlowCallout name="FC-Syng-ErrorHandling">
    <SharedFlowBundle>Syng-ErrorHandling</SharedFlowBundle>
</FlowCallout>
```

---

#### 12. FC-Syng-Preflow

**Purpose:** Shared flow for common request preprocessing.

```xml
<FlowCallout name="FC-Syng-Preflow">
    <SharedFlowBundle>Syng-Preflow</SharedFlowBundle>
</FlowCallout>
```

---

### Rate Limit Tier Policies

| Policy | Tier | Rate Limit |
|--------|------|------------|
| `AM-Set-High-Rate-Header` | High | 10,000 req/hour |
| `AM-Set-Medium-Rate-Header` | Medium | 5,000 req/hour |
| `AM-Set-Low-Rate-Header` | Low | 1,000 req/hour |
| `AM-Set-Default-Rate-Limit` | Default | 1,000 req/hour |

---

## JavaScript Resources

### 1. parse-jwt-token.js

**Location:** `apiproxy/resources/jsc/parse-jwt-token.js`

**Purpose:** Decode JWT tokens and extract claims without external libraries.

**Key Features:**
- Base64URL decoding
- Claim extraction (sub, username, client_id, iss, exp, iat)
- Expiration validation
- Error handling with context variable feedback

**Flow:**
```
Authorization Header
        │
        ▼
Extract "Bearer " prefix
        │
        ▼
Split JWT into 3 parts (header.payload.signature)
        │
        ▼
Base64URL decode payload
        │
        ▼
JSON parse claims
        │
        ▼
Set context variables
```

**Example Output Variables:**
```
jwt.valid = true
jwt.sub = "63d2e89c-604e-465a-a3bd-d74f67e37af5"
jwt.username = "user@example.com"
jwt.client_id = "strix-ui"
jwt.iss = "cropwise-base-strix"
jwt.exp = 1772260652
jwt.expired = false
```

---

### 2. handle-readonly-routes.js

**Location:** `apiproxy/resources/jsc/handle-readonly-routes.js`

**Purpose:** Identify read-only requests that can be routed to read replicas.

**Read-Only Patterns:**
| Pattern | Example |
|---------|---------|
| `/v1/users/{id}` | `GET /v1/users/123` |
| `/v1/data/{id}` | `GET /v1/data/abc` |
| `/v2/accounts/{id}` | `GET /v2/accounts/me` |
| `/remote-sensing/v1/imagery` | `GET /remote-sensing/v1/imagery` |

**Output Variable:**
| Variable | Type | Description |
|----------|------|-------------|
| `is.readonly.request` | Boolean | `true` if request can use read replica |

---

## Conditional Flows

### Flow Evaluation Order

Flows are evaluated in the order defined. First match wins.

| Order | Flow Name | Condition | Action |
|-------|-----------|-----------|--------|
| 1 | `health-check` | `path = "/health" AND method = "GET"` | Pass-through |
| 2 | `remote-sensing` | `path MatchesPath "/remote-sensing/**"` | URI Rewrite |
| 3 | `protector-alerts` | `path MatchesPath "/v2/accounts/**"` | Special headers |
| 4 | `not-found` | `true` (catch-all) | 404 Error |

### Flow: health-check

**Condition:**
```
(proxy.pathsuffix MatchesPath "/health") and (request.verb = "GET")
```

**Purpose:** Health check endpoint for load balancers and monitoring.

**Behavior:** No additional policies applied - passes through to backend.

---

### Flow: remote-sensing

**Condition:**
```
(proxy.pathsuffix MatchesPath "/remote-sensing/**")
```

**Purpose:** Handle Remote Sensing API requests with URI transformation.

**Policy:** `AM-Rewrite-Remote-Sensing-URI`

---

### Flow: protector-alerts

**Condition:**
```
(proxy.pathsuffix MatchesPath "/v2/accounts/**")
```

**Inner Condition:**
```
jwt.username = "protector.alerts.account@syngenta.com"
```

**Purpose:** Special handling for Protector Alerts service account.

**Policy:** `AM-Protector-Alerts-Special-Case`

---

### Flow: not-found

**Condition:**
```
true
```

**Purpose:** Catch-all for undefined routes.

**Policy:** `RF-APINotFound`

---

## Environment Configuration

### Overview

The proxy supports three environments with environment-specific configurations:

| Environment | Apigee Env | Backend Host | Syslog Host |
|-------------|------------|--------------|-------------|
| **Development** | `dev` | `dev.api.insights.cropwise.com` | `syslog-dev.internal.com` |
| **QA** | `qa` | `qa.api.insights.cropwise.com` | `syslog-qa.internal.com` |
| **Production** | `prod` | `api.insights.cropwise.com` | `syslog.internal.com` |

### Configuration File

**File:** `config/environments.json`

```json
{
    "environments": {
        "dev": {
            "name": "dev",
            "apigee_org": "your-apigee-org",
            "apigee_env": "dev",
            "backend_host": "dev.api.insights.cropwise.com",
            "backend_port": 443,
            "backend_protocol": "https",
            "virtual_hosts": ["default", "secure"],
            "base_path": "/cropwise-unified-platform",
            "syslog_host": "syslog-dev.internal.com",
            "syslog_port": 514
        },
        "qa": { ... },
        "prod": { ... }
    }
}
```

### Environment-Specific URLs

| Environment | Proxy URL |
|-------------|-----------|
| **Dev** | `https://dev.api.cropwise.com/cropwise-unified-platform` |
| **QA** | `https://qa.api.cropwise.com/cropwise-unified-platform` |
| **Prod** | `https://api.cropwise.com/cropwise-unified-platform` |

---

## Security Features

### Authentication

| Feature | Implementation |
|---------|----------------|
| **Token Type** | JWT Bearer Token |
| **Header** | `Authorization: Bearer <token>` |
| **Validation** | Format validation, expiration check |
| **Claims Extraction** | Subject, username, client_id, scopes, roles |

### Authorization

The proxy extracts JWT claims and makes them available for backend services:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLC...
                           │
                           ▼
                ┌────────────────────┐
                │  JWT Claims        │
                │  ─────────────────│
                │  sub: user-id     │
                │  username: email  │
                │  roles: [admin]   │
                │  scope: read write│
                └────────────────────┘
                           │
                           ▼
            Backend receives full context
```

### SSL/TLS

| Setting | Value |
|---------|-------|
| **SSL Enabled** | `true` |
| **Protocol** | TLS 1.2+ |
| **Certificate Validation** | Enabled |

---

## Rate Limiting

### Rate Limit Tiers

| Tier | Limit | Interval | Use Case |
|------|-------|----------|----------|
| **High** | 10,000 | 1 hour | Service accounts, internal services |
| **Medium** | 5,000 | 1 hour | Partner integrations |
| **Low** | 1,000 | 1 hour | Standard users |
| **Default** | 1,000 | 1 hour | Unregistered users |

### KVM Configuration

The `user-rate-limits` KVM stores user-to-tier mappings:

```
┌─────────────────────────────────────────────┐
│         KVM: user-rate-limits               │
├──────────────────────────┬──────────────────┤
│ Key (Username)           │ Value (Tier)     │
├──────────────────────────┼──────────────────┤
│ service.account@...      │ high             │
│ partner.api@...          │ medium           │
│ standard.user@...        │ low              │
└──────────────────────────┴──────────────────┘
```

### Response Headers

All responses include rate limit information:

```http
HTTP/1.1 200 OK
x-ratelimit-limit: 10000
x-ratelimit-remaining: 9876
x-ratelimit-reset: 1706918400
x-ratelimit-type: high
```

---

## Logging & Monitoring

### Syslog Integration

All requests are logged to centralized Syslog servers:

| Environment | Syslog Host | Port | Protocol |
|-------------|-------------|------|----------|
| Dev | `syslog-dev.internal.com` | 514 | TCP |
| QA | `syslog-qa.internal.com` | 514 | TCP |
| Prod | `syslog.internal.com` | 514 | TCP |

### Log Format

```
[CropwisePlatform][{environment}] RequestId={id} User={user} ClientIP={ip} Method={method} Path={path} Status={status} Latency={latency}ms
```

**Example:**
```
[CropwisePlatform][dev] RequestId=abc123-def456 User=user@example.com ClientIP=192.168.1.100 Method=GET Path=/cropwise-unified-platform/accounts/me Status=200 Latency=456ms
```

### Logged Fields

| Field | Description | Example |
|-------|-------------|---------|
| `environment.name` | Deployment environment | `dev` |
| `messageid` | Unique request ID | `abc123-def456` |
| `jwt.username` | Authenticated user | `user@example.com` |
| `client.ip` | Client IP address | `192.168.1.100` |
| `request.verb` | HTTP method | `GET` |
| `request.uri` | Request path | `/cropwise-unified-platform/accounts/me` |
| `response.status.code` | HTTP status | `200` |
| Latency | Response time | `456ms` |

---

## Troubleshooting

### Common Issues

#### 1. 404 Not Found

**Symptom:** All requests return 404.

**Possible Causes:**
- Path doesn't match any conditional flow
- Base path missing from URL
- Incorrect proxy configuration

**Solution:**
```bash
# Verify base path is included
curl https://dev.api.cropwise.com/cropwise-unified-platform/health
#                                 ↑ Base path required
```

---

#### 2. JWT Parsing Errors

**Symptom:** `jwt.valid = false`, `jwt.error` set.

**Possible Causes:**
- Malformed JWT token
- Missing Authorization header
- Incorrect Bearer prefix

**Debug:**
```bash
# Check Authorization header format
curl -H "Authorization: Bearer eyJ..." ...
#                       ↑ "Bearer " prefix required (with space)
```

**Check Variables:**
- `jwt.error` - Contains parsing error message
- `extracted.jwt.token` - Raw token extracted

---

#### 3. Rate Limit Issues

**Symptom:** Rate limit not applied correctly.

**Possible Causes:**
- User not in KVM
- KVM name mismatch
- Username variable not set

**Debug:**
1. Verify KVM `user-rate-limits` exists in environment
2. Check `jwt.username` variable is populated
3. Verify `user.rate.limit.type` after KVM lookup

---

#### 4. Backend Connection Timeout

**Symptom:** 504 Gateway Timeout.

**Possible Causes:**
- Backend server overloaded
- Network connectivity issues
- Timeout too short

**Current Timeouts:**
| Setting | Value |
|---------|-------|
| Connect Timeout | 30 seconds |
| I/O Timeout | 60 seconds |

---

### Debug Mode

Enable trace in Apigee console to see:
- All policy executions
- Variable values at each step
- Request/response transformations
- Error details

---

## API Endpoints

### Supported Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/accounts/me` | GET | Current user account |
| `/v2/accounts/{id}` | GET | Account by ID |
| `/v1/users/{id}` | GET/PUT/DELETE | User operations |
| `/v1/data/{id}` | GET/POST | Data operations |
| `/remote-sensing/v1/imagery` | GET | Remote sensing imagery |

### Example Requests

**Health Check:**
```bash
curl -X GET "https://dev.api.cropwise.com/cropwise-unified-platform/health"
```

**Get Account:**
```bash
curl -X GET "https://dev.api.cropwise.com/cropwise-unified-platform/accounts/me" \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json"
```

---

## Appendix

### Policy File Locations

| Policy | File Path |
|--------|-----------|
| AM-SetTarget | `apiproxy/policies/AM-SetTarget.xml` |
| AM-InvalidAPIKey | `apiproxy/policies/AM-InvalidAPIKey.xml` |
| AM-Apply-ReadOnly-Prefix | `apiproxy/policies/AM-Apply-ReadOnly-Prefix.xml` |
| AM-Protector-Alerts-Special-Case | `apiproxy/policies/AM-Protector-Alerts-Special-Case.xml` |
| AM-Rewrite-OAuth-Token-URI | `apiproxy/policies/AM-Rewrite-OAuth-Token-URI.xml` |
| AM-Rewrite-Remote-Sensing-URI | `apiproxy/policies/AM-Rewrite-Remote-Sensing-URI.xml` |
| AM-Set-Default-Rate-Limit | `apiproxy/policies/AM-Set-Default-Rate-Limit.xml` |
| AM-Set-High-Rate-Header | `apiproxy/policies/AM-Set-High-Rate-Header.xml` |
| AM-Set-Low-Rate-Header | `apiproxy/policies/AM-Set-Low-Rate-Header.xml` |
| AM-Set-Medium-Rate-Header | `apiproxy/policies/AM-Set-Medium-Rate-Header.xml` |
| AM-Set-Rate-Limit-Headers | `apiproxy/policies/AM-Set-Rate-Limit-Headers.xml` |
| EV-Extract-JWT-Token | `apiproxy/policies/EV-Extract-JWT-Token.xml` |
| FC-Syng-ErrorHandling | `apiproxy/policies/FC-Syng-ErrorHandling.xml` |
| FC-Syng-Logging | `apiproxy/policies/FC-Syng-Logging.xml` |
| FC-Syng-Preflow | `apiproxy/policies/FC-Syng-Preflow.xml` |
| JS-Handle-ReadOnly-Routes | `apiproxy/policies/JS-Handle-ReadOnly-Routes.xml` |
| JS-Parse-JWT-Token | `apiproxy/policies/JS-Parse-JWT-Token.xml` |
| KVM-Get-User-Rate-Limit | `apiproxy/policies/KVM-Get-User-Rate-Limit.xml` |
| RF-APINotFound | `apiproxy/policies/RF-APINotFound.xml` |

### Related Documentation

- [Deployment Guide](DEPLOYMENT-GUIDE.md)
- [Policy Reference](POLICY-REFERENCE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Latency Analysis Report](../tests/latency-test/LATENCY-ANALYSIS-20260202-190546.md)

---

*Document Version: 1.0*  
*Last Updated: February 2, 2026*  
*Author: Cropwise Platform Team*
