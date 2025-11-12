# File Organization Guide

## Directory Structure

### Root Level
- **`README.md`** - Main project documentation
- **`Makefile`** - Convenience commands for development
- **`Start-Transmission.ps1`** - PowerShell script to start services
- **`.gitignore`** - Git ignore rules
- **`.venv/`** - Virtual environment (ignored by git)

### `BLUEPRINTS/`
Original concept documents and planning materials:
- `Product_Concept.txt`
- `Tech_Stack_Concept.txt`
- `UI_Concept.txt`
- `Action_Sugg_1.txt`
- `Action_Sugg_2.txt`
- etc.

### `docs/`
All project documentation:
- **`status/`** - Status and progress documents
  - `STATUS.md` - Current system status
  - `BACKEND_READY.md` - Backend readiness confirmation
  - `SETUP_COMPLETE.md` - Setup completion status
  - etc.
- **Main Documentation:**
  - `BUILD_PLAN.md` - Development roadmap
  - `NEXT_STEPS.md` - Next development steps
  - `QUICK_START.md` - Quick start guide
  - `QUICK_TEST.md` - Quick testing guide
  - `PROJECT_STRUCTURE.md` - Project structure documentation
  - `TROUBLESHOOTING.md` - Troubleshooting guide
  - `COMPREHENSIVE_REVIEW.md` - Initial review
  - `ARCHITECTURE.md` - System architecture
  - `API_CONTRACTS.md` - API documentation
  - `TESTING_STRATEGY.md` - Testing approach

### `startup/`
All startup and convenience scripts:
- `run_api.py` - Start FastAPI server
- `run_dashboard.py` - Start Streamlit dashboard
- `start_api.ps1` - PowerShell wrapper for API
- `README.md` - Startup instructions

### `transmission/`
Main application source code:
- **`api/`** - FastAPI application
  - `main.py` - FastAPI app initialization
  - `models/` - Pydantic models
  - `routes/` - API route handlers
  - `websocket.py` - WebSocket endpoint
- **`config/`** - Configuration files
  - `broker.yaml` - Broker settings
  - `constraints.yaml` - Constraint settings
  - `instruments.yaml` - Trading instruments
  - `news_calendar.yaml` - Economic calendar
  - `user_profile.yaml` - User profile template
  - `config_loader.py` - Config loader
- **`dashboard/`** - Streamlit dashboard
  - `main.py` - Dashboard application
- **`database/`** - Database layer
  - `schema.py` - Database schema
  - `export.py` - Data export utilities
- **`execution/`** - Execution engine
  - `adapter.py` - Broker adapter protocol
  - `engine.py` - Execution engine
  - `guard.py` - Execution guard
  - `mock_broker.py` - Mock broker implementation
  - `fillsim.py` - Fill simulator
- **`orchestrator/`** - Main orchestrator
  - `transmission.py` - Transmission orchestrator
- **`regime/`** - Market regime classification
  - `classifier.py` - Regime classifier
- **`risk/`** - Risk management
  - `governor.py` - Risk governor
  - `position_sizer.py` - Position sizing
  - `smart_constraints.py` - Smart constraints
  - `constraint_engine.py` - Constraint engine
- **`strategies/`** - Trading strategies
  - `base.py` - Base strategy interface
  - `vwap_pullback.py` - VWAP pullback strategy
- **`telemetry/`** - Market data processing
  - `market_data.py` - Market feature calculations
- **`tests/`** - Test suite
  - `test_e2e.py` - End-to-end tests
  - `test_orchestrator.py` - Orchestrator tests
  - `test_telemetry.py` - Telemetry tests
  - etc.
- **`requirements.txt`** - Python dependencies
- **`data/`** - Data files (database, etc.)

## File Naming Conventions

- **Python modules**: `snake_case.py`
- **Documentation**: `UPPER_SNAKE_CASE.md` or `Title_Case.md`
- **Config files**: `snake_case.yaml`
- **Test files**: `test_*.py`

## Ignored Files (`.gitignore`)

- `__pycache__/` - Python cache directories
- `.venv/` - Virtual environment
- `*.db` - Database files
- `*.log` - Log files
- `.env` - Environment variables
- IDE-specific files (`.vscode/`, `.idea/`, etc.)

## Best Practices

1. **Keep root clean** - Only essential files at root level
2. **Documentation in `docs/`** - All docs organized by category
3. **Startup scripts in `startup/`** - All launcher scripts together
4. **Source code in `transmission/`** - All application code organized by module
5. **Tests mirror source** - Test structure matches source structure

