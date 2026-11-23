<#
.SYNOPSIS
    Runs the Multi-Provider AI ATS Resume Builder with Multi-Profile Support.
.DESCRIPTION
    Accepts job description via interactive paste or file path, selects verified projects
    adhering to candidate-specific profile rules, generates 1-page PDF and DOCX, and calculates ATS score.
    Supports multi-provider AI cascade (Gemini, Groq, Cohere, OpenRouter, Cloudflare, Offline)
    and full multi-profile isolation (Sujal Kadam, Demo Candidate, etc.).
.EXAMPLE
    .\resume.ps1
.EXAMPLE
    .\resume.ps1 -Profile sujal -JDPath ".\job_descriptions\sujal\java_backend.txt"
.EXAMPLE
    .\resume.ps1 -Profile demo_candidate -JDPath ".\job_descriptions\demo_candidate\frontend_developer.txt" -Offline
.EXAMPLE
    .\resume.ps1 -ListProfiles
.EXAMPLE
    .\resume.ps1 -ValidateProfile -Profile sujal
.EXAMPLE
    .\resume.ps1 -ProfileInfo -Profile demo_candidate
.EXAMPLE
    .\resume.ps1 -CheckProviders
.EXAMPLE
    .\resume.ps1 -Offline
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$Profile = "sujal",

    [Parameter(Mandatory=$false)]
    [string]$JDPath,

    [Parameter(Mandatory=$false)]
    [string]$Company,

    [Parameter(Mandatory=$false)]
    [string]$Role,

    [Parameter(Mandatory=$false)]
    [ValidateSet("gemini", "groq", "cohere", "openrouter", "cloudflare", "offline")]
    [string]$Provider,

    [Parameter(Mandatory=$false)]
    [string]$Output,

    [switch]$ListProfiles,

    [Parameter(Mandatory=$false)]
    [string]$CreateProfile,

    [Parameter(Mandatory=$false)]
    [string]$SourceDir,

    [switch]$ValidateProfile,

    [switch]$ProfileInfo,

    [switch]$CheckProviders,

    [switch]$BenchmarkProviders,

    [switch]$Offline,

    [switch]$DryRun,

    [switch]$CheckOnly,

    [switch]$ListProjects,

    [switch]$RefreshProfile,

    [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"

# Handle standalone inspection commands
if ($ListProfiles) {
    python -m resume_builder.cli --list-profiles
    exit $LASTEXITCODE
}

if ($CreateProfile) {
    $createArgs = @("--create-profile", $CreateProfile)
    if ($SourceDir) {
        $createArgs += "--source-dir"
        $createArgs += $SourceDir
    }
    python -m resume_builder.cli @createArgs
    exit $LASTEXITCODE
}

if ($ValidateProfile) {
    python -m resume_builder.cli --profile $Profile --validate-profile
    exit $LASTEXITCODE
}

if ($ProfileInfo) {
    python -m resume_builder.cli --profile $Profile --profile-info
    exit $LASTEXITCODE
}

if ($CheckProviders) {
    python -m resume_builder.cli --check-providers
    exit $LASTEXITCODE
}

if ($BenchmarkProviders) {
    python -m resume_builder.cli --benchmark-providers
    exit $LASTEXITCODE
}

if ($ListProjects) {
    python -m resume_builder.cli --profile $Profile --list-projects
    exit $LASTEXITCODE
}

if ($RefreshProfile) {
    python -m resume_builder.cli --profile $Profile --refresh-profile
    exit $LASTEXITCODE
}

# Build arguments array for Python CLI
$cliArgs = @()

if ($Profile) {
    $cliArgs += "--profile"
    $cliArgs += $Profile
}

if ($JDPath) {
    if (-not (Test-Path $JDPath)) {
        Write-Host "Error: Specified JD file does not exist: $JDPath" -ForegroundColor Red
        exit 1
    }
    $cliArgs += "--jd"
    $cliArgs += $JDPath
}

if ($Company) {
    $cliArgs += "--company"
    $cliArgs += $Company
}

if ($Role) {
    $cliArgs += "--role"
    $cliArgs += $Role
}

if ($Provider) {
    $cliArgs += "--provider"
    $cliArgs += $Provider
}

if ($Output) {
    $cliArgs += "--output"
    $cliArgs += $Output
}

if ($Offline) {
    $cliArgs += "--offline"
}

if ($DryRun) {
    $cliArgs += "--dry-run"
}

if ($CheckOnly) {
    $cliArgs += "--check-only"
}

if ($VerboseOutput) {
    $cliArgs += "--verbose"
}

# Run the CLI
python -m resume_builder.cli @cliArgs
exit $LASTEXITCODE
