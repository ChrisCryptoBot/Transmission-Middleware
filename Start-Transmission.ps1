# Transmission™ Startup Scripts
# PowerShell convenience scripts for starting services

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("api", "dashboard", "both", "dev")]
    [string]$Service = "both"
)

$Root = $PSScriptRoot

function Start-API {
    Write-Host "🚀 Starting Transmission™ API Server..." -ForegroundColor Green
    Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "API docs at: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    
    Set-Location $Root
    python startup/run_api.py
}

function Start-Dashboard {
    Write-Host "📊 Starting Transmission™ Dashboard..." -ForegroundColor Green
    Write-Host "Dashboard will be available at: http://localhost:8501" -ForegroundColor Cyan
    Write-Host ""
    
    Set-Location $Root
    python startup/run_dashboard.py
}

function Start-Both {
    Write-Host "🚀 Starting both API and Dashboard..." -ForegroundColor Green
    Write-Host ""
    
    # Start API in background job
    $apiJob = Start-Job -ScriptBlock {
        Set-Location $using:Root
        python startup/run_api.py
    }
    
    # Wait a moment for API to start
    Start-Sleep -Seconds 3
    
    # Start Dashboard in foreground
    Start-Dashboard
    
    # Clean up background job when dashboard stops
    Stop-Job $apiJob
    Remove-Job $apiJob
}

switch ($Service) {
    "api" {
        Start-API
    }
    "dashboard" {
        Start-Dashboard
    }
    "both" {
        Write-Host "Starting both services..." -ForegroundColor Yellow
        Write-Host "API will run in background, Dashboard in foreground" -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop Dashboard (API will continue)" -ForegroundColor Yellow
        Write-Host ""
        Start-Both
    }
    "dev" {
        Write-Host "Starting development environment..." -ForegroundColor Yellow
        Write-Host "Opening both services in separate windows..." -ForegroundColor Yellow
        Write-Host ""
        
        # Start API in new window
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root'; python startup/run_api.py"
        
        # Wait a moment
        Start-Sleep -Seconds 2
        
        # Start Dashboard in new window
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root'; python startup/run_dashboard.py"
        
        Write-Host "✅ Both services started in separate windows" -ForegroundColor Green
    }
}

