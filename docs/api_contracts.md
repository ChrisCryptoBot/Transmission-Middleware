# Transmission™ API Contracts

## Module Interfaces

This document defines the contracts between modules. All modules must adhere to these interfaces.

---

## Telemetry Module

### Input
```python
bars_15m: pd.DataFrame
  - Columns: ['open', 'high', 'low', 'close', 'volume']
  - Index: DatetimeIndex
  - Minimum: 20 bars required

current_price: float
bid: Optional[float] = None
ask: Optional[float] = None
bid_size: Optional[float] = None
ask_size: Optional[float] = None
timestamp: Optional[datetime] = None
```

### Output
```python
MarketFeatures(
    timestamp: datetime
    adx_14: float  # 0-100
    vwap: float  # > 0
    vwap_slope_abs: float  # >= 0
    vwap_slope_median_20d: float  # >= 0
    atr_14: float  # > 0
    baseline_atr: float  # > 0
    or_high: float  # > 0
    or_low: float  # > 0
    or_hold_minutes: int  # >= 0
    spread_ticks: float  # >= 0
    ob_imbalance: float  # -1.0 to 1.0
    rel_volume_hour: float  # > 0
    news_proximity_min: Optional[int]  # None or >= 0
    entry_p90_slippage: float  # >= 0
    exit_p90_slippage: float  # >= 0
)
```

### Errors
- `ValueError`: If insufficient bars (< 20)
- `TypeError`: If invalid data types
- Returns `MarketFeatures` with zeros/None for missing optional data

---

## Regime Module

### Input
```python
features: MarketFeatures
```

### Output
```python
Literal['TREND', 'RANGE', 'VOLATILE', 'NOTRADE']
```

### Classification Rules
- **TREND**: ADX > 25 AND (VWAP_slope > median OR OR_hold > 30min)
- **RANGE**: ADX < 20 AND VWAP_slope <= median
- **VOLATILE**: Neither TREND nor RANGE conditions met
- **NOTRADE**: News within 30min OR spread > 2 ticks

### Additional Methods
```python
get_regime_multiplier(regime: str) -> float
  - TREND: 0.85
  - RANGE: 1.15
  - VOLATILE: 1.00
  - NOTRADE: 0.00
```

### Errors
- `ValueError`: If features are invalid
- Always returns a valid regime (never None)

---

## Risk Module

### Input
```python
# For tripwire check
daily_pnl_r: float
weekly_pnl_r: float
consecutive_red_days: int

# For trade validation
signal: Signal
current_positions: List[Position]
account_balance: float
```

### Output
```python
# Tripwire check
{
    'can_trade': bool,
    'reason': str,
    'action': str  # 'TRADE', 'FLAT', 'PAUSE'
}

# Trade validation
{
    'approved': bool,
    'reason': str,
    'adjusted_contracts': Optional[int]  # If reduced
}
```

### Risk Rules
- **Daily Limit**: -2R (hard stop)
- **Weekly Limit**: -5R (hard stop)
- **Red Days**: 3 consecutive red days → pause
- **DLL Constraint**: Risk ≤ min($R, 0.10 × DLL)
- **Consistency**: Best day ≤ consistency_rule × total profit

### Errors
- `ValueError`: If invalid inputs
- Always returns a decision (never None)

---

## Strategy Module

### Base Interface
```python
class BaseStrategy(ABC):
    @abstractmethod
    def generate_signal(
        self,
        features: MarketFeatures,
        regime: str,
        current_positions: List[Position]
    ) -> Optional[Signal]:
        """
        Generate trading signal based on market conditions.
        
        Returns:
            Signal if setup found, None otherwise
        """
        pass
    
    @property
    @abstractmethod
    def required_regime(self) -> str:
        """Regime this strategy works in (TREND, RANGE, VOLATILE)"""
        pass
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Human-readable strategy name"""
        pass
```

### Signal Output
```python
@dataclass
class Signal:
    entry_price: float
    stop_price: float
    target_price: float
    direction: Literal['LONG', 'SHORT']
    contracts: int
    confidence: float  # 0.0 to 1.0
    regime: str
    strategy: str
    timestamp: datetime
    notes: Optional[str] = None
```

### Errors
- Returns `None` if no setup (not an error)
- `ValueError`: If invalid inputs
- Strategy should never raise exceptions for normal operation

---

## Execution Module

### Input
```python
signal: Signal
account_id: str
order_type: Literal['LIMIT', 'MARKET'] = 'LIMIT'
```

### Output
```python
@dataclass
class OrderStatus:
    order_id: str
    status: Literal['PENDING', 'FILLED', 'PARTIAL', 'CANCELLED', 'REJECTED']
    filled_contracts: int
    fill_price: Optional[float]
    slippage_ticks: float
    timestamp: datetime
    error: Optional[str] = None
```

### Errors
- `ConnectionError`: If broker API unavailable
- `ValueError`: If invalid order parameters
- Returns `OrderStatus` with error message (doesn't raise)

---

## Analytics Module

### Input
```python
# For trade logging
trade: Trade  # Completed trade with all details

# For metrics calculation
window: int = 20  # Number of trades to analyze
```

### Output
```python
# Trade log
# Writes to SQLite database + CSV export

# Metrics
{
    'pf': float  # Profit Factor
    'er': float  # Expected Return (R)
    'wr_wilson_lb': float  # Win Rate (Wilson 95% lower bound)
    'maxdd_r': float  # Max Drawdown (in R)
    'costs_pct': float  # Costs as % of gross P&L
    'total_trades': int
    'win_rate': float
    'avg_win': float
    'avg_loss': float
}
```

### Errors
- `DatabaseError`: If SQLite write fails
- Logs error and continues (doesn't crash system)

---

## Orchestrator Module

### Main Entry Point
```python
async def process_bar(
    self,
    bar_data: pd.DataFrame,
    current_price: float
) -> Optional[Signal]:
    """
    Main decision loop - called every 15-minute bar.
    
    Returns:
        Signal if generated and approved, None otherwise
    """
    pass
```

### State Management
```python
@property
def current_state(self) -> SystemState:
    """Current system state"""
    pass

def transition_to(self, new_state: SystemState) -> None:
    """Transition to new state"""
    pass
```

### Errors
- Catches all exceptions from modules
- Logs errors with context
- Enters ERROR state on critical failures
- Never crashes silently

---

## Data Contracts

### Market Data Format
```python
pd.DataFrame with columns:
  - 'open': float
  - 'high': float
  - 'low': float
  - 'close': float
  - 'volume': int
  - Index: DatetimeIndex (timezone-aware)
```

### Configuration Format
```yaml
# instruments.yaml
instruments:
  MNQ:
    point_value: float
    tick_size: float
    # ... other properties

# user_profile.yaml
user_profile:
  capital:
    current_capital: float
  prop_constraints:
    dll_amount: float
    # ... other constraints
```

---

## Async Contracts

### Async Functions
All I/O operations must be async:
- Broker API calls
- Database operations
- WebSocket connections
- File I/O (for large files)

### Sync Functions
These can be sync:
- Calculations (ADX, VWAP, ATR)
- Regime classification
- Risk calculations
- Signal generation

---

## Versioning

### API Version
Current version: **0.1.0**

### Breaking Changes
- Major version bump for breaking changes
- Maintain backward compatibility when possible
- Deprecate before removing

### Module Versioning
Each module can have independent version:
- `telemetry/__version__.py`
- Track in module docstring

