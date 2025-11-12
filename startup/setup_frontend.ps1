# Setup script for React frontend
Write-Host "Setting up Beyond Candlesticks Frontend..." -ForegroundColor Cyan

# Check if Node.js is installed
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Node.js is not installed. Please install Node.js 18+ first." -ForegroundColor Red
    exit 1
}

$nodeVersion = node --version
Write-Host "Node.js version: $nodeVersion" -ForegroundColor Green

# Navigate to web directory
Set-Location web

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Frontend setup complete!" -ForegroundColor Green
Write-Host "`nTo start the development server:" -ForegroundColor Cyan
Write-Host "  cd web" -ForegroundColor White
Write-Host "  npm run dev" -ForegroundColor White
Write-Host "`nThe frontend will be available at: http://localhost:5173" -ForegroundColor Cyan

