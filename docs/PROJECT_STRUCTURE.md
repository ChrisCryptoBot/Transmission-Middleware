# Project Structure

## 📁 Directory Organization

```
QUANT_TRADING_TRANSMISSION/
├── startup/                    # Startup scripts
│   ├── run_api.py            # Start API server
│   ├── run_dashboard.py      # Start dashboard
│   └── README.md             # Startup instructions
│
├── docs/                      # Documentation
│   ├── QUICK_START.md        # Quick start guide
│   ├── BUILD_PLAN.md         # Build plan
│   ├── COMPREHENSIVE_REVIEW.md
│   ├── PRE_BUILD_CHECKLIST.md
│   ├── architecture.md        # Architecture docs
│   ├── api_contracts.md       # API documentation
│   ├── testing_strategy.md    # Testing approach
│   └── status/               # Status documentation
│       ├── BACKEND_*.md
│       ├── DATABASE_*.md
│       └── ...
│
├── transmission/              # Main application code
│   ├── api/                  # FastAPI backend
│   ├── dashboard/            # Streamlit dashboard
│   ├── telemetry/           # Market data processing
│   ├── regime/              # Regime classification
│   ├── risk/                # Risk management
│   ├── strategies/          # Trading strategies
│   ├── execution/           # Execution engine
│   ├── orchestrator/        # Main orchestrator
│   ├── database/            # Database layer
│   ├── config/              # Configuration files
│   └── tests/               # Test suite
│
├── BLUEPRINTS/              # Original concept documents
│
└── README.md                # Main project README
```

## 🚀 Quick Start

From the project root:

```bash
# Terminal A: Start API
python startup/run_api.py

# Terminal B: Start Dashboard
python startup/run_dashboard.py
```

## 📝 Documentation Locations

- **Quick Start**: `docs/QUICK_START.md`
- **Build Plan**: `docs/BUILD_PLAN.md`
- **Status Updates**: `docs/status/`
- **Architecture**: `docs/architecture.md`
- **API Contracts**: `docs/api_contracts.md`

## 🎯 Key Directories

- **`startup/`** - All startup scripts in one place
- **`docs/`** - All documentation organized by type
- **`transmission/`** - Main application code
- **`BLUEPRINTS/`** - Original concept documents

