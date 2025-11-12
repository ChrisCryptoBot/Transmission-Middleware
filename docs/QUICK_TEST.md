# Quick API Test Guide

## ✅ Verified Working

**API Server:** Running on `http://localhost:8000`
**Title:** Beyond Candlesticks ✅
**Version:** 0.1.0

## 🧪 Test Endpoints in Swagger UI

Open `http://localhost:8000/docs` and test these:

### 1. Root Endpoint
- **GET** `/` 
- Should return API info and available endpoints

### 2. System Status
- **GET** `/api/system/status`
- Returns orchestrator state, regime, risk status

### 3. Health Check  
- **GET** `/api/system/health`
- Returns `{"status": "ok"}`

### 4. Flatten All (Kill Switch)
- **POST** `/api/system/flatten_all`
- Body: `{"reason": "test"}`
- Should return success and broadcast WebSocket event

### 5. Get Trades
- **GET** `/api/trades`
- Returns trade history

### 6. Get Recent Trades
- **GET** `/api/trades/recent/{limit}`
- Example: `/api/trades/recent/10`

### 7. Get Metrics
- **GET** `/api/metrics`
- Returns performance metrics

## 📊 Dashboard Test

1. Open `http://localhost:8501`
2. Check "API Connected" indicator
3. Click "Flatten All" button
4. Verify "Open Orders" and "Positions" tables

## 🔄 Next: Complete E2E Tests

See `NEXT_STEPS.md` for full roadmap.

