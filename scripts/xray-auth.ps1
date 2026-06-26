<#
.SYNOPSIS
  Authenticate to Xray Cloud and print a bearer token.
.DESCRIPTION
  POSTs client id/secret to the Xray Cloud auth endpoint and returns the JWT.
  Reads credentials from env vars (never commit them):
    XRAY_CLIENT_ID, XRAY_CLIENT_SECRET, XRAY_BASE_URL (optional)
  Usage:
    $token = ./scripts/xray-auth.ps1
.NOTES
  Requires XRAY_CLIENT_ID / XRAY_CLIENT_SECRET to be set (Jira -> Xray -> API Keys).
#>

$ErrorActionPreference = 'Stop'

$clientId     = $env:XRAY_CLIENT_ID
$clientSecret = $env:XRAY_CLIENT_SECRET
$baseUrl      = if ($env:XRAY_BASE_URL) { $env:XRAY_BASE_URL } else { 'https://xray.cloud.getxray.app/api/v2' }

if (-not $clientId -or -not $clientSecret) {
    throw "XRAY_CLIENT_ID and XRAY_CLIENT_SECRET must be set (see .env.example)."
}

$body = @{ client_id = $clientId; client_secret = $clientSecret } | ConvertTo-Json
$resp = Invoke-RestMethod -Method Post -Uri "$baseUrl/authenticate" `
    -ContentType 'application/json' -Body $body

# Xray returns the token as a quoted JSON string; strip surrounding quotes.
$token = ($resp -replace '^"|"$', '')
Write-Output $token
