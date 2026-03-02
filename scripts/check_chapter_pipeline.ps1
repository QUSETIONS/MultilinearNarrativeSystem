param(
  [string]$InputJson = "东方快车谋杀案.json",
  [switch]$NoLegacy,
  [switch]$JsonReport,
  [string]$LogFile = ""
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($LogFile)) {
  $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $LogFile = "logs/chapter-pipeline-$timestamp.log"
}

$LogPath = Join-Path (Get-Location) $LogFile
$LogDir = Split-Path -Parent $LogPath
if (-not (Test-Path $LogDir)) {
  New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$defaultReport = Join-Path $LogDir "validate-default-$stamp.json"
$noLegacyReport = Join-Path $LogDir "validate-nolegacy-$stamp.json"

Start-Transcript -Path $LogPath -Force | Out-Null

try {
  function Get-LastFailRule {
    param([string]$ReportPath)
    if (-not (Test-Path $ReportPath)) { return $null }

    try {
      $json = Get-Content -Raw $ReportPath | ConvertFrom-Json
      $failed = @($json.checks | Where-Object { $_.status -eq 'fail' })
      if ($failed.Count -gt 0) {
        return $failed[-1]
      }
    } catch {
      return $null
    }
    return $null
  }

  function Run-Step {
    param(
      [string]$Name,
      [scriptblock]$Action,
      [string]$ReportPath = "",
      [string]$SuggestCommand = ""
    )

    Write-Host "=== $Name ==="
    & $Action
    if ($LASTEXITCODE -ne 0) {
      Write-Host "[FAILED] $Name (exit=$LASTEXITCODE)"
      if (-not [string]::IsNullOrWhiteSpace($ReportPath)) {
        $lastFail = Get-LastFailRule -ReportPath $ReportPath
        if ($null -ne $lastFail) {
          Write-Host "[FAILED_RULE] $($lastFail.rule_id): $($lastFail.message)"
        }
      }
      if (-not [string]::IsNullOrWhiteSpace($SuggestCommand)) {
        Write-Host "[SUGGEST] Try: $SuggestCommand"
      }
      exit $LASTEXITCODE
    }
    Write-Host "[OK] $Name"
  }

  $legacyFlag = @()
  if ($NoLegacy) {
    $legacyFlag = @("--no-legacy")
  }

  Run-Step "Generate timelines (strict)" {
    python import_orient_express.py --input "$InputJson" --strict @legacyFlag
  } "" "python import_orient_express.py --input `"$InputJson`" --strict"

  $defaultValidateArgs = @("scripts/validate_chapter_outputs.py", "--input", "$InputJson")
  if ($NoLegacy) {
    $defaultValidateArgs += "--no-legacy"
  }
  if ($JsonReport) {
    $defaultValidateArgs += @("--json-out", "$defaultReport")
  }

  Run-Step "Validate outputs (default)" {
    python @defaultValidateArgs
  } $(if ($JsonReport) { $defaultReport } else { "" }) "python scripts/validate_chapter_outputs.py --input `"$InputJson`""

  if (-not $NoLegacy) {
    $noLegacyArgs = @("scripts/validate_chapter_outputs.py", "--input", "$InputJson", "--no-legacy")
    if ($JsonReport) {
      $noLegacyArgs += @("--json-out", "$noLegacyReport")
    }

    Run-Step "Validate outputs (no-legacy mode)" {
      python @noLegacyArgs
    } $(if ($JsonReport) { $noLegacyReport } else { "" }) "python scripts/validate_chapter_outputs.py --input `"$InputJson`" --no-legacy"
  }

  Write-Host "=== Summary ==="
  Write-Host "[OK] chapter pipeline check completed"
  Write-Host "[LOG] $LogPath"
  if ($JsonReport) {
    Write-Host "[REPORT] default=$defaultReport"
    if (-not $NoLegacy) {
      Write-Host "[REPORT] nolegacy=$noLegacyReport"
    }
  }
  exit 0
}
finally {
  Stop-Transcript | Out-Null
}
