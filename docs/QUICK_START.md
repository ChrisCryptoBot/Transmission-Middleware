# Transmission™ Quick Start Guide

## 🚀 How to View & Use the Backend

### Step 1: Start the API Server

**Terminal 1:**
```bash
python startup/run_api.py
```

**Or manually:**
```bash
uvicorn transmission.api.main:app --reload --host 0.0.0.0 --port 8000
```

**You should see:**
```
Starting Transmission™ API Server...
API will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs
WebSocket at: ws://localhost:8000/ws
```

### Step 2: Access the Backend

#### **API Documentation (Swagger UI)**
Open in browser:
```
http://localhost:8000/docs
```
- Interactive API documentation
- Test endpoints directly
- See all available routes

#### **Alternative API Docs (ReDoc)**
```
http://localhost:8000/redoc
```
- Cleaner documentation view
- Better for reading

#### **API Root**
```
http://localhost:8000/
```
- Basic API info
- Endpoint list

#### **Health Check**
```
http://localhost:8000/api/system/health
```
- System health status
- Database connection check

### Step 3: Start the Dashboard

**Terminal 2:**
```bash
python startup/run_dashboard.py
```

**Or manually:**
```bash
streamlit run transmission/dashboard/main.py --server.port 8501
```

**You should see:**
```
Starting Transmission™ Dashboard...
Dashboard will be available at: http://localhost:8501
```

### Step 4: Access the Dashboard

Open in browser:
```
http://localhost:8501
```

**Dashboard Features:**
- System status monitoring
- Regime indicator
- Risk status
- Performance metrics
- Recent trades
- P&L charts
- **Flatten All / Kill Switch** button
- **Open Orders** table
- **Active Positions** table

---

## 📍 Key Endpoints

### System Status
- `GET http://localhost:8000/api/system/status` - System status
- `GET http://localhost:8000/api/system/risk` - Risk status
- `GET http://localhost:8000/api/system/health` - Health check

### Trading
- `GET http://localhost:8000/api/trades` - Trade history
- `GET http://localhost:8000/api/trades/recent/20` - Recent trades
- `GET http://localhost:8000/api/metrics` - Performance metrics

### Execution
- `POST http://localhost:8000/api/system/flatten_all` - Flatten all positions
- `GET http://localhost:8000/api/system/orders` - Open orders
- `GET http://localhost:8000/api/system/positions` - Active positions

### WebSocket
- `ws://localhost:8000/ws` - Real-time updates

---

## 🧪 Quick Test

### Test API Health
```bash
curl http://localhost:8000/api/system/health
```

### Test System Status
```bash
curl http://localhost:8000/api/system/status
```

### Test Flatten All (from command line)
```bash
curl -X POST http://localhost:8000/api/system/flatten_all \
  -H "Content-Type: application/json" \
  -d '{"reason": "test"}'
```

---

## 🔧 Troubleshooting

### Port Already in Use
If port 8000 is taken:
```bash
# Change port in run_api.py or use:
uvicorn transmission.api.main:app --port 8001
```

If port 8501 is taken:
```bash
# Change port in run_dashboard.py or use:
streamlit run transmission/dashboard/main.py --server.port 8502
```

### API Not Responding
1. Check if API is running: `curl http://localhost:8000/api/system/health`
2. Check logs in terminal
3. Verify database is accessible
4. Check firewall settings

### Dashboard Can't Connect to API
1. Verify API is running on port 8000
2. Check API URL in dashboard sidebar (default: `http://localhost:8000`)
3. Verify CORS is enabled in API

---

## 📊 What You'll See

### API Docs (`/docs`)
- **GET /api/system/status** - Current system state
- **GET /api/system/risk** - Risk limits and P&L
- **GET /api/trades** - Trade history
- **GET /api/metrics** - Performance metrics
- **POST /api/system/flatten_all** - Emergency stop
- **GET /api/system/orders** - Open orders
- **GET /api/system/positions** - Active positions

### Dashboard (`http://localhost:8501`)
- **System Status** - Current state, regime, strategy
- **Risk Status** - Daily/weekly P&L, current $R
- **Performance Metrics** - PF, E[R], Win Rate
- **Recent Trades** - Trade history table
- **P&L Chart** - Cumulative performance
- **Emergency Controls** - Flatten All button
- **Open Orders** - Active orders table
- **Positions** - Current positions table

---

## 🎯 Next Steps

1. **Start API**: `python startup/run_api.py`
2. **Start Dashboard**: `python startup/run_dashboard.py` (in another terminal)
3. **Open Dashboard**: `http://localhost:8501`
4. **View API Docs**: `http://localhost:8000/docs`
5. **Test Endpoints**: Use Swagger UI or curl

---

**Status: ✅ Ready to View**

