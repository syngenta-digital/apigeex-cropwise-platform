# Policy Reference

## Overview

This document provides a reference for all Apigee policies used in the Cropwise Unified Platform proxy.

## Policy Categories

### AssignMessage Policies

| Policy | Purpose |
|--------|---------|
| AM-SetTarget | Copies Authorization and Content-Type headers to backend |
| AM-InvalidAPIKey | Returns 401 error for invalid API keys |
| AM-Apply-ReadOnly-Prefix | Applies read-only prefix to request path |
| AM-Protector-Alerts-Special-Case | Handles protector alerts special case |
| AM-Rewrite-OAuth-Token-URI | Rewrites OAuth token request URI |
| AM-Rewrite-Remote-Sensing-URI | Rewrites remote sensing API URI |
| AM-Set-Default-Rate-Limit | Sets default rate limit headers |
| AM-Set-High-Rate-Header | Sets high rate limit header |
| AM-Set-Low-Rate-Header | Sets low rate limit header |
| AM-Set-Medium-Rate-Header | Sets medium rate limit header |
| AM-Set-Rate-Limit-Headers | Adds rate limit headers to response |

### FlowCallout Policies

| Policy | Purpose |
|--------|---------|
| FC-Syng-Preflow | Initializes request tracking variables |
| FC-Syng-ErrorHandling | Standardized error handling |
| FC-Syng-Logging | Logs API transactions to Syslog |

### JavaScript Policies

| Policy | Purpose |
|--------|---------|
| JS-Handle-ReadOnly-Routes | Determines if request should use read replicas |
| JS-Parse-JWT-Token | Parses JWT and extracts claims |

### Other Policies

| Policy | Purpose |
|--------|---------|
| EV-Extract-JWT-Token | Extracts JWT token from Authorization header |
| KVM-Get-User-Rate-Limit | Looks up user rate limits from KVM |
| RF-APINotFound | Returns 404 for undefined routes |

## Policy Details

### AM-SetTarget

**Purpose:** Copies essential headers from client request to backend request.

**Headers Copied:**
- Authorization
- Content-Type

**Customization:** Add additional headers in the `<Headers>` section:

```xml
<Copy source="request">
    <Headers>
        <Header name="Authorization"/>
        <Header name="Content-Type"/>
        <Header name="X-Custom-Header"/>  <!-- Add custom headers -->
    </Headers>
</Copy>
```

### FC-Syng-Logging

**Purpose:** Logs API transactions to a Syslog server.

**Configuration:**
- `<Host>` - Syslog server hostname (environment-specific)
- `<Port>` - Syslog port (default: 514)
- `<Protocol>` - TCP or UDP

**Log Format:**
```
[CropwisePlatform][{environment}] RequestId={id} User={username} ClientIP={ip} Method={verb} Path={uri} Status={status} Latency={ms}ms
```

### JS-Parse-JWT-Token

**Purpose:** Parses JWT tokens and extracts claims for use in other policies.

**Variables Set:**
- `jwt.valid` - Boolean indicating if token is valid
- `jwt.sub` - Subject claim
- `jwt.username` - Username from token
- `jwt.client_id` - Client ID from token
- `jwt.exp` - Expiration timestamp
- `jwt.expired` - Boolean indicating if token is expired

### RF-APINotFound

**Purpose:** Returns a standardized 404 response for undefined routes.

**Response Format:**
```json
{
    "error": "not_found",
    "message": "The requested resource was not found",
    "requestId": "{messageid}",
    "path": "{request.uri}",
    "support contact": "Contact CropwisePlatform team via slack- #cropwise-platform-support"
}
```

## Rate Limiting

Rate limiting is configured using a Key Value Map (KVM) in Apigee.

### KVM Structure

**Map Name:** `user-rate-limits`
**Scope:** Environment

**Entries:**
| Key (Username) | Value (Rate Type) |
|----------------|-------------------|
| user1@syngenta.com | high-rate |
| user2@syngenta.com | low-rate |

### Rate Types

| Type | Description |
|------|-------------|
| high-rate | High volume API access |
| medium-rate | Standard API access (default) |
| low-rate | Limited API access |

## Best Practices

1. **Always validate changes** before deployment using `--validate` flag
2. **Test in dev** before promoting to qa/prod
3. **Use environment-specific settings** via `environments.json`
4. **Document custom policies** added to the proxy
5. **Review logs** after deployment for any issues

## Support

For policy-related questions, contact **#cropwise-platform-support** on Slack.
