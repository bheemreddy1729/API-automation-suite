<#
.SYNOPSIS
  VS Code startup reminder for the QA automation loop.
.DESCRIPTION
  Shows a once-per-day reminder to run /ready-for-testing in Claude Code.
  Wire it to run on folder open via .vscode/tasks.json (runOptions.runOn: folderOpen)
  or a terminal profile. It never blocks and never fails the shell.
#>

$ErrorActionPreference = 'SilentlyContinue'

$stampDir  = Join-Path $PSScriptRoot '..\target'
$stampFile = Join-Path $stampDir '.qa-sync-reminder'
$today     = (Get-Date).ToString('yyyy-MM-dd')

if (-not (Test-Path $stampDir)) {
    New-Item -ItemType Directory -Path $stampDir -Force | Out-Null
}

$last = if (Test-Path $stampFile) { Get-Content $stampFile -Raw } else { '' }

if ($last.Trim() -ne $today) {
    Write-Host ''
    Write-Host '  QA Automation - LBVOICESER ----------------------------------' -ForegroundColor Cyan
    Write-Host '  Tickets may be waiting in "Ready for testing".' -ForegroundColor Yellow
    Write-Host '  In Claude Code, run:  /ready-for-testing' -ForegroundColor Green
    Write-Host '  -------------------------------------------------------------' -ForegroundColor Cyan
    Write-Host ''
    Set-Content -Path $stampFile -Value $today
}
