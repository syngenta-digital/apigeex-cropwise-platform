# Deployment Script - README

## Quick Start

Deploy the Cropwise Unified Platform proxy to Apigee X:

```bash
# Uses default org: 711137019957, env: default-dev
python scripts/deploy.py --env dev
```

## Pre-Configured Defaults

The script is pre-configured for the use1-non-prod-apigeex-service:

- **Organization**: 711137019957
- **Project**: use1-apigeex
- **API Domain**: api.cropwise.com
- **Environments**: 
  - `dev` → `default-dev`
  - `qa` → `default-qa`
  - `prod` → `default-prod`

**You don't need to specify `--org` unless deploying to a different organization.**

## What This Script Does

The `deploy.py` script automates the entire deployment process:

1. ✅ **Creates Proxy Bundle** - Packages apiproxy directory into ZIP file
2. ✅ **Uploads to Apigee** - Sends bundle to Apigee X via REST API  
3. ✅ **Deploys Revision** - Deploys new revision to target environment
4. ✅ **Monitors Status** - Waits for deployment to complete

## Requirements

- Python 3.7+
- `requests` library (`pip install requests`)
- gcloud CLI (optional) or manual token/org

## Usage Examples

### Basic Deployment

```bash
# Deploy to dev (uses org: 711137019957, env: default-dev)
python scripts/deploy.py --env dev

# Deploy to qa (uses org: 711137019957, env: default-qa)
python scripts/deploy.py --env qa

# Deploy to prod (uses org: 711137019957, env: default-prod)
python scripts/deploy.py --env prod
```

### With Manual Token (No gcloud required)

```bash
# Get token
TOKEN=$(gcloud auth print-access-token)

# Deploy
python scripts/deploy.py --env dev --token $TOKEN
```

### With Different Organization

```bash
python scripts/deploy.py --env dev \
  --org YOUR_DIFFERENT_ORG \
  --token YOUR_ACCESS_TOKEN
```

### Bundle Only (No Deployment)

Create ZIP bundle without deploying:

```bash
python scripts/deploy.py --env dev --bundle-only
```

Output: `dist/cropwise-unified-platform-TIMESTAMP.zip`

### Dry Run

Test prerequisites without deploying:

```bash
python scripts/deploy.py --env dev --dry-run
```

### Custom Timeout

Adjust deployment status wait time:

```bash
python scripts/deploy.py --env dev --timeout 180  # 3 minutes
```

### No Wait

Deploy without waiting for status:

```bash
python scripts/deploy.py --env dev --no-wait
```

## Command-Line Options

```
--env, -e           Target environment (required)
                    Choices: dev, qa, prod

--org, -o           Apigee organization name
                    Default: from gcloud config

--token, -t         Access token
                    Default: from gcloud auth print-access-token

--bundle-only       Create bundle only, do not deploy

--no-wait           Deploy without waiting for ready status

--dry-run           Check prerequisites only, no deployment

--timeout           Deployment timeout in seconds
                    Default: 120
```

## Example Output

```
===============================================================
  Apigee X Deployment Script
===============================================================

Proxy Name: cropwise-unified-platform
Environment: dev
Timestamp: 2026-02-02 21:49:57

Checking prerequisites...
  ✓ gcloud CLI found
  ✓ Access token obtained
  ✓ Using organization: your-org-name

Creating proxy bundle...
  Bundle: /path/to/dist/cropwise-unified-platform-20260202-214957.zip
  ✓ Bundle created: 17.20 KB

Uploading proxy bundle to Apigee X...
  URL: https://apigee.googleapis.com/v1/organizations/your-org/apis?action=import&name=cropwise-unified-platform
  ✓ Upload successful - Revision: 5

Deploying revision 5 to dev...
  URL: https://apigee.googleapis.com/v1/organizations/your-org/environments/dev/apis/cropwise-unified-platform/revisions/5/deployments
  ✓ Deployment initiated

Checking deployment status...
  ⏳ Waiting... (2s) - State: progressing
  ⏳ Waiting... (4s) - State: progressing
  ⏳ Waiting... (6s) - State: progressing
  ✓ Deployment is READY!

📄 Deployment result saved: /path/to/dist/deployment-dev-20260202-214957.json

===============================================================
  Deployment Summary
===============================================================

Proxy: cropwise-unified-platform
Revision: 5
Environment: dev → default-dev
Organization: 711137019957
Bundle: /path/to/dist/cropwise-unified-platform-20260202-214957.zip
Status: DEPLOYED

✓ Deployment completed successfully!

API Endpoint: https://api.cropwise.com/cropwise-unified-platform/accounts/me

Test with performance headers:
  curl -H 'Authorization: Bearer YOUR_TOKEN' \
       -H 'X-Debug-Performance: true' \
       https://api.cropwise.com/cropwise-unified-platform/accounts/me

Or run the EC2 performance test:
  export BEARER_TOKEN='your_token'
  python tests/ec2-performance-test.py
```

## Files Generated

### 1. Proxy Bundle
**Location**: `dist/cropwise-unified-platform-TIMESTAMP.zip`

Contains the entire `apiproxy` directory:
- Policy files (including new performance tracking policies)
- Proxy endpoint configurations
- Target endpoint configurations
- JavaScript resources

### 2. Deployment Result
**Location**: `dist/deployment-ENV-TIMESTAMP.json`

JSON file with deployment metadata:
```json
{
  "proxy_name": "cropwise-unified-platform",
  "environment": "dev",
  "organization": "your-org",
  "timestamp": "20260202-214957",
  "revision": "5",
  "bundle_file": "/path/to/bundle.zip",
  "ready": true,
  "success": true
}
```

## Troubleshooting

### gcloud CLI not found

**Error**: `✗ gcloud CLI not found`

**Solution 1**: Install gcloud CLI
```bash
# Mac
brew install google-cloud-sdk

# Or download: https://cloud.google.com/sdk/docs/install
```

**Solution 2**: Use manual credentials
```bash
python scripts/deploy.py --env dev --org YOUR_ORG --token YOUR_TOKEN
```

### Authentication Failed

**Error**: `✗ Failed to get access token`

**Solution**:
```bash
gcloud auth login
gcloud auth application-default login
```

### Upload Failed

**Error**: `✗ Upload failed: 401 Unauthorized`

**Cause**: Token expired

**Solution**:
```bash
# Get fresh token
gcloud auth print-access-token

# Or re-login
gcloud auth login
```

### Deployment Timeout

**Error**: `⚠ Deployment status check timed out`

**Cause**: Deployment taking longer than expected

**Solutions**:
1. Increase timeout: `--timeout 300`
2. Check Apigee console manually
3. Use `--no-wait` and check status later

## What's Being Deployed

This deployment includes **7 new performance tracking policies**:

### New Policy Files
1. `AM-Add-Performance-Headers.xml` - Adds X-Apigee-* headers to response
2. `AM-Timestamp-JWT-Start.xml` - Captures JWT processing start time
3. `AM-Timestamp-JWT-End.xml` - Captures JWT processing end time
4. `AM-Timestamp-KVM-Start.xml` - Captures KVM lookup start time
5. `AM-Timestamp-KVM-End.xml` - Captures KVM lookup end time
6. `AM-Timestamp-RateLimit-Start.xml` - Captures rate limit start time
7. `AM-Timestamp-RateLimit-End.xml` - Captures rate limit end time

### Modified File
- `apiproxy/proxies/default.xml` - Updated with timing instrumentation

### Performance Headers Added

When request includes `X-Debug-Performance: true`:

- `X-Apigee-Total-Time` - End-to-end request time
- `X-Apigee-Proxy-Time` - Total proxy processing
- `X-Apigee-Target-Time` - Backend response time
- `X-Apigee-JWT-Time` - JWT processing duration
- `X-Apigee-KVM-Time` - KVM lookup duration
- `X-Apigee-RateLimit-Time` - Rate limiting duration
- And 9 more timing/metadata headers...

## Post-Deployment Testing

### 1. Basic Test

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.cropwise.com/cropwise-unified-platform/accounts/me
```

Expected: 200 OK

### 2. Performance Headers Test

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "X-Debug-Performance: true" \
     https://api.cropwise.com/cropwise-unified-platform/accounts/me \
     -v | grep X-Apigee
```

Expected: X-Apigee-* headers in response

### 3. Full EC2 Test

```bash
export BEARER_TOKEN="your_jwt_token"
python tests/ec2-performance-test.py
```

Expected: Report with policy-level timing breakdown

## See Also

- **Deployment Guide**: [docs/DEPLOYMENT-GUIDE.md](../docs/DEPLOYMENT-GUIDE.md)
- **Performance Headers Guide**: [docs/PERFORMANCE-HEADERS-TESTING-GUIDE.md](../docs/PERFORMANCE-HEADERS-TESTING-GUIDE.md)
- **EC2 Test Summary**: [tests/EC2-PERFORMANCE-TEST-SUMMARY.md](../tests/EC2-PERFORMANCE-TEST-SUMMARY.md)

---

*For detailed deployment workflows and CI/CD integration, see the full [Deployment Guide](../docs/DEPLOYMENT-GUIDE.md).*
