# Start Beyond Candlesticks API Server
# Ensures virtual environment is activated

$Root = $PSScriptRoot
Set-Location $Root

# Activate virtual environment
& "$Root\.venv\Scripts\Activate.ps1"

Write-Host "🚀 Starting Beyond Candlesticks API Server..." -ForegroundColor Green
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API docs at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Run the API
python startup/run_api.py

