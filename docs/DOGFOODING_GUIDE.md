# Transmission Dogfooding Guide

**How to Trade with Transmission Today**

Last Updated: 2025-11-13
Status: Phase 1 - Manual Trading (Dogfooding)
Audience: You (Chris) - First real user

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Setup](#system-setup)
3. [Manual Signal Workflow](#manual-signal-workflow)
4. [Trade Journaling](#trade-journaling)
5. [Performance Tracking](#performance-tracking)
6. [Troubleshooting](#troubleshooting)
7. [What to Document](#what-to-document)

---

## Quick Start

### Goal: Submit Your First Signal in 5 Minutes

1. **Start the system** (if not already running):
   ```bash
   # Terminal 1: Backend
   python startup/run_api.py

   # Terminal 2: Frontend
   cd web && npm run dev
   ```

2. **Open the dashboard**: http://localhost:5173

3. **Get your API key** (check backend terminal logs):
   ```
   Look for: "Default API key created: sk_..."
   Copy this key - you'll need it for every signal submission
   ```

4. **Submit a test signal**:
   - Scroll to "Manual Signal Submission" form
   - Paste your API key
   - Fill in signal details (see example below)
   - Click "Submit Signal to Transmission"

5. **Watch the magic happen**:
   - Transmission validates against all rules
   - Calculates position size dynamically
   - Checks constraints (spread, DLL, mental state)
   - Executes or rejects with clear reasoning

**You're now trading with Transmission.** 🎉

---

## System Setup

### Backend Configuration

**Location**: `transmission/config/`

**Key Files**:
- `instruments.yaml` - Instrument specifications (MNQ, MES, ES, NQ)
- `config.yaml` - System configuration (risk limits, broker settings)

**Default Settings** (Already configured):
- **Risk Per Trade**: 2% of account (max_risk_pct)
- **Daily Loss Limit**: 10% (dll_risk_pct)
- **Mental State Baseline**: 5 (neutral, scale 1-10)
- **Broker**: Rithmic (simulated mode)

### Frontend Access

**Dashboard**: http://localhost:5173
**Pages**:
- `/` - Dashboard (Manual Signal Form, Status, Orders, Positions)
- `/trades` - Trade History

**WebSocket**: Real-time updates for order fills, rejections, regime changes

---

## Manual Signal Workflow

### Step 1: Identify a Trade Setup

**Off-platform** (TradingView, MT5, your own analysis):
- Identify entry, stop, target
- Note confluence factors
- Check market regime (TREND/RANGE/VOLATILE)
- Rate your confidence (0.0-1.0)

### Step 2: Submit Signal via Dashboard

**Form Fields**:

| Field | Example | Notes |
|-------|---------|-------|
| **API Key** | `sk_...` | From backend logs, stored in localStorage |
| **Symbol** | MNQ | Trading symbol |
| **Asset Class** | Futures | Auto-configures tick size, point value |
| **Direction** | LONG / SHORT | Click the gradient button |
| **Entry Price** | 20500.00 | Your intended entry |
| **Stop Price** | 20450.00 | Hard stop loss |
| **Target Price** | 20600.00 | Take profit target |
| **Contracts** | (leave blank) | Let Transmission calculate |
| **Confidence** | 0.8 | Your conviction (0-1 scale) |
| **Strategy** | "VWAP Pullback" | Name of your setup |
| **Notes** | "15m pullback to VWAP, ADX 25..." | Trade rationale |

**Risk Calculator** (Auto-computed):
- **Stop Distance**: 50 pts (Entry - Stop)
- **Target Distance**: 100 pts (Target - Entry)
- **Risk:Reward**: 1:2.00 (green = good, yellow = marginal)

### Step 3: Transmission Processes Your Signal

**What Happens Behind the Scenes**:

1. **Authentication**: Validates your API key
2. **Instrument Lookup**: Loads MNQ specs (point_value=2.0, tick_size=0.25)
3. **Mental State Check**: Current state vs. baseline
4. **News Blackout Check**: No trading during high-impact news
5. **Risk Tripwire Check**: Daily loss limit, consecutive losers
6. **Position Sizing**:
   - Calculates risk dollars (account * 2%)
   - ATR normalization (if strategy requires)
   - Applies mental state adjustment
   - Returns exact contract count
7. **Constraint Validation**:
   - Stop distance (min 10 ticks)
   - Risk:Reward ratio (min 1.5:1)
   - Spread check (bid-ask < 3 ticks)
8. **Execution Guard**: Final price/spread check before order submission
9. **Order Submission**: Sends order to broker (Rithmic)
10. **Trade Logging**: Records to database with full context

### Step 4: Review Result

**Success Response** (Green panel):
```
✓ Success!
Generic LONG signal for MNQ processed
Order submitted: ORD_20251113_123456
```

**Rejection Response** (Red panel):
```
✗ Error
Signal rejected: DLL constraint violated
Daily loss limit exceeded: -$520 / -$500 limit
```

**Possible Rejection Reasons**:
- Daily loss limit exceeded
- Mental state too low (< 3)
- High-impact news event active
- Spread too wide (> 3 ticks)
- Consecutive red days limit (3+)
- Stop distance too small (< 10 ticks)
- Risk:reward too low (< 1.5:1)

---

## Trade Journaling

### Use TRADE_LOG_TEMPLATE.md

**Location**: `docs/TRADE_LOG_TEMPLATE.md`

**After Each Trade**:

1. **Copy the template**:
   ```bash
   cp docs/TRADE_LOG_TEMPLATE.md journal/2025-11-13_MNQ_LONG.md
   ```

2. **Fill in trade details**:
   - Setup description
   - Why you took it
   - Transmission's decision (approved/rejected)
   - If rejected, why?
   - If executed, outcome?
   - What you learned

3. **Track "saves"**:
   - Count times Transmission rejected a bad signal
   - Count times constraints prevented over-trading
   - Document rule violations prevented

### Example Journal Entry

```markdown
# Trade Log: 2025-11-13 MNQ LONG

## Setup
VWAP pullback on 15m chart, ADX 25, trending day.

## Signal Details
- Entry: 20500.00
- Stop: 20450.00
- Target: 20600.00
- R:R: 1:2.00
- Confidence: 0.8

## Transmission Decision
✅ **APPROVED** - 2 contracts

Reason: All constraints passed. Position sized to 2% risk ($100).

## Outcome
- Fill Price: 20500.50
- Exit Price: 20598.25
- P&L: +$195.50 (+0.97R)
- Duration: 23 minutes

## Reflection
Great execution. Transmission's 2-contract sizing felt comfortable.
No overtrading because system enforced proper position size.

## Rule Saves
None - clean trade within all limits.
```

---

## Performance Tracking

### Key Metrics to Monitor

**Daily**:
- Daily P&L (R and $)
- Win rate
- Average R per trade
- Trades taken / signals submitted
- Rejection rate

**Weekly**:
- Weekly P&L
- Consecutive red days
- Largest win/loss
- Regime performance (TREND vs RANGE)
- Mental state correlation

**Monthly**:
- Profit factor
- Max drawdown
- Recovery time
- Rule violation saves (estimated $ saved)
- Strategy performance breakdown

### Using the Dashboard

**System Status Card**:
- Current R (running total)
- Daily/Weekly P&L
- Consecutive red days
- Can Trade? (Yes/No with reason)

**Orders Table**:
- Active orders
- Fill status
- Submitted time

**Positions Table**:
- Current positions
- Unrealized P&L
- Entry/Stop/Target prices

**Trades Page** (`/trades`):
- Historical trades
- Filters by date, symbol, strategy
- Export to CSV for analysis

---

## What to Document

### Goal: Build Case Studies & Marketing Content

Document these scenarios:

### 1. **Rule Violation Prevented**

Example:
> "On Day 3, after two losing trades, I wanted to revenge trade with 4 contracts. Transmission rejected the signal because my mental state was 2/10 (below threshold). This saved me from a potential $800 loss. **Estimated save: $800**."

### 2. **Position Sizing Saved Me**

Example:
> "I wanted to trade 3 contracts, but Transmission calculated 1 contract based on ATR volatility being 2x normal. The trade lost, but I only lost $50 instead of $150. **Actual save: $100**."

### 3. **Daily Loss Limit Protection**

Example:
> "After hitting my $500 DLL at 11am, Transmission blocked all further signals. In the past, I would have revenge traded and turned -$500 into -$1200. **Estimated save: $700**."

### 4. **Spread Protection**

Example:
> "Signal looked perfect, but spread was 1.0 points (4 ticks). Transmission rejected due to spread > 3 ticks. I would have gotten filled at a worse price, costing me ~$8/contract. **Estimated save: $16** (2 contracts)."

### 5. **Successful Trade Execution**

Example:
> "Transmission approved my signal, sized position to 2 contracts, executed flawlessly. Trade hit target for +$195 (+0.97R). System worked exactly as designed."

---

## Troubleshooting

### Common Issues

#### 1. **"Invalid or expired API key"**

**Solution**:
- Check backend logs for default API key
- Ensure key starts with `sk_`
- Re-paste key into form (localStorage may have cleared)

#### 2. **"System not initialized"**

**Solution**:
- Backend not running
- Run `python startup/run_api.py`
- Wait for "Uvicorn running on http://0.0.0.0:8000"

#### 3. **"Signal rejected: DLL constraint violated"**

**Solution**:
- Check current daily P&L on dashboard
- If you've hit your loss limit, stop trading (as designed!)
- Reset happens at midnight

#### 4. **WebSocket "Disconnected"**

**Solution**:
- Backend crashed or restarted
- Check backend logs
- Refresh frontend page

#### 5. **Form shows "Failed to submit signal"**

**Solution**:
- Open browser console (F12)
- Check network tab for error details
- Common causes:
  - Backend not running
  - Wrong API key
  - Network issue (port 8000 blocked)

---

## Next Steps

### Week 1 Goals

- [ ] Submit 10 manual signals through Transmission
- [ ] Document 2+ "saves" (rule violations prevented)
- [ ] Create 1 detailed journal entry
- [ ] Track daily P&L in R terms
- [ ] Note any bugs/UX issues

### Week 2 Goals

- [ ] Write first case study using CASE_STUDY_TEMPLATE.md
- [ ] Analyze rejection rate (target: 20-30%)
- [ ] Test all asset classes (MNQ, MES, ES, NQ)
- [ ] Document "aha moments" when Transmission saved you

### After 10 Trades

**Write Your First Blog Post**:
> "I Traded with Transmission for 2 Weeks: How Adaptive Middleware Prevented 3 Rule Violations and Saved Me $600"

**Include**:
- Specific examples of saves
- Before/after comparison (manual trading vs Transmission)
- Exact dollar amounts saved
- Screenshots of rejection messages
- Link to case study templates

---

## Support & Feedback

### Need Help?

**Check Logs**:
- Backend: Terminal running `run_api.py`
- Frontend: Browser console (F12)
- Database: `data/transmission.db` (SQLite)

**Common Log Locations**:
```
transmission/logs/transmission.log
transmission/logs/error.log
```

**Report Issues**:
- Document the exact error message
- Note the signal details you submitted
- Check backend logs for stack trace
- Create issue in GitHub repo

### Feedback Loop

**What to Track**:
- UX friction points (hard to use?)
- Missing features (wish it could...?)
- Bugs (doesn't work as expected?)
- Performance (too slow?)

**Goal**: Refine the system based on real-world usage before beta launch.

---

## Appendix: Example Signals

### Example 1: Clean MNQ Long

```
Symbol: MNQ
Asset Class: Futures
Direction: LONG
Entry: 20500.00
Stop: 20450.00
Target: 20600.00
Confidence: 0.8
Strategy: "VWAP Pullback"
Notes: "15m pullback to VWAP, ADX 25, uptrend confirmed"
```

**Expected Result**: Approved (2 contracts, assuming 2% risk on $10k account)

### Example 2: ES Short (Higher Volatility)

```
Symbol: ES
Asset Class: Futures
Direction: SHORT
Entry: 5900.00
Stop: 5912.00
Target: 5875.00
Confidence: 0.75
Strategy: "Range Fade"
Notes: "Failed breakout, range-bound day, fading highs"
```

**Expected Result**: Approved (1 contract, ES has higher point value = $50/pt)

### Example 3: Rejected - DLL Hit

```
Symbol: MNQ
Asset Class: Futures
Direction: LONG
Entry: 20500.00
Stop: 20450.00
Target: 20600.00
Confidence: 0.8
Strategy: "Recovery Trade"
Notes: "Trying to recover from earlier losses"
```

**Expected Result**: ❌ REJECTED - "Daily loss limit exceeded: -$520 / -$500 limit"

### Example 4: Rejected - Mental State Low

```
Symbol: MNQ
Asset Class: Futures
Direction: SHORT
Entry: 20500.00
Stop: 20550.00
Target: 20450.00
Confidence: 0.5
Strategy: "Revenge Trade"
Notes: "Frustrated from last trade, forcing setup"
```

**Expected Result**: ❌ REJECTED - "Mental state below threshold: 2/10 (min: 3/10)"

---

## Success Criteria

### You'll know dogfooding is successful when:

✅ **10+ trades executed** through Transmission
✅ **2+ documented saves** (rule violations prevented)
✅ **1+ case study written** with real examples
✅ **Win rate > 50%** or **Profit Factor > 1.5**
✅ **Zero rule violations** (Transmission caught everything)
✅ **You trust the system** enough to use it for real money

---

## Strategic Impact

### Why This Matters

**Dogfooding = Proof**

Before telling others "Transmission prevents rule violations," you need to prove it yourself. This phase:

1. **Validates the product** - Does it actually work?
2. **Generates content** - Real case studies > hypothetical examples
3. **Builds credibility** - "I use this myself"
4. **Finds bugs** - Real usage reveals edge cases
5. **Refines UX** - What's confusing? What's missing?

### From Dogfooding → Beta → Launch

**Phase 1 (Now)**: You dogfood for 2 weeks
→ **Output**: Case studies, blog post, testimonial

**Phase 2**: 10-20 prop traders beta test
→ **Output**: External validation, more case studies

**Phase 3**: Public launch with proven track record
→ **Output**: 50+ users, $1k+ MRR

**It all starts with your first 10 trades.**

---

**Ready to trade? Open http://localhost:5173 and submit your first signal.** 🚀
