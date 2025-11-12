# Quick Start - Frontend

## Prerequisites

- Node.js 18+ installed
- Backend API running at `http://localhost:8000`

## Setup (One-Time)

### Option 1: PowerShell Script (Windows)

```powershell
.\startup\setup_frontend.ps1
```

### Option 2: Manual

```bash
cd web
npm install
```

## Running the Frontend

### Option 1: PowerShell Script (Windows)

```powershell
.\startup\run_frontend.ps1
```

### Option 2: Manual

```bash
cd web
npm run dev
```

## Access

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## What You'll See

1. **Dashboard** - System status, risk metrics, orders, positions
2. **Trades** - Trade history with filters
3. **Real-time Updates** - WebSocket connection for live data
4. **Kill Switch** - Flatten all positions button

## Troubleshooting

### Port Already in Use

If port 5173 is in use, Vite will automatically use the next available port.

### CORS Errors

Make sure the backend is running and CORS is configured (default allows localhost:5173).

### WebSocket Connection Failed

- Verify backend is running
- Check WebSocket endpoint: `ws://localhost:8000/ws`
- Check browser console for errors

### Module Not Found

Run `npm install` again in the `web/` directory.

## Next Steps

- Add P&L charts
- Add metrics visualization
- Customize styling
- Add more features

