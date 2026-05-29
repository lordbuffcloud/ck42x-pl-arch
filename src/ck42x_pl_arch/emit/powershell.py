from __future__ import annotations


def template_agent_ps1(goal: str) -> str:
    safe_goal = goal.replace("'", "''")
    return f"""$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'CK42X PL-ARCH Agent'
$env:PAYLOADBAY_MISSION_GOAL = '{safe_goal}'

function Get-DeepSeekKey {{
    $k = [Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY', 'User')
    if ([string]::IsNullOrWhiteSpace($k)) {{ $k = $env:DEEPSEEK_API_KEY }}
    return $k
}}

Write-Host ''
Write-Host ' CK42X Payload Lab Architect — Mission Agent' -ForegroundColor Cyan
Write-Host ' AUTHORIZED SYSTEMS ONLY' -ForegroundColor Yellow
Write-Host ''
Write-Host " Goal: $env:PAYLOADBAY_MISSION_GOAL" -ForegroundColor White
Write-Host ''

$key = Get-DeepSeekKey
if ([string]::IsNullOrWhiteSpace($key)) {{
    Write-Host ' Set DEEPSEEK_API_KEY for AI-assisted planning.' -ForegroundColor DarkYellow
    Write-Host ' Running read-only lab snapshot instead...' -ForegroundColor DarkGray
    Get-Location
    if (Get-Command git -ErrorAction SilentlyContinue) {{ git status --short --branch }}
    Read-Host 'Press Enter to exit'
    exit 0
}}

$body = @{{
    model = 'deepseek-chat'
    messages = @(
        @{{ role = 'system'; content = 'You are a cautious lab assistant. Propose read-only PowerShell diagnostics only. JSON: {{summary,commands[]}}' }}
        @{{ role = 'user'; content = $env:PAYLOADBAY_MISSION_GOAL }}
    )
    temperature = 0.2
}} | ConvertTo-Json -Depth 6

$r = Invoke-RestMethod -Method Post -Uri 'https://api.deepseek.com/chat/completions' `
    -Headers @{{ Authorization = "Bearer $key"; 'Content-Type' = 'application/json' }} -Body $body
Write-Host $r.choices[0].message.content
Read-Host 'Press Enter to exit'
"""
