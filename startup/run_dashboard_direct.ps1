# Direct Streamlit Dashboard Launcher
# Use this if run_dashboard.py has issues

$Root = $PSScriptRoot
Set-Location $Root

Write-Host "Starting Transmission™ Dashboard..." -ForegroundColor Green
Write-Host "Dashboard will be available at: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""

& python -m streamlit run transmission/dashboard/main.py --server.port=8501 --server.address=0.0.0.0

