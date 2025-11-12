"""
Trade API Routes

Endpoints for trade history and management.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
from transmission.api.models.trade import TradeResponse, TradeListResponse
from transmission.database import Database

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("/", response_model=TradeListResponse)
async def get_trades(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    strategy: Optional[str] = None,
    regime: Optional[str] = None,
    symbol: Optional[str] = None
):
    """
    Get trade history.
    
    Args:
        limit: Number of trades to return (1-100)
        offset: Pagination offset
        strategy: Filter by strategy name
        regime: Filter by regime
        symbol: Filter by symbol
    """
    try:
        db = Database()
        
        # Build query
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if strategy:
            query += " AND strategy_used = ?"
            params.append(strategy)
        
        if regime:
            query += " AND regime_at_entry = ?"
            params.append(regime)
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        query += " ORDER BY timestamp_entry DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = db.conn.cursor()
        cursor.execute(query, params)
        trades = [dict(row) for row in cursor.fetchall()]
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM trades WHERE 1=1"
        count_params = []
        if strategy:
            count_query += " AND strategy_used = ?"
            count_params.append(strategy)
        if regime:
            count_query += " AND regime_at_entry = ?"
            count_params.append(regime)
        if symbol:
            count_query += " AND symbol = ?"
            count_params.append(symbol)
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        
        db.close()
        
        return TradeListResponse(
            trades=[TradeResponse(**trade) for trade in trades],
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trades: {str(e)}")


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: int):
    """Get a specific trade by ID"""
    try:
        db = Database()
        cursor = db.conn.cursor()
        
        cursor.execute("SELECT * FROM trades WHERE trade_id = ?", (trade_id,))
        trade = cursor.fetchone()
        
        db.close()
        
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        return TradeResponse(**dict(trade))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trade: {str(e)}")


@router.get("/recent/{limit}", response_model=TradeListResponse)
async def get_recent_trades(limit: int):
    """Get recent trades"""
    try:
        db = Database()
        trades = db.get_recent_trades(limit=limit)
        db.close()
        
        return TradeListResponse(
            trades=[TradeResponse(**trade) for trade in trades],
            total=len(trades),
            limit=limit,
            offset=0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent trades: {str(e)}")

