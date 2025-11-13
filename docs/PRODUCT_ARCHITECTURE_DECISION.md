# Product Architecture Decision

**Date:** 2024-12-19  
**Status:** ✅ **APPROVED** - Multi-Interface Middleware Platform  
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

## Architecture Strategy

```
┌─────────────────────────────────────────────────┐
│         TRANSMISSION CORE (Python)              │
│  (Regime AI, Risk Governor, Execution Engine)   │
└──────────────┬──────────────────────────────────┘
               │
       ┌───────┴───────┐
       │   REST API     │ (FastAPI - Already built ✅)
       │   WebSocket    │
       └───────┬───────┘
               │
    ┌──────────┼──────────┬──────────────┐
    │          │          │              │
┌───▼───┐  ┌──▼───┐  ┌───▼────┐   ┌────▼─────┐
│ React │  │Stream│  │ Webhook│   │   SDK    │
│ Web   │  │ lit  │  │Adapter │   │(Future)  │
│ App   │  │Dash  │  │(Future)│   │          │
└───────┘  └──────┘  └────────┘   └──────────┘
   ✅         ✅         📅            📅
```

---

## Why This Hybrid Approach Wins

| Architecture | Pros | Cons | Verdict |
|--------------|------|------|---------|
| Dashboard Only | Full control, beautiful UX | Users must leave their platform | ❌ Too limiting |
| Plugin Only | Users stay in their workflow | Platform-dependent, fragmented | ❌ Risky bet |
| SDK Only | Developers can integrate | Excludes non-technical users | ❌ Too niche |
| ✅ **Middleware + Multi-Interface** | Reaches all segments, flexible | More build effort | ✅ **BEST** |

---

## Go-To-Market Architecture (Phased)

### Phase 1: MVP (Current - ✅ Complete)

**Backend:** FastAPI (REST + WebSocket) ✅  
**Frontend:** React 18 (primary UI) ✅  
**Ops:** Streamlit (QA/monitoring) ✅

**This is CORRECT. Ship this first for:**
- Direct users (traders running it locally/cloud)
- Proof of concept
- Beta testers

**Status:** ✅ **100% Complete**

---

### Phase 2: Webhook Integration (Q1 2025)

**Build adapters for existing platforms:**

#### TradingView Webhook → Transmission
```python
@app.post("/webhook/tradingview")
async def tradingview_signal(signal: TradingViewAlert):
    return await transmission.process_signal(signal)
```

#### MetaTrader EA → Transmission
```python
@app.post("/webhook/mt5")
async def mt5_signal(signal: MT5Signal):
    return await transmission.process_signal(signal)
```

**Why this matters:**
- Traders already use TradingView/MT5
- Your middleware adds the "intelligence layer"
- They don't have to abandon their workflow
- **5M+ potential users** who already use TradingView

**Target:** Month 4-6 post-MVP

---

### Phase 3: SDK for Developers (Q2 2025)

```python
# transmission-sdk for Python
from transmission import TransmissionClient

client = TransmissionClient(api_key="...")
signal = {"symbol": "ES", "side": "long"}
result = await client.process(signal)
```

**Target:** Month 7+ post-MVP

---

## Product Tier Architecture

### Transmission Core (Free/Open Source)

**✅ Standalone CLI** - Run locally, configure via YAML  
**✅ Web Dashboard** - React frontend (basic)  
**❌ No cloud hosting** - Self-hosted only  
**❌ No webhooks** - Manual signal entry only

**Target Users:**
- Technical traders
- Developers
- Self-hosters

---

### Transmission Pro ($99-199/month)

**✅ Cloud-hosted** - You run the middleware, users connect  
**✅ Full Web Dashboard** - Advanced charts, analytics  
**✅ Webhook Support** - TradingView, MT5 integration  
**✅ Multi-account** - Manage multiple prop firm accounts  
**✅ API Access** - REST + WebSocket

**Target Users:**
- Prop firm traders
- Serious retail traders
- Strategy developers

**Revenue Model:**
- Subscription: $99-199/month
- Per-account pricing: +$29/month per additional account
- Webhook usage: Included (up to 1000 signals/month)

---

### Transmission Enterprise ($5k+/month)

**✅ White-label Dashboard** - Branded for strategy sellers  
**✅ SDK Access** - Python/REST API for custom integrations  
**✅ Custom Plugins** - Build your own connectors  
**✅ Dedicated Infrastructure** - Private deployment  
**✅ SLA** - 99.9% uptime guarantee  
**✅ Custom Development** - Strategy-specific adaptations

**Target Users:**
- Strategy sellers
- Small hedge funds
- CTAs (Commodity Trading Advisors)
- Prop firms (white-label)

**Revenue Model:**
- Base: $5,000/month
- Custom development: $150/hour
- White-label: +$2,000/month
- Dedicated infrastructure: +$3,000/month

---

## Critical Architectural Decisions

### ✅ DO THIS:

#### 1. Keep FastAPI as the Core

**All logic lives in `transmission/` modules**  
**API is the universal interface**  
**Multiple frontends connect to same backend**

**Current State:** ✅ Already implemented

#### 2. Build React Dashboard First

**Primary user interface for MVP**  
**Ship this for beta users**  
**Prove the value before expanding**

**Current State:** ✅ React 18 + TypeScript + Vite setup complete

#### 3. Design for Multi-Tenancy Now

```python
# transmission/api/routes.py
@app.post("/api/v1/signals", dependencies=[Depends(verify_api_key)])
async def process_signal(
    signal: Signal, 
    user_id: str = Depends(get_user_from_api_key)
):
    # Each user has isolated state
    orchestrator = get_orchestrator_for_user(user_id)
    return await orchestrator.process(signal)
```

**Action Required:** ⚠️ Not yet implemented

#### 4. Abstract the Signal Source

```python
# transmission/strategies/base.py
class SignalAdapter:
    """Convert ANY signal format → Transmission format"""
    
    @abstractmethod
    def parse(self, raw_signal: dict) -> Signal:
        pass

class TradingViewAdapter(SignalAdapter):
    def parse(self, alert: dict) -> Signal:
        return Signal(
            symbol=alert["ticker"],
            direction=alert["action"].upper(),
            entry_price=alert["close"],
            timestamp=datetime.fromtimestamp(alert["time"])
        )
```

**Action Required:** ⚠️ Not yet implemented

---

### ❌ DON'T DO THIS:

- ❌ **Don't build native desktop app** - Web + cloud is enough
- ❌ **Don't build mobile app yet** - Web responsive is sufficient
- ❌ **Don't build browser extension** - Overhead not worth it for MVP
- ❌ **Don't build platform-specific plugins first** - Webhooks are more flexible

---

## Multi-Tenancy Design

### User Isolation Strategy

**Each user gets:**
- Isolated orchestrator instance
- Separate database schema (or user_id filtering)
- Independent risk limits
- Own API keys

**Implementation Pattern:**
```python
# transmission/api/dependencies.py
from fastapi import Depends, HTTPException, Header
from transmission.orchestrator.transmission import TransmissionOrchestrator

# User orchestrator cache
user_orchestrators: Dict[str, TransmissionOrchestrator] = {}

def get_user_from_api_key(api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Validate API key and return user_id"""
    user_id = validate_api_key(api_key)
    if not user_id:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return user_id

def get_orchestrator_for_user(user_id: str) -> TransmissionOrchestrator:
    """Get or create orchestrator for user"""
    if user_id not in user_orchestrators:
        user_orchestrators[user_id] = TransmissionOrchestrator(
            db_path=f"data/user_{user_id}.db"
        )
    return user_orchestrators[user_id]
```

---

## Database Schema Updates

### Multi-User Support

**Current:** Single SQLite database  
**Future:** User-isolated databases or user_id filtering

**Option A: Separate Databases (Recommended for MVP)**
```python
# Each user gets their own database
db_path = f"data/user_{user_id}/transmission.db"
```

**Option B: Shared Database with user_id (Recommended for Scale)**
```sql
-- Add user_id to all tables
ALTER TABLE trades ADD COLUMN user_id TEXT NOT NULL;
CREATE INDEX idx_trades_user_id ON trades(user_id);

-- Filter all queries by user_id
SELECT * FROM trades WHERE user_id = ?;
```

**Migration Path:**
1. **MVP:** Separate databases (simpler, isolated)
2. **Scale:** Shared database with user_id (better for cloud)

---

## SignalAdapter Abstraction

### Platform-Agnostic Signal Processing

**File:** `transmission/strategies/signal_adapter.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from transmission.strategies.base import Signal

class SignalAdapter(ABC):
    """Convert platform-specific signals to Transmission format"""
    
    @abstractmethod
    def parse(self, raw_signal: Dict[str, Any]) -> Signal:
        """Parse platform signal → Transmission Signal"""
        pass
    
    @abstractmethod
    def validate(self, raw_signal: Dict[str, Any]) -> bool:
        """Validate signal format"""
        pass

class TradingViewAdapter(SignalAdapter):
    """TradingView webhook format"""
    
    def validate(self, raw_signal: Dict[str, Any]) -> bool:
        required = ["ticker", "action", "close", "time"]
        return all(k in raw_signal for k in required)
    
    def parse(self, alert: Dict[str, Any]) -> Signal:
        return Signal(
            symbol=alert["ticker"],
            direction="LONG" if alert["action"].upper() == "BUY" else "SHORT",
            entry_price=float(alert["close"]),
            timestamp=datetime.fromtimestamp(alert["time"]),
            strategy="TradingView",
            confidence=0.8,  # Default confidence
            notes=f"TradingView alert: {alert.get('message', '')}"
        )

class MT5Adapter(SignalAdapter):
    """MetaTrader 5 EA format"""
    
    def validate(self, raw_signal: Dict[str, Any]) -> bool:
        required = ["symbol", "type", "price"]
        return all(k in raw_signal for k in required)
    
    def parse(self, signal: Dict[str, Any]) -> Signal:
        return Signal(
            symbol=signal["symbol"],
            direction="LONG" if signal["type"] == 0 else "SHORT",
            entry_price=float(signal["price"]),
            timestamp=datetime.now(),
            strategy="MT5_EA",
            confidence=0.75,
            notes=f"MT5 EA: {signal.get('comment', '')}"
        )
```

---

## Webhook Integration Endpoints

### Phase 2 Implementation

**File:** `transmission/api/routes/webhooks.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Header
from transmission.strategies.signal_adapter import (
    TradingViewAdapter, 
    MT5Adapter,
    SignalAdapter
)
from transmission.api.dependencies import verify_api_key, get_orchestrator_for_user

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/tradingview")
async def tradingview_webhook(
    alert: dict,
    api_key: str = Header(..., alias="X-API-Key")
):
    """TradingView webhook endpoint"""
    user_id = verify_api_key(api_key)
    orchestrator = get_orchestrator_for_user(user_id)
    
    adapter = TradingViewAdapter()
    if not adapter.validate(alert):
        raise HTTPException(status_code=400, detail="Invalid TradingView alert format")
    
    signal = adapter.parse(alert)
    result = await orchestrator.process_signal(signal)
    
    return {
        "status": "processed",
        "signal_id": signal.id,
        "action": result.action,
        "reason": result.reason
    }

@router.post("/mt5")
async def mt5_webhook(
    signal: dict,
    api_key: str = Header(..., alias="X-API-Key")
):
    """MetaTrader 5 webhook endpoint"""
    user_id = verify_api_key(api_key)
    orchestrator = get_orchestrator_for_user(user_id)
    
    adapter = MT5Adapter()
    if not adapter.validate(signal):
        raise HTTPException(status_code=400, detail="Invalid MT5 signal format")
    
    transmission_signal = adapter.parse(signal)
    result = await orchestrator.process_signal(transmission_signal)
    
    return {
        "status": "processed",
        "signal_id": transmission_signal.id,
        "action": result.action,
        "reason": result.reason
    }
```

---

## Revenue Projections

### Conservative Year 1 Estimate

**Assumptions:**
- 10 beta users (Month 1-3) → 5 convert to Pro
- 50 Pro users by Month 6 ($99/month avg)
- 2 Enterprise customers by Month 9 ($5k/month)

**Revenue Breakdown:**

| Tier | Users | Price | Monthly | Annual |
|------|-------|-------|---------|--------|
| Pro | 50 | $99 | $4,950 | $59,400 |
| Enterprise | 2 | $5,000 | $10,000 | $120,000 |
| **Total** | **52** | - | **$14,950** | **$179,400** |

**Optimistic Scenario (Year 1):**
- 100 Pro users → $118,800/year
- 5 Enterprise → $300,000/year
- **Total: $418,800 ARR**

**Conservative Scenario (Year 1):**
- 30 Pro users → $35,640/year
- 1 Enterprise → $60,000/year
- **Total: $95,640 ARR**

**Target: $238k ARR Year 1** (realistic middle ground)

---

## Implementation Roadmap

### Immediate (Next 2 Weeks)

1. **Multi-Tenancy Foundation**
   - [ ] API key authentication middleware
   - [ ] User isolation in orchestrator
   - [ ] Database schema updates (user_id)
   - [ ] User management endpoints

2. **Production Hardening**
   - [ ] Idempotency (dedupe fills)
   - [ ] Crash recovery (reconcile on boot)
   - [ ] Retry logic with circuit breaker

### Short-Term (Month 1-2)

3. **Webhook Infrastructure**
   - [ ] SignalAdapter abstraction
   - [ ] TradingView webhook endpoint
   - [ ] MT5 webhook endpoint
   - [ ] Webhook documentation

4. **Frontend Enhancements**
   - [ ] Charts (PnL, drawdown, heatmaps)
   - [ ] Toast notifications
   - [ ] Mental state badge
   - [ ] News calendar view

### Medium-Term (Month 3-4)

5. **SDK Development**
   - [ ] Python SDK package
   - [ ] SDK documentation
   - [ ] Example integrations

6. **Cloud Infrastructure**
   - [ ] Multi-tenant database (PostgreSQL)
   - [ ] User onboarding flow
   - [ ] Billing integration

---

## Technical Specifications

### API Key Authentication

**Implementation:**
```python
# transmission/api/middleware.py
from fastapi import Request, HTTPException
from fastapi.security import APIKeyHeader
import os

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(request: Request, api_key: str = Depends(api_key_header)):
    """Verify API key and attach user_id to request"""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Validate against database or environment
    user_id = validate_api_key(api_key)
    if not user_id:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    request.state.user_id = user_id
    return user_id
```

**Storage:**
- **MVP:** Environment variables or simple database
- **Production:** Encrypted database with key rotation

---

### User Isolation Pattern

**Orchestrator Per User:**
```python
# transmission/api/dependencies.py
from typing import Dict
from transmission.orchestrator.transmission import TransmissionOrchestrator

# In-memory cache (for MVP)
# Production: Redis or database-backed
user_orchestrators: Dict[str, TransmissionOrchestrator] = {}

def get_orchestrator_for_user(user_id: str) -> TransmissionOrchestrator:
    """Get or create user-specific orchestrator"""
    if user_id not in user_orchestrators:
        # Create isolated orchestrator
        orchestrator = TransmissionOrchestrator(
            db_path=f"data/user_{user_id}/transmission.db",
            config_path=f"config/user_{user_id}/"
        )
        user_orchestrators[user_id] = orchestrator
    
    return user_orchestrators[user_id]
```

---

## Competitive Positioning

### Why This Architecture Wins

**1. Market Reach**
- Dashboard → Direct users (prop traders, retail)
- Webhooks → Platform users (TradingView, MT5)
- SDK → Developers and enterprises

**2. Flexibility**
- Users choose their interface
- No vendor lock-in
- Works with existing workflows

**3. Scalability**
- Multi-tenant architecture from day one
- Cloud-ready
- Can scale to thousands of users

**4. Revenue Diversification**
- Free tier (open source) → Community growth
- Pro tier → Recurring revenue
- Enterprise → High-value customers

---

## Risk Mitigation

### Platform Dependency Risk

**Problem:** Building plugins for TradingView/MT5 creates dependency  
**Solution:** Webhook abstraction layer - if platform changes, only adapter needs update

### Multi-Tenancy Complexity

**Problem:** User isolation adds complexity  
**Solution:** Start simple (separate databases), migrate to shared later

### Revenue Concentration

**Problem:** Too dependent on one tier  
**Solution:** Three-tier model diversifies revenue streams

---

## Success Metrics

### Phase 1 (MVP) - ✅ Complete
- [x] 100% Blueprint compliance
- [x] All Tier-1 & Tier-2 modules
- [x] FastAPI backend
- [x] React frontend

### Phase 2 (Webhooks) - 📅 Q1 2025
- [ ] 10 TradingView integrations
- [ ] 5 MT5 integrations
- [ ] 50 Pro users
- [ ] $5k MRR

### Phase 3 (SDK) - 📅 Q2 2025
- [ ] Python SDK released
- [ ] 5 enterprise customers
- [ ] $25k MRR
- [ ] 200 total users

---

## Conclusion

**✅ APPROVED: Multi-Interface Middleware Platform**

This architecture:
- ✅ Maximizes market reach (all segments)
- ✅ Minimizes platform risk (webhook abstraction)
- ✅ Enables revenue diversification (three tiers)
- ✅ Scales from MVP to enterprise

**Next Action:** Implement multi-tenancy foundation and webhook infrastructure.

---

**Document Version:** 1.0  
**Last Updated:** 2024-12-19  
**Status:** ✅ **APPROVED FOR IMPLEMENTATION**

