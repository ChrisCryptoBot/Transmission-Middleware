# Case Study Template: [Title]

**Example:** "How Transmission Prevented 3 Prop Firm Violations in One Week"

---

## Header

**Trader:** [Name or "Anonymous Prop Trader"]
**Experience Level:** [Beginner / Intermediate / Advanced]
**Trading Style:** [Scalper / Day Trader / Swing Trader]
**Account Type:** [Prop Firm Evaluation / Funded Account / Personal Account]
**Prop Firm:** [FTMO / TopstepTrader / Apex / etc. or N/A]
**Timeframe:** [Date range]

---

## The Problem (Before Transmission)

### Pain Points
[Describe the specific challenges faced]

**Example:**
> "I was consistently failing FTMO evaluations despite having a profitable strategy. My biggest issues were:
> 1. Hitting the daily loss limit (-5%) too frequently
> 2. Trading during high-impact news events
> 3. Over-trading after wins (emotional revenge trading)
> 4. Inconsistent position sizing"

### Financial Impact
- **Failed Evaluations:** [count]
- **Cost:** $[total spent on evaluations]
- **Time Lost:** [months]
- **Emotional Toll:** [brief description]

---

## The Solution (Transmission Implementation)

### Setup
- **Date Started:** [YYYY-MM-DD]
- **Configuration:**
  - Daily Loss Limit: -$[amount] (-2R)
  - Weekly Loss Limit: -$[amount] (-5R)
  - Position Sizing: ATR-normalized
  - Mental Governor: Enabled
  - News Blackout: Enabled (30 min before/after high-impact events)

### Integration
[How was Transmission integrated into workflow?]

**Example:**
> "I connected my TradingView alerts to Transmission's webhook endpoint. Every signal from my VWAP pullback strategy was processed through Transmission's adaptive pipeline before execution."

OR

> "I used Transmission's dashboard to manually submit signals. Before each trade, I'd check the regime, risk limits, and mental state indicators."

---

## Results (After Transmission)

### Performance Metrics

#### Week 1
- **Trades:** [count]
- **Win Rate:** [percentage]
- **R Total:** [+/-X]R
- **Max Drawdown:** [-X]R
- **Violations Prevented:** [count]

#### Week 2
[Same metrics]

#### Overall (Full Period)
- **Total Trades:** [count]
- **Win Rate:** [percentage]
- **Profit Factor:** [ratio]
- **Total R:** [+/-X]R
- **Sharpe Ratio:** [if available]
- **Max Drawdown:** [-X]R

### Transmission Interventions

| Intervention Type | Count | Estimated Value |
|------------------|-------|----------------|
| Daily Loss Limit Enforced | [X] | $[savings] |
| News Blackout | [X] | $[estimated avoided loss] |
| Mental State Block | [X] | $[estimated avoided loss] |
| Position Size Reduction | [X] | $[risk reduction] |
| Spread/Slippage Protection | [X] | $[estimated savings] |
| **TOTAL** | **[X]** | **$[total value]** |

---

## Specific Examples

### Example 1: Daily Loss Limit Enforcement

**Date:** [YYYY-MM-DD]

**Situation:**
> "I had already lost -1.8R in the morning session due to two stopped-out trades. My next signal came at 2:15 PM—a perfect VWAP pullback setup."

**Without Transmission:**
> "I would have taken this trade (1R risk), which ended up stopping out for -1R loss. This would have put me at -2.8R for the day, violating FTMO's -2% daily limit and failing the evaluation."

**With Transmission:**
> "Transmission blocked the entry with reason: 'Daily loss limit approach (-1.8R of -2R max).' This saved my evaluation. The day ended at -1.8R, within limits."

**Value Added:** $600 (cost of FTMO evaluation saved)

---

### Example 2: News Blackout Protection

**Date:** [YYYY-MM-DD]

**Situation:**
> "FOMC announcement at 2:00 PM. My strategy generated a long signal at 1:45 PM."

**Without Transmission:**
> "I would have entered, likely getting whipsawed during the volatile spike. Historical data shows I lose an average of -2R on news-based entries."

**With Transmission:**
> "Transmission rejected the entry: 'News blackout active (FOMC in 15 min).' The market spiked 40 points in both directions within 5 minutes. My entry would have been stopped out."

**Value Added:** $200 (estimated -2R loss avoided)

---

### Example 3: Mental State Governor

**Date:** [YYYY-MM-DD]

**Situation:**
> "After taking a -1R loss on the first trade, I immediately saw another setup. I was feeling angry and wanted to 'get my money back.'"

**Without Transmission:**
> "Classic revenge trading. I would have doubled my position size and likely taken another loss, compounding the damage."

**With Transmission:**
> "Transmission's Mental Governor detected the loss streak and reduced my position size by 50%. The trade ended up losing -0.5R instead of -1R. More importantly, the forced pause helped me regain composure."

**Value Added:** $100 (reduced loss) + emotional control

---

## Quantified Results

### Financial Impact

**Before Transmission (6 months):**
- Evaluations Failed: [X]
- Cost: $[amount]
- Average Monthly P&L: -$[amount]

**After Transmission ([timeframe]):**
- Evaluations Passed: [X]
- Cost Saved: $[amount]
- Average Monthly P&L: +$[amount]

**Net Improvement:** +$[total improvement]

### Behavioral Changes

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Daily Loss Limit Violations | [X/month] | [X/month] | [-X%] |
| Revenge Trades | [X/month] | [X/month] | [-X%] |
| News Event Losses | [X/month] | [X/month] | [-X%] |
| Average Position Size Consistency | [±X%] | [±X%] | [+/-X%] |
| Max Drawdown | [-X%] | [-X%] | [+/-X%] |

---

## Testimonial Quote

> "[Insert powerful quote from trader about their experience]"

**Example:**
> "Transmission didn't just make me profitable—it made me fundable. The system prevented me from sabotaging myself during emotional moments, which was my biggest problem. I'm now trading a $100k funded account and haven't violated a single rule in 3 months."

---

## Key Takeaways

### What Worked Best
1. [Specific feature/capability]
2. [Specific feature/capability]
3. [Specific feature/capability]

**Example:**
1. **Daily Loss Limit:** Prevented 3 evaluation failures worth $1,800
2. **Mental Governor:** Stopped revenge trading that historically cost -5R/month
3. **News Blackout:** Avoided 4 high-volatility entries that average -2R each

### Unexpected Benefits
[Things that weren't anticipated but proved valuable]

**Example:**
> "The regime classifier helped me understand when NOT to trade. I used to force trades in choppy markets. Transmission's 'NOTRADE' regime detection saved me from numerous false entries."

### Advice for Others
[What would you tell someone considering Transmission?]

---

## Visual Evidence

### Screenshots
- [ ] Dashboard showing blocked entry
- [ ] Trade log with interventions highlighted
- [ ] Performance chart (before vs after)
- [ ] Prop firm evaluation results

### Data
- [ ] CSV export of trades
- [ ] Performance metrics from Transmission
- [ ] Comparison charts

---

## Technical Details (Optional)

### Configuration Used
```yaml
# transmission/config/constraints.yaml
daily_loss_limit_dollars: -500.0  # -2R
weekly_loss_limit_dollars: -1250.0  # -5R
max_position_size: 2
mental_governor_enabled: true
news_blackout_minutes: 30
```

### Strategies Run
- VWAP Pullback (primary)
- [Others if applicable]

### Broker/Platform
- Broker: [Name]
- Integration Method: [Webhook / Manual / SDK]

---

## Conclusion

### Summary of Impact

**Problem Solved:**
[Concise statement of the main problem]

**Solution Implemented:**
[How Transmission addressed it]

**Results Achieved:**
[Quantified outcomes]

**Value Created:**
$[total value] in [timeframe]

**Example:**
> "By enforcing discipline through automated risk management, Transmission helped me pass my FTMO evaluation on the first try—something I failed 3 times before. The $99/month cost paid for itself in the first week by preventing a single daily loss limit violation."

### Recommendation
- **For Prop Traders:** [Would you recommend? Why?]
- **For Retail Traders:** [Would you recommend? Why?]
- **Overall Rating:** [X/10]

---

## Contact Information (Optional)

**Trader:** [Name or remain anonymous]
**Willing to be contacted:** [Yes/No]
**Social Media:** [Twitter/Discord handle if applicable]

---

## Usage Rights

- [ ] Permission granted to use this case study for marketing
- [ ] Permission granted to use quotes
- [ ] Permission granted to use screenshots
- [ ] Prefer to remain anonymous
- [ ] OK to use real name

---

**Template Version:** 1.0
**Last Updated:** 2024-12-19

---

## Notes for Creating Your Case Study

1. **Be Specific:** Exact numbers, dates, and scenarios are more credible than generalizations
2. **Show Contrast:** Clear before/after comparison demonstrates value
3. **Quantify Everything:** Dollar amounts, percentages, time saved
4. **Tell a Story:** Make it relatable and human
5. **Include Proof:** Screenshots, data exports, prop firm certificates
6. **Focus on Pain → Solution → Results:** Classic case study structure

**Good Example:**
> "On March 15th, Transmission blocked my 3rd trade of the day because I had already lost -1.8R. Without this intervention, I would have taken a -1R loss, violating FTMO's -2% daily limit and failing my $80k evaluation. That single decision was worth $549 (the cost of the evaluation)."

**Bad Example:**
> "Transmission helped me be more disciplined and I'm doing better now."

The difference is specificity and quantification.
