<#
.SYNOPSIS
  Import JUnit results into Xray Cloud (creates/updates a Test Execution).
.DESCRIPTION
  Authenticates via xray-auth.ps1, then POSTs the enhanced JUnit XML produced by the
  surefire run (with xray-junit-extensions annotations) to the Xray Cloud import API.

  Usage:
    ./scripts/xray-import.ps1                       # imports target/surefire-reports/*.xml
    ./scripts/xray-import.ps1 -ReportGlob "target/surefire-reports/TEST-*.xml" `
                              -ProjectKey LBVOICESER

  Requires XRAY_CLIENT_ID / XRAY_CLIENT_SECRET (see .env.example). Blocked until set.
.NOTES
  Endpoint: POST {XRAY_BASE_URL}/import/execution/junit?projectKey=KEY
#>
param(
    [string]$ReportGlob = 'target/surefire-reports/TEST-*.xml',
    [string]$ProjectKey = 'LBVOICESER'
)

$ErrorActionPreference = 'Stop'

$baseUrl = if ($env:XRAY_BASE_URL) { $env:XRAY_BASE_URL } else { 'https://xray.cloud.getxray.app/api/v2' }
$token   = & "$PSScriptRoot/xray-auth.ps1"

$files = Get-ChildItem -Path (Join-Path (Get-Location) $ReportGlob) -ErrorAction Stop
if (-not $files) { throw "No JUnit reports matched: $ReportGlob (run 'mvn test' first)." }

$headers = @{ Authorization = "Bearer $token" }

foreach ($f in $files) {
    Write-Host "Importing $($f.Name) -> Xray ($ProjectKey)..." -ForegroundColor Cyan
    $uri = "$baseUrl/import/execution/junit?projectKey=$ProjectKey"
    $resp = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers `
        -ContentType 'text/xml' -InFile $f.FullName
    $resp | ConvertTo-Json -Depth 6 | Write-Output
}
