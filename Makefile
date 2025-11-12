# Transmission™ Makefile
# Convenience commands for development

.PHONY: api dash dev test help

help:
	@echo "Transmission™ Development Commands:"
	@echo ""
	@echo "  make api      - Start API server"
	@echo "  make dash     - Start dashboard"
	@echo "  make dev      - Start both (API in background)"
	@echo "  make test     - Run test suite"
	@echo "  make help     - Show this help"

api:
	@echo "🚀 Starting API Server..."
	python startup/run_api.py

dash:
	@echo "📊 Starting Dashboard..."
	python startup/run_dashboard.py

dev:
	@echo "🚀 Starting both services..."
	@echo "API will run in background, Dashboard in foreground"
	@python startup/run_api.py & python startup/run_dashboard.py

test:
	@echo "🧪 Running tests..."
	pytest transmission/tests/ -v

