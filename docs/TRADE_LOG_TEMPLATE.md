# Daily Trade Log Template

**Trader:** [Your Name]
**Date:** [YYYY-MM-DD]
**Trading Session:** [AM/PM/Evening]

---

## Pre-Session Checklist

- [ ] API running (`python startup/run_api.py`)
- [ ] Dashboard accessible (http://localhost:5173)
- [ ] Current regime checked
- [ ] Daily R limit checked (-2R max)
- [ ] Mental state: [1-5, where 5 = optimal]
- [ ] News calendar checked

---

## Trade 1

### Signal Details
- **Time:** [HH:MM]
- **Symbol:** [MNQ/ES/NQ]
- **Strategy:** [VWAP Pullback / Manual Analysis]
- **Direction:** [LONG / SHORT]
- **Entry Price:** $[price]
- **Stop Price:** $[price]
- **Target Price:** $[price]
- **Risk:** $[amount] ([X]R)
- **Contracts:** [quantity]

### Market Context
- **Regime:** [TREND / RANGE / VOLATILE / NOTRADE]
- **ADX:** [value]
- **ATR:** [value]
- **VWAP:** [value]
- **Current Price vs VWAP:** [above/below/at]

### Transmission Decision
- **Status:** [✅ APPROVED / ❌ REJECTED / ⏸️ MODIFIED]
- **Reason:** [Why approved/rejected]
- **Modifications:** [If position size or stops were adjusted]

#### If Approved:
- **Adjusted Contracts:** [final quantity after position sizer]
- **Adjusted Stop:** [if trailing stop applied]
- **Order ID:** [from execution]
- **Fill Price:** $[actual fill]
- **Slippage:** [ticks]

#### If Rejected:
- **Rejection Reason:**
  - [ ] Mental Governor (state: BLOCKED)
  - [ ] News Blackout (event: ________)
  - [ ] Daily Loss Limit (-2R hit)
  - [ ] Weekly Loss Limit (-5R hit)
  - [ ] Spread Too Wide (>X ticks)
  - [ ] Slippage Risk High
  - [ ] Position Size < 1 Contract
  - [ ] Regime Mismatch
  - [ ] Other: __________

### Outcome
- **Result:** [WIN / LOSS / BREAKEVEN]
- **Exit Time:** [HH:MM]
- **Exit Price:** $[price]
- **Exit Reason:**
  - [ ] Target Hit
  - [ ] Stop Hit
  - [ ] Trailing Stop
  - [ ] Scale-Out (partial)
  - [ ] Manual Exit
  - [ ] Time Stop
  - [ ] End of Day Flatten

- **P&L:** $[amount] ([+/-X]R)
- **Commission:** $[amount]
- **Net P&L:** $[net amount]

### Notes
[What worked? What didn't? What did Transmission prevent?]

---

## Trade 2

[Repeat above structure]

---

## Session Summary

### Statistics
- **Total Trades:** [count]
- **Wins:** [count]
- **Losses:** [count]
- **Win Rate:** [percentage]
- **Total R:** [+/-X]R
- **Gross P&L:** $[amount]
- **Net P&L:** $[amount after commissions]

### Transmission Interventions
- **Total Signals Submitted:** [count]
- **Approved:** [count]
- **Rejected:** [count]
- **Modified:** [count]

#### Key Rejections (Value Added)
1. [e.g., "Prevented entry during news spike - saved -1.5R"]
2. [e.g., "Reduced size due to volatile regime - limited loss to -0.5R instead of -1R"]
3. [e.g., "Mental governor blocked revenge trade after loss"]

### Learning Points
1. [What did you learn today?]
2. [How did Transmission help?]
3. [What would you have done differently without Transmission?]

### Tomorrow's Goals
- [ ] [Specific improvement]
- [ ] [Risk management focus]
- [ ] [Strategy refinement]

---

## Weekly Summary (Fill at end of week)

### Performance
- **Total Trades This Week:** [count]
- **Win Rate:** [percentage]
- **Profit Factor:** [wins/losses]
- **Weekly R:** [+/-X]R
- **Max Drawdown:** [-X]R
- **Sharpe Ratio:** [if calculated]

### Transmission Value Analysis

#### Rules Enforced
- **Daily Loss Limits:** [X times stopped trading]
- **Mental State Blocks:** [X times prevented emotional trading]
- **News Blackouts:** [X times prevented high-risk entries]
- **Position Sizing Adjustments:** [X times reduced size]

#### Estimated Value
- **Prop Firm Violations Prevented:** [count]
- **Estimated Savings:** $[amount]
- **ROI on Transmission:** [savings / cost]

### Case Study Material
[Note any particularly compelling examples for blog posts or marketing]

---

## Template Usage Notes

**How to Use:**
1. Copy this template daily
2. Fill out BEFORE submitting signals to Transmission
3. Log Transmission's decisions in real-time
4. Complete outcome after trade closes
5. Review weekly for patterns

**Key Metrics to Track:**
- Transmission approval vs rejection rate
- Value of rejections (prevented losses)
- Position sizing adjustments (risk management)
- Mental state correlation with performance

**Goal:**
Document how Transmission makes you a better trader through:
1. Risk management (prevents violations)
2. Discipline (enforces rules)
3. Adaptation (regime-aware position sizing)

---

**Last Updated:** 2024-12-19
