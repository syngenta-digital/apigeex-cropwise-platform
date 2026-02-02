# Deployment Guide

## Overview

This guide covers deploying the Cropwise Unified Platform API proxy to Apigee X with the new performance header instrumentation. The deployment uses a cross-platform Python script that works on Mac, Linux, and Windows.

## Prerequisites

### Required Access & Permissions

1. **Apigee X Organization Access**
   - Organization: `use1-apigeex`
   - Project: `use1-apigeex`
   - API Domain: `api.cropwise.com`
   - Environment: `default-dev` (mapped from `dev`)

2. **Required IAM Roles**
   - Apigee API Admin (`roles/apigee.apiAdmin`) - For deploying proxies
   - Apigee Environment Admin (`roles/apigee.environmentAdmin`) - For managing deployments
   - Or Project Editor/Owner role with Apigee permissions

3. **Network Requirements**
   - Access to Apigee Management API: `https://apigee.googleapis.com`
   - Access to target backend: `https://dev.api.insights.cropwise.com`
   - Port 443 (HTTPS) outbound access

### Required Tools

1. **Python 3.7+**
   ```bash
   python3 --version
   ```

2. **requests library**
   ```bash
   pip3 install requests
   ```

3. **gcloud CLI** (recommended but optional)
   ```bash
   # Install from: https://cloud.google.com/sdk/docs/install
   gcloud version
   
   # Verify you have access to the correct project
   gcloud config get-value project
   # Should return: use1-apigeex
   ```

### Authentication

#### Option 1: Using gcloud (Recommended)

```bash
# Login to Google Cloud
gcloud auth login

# Set your project to use1-apigeex
gcloud config set project use1-apigeex

# Verify authentication
gcloud auth print-access-token

# Verify you can access Apigee
gcloud alpha apigee organizations describe use1-apigeex
```

#### Option 2: Manual Token (Alternative)

If gcloud is not available:

1. Go to Google Cloud Console (https://console.cloud.google.com)
2. Select project: `use1-apigeex`
3. Navigate to IAM & Admin > Service Accounts
4. Create or use existing service account with Apigee Admin role
5. Generate access token:
   ```bash
   # Using service account key
   gcloud auth activate-service-account --key-file=KEY_FILE.json
   gcloud auth print-access-token
   ```

### Environment Mapping

The deployment script automatically maps logical environments to Apigee environments:

| Logical Env | Apigee Environment | Description |
|-------------|-------------------|-------------|
| `dev`       | `default-dev`     | Development environment |
| `qa`        | `default-qa`      | QA/Testing environment |
| `prod`      | `default-prod`    | Production environment |

### Pre-Deployment Checklist

- [ ] Python 3.7+ installed and accessible
- [ ] `requests` library installed (`pip install requests`)
- [ ] gcloud CLI installed and configured (or access token ready)
- [ ] Authenticated with Google Cloud
- [ ] Verified access to `use1-apigeex` project
- [ ] Confirmed IAM permissions for Apigee deployment
- [ ] Network access to Apigee APIs verified

## Deployment Commands

### 1. Quick Deploy (Default)

Deploy to dev environment using gcloud authentication:

```bash
python scripts/deploy.py --env dev
```

### 2. Deploy with Custom Organization

```bash
python scripts/deploy.py --env dev --org YOUR_ORG_NAME
```

### 3. Deploy with Manual Token

```bash
python scripts/deploy.py --env dev \
  --org YOUR_ORG_NAME \
  --token YOUR_ACCESS_TOKEN
```

### 4. Create Bundle Only (No Deployment)

```bash
python scripts/deploy.py --env dev --bundle-only
```

### 5. Dry Run (Test Prerequisites)

```bash
python scripts/deploy.py --env dev --dry-run
```

```bash
python scripts/generate_proxy.py --env dev --validate
```

### Step 2: Generate Bundle

Generate the proxy bundle for your target environment:

```bash
# Development
python scripts/generate_proxy.py --env dev

# QA
python scripts/generate_proxy.py --env qa

# Production
python scripts/generate_proxy.py --env prod
```

### Step 3: Deploy

Deploy the generated bundle:

```bash
# Upload and deploy to dev
python scripts/deploy_proxy.py --env dev --bundle ./dist/cropwise-*.zip --deploy --wait

# Check deployment status
python scripts/deploy_proxy.py --env dev --status
```

### Step 4: Verify Deployment

Run smoke tests to verify the deployment:

```bash
python scripts/test_proxy.py --env dev --test-suite smoke
```

## Rollback Procedure

If a deployment fails or causes issues:

1. **Identify the previous working revision:**
   ```bash
   python scripts/deploy_proxy.py --env dev --status
   ```

2. **Undeploy current revision** (manual via Apigee Console or API)

3. **Redeploy previous revision**

## CI/CD Integration

The repository includes GitHub Actions workflows for automated deployments:

- **develop branch** → Deploys to `dev` environment
- **main branch** → Deploys to `qa` environment
- **Manual trigger** → Can deploy to any environment including `prod`

See `.github/workflows/deploy.yml` for the complete workflow.

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Authentication failed | Run `gcloud auth application-default login` |
| Bundle upload failed | Check XML syntax with `--validate` flag |
| Deployment stuck | Check Apigee Console for stuck deployments |
| 502 errors | Verify backend host is reachable |

### Debug Commands

```bash
# Check Apigee API connectivity
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://apigee.googleapis.com/v1/organizations/YOUR_ORG/apis"

# Verbose test output
python scripts/test_proxy.py --env dev --verbose
```

## Support

Contact the CropwisePlatform team via Slack: **#cropwise-platform-support**
