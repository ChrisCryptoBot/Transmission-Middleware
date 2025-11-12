# Startup Scripts

This folder contains startup scripts for running the Transmission™ system.

## Scripts

### `run_api.py`
Starts the FastAPI backend server.

**Usage:**
```bash
python startup/run_api.py
```

**Access:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws

### `run_dashboard.py`
Starts the Streamlit dashboard.

**Usage:**
```bash
python startup/run_dashboard.py
```

**Access:**
- Dashboard: http://localhost:8501

## Quick Start

1. **Activate virtual environment:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. **Start API (Terminal A):**
   ```bash
   python startup/run_api.py
   ```

3. **Start Dashboard (Terminal B):**
   ```bash
   python startup/run_dashboard.py
   ```

4. **Access:**
   - API Docs: http://localhost:8000/docs
   - Dashboard: http://localhost:8501

## Notes

- Make sure the API is running before starting the dashboard
- Both services run in the foreground (use separate terminals)
- Press `Ctrl+C` to stop either service

