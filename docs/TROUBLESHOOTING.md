# Troubleshooting Guide

## Dashboard Won't Start

If you see `ERR_CONNECTION_REFUSED` on `localhost:8501`:

### Quick Fix
```bash
# Run directly with streamlit
streamlit run transmission/dashboard/main.py --server.port=8501
```

### Check if Port is in Use
```powershell
netstat -ano | findstr :8501
```

If something is using the port, either:
1. Kill the process using that port
2. Use a different port: `--server.port=8502`

### Verify Streamlit Installation
```bash
python -c "import streamlit; print(streamlit.__version__)"
```

### Check Python Path
Make sure you're in the project root when running:
```bash
python startup/run_dashboard.py
```

## API Won't Start

### Check Port 8000
```powershell
netstat -ano | findstr :8000
```

### Verify Dependencies
```bash
python -c "from transmission.api.main import app; print('OK')"
```

### Check Database
The API needs to initialize the database. Make sure:
- SQLite can create files in the project directory
- No permission issues

## Both Services Running But Can't Connect

### Check Firewall
Windows Firewall might be blocking localhost connections.

### Verify Services Are Actually Running
```powershell
# Check API
Test-NetConnection -ComputerName localhost -Port 8000

# Check Dashboard
Test-NetConnection -ComputerName localhost -Port 8501
```

### Check Logs
Look at the terminal output where you started the services for error messages.

## Common Issues

### "ModuleNotFoundError: No module named 'transmission'"
**Solution:** Make sure you're running from project root and virtual environment is activated:
```powershell
.\.venv\Scripts\Activate.ps1
python startup/run_api.py
```

### "Port already in use"
**Solution:** Either kill the process using the port or change the port in the startup script.

### "Database locked"
**Solution:** Close any other processes accessing the database file, or delete the database file to recreate it.

### Dashboard Shows "Connection Error"
**Solution:** Make sure the API is running first, then start the dashboard.

