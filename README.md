# Cropwise Unified Platform - Apigee X Proxy Repository

**Project:** Cropwise Unified Platform API Proxy  
**Version:** 1.0  
**Team:** CropwisePlatform Team

## Overview

This repository contains the Apigee X proxy configuration and deployment scripts for the Cropwise Unified Platform API.

## Quick Start

```bash
# 1. Set up Python environment
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your values

# 3. Authenticate
gcloud auth application-default login

# 4. Validate proxy
python scripts/generate_proxy.py --env dev --validate

# 5. Generate bundle
python scripts/generate_proxy.py --env dev --output ./dist

# 6. Deploy
python scripts/deploy_proxy.py --env dev --bundle ./dist/cropwise-*.zip --deploy --wait

# 7. Test
python scripts/test_proxy.py --env dev --test-suite all
```

## Repository Structure

```
cropwise-unified-platform-proxy/
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── config/
│   ├── environments.json
│   ├── policies.json
│   └── endpoints.json
├── apiproxy/
│   ├── cropwise-unified-platform-proxy.xml
│   ├── policies/
│   ├── proxies/
│   ├── resources/
│   └── targets/
├── scripts/
│   ├── generate_proxy.py
│   ├── deploy_proxy.py
│   ├── test_proxy.py
│   └── utils/
├── tests/
│   ├── test_endpoints.py
│   ├── test_policies.py
│   └── fixtures/
└── docs/
```

## Scripts

- **generate_proxy.py** - Generate proxy bundle with environment-specific configurations
- **deploy_proxy.py** - Deploy proxy bundle to Apigee X
- **test_proxy.py** - Test deployed proxy endpoints

## Documentation

- [Setup Guide](docs/CROPWISE-PLATFORM-REPO-SETUP-GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT-GUIDE.md)
- [Policy Reference](docs/POLICY-REFERENCE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Support

Contact CropwisePlatform team via Slack: #cropwise-platform-support
