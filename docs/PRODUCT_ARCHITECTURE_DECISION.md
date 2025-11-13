# Product Architecture Decision

**Date:** 2025-11-13
**Status:** ✅ **RECOMMENDED** - Multi-Interface Middleware Platform
**Context:** MVP complete (100% Blueprint compliance), determining best product delivery model

---

## Executive Summary

**Decision: Build Transmission as a MIDDLEWARE PLATFORM with multiple interfaces, not a single-purpose dashboard or plugin.**

**Rationale:**
- **Dashboard-only** = Limits reach to users willing to switch platforms
- **Plugin-only** = Platform-dependent risk, fragmented codebase
- **SDK-only** = Excludes non-technical users
- **✅ Middleware + Multi-Interface** = Reaches all segments, maximizes market penetration

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│              TRANSMISSION CORE MIDDLEWARE                     │
│  • Regime Classifier  • Risk Governor  • Execution Engine    │
│  • Multi-TF Fusion    • Mental Governor • News Flat          │
│  • In-Trade Manager   • Journal Analytics                    │
└───────────────────────────┬──────────────────────────────────┘
                            │
                 ┌──────────┴──────────┐
                 │   FastAPI Backend   │ ✅ IMPLEMENTED
                 │  REST + WebSocket   │
                 └──────────┬──────────┘
                            │
         ┌──────────────────┼──────────────────┬────────────┐
         │                  │                  │            │
    ┌────▼─────┐      ┌─────▼──────┐    ┌─────▼────┐  ┌────▼─────┐
    │  React   │      │ Streamlit  │    │ Webhooks │  │   SDK    │
    │   Web    │      │ Dashboard  │    │  Plugin  │  │  (API)   │
    │   App    │      │  (Ops/QA)  │    │  System  │  │          │
    └──────────┘      └────────────┘    └──────────┘  └──────────┘
        ✅                 ✅               📅 Phase 2    📅 Phase 3

   Primary UI         Internal Ops      Integration      Developer
   for traders        monitoring        adapters         access
```

---

## Decision Matrix

| Architecture Model | Market Reach | Time to Market | Revenue Potential | Risk | Verdict |
|-------------------|--------------|----------------|-------------------|------|---------|
| **Dashboard Only** | 🟡 Medium (direct users only) | 🟢 Fast (2-3 months) | 🟡 Medium ($99/mo SaaS) | 🟢 Low | ❌ Too limiting |
| **Plugin Only** | 🟢 High (existing platform users) | 🔴 Slow (6+ months) | 🟡 Medium (platform-dependent) | 🔴 High (fragmentation) | ❌ Risky |
| **SDK Only** | 🔴 Low (developers only) | 🟢 Fast (1-2 months) | 🔴 Low (niche market) | 🟢 Low | ❌ Too niche |
| **✅ Hybrid Platform** | 🟢 High (all segments) | 🟡 Medium (3-6 months phased) | 🟢 High (multi-tier pricing) | 🟡 Medium | ✅ **BEST** |

---

## Phased Implementation Roadmap

### **Phase 1: Standalone Web App (MVP - Current)**
**Timeline:** ✅ COMPLETE
**Status:** 100% Blueprint compliance achieved

**Components:**
- ✅ FastAPI backend (REST + WebSocket)
- ✅ React 18 frontend (TypeScript + Vite)
- ✅ Streamlit dashboard (Ops/QA)
- ✅ SQLite database (MVP)
- ✅ All Tier-1 & Tier-2 modules implemented

**Target Users:**
- Beta testers (10-20 funded traders)
- Early adopters willing to run locally/self-hosted
- Proof-of-concept customers

**Deployment:**
```bash
# User runs locally
python startup/run_api.py        # Backend on :8000
npm run dev (in web/)            # Frontend on :5173
python startup/run_dashboard.py # Ops dashboard on :8501
```

**Revenue Model:**
- Free during beta
- $99-199/month once proven

---

### **Phase 2: Webhook Integration Layer (Months 4-6)**
**Timeline:** 📅 Q1 2025
**Priority:** ⚠️ HIGH (unlocks existing platform users)

**Objective:** Allow users to keep their existing workflow (TradingView, MT5, etc.) while Transmission adds the intelligence layer.

**Implementation:**

1. **TradingView Webhook Adapter**
```python
# transmission/api/routes/webhooks.py
from transmission.adapters.tradingview import TradingViewAdapter

@app.post("/api/v1/webhooks/tradingview")
async def tradingview_webhook(
    alert: dict,
    api_key: str = Depends(validate_api_key),
    user_id: str = Depends(get_user_from_key)
):
    """
    TradingView sends:
    {
      "ticker": "ES",
      "action": "buy",
      "price": 4500,
      "strategy": "VWAP Pullback"
    }

    Transmission processes through:
    - Regime check (is market in TREND?)
    - Risk check (within daily limits?)
    - Multi-TF confirmation
    - Execution guard (liquidity ok?)
    """
    adapter = TradingViewAdapter()
    signal = adapter.parse(alert)

    orchestrator = get_orchestrator_for_user(user_id)
    result = await orchestrator.process_signal(signal)

    return {"status": result.status, "reason": result.reason}
```

2. **MetaTrader 5 Adapter**
```python
# transmission/api/routes/webhooks.py
@app.post("/api/v1/webhooks/mt5")
async def mt5_webhook(signal: MT5Signal, user: User = Depends(auth)):
    adapter = MT5Adapter()
    return await process_via_transmission(adapter.parse(signal), user)
```

3. **Generic Signal Adapter**
```python
# transmission/adapters/base.py
class SignalAdapter(ABC):
    """Base class for converting external signals → Transmission format"""

    @abstractmethod
    def parse(self, raw_signal: dict) -> Signal:
        """Convert platform-specific format → Transmission Signal"""
        pass

    def validate(self, signal: Signal) -> bool:
        """Ensure signal has required fields"""
        return signal.symbol and signal.side and signal.quantity

# transmission/adapters/tradingview.py
class TradingViewAdapter(SignalAdapter):
    def parse(self, alert: dict) -> Signal:
        return Signal(
            symbol=alert["ticker"],
            side="LONG" if alert["action"] == "buy" else "SHORT",
            quantity=alert.get("contracts", 1),
            strategy_name=alert.get("strategy", "TradingView"),
            timestamp=datetime.utcnow()
        )
```

**User Experience:**
```javascript
// In TradingView Pine Script
strategy.entry("Buy", strategy.long, when=entry_condition,
    alert_message='{
        "ticker": "{{ticker}}",
        "action": "buy",
        "price": {{close}},
        "strategy": "VWAP Pullback"
    }'
)

// Alert webhook URL
https://transmission.yourapp.com/api/v1/webhooks/tradingview?key=USER_API_KEY
```

**Benefits:**
- Users DON'T leave TradingView/MT5
- Transmission adds intelligence layer invisibly
- Expands market to existing platform users (HUGE TAM)

**Revenue Impact:**
- Unlocks TradingView Premium users (5M+ users)
- Unlocks MT5 users (millions globally)
- Plugin tier: $49-99/month (lower than standalone)

---

### **Phase 3: SDK for Developers (Months 7-12)**
**Timeline:** 📅 Q2-Q3 2025
**Priority:** 🟡 MEDIUM (enables enterprise/custom integrations)

**Objective:** Allow strategy developers, hedge funds, CTAs to integrate Transmission into their own systems.

**Implementation:**

1. **Python SDK**
```python
# transmission-sdk (separate PyPI package)
from transmission import TransmissionClient

client = TransmissionClient(
    api_key="sk_live_...",
    endpoint="https://api.transmission.com"
)

# Process a signal
signal = {
    "symbol": "ES",
    "side": "LONG",
    "quantity": 2,
    "strategy": "Custom Mean Reversion"
}

result = await client.process_signal(signal)
if result.approved:
    print(f"✅ Signal approved: {result.reason}")
    print(f"   Adjusted size: {result.adjusted_quantity}")
else:
    print(f"❌ Signal rejected: {result.reason}")

# Query analytics
pnl = await client.get_daily_pnl()
regime = await client.get_current_regime("ES")
```

2. **REST API (Already Exists ✅)**
```bash
# Direct API access
curl -X POST https://api.transmission.com/v1/signals \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "ES",
    "side": "LONG",
    "quantity": 2,
    "strategy": "VWAP Pullback"
  }'
```

3. **WebSocket Streaming**
```python
# Real-time regime updates
async with client.stream_regime("ES") as stream:
    async for regime_update in stream:
        print(f"Regime changed: {regime_update.regime}")
        # Adjust strategy accordingly
```

**Target Users:**
- Strategy developers (build on top of Transmission)
- Small hedge funds/CTAs
- Proprietary trading firms
- Platform builders

**Revenue Model:**
- Enterprise tier: $299-999/month
- API usage-based pricing (per signal processed)
- White-label: $5k+/month

---

## Product Tier Architecture Mapping

### **Free Tier (Open Source Core)**
**Architecture:**
```
┌──────────────────────┐
│  transmission/ core  │ ← Open source on GitHub
└──────────┬───────────┘
           │
      ┌────▼────┐
      │ CLI     │ ← Run locally via Python
      └─────────┘
```

**What's included:**
- Core middleware logic (regime, risk, execution)
- Plugin SDK (BaseStrategy interface)
- YAML configuration
- SQLite database
- Self-hosted only

**What's missing:**
- No cloud hosting
- No web dashboard
- No webhook support
- Community support only

**Revenue Impact:** Lead generation, community building

---

### **Pro Tier ($99-199/month)**
**Architecture:**
```
┌────────────────────────┐
│ Cloud-hosted backend   │ ← We run FastAPI
└──────────┬─────────────┘
           │
    ┌──────┴────────┐
    │               │
┌───▼────┐     ┌────▼────┐
│ React  │     │Webhooks │
│  Web   │     │(TV/MT5) │
└────────┘     └─────────┘
```

**What's included:**
- ✅ Full web dashboard (React frontend)
- ✅ Cloud-hosted execution (we run it)
- ✅ Webhook support (TradingView, MT5)
- ✅ Multi-account support (3+ prop firm accounts)
- ✅ Advanced analytics (PF, E[R], drawdown)
- ✅ Priority support

**Target Users:**
- Funded prop traders
- Serious retail traders
- Strategy developers

**Revenue Model:**
- $99/month: 1 account, 100 signals/day
- $149/month: 3 accounts, 500 signals/day
- $199/month: 10 accounts, unlimited signals

---

### **Enterprise Tier ($499-5k+/month)**
**Architecture:**
```
┌─────────────────────────────┐
│ White-label deployment      │ ← Custom branding
│ (your-brand.transmission.ai)│
└──────────┬──────────────────┘
           │
    ┌──────┴────────┬────────────┐
    │               │            │
┌───▼────┐     ┌────▼────┐  ┌───▼────┐
│Custom  │     │  SDK    │  │Private │
│  UI    │     │ Access  │  │  API   │
└────────┘     └─────────┘  └────────┘
```

**What's included:**
- ✅ All Pro features
- ✅ White-label dashboard (custom branding)
- ✅ SDK access (Python + REST)
- ✅ Private deployment (dedicated infrastructure)
- ✅ Custom engine development
- ✅ Dedicated support (Slack channel)
- ✅ Multi-broker support (live API keys)

**Target Users:**
- Strategy sellers (white-label for clients)
- Small hedge funds/CTAs
- Proprietary trading firms
- Platform builders

**Revenue Model:**
- $499/month: SDK access, shared infrastructure
- $999/month: White-label, dedicated resources
- $5k+/month: Custom development, SLA, dedicated support

---

## Technical Architecture Recommendations

### **1. Multi-Tenancy Design**

**Current State:** Single-user orchestrator
**Required:** User-isolated state management

```python
# transmission/orchestrator/manager.py
class OrchestratorManager:
    """Manages multiple orchestrators (one per user)"""

    def __init__(self):
        self._orchestrators: Dict[str, TransmissionOrchestrator] = {}
        self._lock = asyncio.Lock()

    async def get_orchestrator(self, user_id: str) -> TransmissionOrchestrator:
        """Get or create orchestrator for user"""
        async with self._lock:
            if user_id not in self._orchestrators:
                config = await self._load_user_config(user_id)
                self._orchestrators[user_id] = TransmissionOrchestrator(config)
            return self._orchestrators[user_id]

    async def _load_user_config(self, user_id: str) -> Config:
        """Load user-specific configuration from DB"""
        # Each user has their own:
        # - Risk limits (-2R day, -5R week)
        # - Strategy preferences
        # - Broker connections
        # - Prop firm rules
        pass

# transmission/api/dependencies.py
async def get_current_user(api_key: str = Header(...)) -> User:
    """Validate API key and return user"""
    user = await db.get_user_by_api_key(api_key)
    if not user:
        raise HTTPException(401, "Invalid API key")
    return user

# transmission/api/routes/signals.py
@app.post("/api/v1/signals")
async def process_signal(
    signal: SignalInput,
    user: User = Depends(get_current_user),
    manager: OrchestratorManager = Depends(get_manager)
):
    """Each user has isolated orchestrator instance"""
    orchestrator = await manager.get_orchestrator(user.id)
    return await orchestrator.process_signal(signal)
```

**Benefits:**
- Scales to thousands of users on single server
- User data isolation (security/privacy)
- Per-user configuration
- Independent state management

---

### **2. Signal Adapter Abstraction**

**Purpose:** Accept signals from ANY source, normalize to Transmission format

```python
# transmission/adapters/__init__.py
from .base import SignalAdapter
from .tradingview import TradingViewAdapter
from .mt5 import MT5Adapter
from .manual import ManualSignalAdapter

ADAPTERS = {
    "tradingview": TradingViewAdapter,
    "mt5": MT5Adapter,
    "manual": ManualSignalAdapter,
}

# transmission/models/signal.py
@dataclass
class Signal:
    """Universal signal format (platform-agnostic)"""
    symbol: str              # "ES", "NQ", "AAPL"
    side: Literal["LONG", "SHORT"]
    quantity: int            # Number of contracts/shares
    strategy_name: str       # Which strategy generated this
    timestamp: datetime
    source: str              # "tradingview", "mt5", "manual"
    metadata: dict           # Platform-specific extras

# transmission/api/routes/signals.py
@app.post("/api/v1/signals/{adapter_type}")
async def process_external_signal(
    adapter_type: str,
    raw_signal: dict,
    user: User = Depends(auth)
):
    """Route signal through appropriate adapter"""
    if adapter_type not in ADAPTERS:
        raise HTTPException(400, f"Unknown adapter: {adapter_type}")

    adapter = ADAPTERS[adapter_type]()
    signal = adapter.parse(raw_signal)

    orchestrator = await get_orchestrator_for_user(user.id)
    return await orchestrator.process_signal(signal)
```

---

### **3. Database Schema for Multi-User**

**Current:** Single SQLite file
**Needed:** User-scoped tables

```sql
-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    api_key TEXT UNIQUE NOT NULL,
    tier TEXT CHECK(tier IN ('free', 'pro', 'enterprise')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User configs (per-user risk limits, strategies)
CREATE TABLE user_configs (
    user_id TEXT PRIMARY KEY REFERENCES users(id),
    daily_loss_limit REAL DEFAULT -500.0,  -- -2R in dollars
    weekly_loss_limit REAL DEFAULT -1250.0, -- -5R in dollars
    max_position_size INT DEFAULT 2,
    strategies_enabled TEXT,  -- JSON array of strategy names
    broker_config TEXT        -- JSON broker settings
);

-- Trades (user-scoped)
CREATE TABLE trades (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),  -- ← KEY: User isolation
    symbol TEXT NOT NULL,
    -- ... existing trade fields ...
    INDEX idx_user_trades (user_id, timestamp)
);

-- API keys (support multiple keys per user)
CREATE TABLE api_keys (
    key TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    name TEXT,  -- "Production", "Testing", etc.
    scopes TEXT,  -- JSON array of permissions
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Deployment Architecture

### **MVP (Phase 1):** Self-Hosted
```
User's Machine:
┌─────────────────────────┐
│  Docker Compose         │
│  ├─ FastAPI (port 8000) │
│  ├─ React (port 5173)   │
│  └─ SQLite (volume)     │
└─────────────────────────┘
```

### **Pro Tier (Phase 2):** Cloud Hosted (Multi-Tenant)
```
Cloud (AWS/GCP/DO):
┌──────────────────────────────┐
│  Load Balancer               │
└────────┬─────────────────────┘
         │
    ┌────▼────┐
    │ FastAPI │ (Gunicorn + Uvicorn workers)
    │ (3 pods)│
    └────┬────┘
         │
    ┌────▼────────┐
    │ PostgreSQL  │ (managed DB)
    │ + TimescaleDB│
    └─────────────┘

CDN:
┌──────────────┐
│ React Build  │ (Vercel/Cloudflare)
└──────────────┘
```

### **Enterprise (Phase 3):** Private Deployment
```
Client's VPC:
┌─────────────────────────────┐
│  Kubernetes Cluster         │
│  ├─ transmission-api (pods) │
│  ├─ postgresql (stateful)   │
│  └─ redis (caching)         │
└─────────────────────────────┘
```

---

## Migration Path (Current MVP → Multi-User SaaS)

### **Step 1: API Key Authentication**
```python
# transmission/api/middleware.py
@app.middleware("http")
async def require_api_key(request: Request, call_next):
    if request.url.path.startswith("/api/v1/"):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse({"error": "Missing API key"}, 401)

        user = await validate_api_key(api_key)
        if not user:
            return JSONResponse({"error": "Invalid API key"}, 401)

        request.state.user = user  # Attach to request

    return await call_next(request)
```

### **Step 2: User-Scoped Orchestrators**
```python
# transmission/orchestrator/manager.py (created above)
# Replace global orchestrator with per-user instances
```

### **Step 3: Database Migration**
```sql
-- Add user_id to existing tables
ALTER TABLE trades ADD COLUMN user_id TEXT;
ALTER TABLE positions ADD COLUMN user_id TEXT;
ALTER TABLE performance_metrics ADD COLUMN user_id TEXT;

-- Migrate existing data to default user
UPDATE trades SET user_id = 'default_user';
```

### **Step 4: Webhook Endpoints**
```python
# transmission/api/routes/webhooks.py (created in Phase 2)
# Add TradingView, MT5 adapters
```

---

## Revenue Projection (3-Tier Model)

| Tier | Price/Month | Target Users (Year 1) | Annual Revenue |
|------|-------------|------------------------|----------------|
| Free (Open Source) | $0 | 1,000 users | $0 (lead gen) |
| Pro | $149 | 100 users | $178,800 |
| Enterprise | $999 | 5 users | $59,940 |
| **TOTAL** | - | **1,105 users** | **$238,740** |

**Assumptions:**
- 10% conversion from Free → Pro
- 5% conversion from Pro → Enterprise
- Year 1 goals (conservative)

---

## Competitive Positioning

| Product | Model | Price | Transmission Advantage |
|---------|-------|-------|------------------------|
| **QuantConnect** | Cloud platform | $0-$200/mo | ✅ We're adaptive, they're static |
| **TradingView Premium** | Charting + alerts | $15-60/mo | ✅ We execute + manage risk, they just alert |
| **MetaTrader EAs** | Desktop plugins | $50-500 one-time | ✅ We're regime-aware, they're dumb bots |
| **3Commas** | Crypto bots | $99/mo | ✅ We handle futures, multi-TF, prop rules |
| **Hedge Fund Tools** | Enterprise software | $50k+/year | ✅ We're 1/100th the cost for retail/small firms |

**Your Moat:**
- Only platform with **regime-adaptive** signal processing
- Only platform with **prop firm compliance** baked in
- Only platform with **multi-timeframe fusion** for entries
- Only platform with **mental state protection**

---

## Success Metrics

### **Phase 1 (MVP):** ✅ COMPLETE
- [x] System runs without crashing
- [x] All Tier-1 & Tier-2 modules implemented
- [x] Dashboard shows live status
- [x] 100% Blueprint compliance

### **Phase 2 (Webhook Integration):** Target Q1 2025
- [ ] TradingView webhook processes 100+ signals/day
- [ ] MT5 adapter live with 5+ beta users
- [ ] 50% of new signups use webhook (not standalone)
- [ ] Churn rate < 10%/month

### **Phase 3 (SDK Launch):** Target Q2 2025
- [ ] SDK published to PyPI
- [ ] 5+ enterprise customers using API
- [ ] 100k+ API calls/month processed
- [ ] Enterprise tier revenue > $5k/month

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Platform dependency (TV/MT5)** | High | Medium | Build abstraction layer, support multiple sources |
| **Scaling costs (cloud hosting)** | Medium | High | Start with serverless, optimize before scaling |
| **Competitive response** | High | Low | Move fast, build moat via regime intelligence |
| **User data security** | Critical | Low | Multi-tenancy isolation, encryption, SOC2 compliance |
| **Broker API reliability** | Medium | Medium | Fallback brokers, retry logic, monitoring |

---

## Conclusion & Recommendation

### **✅ BUILD AS: Multi-Interface Middleware Platform**

**Rationale:**
1. **Maximum Market Reach** - Dashboard (direct users) + Webhooks (platform users) + SDK (developers)
2. **Revenue Diversification** - Free (lead gen) → Pro (SaaS) → Enterprise (custom)
3. **Competitive Moat** - Only adaptive middleware with prop-firm compliance
4. **Phased Risk** - Ship dashboard first (MVP), expand to webhooks/SDK later

**Next Immediate Actions:**
1. ✅ Harden current MVP (production-ready FastAPI + React)
2. 📅 Design multi-tenancy architecture (user isolation, API keys)
3. 📅 Build TradingView webhook adapter (unlocks 5M+ users)
4. 📅 Launch Pro tier beta (10-20 paying customers)

**Timeline:**
- **Now - Month 3:** Production harden MVP, launch beta
- **Month 4-6:** Webhook integration (TradingView, MT5)
- **Month 7-12:** SDK launch, enterprise tier

---

## Additional Resources

- **Blueprint:** [Product_Concept.txt](../BLUEPRINTS/Product_Concept.txt)
- **Tech Stack:** [Tech_Stack_Concept.txt](../BLUEPRINTS/Tech_Stack_Concept.txt)
- **Market Positioning:** [Product_Package_Concept.txt](../BLUEPRINTS/Product_Package_Concept.txt)
- **Implementation Status:** [BLUEPRINT_ADHERENCE_REPORT.md](./BLUEPRINT_ADHERENCE_REPORT.md)

---

**Decision Owner:** Chris - Superior One Logistics
**Last Updated:** 2025-11-13
**Status:** ✅ Approved for implementation
