param(
    [ValidateRange(1, 86400)]
    [int]$IntervalSeconds = 10
)

$ErrorActionPreference = "Continue"

# Always run from the folder containing this script.
Set-Location -LiteralPath $PSScriptRoot

Write-Host "Running 'uv run python3 main.py' every $IntervalSeconds seconds."
Write-Host "Press Ctrl+C to stop."

while ($true) {
    $startedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$startedAt] Starting..."

    & uv run python3 main.py
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        Write-Warning "Command exited with code $exitCode. It will be retried."
    }

    Write-Host "Waiting $IntervalSeconds seconds..."
    Start-Sleep -Seconds $IntervalSeconds
}
