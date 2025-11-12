# Transmission™ Testing Strategy

## Testing Philosophy

**Goal:** Ensure system reliability and correctness before live trading.

**Principles:**
- Test in isolation (unit tests)
- Test integration (module interactions)
- Test edge cases (boundary conditions)
- Test error handling (failure scenarios)
- Test performance (latency, throughput)

---

## Test Structure

```
transmission/tests/
├── unit/
│   ├── test_telemetry.py
│   ├── test_regime.py
│   ├── test_risk.py
│   └── ...
├── integration/
│   ├── test_signal_generation.py
│   ├── test_risk_enforcement.py
│   └── ...
├── fixtures/
│   ├── market_data.py
│   ├── sample_trades.py
│   └── ...
└── conftest.py  # Shared fixtures
```

---

## Unit Tests

### Telemetry Tests

**Test Cases:**
- ✅ ADX calculation with trending data
- ✅ ADX calculation with ranging data
- ✅ VWAP calculation accuracy
- ✅ ATR calculation with volatile data
- ✅ Opening Range detection
- ✅ Spread calculation
- ✅ Order book imbalance calculation
- ✅ Edge cases: insufficient data, NaN values, empty series

**Example:**
```python
def test_calculate_adx_trending_data(telemetry, trending_bars):
    """ADX should be > 25 for trending data"""
    adx = telemetry.calculate_adx(
        trending_bars['high'],
        trending_bars['low'],
        trending_bars['close']
    )
    assert adx > 25
    assert 0 <= adx <= 100
```

### Regime Tests

**Test Cases:**
- ✅ TREND classification (ADX > 25, VWAP slope > median)
- ✅ RANGE classification (ADX < 20, VWAP slope <= median)
- ✅ VOLATILE classification (neither trend nor range)
- ✅ NOTRADE classification (news proximity, wide spread)
- ✅ Regime transitions (trend → range, etc.)
- ✅ Edge cases: boundary values (ADX = 25, ADX = 20)

**Example:**
```python
def test_classify_trend_regime(regime_classifier, trend_features):
    """Should classify as TREND when ADX > 25"""
    regime = regime_classifier.classify(trend_features)
    assert regime == 'TREND'
```

### Risk Tests

**Test Cases:**
- ✅ -2R daily limit enforcement
- ✅ -5R weekly limit enforcement
- ✅ 3 consecutive red days → pause
- ✅ DLL constraint (risk ≤ 0.10 × DLL)
- ✅ Consistency rule enforcement
- ✅ Step-down logic (PF < 1.10 → reduce $R by 30%)
- ✅ Scale-up logic (PF ≥ 1.30 → increase $R by 15%)
- ✅ Edge cases: exactly at limits, boundary conditions

**Example:**
```python
def test_daily_limit_enforcement(risk_governor):
    """Should block trading when daily P&L <= -2R"""
    risk_governor.daily_pnl_r = -2.1
    result = risk_governor.check_tripwires()
    assert result['can_trade'] is False
    assert 'daily limit' in result['reason'].lower()
```

### Strategy Tests

**Test Cases:**
- ✅ VWAP Pullback: generates signal in TREND regime
- ✅ VWAP Pullback: no signal in RANGE regime
- ✅ ORB Retest: generates signal in RANGE regime
- ✅ Signal validation (entry, stop, target distances)
- ✅ Confidence calculation
- ✅ Edge cases: no setup, invalid regime

**Example:**
```python
def test_vwap_pullback_trend_regime(vwap_strategy, trend_features):
    """Should generate signal in TREND regime"""
    signal = vwap_strategy.generate_signal(trend_features, 'TREND', [])
    assert signal is not None
    assert signal.direction in ['LONG', 'SHORT']
    assert signal.entry_price > 0
```

---

## Integration Tests

### Signal Generation Flow

**Test:** Complete signal generation from market data to final signal

```python
async def test_complete_signal_generation(orchestrator, market_data):
    """Test end-to-end signal generation"""
    signal = await orchestrator.process_bar(market_data, current_price=16000.0)
    
    if signal:
        assert signal.entry_price > 0
        assert signal.stop_price > 0
        assert signal.contracts > 0
        assert signal.regime in ['TREND', 'RANGE', 'VOLATILE']
```

### Risk Enforcement Flow

**Test:** Risk governor blocks trades when limits hit

```python
async def test_risk_blocking(orchestrator, risk_governor):
    """Risk governor should block trades at limits"""
    risk_governor.daily_pnl_r = -2.0
    signal = await orchestrator.process_bar(market_data, current_price=16000.0)
    assert signal is None  # Blocked by risk
```

### Strategy Switching

**Test:** Transmission switches strategies based on regime

```python
async def test_strategy_switching(orchestrator):
    """Should switch from VWAP to ORB when regime changes"""
    # Start in TREND (VWAP active)
    signal1 = await orchestrator.process_bar(trend_data, price=16000.0)
    assert orchestrator.current_strategy.name == 'VWAP Pullback'
    
    # Switch to RANGE (ORB active)
    signal2 = await orchestrator.process_bar(range_data, price=16000.0)
    assert orchestrator.current_strategy.name == 'ORB Retest'
```

---

## Test Fixtures

### Market Data Fixtures

```python
@pytest.fixture
def trending_bars():
    """Generate trending market data"""
    dates = pd.date_range(start='2025-01-01', periods=50, freq='15min')
    base_price = 16000.0
    prices = base_price + np.cumsum(np.random.randn(50) * 2)  # Upward trend
    
    return pd.DataFrame({
        'open': prices + np.random.randn(50) * 0.5,
        'high': prices + abs(np.random.randn(50) * 1.0),
        'low': prices - abs(np.random.randn(50) * 1.0),
        'close': prices,
        'volume': np.random.randint(1000, 5000, 50)
    }, index=dates)

@pytest.fixture
def ranging_bars():
    """Generate ranging market data"""
    # Similar but prices oscillate around mean
    pass

@pytest.fixture
def volatile_bars():
    """Generate volatile market data"""
    # High ATR, wide ranges
    pass
```

### Trade Fixtures

```python
@pytest.fixture
def sample_trades():
    """Sample completed trades for analytics testing"""
    return [
        Trade(entry=16000, exit=16050, pnl_r=+1.0, fees=1.0),
        Trade(entry=16000, exit=15950, pnl_r=-1.0, fees=1.0),
        # ... more trades
    ]
```

---

## Performance Tests

### Latency Tests

```python
def test_telemetry_latency(telemetry, large_dataset):
    """Telemetry should process data in < 100ms"""
    start = time.time()
    features = telemetry.calculate_all_features(large_dataset, price=16000.0)
    elapsed = (time.time() - start) * 1000  # Convert to ms
    
    assert elapsed < 100, f"Telemetry took {elapsed}ms (target: <100ms)"
```

### Throughput Tests

```python
def test_regime_classification_throughput(regime_classifier, many_features):
    """Should classify 1000 features in < 1 second"""
    start = time.time()
    for features in many_features:
        regime_classifier.classify(features)
    elapsed = time.time() - start
    
    assert elapsed < 1.0, f"Classified 1000 features in {elapsed}s (target: <1s)"
```

---

## Error Handling Tests

### Data Validation

```python
def test_telemetry_insufficient_data(telemetry):
    """Should raise ValueError for insufficient data"""
    bars = pd.DataFrame({'close': [16000] * 10})  # Only 10 bars
    
    with pytest.raises(ValueError, match="Need at least 20 bars"):
        telemetry.calculate_all_features(bars, current_price=16000.0)
```

### Error Recovery

```python
async def test_broker_disconnect_recovery(orchestrator):
    """Should handle broker disconnect gracefully"""
    # Simulate disconnect
    orchestrator.broker.disconnect()
    
    # System should enter ERROR state, not crash
    assert orchestrator.current_state == SystemState.ERROR
    
    # Should recover on reconnect
    orchestrator.broker.reconnect()
    await orchestrator.recover()
    assert orchestrator.current_state == SystemState.READY
```

---

## Coverage Goals

- **Unit Tests:** 80%+ code coverage
- **Integration Tests:** All critical paths
- **Error Handling:** All exception paths
- **Edge Cases:** Boundary conditions

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=transmission --cov-report=html

# Run specific test file
pytest tests/unit/test_telemetry.py

# Run async tests
pytest tests/integration/ -v

# Run performance tests
pytest tests/performance/ -m performance
```

---

## Continuous Integration

**GitHub Actions:**
- Run tests on every commit
- Check coverage thresholds
- Run linting (ruff, mypy)
- Fail build if tests fail

---

## Test Data Management

- Use fixtures for common data
- Generate synthetic data for edge cases
- Use real historical data for integration tests
- Never use production data in tests

