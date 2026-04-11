<#
.SYNOPSIS
    Ralph Wiggum - Long-running AI agent loop (PowerShell Port)
    Usage: .\ralph.ps1 [-MaxIterations 10]
#>

param (
    [int]$MaxIterations = 10,
    [string]$Tool = "claude" # Currently supports 'claude-code' if installed
)

$ErrorActionPreference = "Stop"

$ScriptDir = $PSScriptRoot
$PrdFile = Join-Path $ScriptDir "..\..\prd.json"
$ProgressFile = Join-Path $ScriptDir "..\..\progress.txt"
$ClaudePrompt = Join-Path $ScriptDir "..\..\CLAUDE.md"

if (-not (Test-Path $PrdFile)) {
    Write-Error "prd.json not found in the root directory."
}

Write-Host "Starting Ralph - Tool: $Tool - Max iterations: $MaxIterations" -ForegroundColor Cyan

for ($i = 1; $i -le $MaxIterations; $i++) {
    Write-Host "`n==============================================================="
    Write-Host "  Ralph Iteration $i of $MaxIterations ($Tool)"
    Write-Host "==============================================================="

    # Check for Tool availability
    if ($Tool -eq "claude") {
        if (-not (Get-Command "claude" -ErrorAction SilentlyContinue)) {
            Write-Host "Error: 'claude' CLI not found. Please install with 'npm install -g @anthropic-ai/claude-code'" -ForegroundColor Red
            exit 1
        }

        # Run Claude Code with the prompt
        # We use Get-Content and pass it to stdin
        $Output = Get-Content $ClaudePrompt | claude --dangerously-skip-permissions --print | Tee-Object -FilePath "ralph_iteration_$i.log"
    }
    else {
        Write-Host "Error: Tool '$Tool' not yet implemented in this PowerShell port." -ForegroundColor Red
        exit 1
    }

    # Check for completion signal
    if ($Output -match "<promise>COMPLETE</promise>") {
        Write-Host "`nRalph completed all tasks!" -ForegroundColor Green
        Write-Host "Completed at iteration $i of $MaxIterations"
        exit 0
    }

    Write-Host "Iteration $i complete. Continuing..."
    Start-Sleep -Seconds 2
}

Write-Host "`nRalph reached max iterations ($MaxIterations) without completing all tasks." -ForegroundColor Yellow
Write-Host "Check progress.txt for status."
exit 1
