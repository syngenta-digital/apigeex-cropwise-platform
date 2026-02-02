# Troubleshooting Guide

## Overview

This guide helps diagnose and resolve common issues with the Cropwise Unified Platform API proxy.

## Common Issues

### Authentication Issues

#### Issue: 401 Unauthorized responses

**Symptoms:**
- All requests return 401 status
- Error message: "Invalid or missing API key"

**Possible Causes:**
1. Missing Authorization header
2. Malformed JWT token
3. Expired token

**Solutions:**
1. Verify Authorization header is present:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" https://api-endpoint/health
   ```
2. Decode and verify JWT at [jwt.io](https://jwt.io)
3. Generate a fresh token

#### Issue: Token parsing errors

**Symptoms:**
- `jwt.valid` is false in logs
- Error: "Failed to parse JWT"

**Solution:**
Check the JWT format and ensure it's properly encoded:
```bash
# Decode JWT payload
echo "YOUR_JWT_PAYLOAD" | base64 -d
```

### Deployment Issues

#### Issue: Bundle upload fails

**Symptoms:**
- Error during `deploy_proxy.py`
- "Failed to upload proxy" message

**Possible Causes:**
1. Invalid XML syntax in policies
2. Missing required files
3. Authentication issues

**Solutions:**
1. Validate proxy structure:
   ```bash
   python scripts/generate_proxy.py --env dev --validate
   ```
2. Check XML syntax:
   ```bash
   xmllint --noout apiproxy/policies/*.xml
   ```
3. Re-authenticate:
   ```bash
   gcloud auth application-default login
   ```

#### Issue: Deployment stuck in "PROGRESSING" state

**Symptoms:**
- Deployment doesn't complete
- `--wait` flag times out

**Solutions:**
1. Check Apigee Console for detailed status
2. Undeploy and redeploy:
   ```bash
   # Via Apigee Console or API
   ```
3. Contact Apigee support if issue persists

### Connectivity Issues

#### Issue: 502 Bad Gateway

**Symptoms:**
- Proxy returns 502 errors
- Backend not responding

**Possible Causes:**
1. Incorrect backend URL
2. Backend service down
3. Network/firewall issues

**Solutions:**
1. Verify backend URL in `targets/default.xml`
2. Test backend directly:
   ```bash
   curl https://backend-host/health
   ```
3. Check VPC/firewall rules

#### Issue: Connection timeout

**Symptoms:**
- Requests hang and eventually timeout
- Error: "Connection timed out"

**Solutions:**
1. Increase timeout settings in target endpoint:
   ```xml
   <Properties>
       <Property name="connect.timeout.millis">60000</Property>
       <Property name="io.timeout.millis">120000</Property>
   </Properties>
   ```
2. Check network connectivity

### Rate Limiting Issues

#### Issue: Unexpected rate limit type

**Symptoms:**
- User getting wrong rate limit
- `x-ratelimit-type` header incorrect

**Solutions:**
1. Verify KVM entries in Apigee Console
2. Check username extraction in JWT parsing
3. Ensure default rate limit policy is active

### Logging Issues

#### Issue: Logs not appearing in Syslog

**Symptoms:**
- No entries in Syslog server
- Missing request traces

**Possible Causes:**
1. Incorrect Syslog host/port
2. Network issues to Syslog server
3. Policy disabled

**Solutions:**
1. Verify Syslog settings in `FC-Syng-Logging.xml`
2. Test Syslog connectivity:
   ```bash
   nc -zv syslog-host 514
   ```
3. Ensure `enabled="true"` in policy

## Debug Commands

### Check API proxy status

```bash
python scripts/deploy_proxy.py --env dev --status
```

### Run tests with verbose output

```bash
python scripts/test_proxy.py --env dev --verbose --test-suite all
```

### Verify Apigee API access

```bash
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://apigee.googleapis.com/v1/organizations/YOUR_ORG/apis"
```

### Check proxy revisions

```bash
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://apigee.googleapis.com/v1/organizations/YOUR_ORG/apis/cropwise-unified-platform/revisions"
```

### View deployment details

```bash
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://apigee.googleapis.com/v1/organizations/YOUR_ORG/environments/dev/apis/cropwise-unified-platform/deployments"
```

## Log Analysis

### Finding errors in Apigee logs

1. Go to Apigee Console → Analytics → Logs
2. Filter by proxy name: `cropwise-unified-platform`
3. Look for 4xx/5xx status codes
4. Check `fault.name` for error details

### Common fault names

| Fault Name | Meaning | Resolution |
|------------|---------|------------|
| `steps.oauth.v2.InvalidApiKey` | Invalid API key | Check key configuration |
| `messaging.runtime.RouteFailed` | No route matched | Check proxy flows |
| `messaging.adaptors.http.flow.ErrorResponseCode` | Backend error | Check backend logs |

## Getting Help

### Internal Support
- **Slack:** #cropwise-platform-support
- **Email:** cropwise-platform@syngenta.com

### External Resources
- [Apigee X Documentation](https://cloud.google.com/apigee/docs)
- [Apigee Community](https://www.googlecloudcommunity.com/gc/Apigee/bd-p/apigee)

## Escalation Path

1. **Level 1:** Self-service using this guide
2. **Level 2:** Slack #cropwise-platform-support
3. **Level 3:** DevOps team escalation
4. **Level 4:** Google Cloud support (for Apigee platform issues)
