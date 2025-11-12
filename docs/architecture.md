# Transmission™ Architecture

## System Overview

Transmission™ is an adaptive trading middleware that sits between trading strategies and execution. It provides:

1. **Regime Detection** - Automatically detects market conditions (Trend/Range/Volatile)
2. **Risk Management** - Enforces limits (-2R day, -5R week, prop firm rules)
3. **Strategy Adaptation** - Switches strategies based on regime
4. **Execution Quality** - Monitors slippage, liquidity, order fills
5. **Performance Tracking** - Journals trades, calculates metrics (PF, E[R], WR)

## Module Architecture

```
┌─────────────────────────────────────────────────┐
│           Orchestrator (Main Loop)              │
│  - Coordinates all modules                      │
│  - Manages state transitions                    │
│  - Handles errors and circuit breakers          │
└───────────────┬─────────────────────────────────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐  ┌───▼───┐  ┌────▼────┐
│Telemetry│  │Regime │  │  Risk  │
│         │  │       │  │Governor│
└───┬────┘  └───┬───┘  └────┬────┘
    │           │           │
    └───────────┼───────────┘
                │
         ┌──────▼──────┐
         │  Strategies │
         │  (Engines)  │
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │  Execution  │
         │   Engine    │
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │  Analytics  │
         │  (Journal)  │
         └─────────────┘
```

## Module Responsibilities

### Telemetry
- **Purpose:** Calculate market features from OHLCV data
- **Key Functions:**
  - `calculate_adx()` - Trend strength
  - `calculate_vwap()` - Volume-weighted average price
  - `calculate_atr()` - Volatility measure
  - `calculate_all_features()` - Main entry point
- **Dependencies:** pandas, numpy, pandas-ta
- **Output:** `MarketFeatures` dataclass

### Regime
- **Purpose:** Classify market regime (Trend/Range/Volatile/NoTrade)
- **Key Functions:**
  - `classify()` - Main classification logic
  - `get_regime_multiplier()` - Returns multiplier for position sizing
- **Dependencies:** Telemetry (MarketFeatures)
- **Output:** `Literal['TREND', 'RANGE', 'VOLATILE', 'NOTRADE']`

### Risk
- **Purpose:** Enforce risk limits and prop firm rules
- **Key Functions:**
  - `check_tripwires()` - Daily/weekly limits
  - `evaluate_scaling()` - Step-down/scale-up logic
  - `validate_trade()` - Pre-trade risk check
- **Dependencies:** Analytics (for trade history)
- **Output:** Risk decision (allow/deny/reduce)

### Strategies
- **Purpose:** Generate trading signals based on regime
- **Key Functions:**
  - `generate_signal()` - Main signal generation
  - `validate_setup()` - Pre-entry validation
- **Dependencies:** Regime, Telemetry
- **Output:** `Signal` dataclass (entry, stop, target, contracts)

### Execution
- **Purpose:** Manage order placement and fills
- **Key Functions:**
  - `place_order()` - Submit order to broker
  - `monitor_fill()` - Track order status
  - `calculate_slippage()` - Measure execution quality
- **Dependencies:** Broker API (abstracted)
- **Output:** Order status, fill details

### Analytics
- **Purpose:** Track performance and calculate metrics
- **Key Functions:**
  - `log_trade()` - Record trade in journal
  - `calculate_metrics()` - PF, E[R], WR, MaxDD
  - `detect_edge_decay()` - Performance degradation detection
- **Dependencies:** SQLite database
- **Output:** Performance metrics, trade history

### Orchestrator
- **Purpose:** Coordinate all modules in main trading loop
- **Key Functions:**
  - `process_bar()` - Main decision loop (called every 15-min bar)
  - `shift_gear()` - Strategy switching logic
  - `handle_error()` - Error recovery
- **Dependencies:** All modules
- **Output:** Trading decisions, system state

## Data Flow

### Signal Generation Flow

```
1. Market Data → Telemetry
   └─> MarketFeatures

2. MarketFeatures → Regime
   └─> Regime Classification

3. Regime + MarketFeatures → Risk Governor
   └─> Risk Decision (allow/deny)

4. If allowed: Regime → Strategy Selection
   └─> Active Strategy

5. MarketFeatures + Regime → Strategy.generate_signal()
   └─> Signal (entry, stop, target, contracts)

6. Signal → Risk Governor.validate_trade()
   └─> Final Risk Check

7. Signal → Execution Engine
   └─> Order Placement

8. Order Fill → Analytics
   └─> Trade Journal Entry
```

## State Management

### System States

1. **INITIALIZING** - Loading config, connecting to data feeds
2. **READY** - System ready, waiting for signals
3. **ANALYZING** - Processing market data, evaluating strategies
4. **SIGNAL_GENERATED** - Signal found, awaiting risk approval
5. **TRADING** - Active position management
6. **PAUSED** - Risk limit hit, waiting for reset
7. **ERROR** - System error, requires intervention

### State Transitions

```
INITIALIZING → READY
READY → ANALYZING (on new bar)
ANALYZING → SIGNAL_GENERATED (if signal found)
SIGNAL_GENERATED → TRADING (if risk approved)
TRADING → READY (on exit)
ANY → PAUSED (if risk limit hit)
ANY → ERROR (on critical error)
```

## Error Handling

### Error Levels

1. **WARNING** - Non-critical (log and continue)
2. **ERROR** - Recoverable (retry, fallback)
3. **CRITICAL** - Unrecoverable (stop trading, alert)

### Circuit Breakers

- **Data Feed Loss** - Pause trading after 60s no data
- **Risk Limit Hit** - Immediate stop, require manual reset
- **Broker Disconnect** - Close positions, alert user
- **System Error** - Enter ERROR state, log details

## Performance Considerations

### Caching
- VWAP calculations (cache by symbol)
- Regime classification (cache for 15-min bars)
- Risk metrics (cache until next trade)

### Optimization
- Vectorized pandas operations
- Async I/O for broker connections
- Batch database writes
- Lazy loading of historical data

## Testing Strategy

### Unit Tests
- Each module tested in isolation
- Mock dependencies
- Test edge cases

### Integration Tests
- Test module interactions
- End-to-end signal generation
- Error recovery scenarios

### Performance Tests
- Load testing with historical data
- Latency measurements
- Memory profiling

