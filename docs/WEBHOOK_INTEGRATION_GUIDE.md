# Webhook Integration Guide

**Transmission™ Multi-Interface Middleware**

This guide explains how to integrate external trading platforms (TradingView, MetaTrader 5, custom apps) with Transmission using webhooks.

---

## Overview

Webhooks enable Transmission to receive signals from ANY platform while adding:
- ✅ **Regime detection** - Signal only executed in appropriate market conditions
- ✅ **Risk management** - Enforces daily/weekly loss limits
- ✅ **Multi-timeframe confirmation** - HTF validation before entry
- ✅ **Mental state protection** - Prevents revenge trading
- ✅ **Prop firm compliance** - DLL, consistency rules automatically enforced

**Architecture:**
```
[TradingView Alert] → [Webhook] → [Transmission] → [Risk Check] → [Execution]
       or                              ↓
[MT5 EA Signal] → [Webhook] → [Regime Check] → [Position Sizing] → [Broker]
       or                              ↓
[Custom App] → [Webhook] → [Multi-TF Fusion] → [Mental Governor] → [Fill]
```

---

## Authentication

All webhook endpoints require API key authentication.

### Get Your API Key

1. **Start Transmission API:**
   ```bash
   python startup/run_api.py
   ```

2. **Check logs for default API key:**
   ```
   Default API key created: sk_xxxxxxxxxxxxx
   ⚠️ In production, store this securely!
   ```

3. **Or create new API key via API:**
   ```bash
   curl -X POST http://localhost:8000/api/auth/keys \
     -H "X-API-Key: sk_xxxxxxxxxxxxx" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "TradingView Webhook",
       "scopes": ["read", "write"]
     }'
   ```

4. **Store your API key securely** - it's shown only once!

---

## TradingView Integration

### Setup Steps

#### 1. Create Alert in TradingView

1. Open TradingView chart
2. Right-click on chart → **Add alert**
3. Set conditions (e.g., "Price crosses MA")

#### 2. Configure Alert Message (JSON Format)

In the **Message** field, enter:

```json
{
  "ticker": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "close": {{close}},
  "time": {{time}},
  "strategy": "My VWAP Strategy",
  "message": "Entry signal detected"
}
```

**TradingView Variables:**
- `{{ticker}}` - Symbol (e.g., "MNQ", "NQ1!")
- `{{strategy.order.action}}` - "buy" or "sell"
- `{{close}}` - Current price
- `{{time}}` - Unix timestamp

#### 3. Set Webhook URL

In the **Notifications** tab:

**Webhook URL:**
```
http://your-server.com:8000/api/webhooks/tradingview
```

*For local testing:*
```
http://localhost:8000/api/webhooks/tradingview
```

**Headers:**
```
X-API-Key: sk_your_api_key_here
```

**Note:** TradingView webhooks require **Pro+ plan** ($15-60/month)

#### 4. Test the Alert

Trigger the alert manually and check Transmission logs:

```bash
# Transmission API logs
✅ TradingView webhook received from user default_user: My VWAP Strategy LONG on MNQ
```

### Example TradingView Pine Script

```pine
//@version=5
strategy("VWAP Pullback - Transmission", overlay=true)

// Calculate VWAP
vwap_value = ta.vwap(close)

// Entry conditions
long_condition = close < vwap_value and close > ta.ema(close, 20)
short_condition = close > vwap_value and close < ta.ema(close, 20)

// Generate signals with webhook alerts
if long_condition
    strategy.entry("Long", strategy.long,
        alert_message='{"ticker":"{{ticker}}","action":"BUY","close":{{close}},"time":{{time}},"strategy":"VWAP Pullback"}')

if short_condition
    strategy.entry("Short", strategy.short,
        alert_message='{"ticker":"{{ticker}}","action":"SELL","close":{{close}},"time":{{time}},"strategy":"VWAP Pullback"}')
```

### Test with cURL

```bash
curl -X POST http://localhost:8000/api/webhooks/tradingview \
  -H "X-API-Key: sk_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MNQ",
    "action": "BUY",
    "close": 12345.50,
    "time": 1703001600,
    "strategy": "VWAP Pullback",
    "message": "Entry signal"
  }'
```

**Expected Response:**
```json
{
  "status": "received",
  "signal_id": "tv_1703001600",
  "reason": "Signal received and queued for processing",
  "timestamp": "2024-12-19T10:00:00",
  "message": "TradingView LONG signal for MNQ acknowledged"
}
```

---

## MetaTrader 5 Integration

### Setup Steps

#### 1. Create EA Webhook Function

Add this function to your MetaTrader 5 Expert Advisor:

```mql5
// WebRequest must be enabled:
// Tools → Options → Expert Advisors → Allow WebRequests
// Add URL: http://your-server.com:8000

#include <JSON.mqh>  // JSON library (download from MQL5 community)

bool SendToTransmission(string symbol, int type, double price, double sl, double tp, double volume) {
    string url = "http://your-server.com:8000/api/webhooks/mt5";
    string api_key = "sk_your_api_key_here";

    // Build JSON payload
    JSONObject *json = new JSONObject();
    json.Put("symbol", symbol);
    json.Put("type", type);  // 0=BUY, 1=SELL
    json.Put("price", price);
    json.Put("sl", sl);
    json.Put("tp", tp);
    json.Put("volume", volume);
    json.Put("comment", _Symbol);
    json.Put("magic", MagicNumber);

    string data = json.Serialize();
    delete json;

    // Set headers
    string headers = "X-API-Key: " + api_key + "\r\n";
    headers += "Content-Type: application/json\r\n";

    // Send POST request
    char post[];
    char result[];
    string result_headers;

    StringToCharArray(data, post, 0, StringLen(data));

    int res = WebRequest(
        "POST",
        url,
        headers,
        5000,  // 5 second timeout
        post,
        result,
        result_headers
    );

    if(res == 200) {
        Print("✅ Signal sent to Transmission: ", symbol, " ", type);
        return true;
    } else {
        Print("❌ Failed to send signal. Code: ", res);
        return false;
    }
}
```

#### 2. Use in EA

```mql5
void OnTick() {
    // Your strategy logic
    if(BuyCondition()) {
        double price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
        double sl = price - 100 * _Point;  // 100 points SL
        double tp = price + 200 * _Point;  // 200 points TP

        // Send to Transmission instead of direct OrderSend
        SendToTransmission(_Symbol, 0, price, sl, tp, 1.0);
    }

    if(SellCondition()) {
        double price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
        double sl = price + 100 * _Point;
        double tp = price - 200 * _Point;

        SendToTransmission(_Symbol, 1, price, sl, tp, 1.0);
    }
}
```

### Test with cURL

```bash
curl -X POST http://localhost:8000/api/webhooks/mt5 \
  -H "X-API-Key: sk_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "MNQ",
    "type": 0,
    "price": 12345.50,
    "sl": 12300.0,
    "tp": 12400.0,
    "volume": 1.0,
    "comment": "MA Crossover",
    "magic": 123456
  }'
```

---

## Generic Webhook (Custom Integrations)

### Use Cases
- Custom Python/Node.js trading apps
- Discord bots
- Telegram bots
- Third-party signal services

### Example: Python Script

```python
import requests
import json

def send_signal_to_transmission(symbol, side, entry, stop=None, target=None):
    """Send signal to Transmission webhook"""

    url = "http://localhost:8000/api/webhooks/generic"
    headers = {
        "X-API-Key": "sk_your_api_key_here",
        "Content-Type": "application/json"
    }

    payload = {
        "symbol": symbol,
        "side": side,  # "LONG" or "SHORT"
        "entry": entry,
        "stop": stop,
        "target": target,
        "strategy": "Custom Python Bot",
        "confidence": 0.85,
        "notes": "Signal from custom strategy"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"✅ Signal sent: {response.json()}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

# Example usage
send_signal_to_transmission(
    symbol="MNQ",
    side="LONG",
    entry=12345.50,
    stop=12300.0,
    target=12400.0
)
```

### Example: Discord Bot

```python
import discord
from discord.ext import commands
import requests

bot = commands.Bot(command_prefix='!')

@bot.command()
async def trade(ctx, symbol: str, side: str, entry: float):
    """Send trade signal to Transmission

    Usage: !trade MNQ LONG 12345.50
    """

    url = "http://localhost:8000/api/webhooks/generic"
    headers = {"X-API-Key": "sk_your_api_key_here"}

    payload = {
        "symbol": symbol,
        "side": side.upper(),
        "entry": entry,
        "strategy": "Discord Bot",
        "notes": f"Signal from {ctx.author.name}"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        await ctx.send(f"✅ Signal sent: {side} {symbol} @ {entry}")
    else:
        await ctx.send(f"❌ Failed to send signal")

bot.run("YOUR_DISCORD_TOKEN")
```

### Test with cURL

```bash
curl -X POST http://localhost:8000/api/webhooks/generic \
  -H "X-API-Key: sk_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "MNQ",
    "side": "LONG",
    "entry": 12345.50,
    "stop": 12300.0,
    "target": 12400.0,
    "contracts": 1,
    "strategy": "Custom Strategy",
    "confidence": 0.8,
    "notes": "Test signal"
  }'
```

---

## Signal Processing Flow

Once a webhook receives a signal, Transmission processes it through:

### 1. **Signal Adapter**
- Validates format
- Normalizes symbol (MNQM2023 → MNQ)
- Converts to internal Signal format

### 2. **Regime Classifier** (TODO: Connect)
- Checks current market regime (TREND, RANGE, VOLATILE)
- Rejects if regime doesn't match strategy requirements
- Example: VWAP Pullback requires TREND regime

### 3. **Risk Governor** (TODO: Connect)
- Checks daily loss limit (-2R max)
- Checks weekly loss limit (-5R max)
- Rejects if limits exceeded

### 4. **Multi-Timeframe Fusion** (TODO: Connect)
- Validates signal with higher timeframe
- Checks HTF trend alignment
- Rejects if HTF doesn't confirm

### 5. **Position Sizer** (TODO: Connect)
- Calculates position size based on ATR
- Adjusts stop loss for volatility
- Ensures proper R:R ratio

### 6. **Execution Guard** (TODO: Connect)
- Checks liquidity
- Checks slippage tolerance
- Queues for execution if passed

### 7. **Execution Engine** (TODO: Connect)
- Submits order to broker
- Tracks order state
- Logs trade to database

---

## API Endpoints Reference

### Authentication

**Create User:**
```bash
POST /api/auth/users
{
  "email": "trader@example.com",
  "tier": "pro"  # "free", "pro", "enterprise"
}
```

**Get Current User:**
```bash
GET /api/auth/me
Headers: X-API-Key: sk_xxxxx
```

**Create API Key:**
```bash
POST /api/auth/keys
Headers: X-API-Key: sk_xxxxx  # Use existing key
{
  "name": "TradingView Webhook",
  "scopes": ["read", "write"]
}
```

**List API Keys:**
```bash
GET /api/auth/keys
Headers: X-API-Key: sk_xxxxx
```

**Revoke API Key:**
```bash
DELETE /api/auth/keys/{key_id}
Headers: X-API-Key: sk_xxxxx  # Use different key
```

### Webhooks

**TradingView Webhook:**
```bash
POST /api/webhooks/tradingview
Headers: X-API-Key: sk_xxxxx
Body: TradingView alert JSON
```

**MT5 Webhook:**
```bash
POST /api/webhooks/mt5
Headers: X-API-Key: sk_xxxxx
Body: MT5 signal JSON
```

**Generic Webhook:**
```bash
POST /api/webhooks/generic
Headers: X-API-Key: sk_xxxxx
Body: Generic signal JSON
```

**Health Check:**
```bash
GET /api/webhooks/health
# No authentication required
```

---

## Security Best Practices

### 1. **Protect Your API Key**
- ❌ Don't commit to Git
- ❌ Don't share in screenshots
- ✅ Store in environment variables
- ✅ Rotate periodically

### 2. **Use HTTPS in Production**
```bash
# Use reverse proxy (Nginx/Caddy) with SSL
https://api.yourdomain.com/api/webhooks/tradingview
```

### 3. **Validate Webhook Sources**
- TradingView: Check `User-Agent` header
- MT5: Use unique magic numbers per EA
- Custom: Implement IP whitelisting

### 4. **Rate Limiting** (TODO: Implement)
- Limit webhook calls per minute
- Prevent abuse/DDoS

---

## Troubleshooting

### "Invalid API key"
- Check `X-API-Key` header is set correctly
- Ensure key starts with `sk_`
- Verify key hasn't been revoked: `GET /api/auth/keys`

### "Invalid signal format"
- Check JSON format is correct
- Ensure required fields are present
- Review adapter validation logs

### TradingView webhook not firing
- Ensure TradingView Pro+ subscription active
- Check alert is set to "webhook" notification
- Verify URL is correct (no trailing slash)
- Check TradingView webhook logs (in alert settings)

### MT5 WebRequest fails
- Enable WebRequests: Tools → Options → Expert Advisors
- Add URL to allowed list
- Check EA has permission to access internet

### Signal received but not executed (TODO)
- Check Transmission logs for rejection reason
- Likely regime mismatch or risk limit hit
- Query `/api/system/status` for current state

---

## Next Steps

### Phase 2 (In Progress)
- [x] Multi-tenancy foundation
- [x] API key authentication
- [x] Signal adapters (TradingView, MT5, generic)
- [x] Webhook endpoints
- [ ] **Connect webhooks → orchestrator processing pipeline**
- [ ] Test with live TradingView alerts

### Phase 3 (Future)
- [ ] Production hardening (idempotency, crash recovery)
- [ ] Frontend webhook configuration panel
- [ ] Webhook retry logic with exponential backoff
- [ ] Webhook analytics dashboard
- [ ] Additional adapters (NinjaTrader, Sierra Chart)

---

## Support

**Documentation:** [PRODUCT_ARCHITECTURE_DECISION.md](./PRODUCT_ARCHITECTURE_DECISION.md)

**API Docs:** http://localhost:8000/docs (when running)

**Report Issues:** GitHub Issues

---

**Last Updated:** 2024-12-19
**Status:** ⚠️ Webhooks infrastructure complete, orchestrator integration pending
