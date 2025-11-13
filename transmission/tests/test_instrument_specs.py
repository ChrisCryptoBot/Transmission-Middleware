"""
Tests for Instrument Specification Service
"""

import pytest
from transmission.config.instrument_specs import InstrumentSpecService, InstrumentSpec


def test_load_instruments():
    """Test loading instruments from YAML"""
    service = InstrumentSpecService()
    
    assert len(service.list_symbols()) >= 1
    assert 'MNQ' in service.list_symbols()


def test_get_spec():
    """Test getting instrument spec"""
    service = InstrumentSpecService()
    
    mnq_spec = service.get_spec('MNQ')
    assert mnq_spec.symbol == 'MNQ'
    assert mnq_spec.point_value == 2.0
    assert mnq_spec.tick_size == 0.25
    assert mnq_spec.tick_value == 0.50
    assert mnq_spec.asset_class == 'futures'


def test_get_helpers():
    """Test helper methods"""
    service = InstrumentSpecService()
    
    assert service.get_tick_size('MNQ') == 0.25
    assert service.get_point_value('MNQ') == 2.0
    assert service.get_tick_value('MNQ') == 0.50
    assert service.get_asset_class('MNQ') == 'futures'


def test_multiple_instruments():
    """Test loading multiple instruments"""
    service = InstrumentSpecService()
    
    # Test MNQ
    mnq = service.get_spec('MNQ')
    assert mnq.point_value == 2.0
    
    # Test MES (if added)
    if 'MES' in service.list_symbols():
        mes = service.get_spec('MES')
        assert mes.point_value == 5.0
        assert mes.tick_value == 1.25
    
    # Test ES (if added)
    if 'ES' in service.list_symbols():
        es = service.get_spec('ES')
        assert es.point_value == 50.0
        assert es.tick_value == 12.50
    
    # Test NQ (if added)
    if 'NQ' in service.list_symbols():
        nq = service.get_spec('NQ')
        assert nq.point_value == 20.0
        assert nq.tick_value == 5.00


def test_invalid_symbol():
    """Test error handling for invalid symbol"""
    service = InstrumentSpecService()
    
    with pytest.raises(ValueError, match="not found"):
        service.get_spec('INVALID')


def test_asset_class_inference():
    """Test asset class inference"""
    service = InstrumentSpecService()
    
    # Futures should be inferred correctly
    assert service.get_asset_class('MNQ') == 'futures'
    if 'MES' in service.list_symbols():
        assert service.get_asset_class('MES') == 'futures'

