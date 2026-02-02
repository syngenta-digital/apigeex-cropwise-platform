# Deploy Cropwise Unified Platform Proxy to Apigee X
# Usage: .\scripts\deploy.ps1 -Environment dev

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('dev', 'qa', 'prod')]
    [string]$Environment = 'dev',
    
    [Parameter(Mandatory=$false)]
    [string]$Organization = 'your-org-name',
    
    [Parameter(Mandatory=$false)]
    [string]$Token = $env:APIGEE_TOKEN,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBundle,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Success { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Info { param($msg) Write-Host $msg -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-Failure { param($msg) Write-Host $msg -ForegroundColor Red }

# Configuration
$ProxyName = "cropwise-unified-platform"
$BaseDir = Split-Path $PSScriptRoot -Parent
$ApiProxyDir = Join-Path $BaseDir "apiproxy"
$DistDir = Join-Path $BaseDir "dist"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BundleFile = Join-Path $DistDir "$ProxyName-$Timestamp.zip"

Write-Info "==============================================================="
Write-Info "  Apigee X Deployment Script"
Write-Info "==============================================================="
Write-Info "Proxy Name: $ProxyName"
Write-Info "Environment: $Environment"
Write-Info "Timestamp: $Timestamp"
Write-Info ""

# Step 1: Create bundle
if (-not $SkipBundle) {
    Write-Info "Step 1: Creating proxy bundle..."
    
    # Create dist directory if it doesn't exist
    if (-not (Test-Path $DistDir)) {
        New-Item -ItemType Directory -Path $DistDir | Out-Null
    }
    
    # Check if apiproxy directory exists
    if (-not (Test-Path $ApiProxyDir)) {
        Write-Failure "ERROR: apiproxy directory not found at $ApiProxyDir"
        exit 1
    }
    
    # Create ZIP bundle
    Write-Info "  Creating ZIP bundle: $BundleFile"
    
    # Remove old bundle if exists
    if (Test-Path $BundleFile) {
        Remove-Item $BundleFile -Force
    }
    
    # Create ZIP with apiproxy folder structure
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory($ApiProxyDir, $BundleFile)
    
    $BundleSize = (Get-Item $BundleFile).Length / 1KB
    Write-Success "  ✓ Bundle created: $([math]::Round($BundleSize, 2)) KB"
} else {
    Write-Info "Step 1: Skipping bundle creation (using existing bundle)"
}

Write-Info ""

# Step 2: Check prerequisites
Write-Info "Step 2: Checking prerequisites..."

# Check for gcloud CLI
$GcloudPath = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $GcloudPath) {
    Write-Failure "ERROR: gcloud CLI not found. Please install Google Cloud SDK."
    Write-Info "Download from: https://cloud.google.com/sdk/docs/install"
    exit 1
}
Write-Success "  ✓ gcloud CLI found"

# Get access token if not provided
if (-not $Token) {
    Write-Info "  Getting access token from gcloud..."
    $Token = gcloud auth print-access-token 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Failure "ERROR: Failed to get access token. Please run: gcloud auth login"
        exit 1
    }
    Write-Success "  ✓ Access token obtained"
} else {
    Write-Success "  ✓ Using provided access token"
}

# Get organization if not provided
if ($Organization -eq 'your-org-name') {
    Write-Info "  Getting Apigee organization..."
    $ProjectId = gcloud config get-value project 2>$null
    if ($ProjectId) {
        $Organization = $ProjectId
        Write-Success "  ✓ Using organization: $Organization"
    } else {
        Write-Failure "ERROR: Could not determine organization. Please provide -Organization parameter"
        exit 1
    }
}

Write-Info ""

if ($DryRun) {
    Write-Warning "DRY RUN MODE - No actual deployment will occur"
    Write-Info ""
    Write-Info "Would deploy:"
    Write-Info "  Bundle: $BundleFile"
    Write-Info "  Organization: $Organization"
    Write-Info "  Proxy: $ProxyName"
    Write-Info "  Environment: $Environment"
    exit 0
}

# Step 3: Upload proxy bundle
Write-Info "Step 3: Uploading proxy bundle to Apigee X..."

$UploadUrl = "https://apigee.googleapis.com/v1/organizations/$Organization/apis?action=import`&name=$ProxyName"

Write-Info "  URL: $UploadUrl"

try {
    # Read bundle file
    $BundleBytes = [System.IO.File]::ReadAllBytes($BundleFile)
    
    # Create multipart form data
    $Boundary = [System.Guid]::NewGuid().ToString()
    $Headers = @{
        "Authorization" = "Bearer $Token"
        "Content-Type" = "multipart/form-data; boundary=$Boundary"
    }
    
    # Build multipart body
    $BodyLines = @(
        "--$Boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"$ProxyName.zip`"",
        "Content-Type: application/zip",
        "",
        [System.Text.Encoding]::GetEncoding("ISO-8859-1").GetString($BundleBytes),
        "--$Boundary--"
    )
    $Body = $BodyLines -join "`r`n"
    
    # Upload
    $Response = Invoke-RestMethod -Uri $UploadUrl -Method Post -Headers $Headers -Body ([System.Text.Encoding]::GetEncoding("ISO-8859-1").GetBytes($Body)) -ContentType "multipart/form-data; boundary=$Boundary"
    
    $Revision = $Response.revision
    Write-Success "  ✓ Upload successful - Revision: $Revision"
    
} catch {
    Write-Failure "ERROR: Failed to upload proxy bundle"
    Write-Failure $_.Exception.Message
    if ($_.ErrorDetails) {
        Write-Failure $_.ErrorDetails.Message
    }
    exit 1
}

Write-Info ""

# Step 4: Deploy proxy
Write-Info "Step 4: Deploying proxy revision $Revision to $Environment..."

$DeployUrl = "https://apigee.googleapis.com/v1/organizations/$Organization/environments/$Environment/apis/$ProxyName/revisions/$Revision/deployments"

Write-Info "  URL: $DeployUrl"

try {
    $Headers = @{
        "Authorization" = "Bearer $Token"
        "Content-Type" = "application/json"
    }
    
    $Response = Invoke-RestMethod -Uri $DeployUrl -Method Post -Headers $Headers
    
    Write-Success "  ✓ Deployment initiated"
    
} catch {
    Write-Failure "ERROR: Failed to deploy proxy"
    Write-Failure $_.Exception.Message
    if ($_.ErrorDetails) {
        Write-Failure $_.ErrorDetails.Message
    }
    exit 1
}

Write-Info ""

# Step 5: Check deployment status
Write-Info "Step 5: Checking deployment status..."

$StatusUrl = "https://apigee.googleapis.com/v1/organizations/$Organization/environments/$Environment/apis/$ProxyName/revisions/$Revision/deployments"

$MaxAttempts = 30
$Attempt = 0
$DeploymentReady = $false

while ($Attempt -lt $MaxAttempts -and -not $DeploymentReady) {
    Start-Sleep -Seconds 2
    $Attempt++
    
    try {
        $Headers = @{
            "Authorization" = "Bearer $Token"
        }
        
        $Status = Invoke-RestMethod -Uri $StatusUrl -Method Get -Headers $Headers
        
        if ($Status.state -eq 'deployed') {
            $DeploymentReady = $true
            Write-Success "  ✓ Deployment is READY!"
        } elseif ($Status.state -eq 'error') {
            Write-Failure "  ✗ Deployment FAILED with error"
            exit 1
        } else {
            Write-Info "  ⏳ Waiting for deployment... ($Attempt/$MaxAttempts) - State: $($Status.state)"
        }
        
    } catch {
        Write-Info "  ⏳ Waiting for deployment... ($Attempt/$MaxAttempts)"
    }
}

if (-not $DeploymentReady) {
    Write-Warning "  ⚠ Deployment status check timed out after $MaxAttempts attempts"
    Write-Info "  Check Apigee console for deployment status"
}

Write-Info ""

# Summary
Write-Success "==============================================================="
Write-Success "  Deployment Summary"
Write-Success "==============================================================="
Write-Success "Proxy: $ProxyName"
Write-Success "Revision: $Revision"
Write-Success "Environment: $Environment"
Write-Success "Organization: $Organization"
Write-Success "Bundle: $BundleFile"
Write-Success "Status: $(if ($DeploymentReady) { 'DEPLOYED' } else { 'IN PROGRESS' })"
Write-Success ""
Write-Success "✓ Deployment completed successfully!"
Write-Success ""

# API endpoint
$ApiEndpoint = "https://$Environment.api.cropwise.com/$ProxyName/accounts/me"
Write-Info "API Endpoint: $ApiEndpoint"
Write-Info ""
Write-Info "Test with performance headers:"
Write-Info "  curl -H 'Authorization: Bearer YOUR_TOKEN' -H 'X-Debug-Performance: true' $ApiEndpoint"
Write-Info ""
