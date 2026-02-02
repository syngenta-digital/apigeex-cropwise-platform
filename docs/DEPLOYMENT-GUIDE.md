# Deployment Guide

## Overview

This guide covers the deployment process for the Cropwise Unified Platform API proxy to Apigee X.

## Prerequisites

1. **Python 3.9+** installed
2. **Google Cloud SDK** installed and configured
3. **Apigee X** organization access with deployer permissions
4. **Service Account** with appropriate IAM roles

## Environment Setup

### 1. Install Dependencies

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and update with your values:

```bash
cp .env.example .env
```

Edit `.env`:
```
APIGEE_ORG=your-apigee-org
APIGEE_ENV=dev
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json
```

### 3. Authenticate to Google Cloud

```bash
gcloud auth application-default login
```

## Deployment Steps

### Step 1: Validate Proxy

Before deploying, validate the proxy structure:

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
