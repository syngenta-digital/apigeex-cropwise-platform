# Apigee X Configuration

## Organization Details

**Project**: use1-apigeex  
**Organization ID**: 711137019957  
**Type**: use1-non-prod-apigeex-service  
**API Domain**: api.cropwise.com

## Environments

| Environment | Apigee Environment | API URL |
|-------------|-------------------|---------|
| dev | default-dev | https://api.cropwise.com/cropwise-unified-platform |
| qa | default-qa | https://api.cropwise.com/cropwise-unified-platform |
| prod | default-prod | https://api.cropwise.com/cropwise-unified-platform |

## Deployment Configuration

The deployment script (`scripts/deploy.py`) is pre-configured with these defaults:

```python
DEFAULT_ORG = "711137019957"
DEFAULT_PROJECT = "use1-apigeex"

ENV_MAP = {
    'dev': 'default-dev',
    'qa': 'default-qa', 
    'prod': 'default-prod'
}
```

## Quick Deployment

With these defaults, you can deploy without specifying organization:

```bash
# Deploy to dev (uses default org: 711137019957)
python scripts/deploy.py --env dev

# Or with manual token
python scripts/deploy.py --env dev --token YOUR_ACCESS_TOKEN
```

The script will automatically:
- Use organization: **711137019957**
- Map `dev` → `default-dev` environment
- Deploy to **api.cropwise.com**

## Authentication

### Option 1: gcloud CLI (Recommended)

```bash
gcloud auth login
gcloud config set project use1-apigeex
python scripts/deploy.py --env dev
```

### Option 2: Manual Token

```bash
# Get token from gcloud
TOKEN=$(gcloud auth print-access-token)

# Deploy with token
python scripts/deploy.py --env dev --token $TOKEN
```

### Option 3: Service Account

```bash
# Authenticate with service account
gcloud auth activate-service-account --key-file=path/to/key.json

# Deploy
python scripts/deploy.py --env dev
```

## API Testing

After deployment, test the API:

```bash
# Basic test
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.cropwise.com/cropwise-unified-platform/accounts/me

# With performance headers
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "X-Debug-Performance: true" \
     https://api.cropwise.com/cropwise-unified-platform/accounts/me
```

## Environment Variables

You can also set these as environment variables:

```bash
export APIGEE_ORG="711137019957"
export APIGEE_TOKEN="your_access_token"
export BEARER_TOKEN="your_jwt_token"  # For testing

python scripts/deploy.py --env dev
```

## IAM Roles Required

The deployment account needs these permissions:

- `roles/apigee.admin` or
- `roles/apigee.developer`

## Support

For deployment issues:

1. Verify organization: `711137019957`
2. Verify project: `use1-apigeex`
3. Check environment exists: `default-dev`, `default-qa`, or `default-prod`
4. Verify API domain: `api.cropwise.com`

---

*Configuration for use1-non-prod-apigeex-service*  
*Organization: 711137019957*
