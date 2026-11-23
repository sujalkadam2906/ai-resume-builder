<#
.SYNOPSIS
    First-time setup script for Sujal Kadam's AI-Powered ATS Resume Builder.
.DESCRIPTION
    Verifies Python environment, dependencies, directories, and prepares configuration.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  SUJAL KADAM — AI-POWERED ATS RESUME TAILORING SYSTEM SETUP" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "`n[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  [OK] Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python is not installed or not in PATH. Please install Python 3.10+." -ForegroundColor Red
    exit 1
}

# 2. Ensure Required Directories Exist
Write-Host "`n[2/5] Creating application directories..." -ForegroundColor Yellow
$dirs = @(
    "data",
    "data/backups",
    "job_descriptions",
    "output",
    "logs",
    "tests"
)
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  [+] Created directory: $dir" -ForegroundColor Gray
    } else {
        Write-Host "  [OK] Directory exists: $dir" -ForegroundColor Gray
    }
}

# 3. Install / Verify Dependencies
Write-Host "`n[3/5] Installing and verifying dependencies..." -ForegroundColor Yellow
try {
    pip install -e . | Out-Null
    Write-Host "  [OK] Dependencies and resume-builder package installed successfully." -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] pip install failed: $_" -ForegroundColor Red
    exit 1
}

# 4. Prepare .env file
Write-Host "`n[4/5] Checking environment configuration (.env)..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "  [+] Created .env from .env.example" -ForegroundColor Green
        Write-Host "  [!] Please edit .env to add your GEMINI_API_KEY for online AI tailoring." -ForegroundColor Yellow
    }
} else {
    Write-Host "  [OK] .env file exists." -ForegroundColor Green
}

# 5. Check Initial Resumes
Write-Host "`n[5/5] Checking source resume files..." -ForegroundColor Yellow
python -c "
from pathlib import Path
from resume_builder.extraction.discovery import find_resume_files
found = find_resume_files(Path('.'))
r1, r2 = found.get('r1'), found.get('r2')
if r1 and r2:
    print(f'  [OK] Found R1: {r1}')
    print(f'  [OK] Found R2: {r2}')
else:
    print('  [WARNING] Could not find both source resumes in root or Current Resumes/')
"

Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
Write-Host "  To generate a resume, simply run:" -ForegroundColor White
Write-Host "    .\resume.ps1" -ForegroundColor Yellow
Write-Host "  Or with a JD file:" -ForegroundColor White
Write-Host "    .\resume.ps1 -JDPath 'job_descriptions\sample_jd.txt'" -ForegroundColor Yellow
Write-Host "==================================================================`n" -ForegroundColor Cyan
