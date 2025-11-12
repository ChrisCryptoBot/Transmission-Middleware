# Start React frontend development server
Write-Host "Starting Beyond Candlesticks Frontend..." -ForegroundColor Cyan

Set-Location web

if (-not (Test-Path "node_modules")) {
    Write-Host "Dependencies not installed. Running setup..." -ForegroundColor Yellow
    npm install
}

Write-Host "`nStarting Vite dev server..." -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Make sure the API is running at: http://localhost:8000`n" -ForegroundColor Yellow

npm run dev

