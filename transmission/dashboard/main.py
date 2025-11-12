"""
Transmission™ Streamlit Dashboard

MVP Dashboard for monitoring system status, trades, and performance.
Connects to FastAPI backend for data.
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import Optional
import plotly.graph_objects as go
import plotly.express as px

# Page config
st.set_page_config(
    page_title="Transmission™ Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_BASE_URL = st.sidebar.text_input(
    "API URL",
    value="http://localhost:8000",
    help="FastAPI backend URL"
)

# Custom CSS for glassmorphism effect
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    .regime-indicator {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
    }
    .regime-trend {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        border: 2px solid #22c55e;
    }
    .regime-range {
        background: rgba(251, 191, 36, 0.2);
        color: #fbbf24;
        border: 2px solid #fbbf24;
    }
    .regime-volatile {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 2px solid #ef4444;
    }
    .regime-notrade {
        background: rgba(107, 114, 128, 0.2);
        color: #6b7280;
        border: 2px solid #6b7280;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=5)  # Cache for 5 seconds
def fetch_system_status():
    """Fetch system status from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/system/status", timeout=2)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching system status: {e}")
        return None


@st.cache_data(ttl=5)
def fetch_risk_status():
    """Fetch risk status from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/system/risk", timeout=2)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching risk status: {e}")
        return None


@st.cache_data(ttl=10)
def fetch_recent_trades(limit: int = 20):
    """Fetch recent trades from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/trades/recent/{limit}", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get("trades", [])
        return []
    except Exception as e:
        st.error(f"Error fetching trades: {e}")
        return []


@st.cache_data(ttl=30)
def fetch_metrics():
    """Fetch performance metrics from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/metrics?window=20", timeout=2)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching metrics: {e}")
        return None


def get_regime_color(regime: Optional[str]) -> str:
    """Get color class for regime"""
    if not regime:
        return "regime-notrade"
    
    regime_lower = regime.lower()
    if "trend" in regime_lower:
        return "regime-trend"
    elif "range" in regime_lower:
        return "regime-range"
    elif "volatile" in regime_lower:
        return "regime-volatile"
    else:
        return "regime-notrade"


def get_regime_emoji(regime: Optional[str]) -> str:
    """Get emoji for regime"""
    if not regime:
        return "⏸️"
    
    regime_lower = regime.lower()
    if "trend" in regime_lower:
        return "📈"
    elif "range" in regime_lower:
        return "↔️"
    elif "volatile" in regime_lower:
        return "⚡"
    else:
        return "⏸️"


def main():
    """Main dashboard"""
    
    # Header
    st.title("⚙️ Transmission™ Dashboard")
    st.markdown("**Adaptive Trading Middleware - Real-Time Monitoring**")
    
    # Check API connection
    try:
        health = requests.get(f"{API_BASE_URL}/api/system/health", timeout=2)
        if health.status_code == 200:
            st.sidebar.success("✅ API Connected")
        else:
            st.sidebar.error("❌ API Error")
            st.stop()
    except Exception as e:
        st.sidebar.error(f"❌ Cannot connect to API: {e}")
        st.info(f"💡 Make sure the API is running at {API_BASE_URL}")
        st.stop()
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (5s)", value=True)
    if auto_refresh:
        st.rerun()
    
    # Fetch data
    system_status = fetch_system_status()
    risk_status = fetch_risk_status()
    recent_trades = fetch_recent_trades(20)
    metrics = fetch_metrics()
    
    # Main layout
    col1, col2, col3, col4 = st.columns(4)
    
    # System Status Card
    with col1:
        st.markdown("### System Status")
        if system_status:
            state = system_status.get("system_state", "unknown")
            st.markdown(f"**{state.upper()}**")
            regime = system_status.get("current_regime")
            if regime:
                emoji = get_regime_emoji(regime)
                st.markdown(f"### {emoji} {regime}")
        else:
            st.markdown("**Loading...**")
    
    # Risk Status Card
    with col2:
        st.markdown("### Risk Status")
        if risk_status:
            can_trade = risk_status.get("can_trade", False)
            action = risk_status.get("action", "UNKNOWN")
            daily_pnl = risk_status.get("daily_pnl_r", 0.0)
            
            if can_trade:
                st.success(f"✅ **{action}**")
            else:
                st.error(f"❌ **{action}**")
            
            st.metric("Daily P&L", f"{daily_pnl:+.2f}R")
        else:
            st.markdown("**Loading...**")
    
    # Current R Card
    with col3:
        st.markdown("### Position Size")
        if risk_status:
            current_r = risk_status.get("current_r", 5.0)
            st.metric("Current $R", f"${current_r:.2f}")
        else:
            st.metric("Current $R", "$5.00")
    
    # Active Strategy Card
    with col4:
        st.markdown("### Active Strategy")
        if system_status:
            strategy = system_status.get("active_strategy", "None")
            st.markdown(f"**{strategy}**")
        else:
            st.markdown("**Loading...**")
    
    st.divider()
    
    # Regime Indicator (Large)
    if system_status:
        regime = system_status.get("current_regime")
        if regime:
            regime_color = get_regime_color(regime)
            emoji = get_regime_emoji(regime)
            st.markdown(
                f'<div class="regime-indicator {regime_color}">'
                f'{emoji} Current Regime: {regime.upper()}'
                f'</div>',
                unsafe_allow_html=True
            )
    
    st.divider()
    
    # Performance Metrics
    st.markdown("## 📊 Performance Metrics")
    
    if metrics:
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            pf = metrics.get("profit_factor")
            if pf:
                st.metric("Profit Factor", f"{pf:.2f}")
            else:
                st.metric("Profit Factor", "N/A")
        
        with metric_col2:
            expected_r = metrics.get("expected_r")
            if expected_r:
                st.metric("Expected R", f"{expected_r:+.2f}")
            else:
                st.metric("Expected R", "N/A")
        
        with metric_col3:
            win_rate = metrics.get("win_rate")
            if win_rate:
                st.metric("Win Rate", f"{win_rate*100:.1f}%")
            else:
                st.metric("Win Rate", "N/A")
        
        with metric_col4:
            total_trades = metrics.get("total_trades", 0)
            st.metric("Total Trades", total_trades)
    else:
        st.info("No metrics available yet. Start trading to see performance data.")
    
    st.divider()
    
    # Recent Trades
    st.markdown("## 📋 Recent Trades")
    
    if recent_trades:
        # Convert to DataFrame
        df = pd.DataFrame(recent_trades)
        
        # Format columns
        if "timestamp_entry" in df.columns:
            df["timestamp_entry"] = pd.to_datetime(df["timestamp_entry"])
        
        # Display table
        st.dataframe(
            df[["trade_id", "symbol", "trade_type", "entry_price", "result_r", "win_loss", "exit_reason"]].head(10),
            use_container_width=True,
            hide_index=True
        )
        
        # P&L Chart
        if "result_r" in df.columns and len(df) > 0:
            st.markdown("### P&L Chart")
            fig = go.Figure()
            
            # Filter out None values
            pnl_data = df[df["result_r"].notna()]["result_r"]
            
            if len(pnl_data) > 0:
                fig.add_trace(go.Scatter(
                    y=pnl_data.cumsum(),
                    mode='lines+markers',
                    name='Cumulative P&L (R)',
                    line=dict(color='#22c55e', width=2)
                ))
                
                fig.update_layout(
                    title="Cumulative P&L (R)",
                    xaxis_title="Trade #",
                    yaxis_title="Cumulative R",
                    height=400,
                    template="plotly_dark"
                )
                
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trades yet. Signals will appear here when generated.")
    
    st.divider()
    
    # Risk Details
    st.markdown("## ⚠️ Risk Details")
    
    if risk_status:
        risk_col1, risk_col2, risk_col3 = st.columns(3)
        
        with risk_col1:
            daily_pnl = risk_status.get("daily_pnl_r", 0.0)
            weekly_pnl = risk_status.get("weekly_pnl_r", 0.0)
            st.metric("Daily P&L", f"{daily_pnl:+.2f}R")
            st.metric("Weekly P&L", f"{weekly_pnl:+.2f}R")
        
        with risk_col2:
            consecutive_red = risk_status.get("consecutive_red_days", 0)
            st.metric("Consecutive Red Days", consecutive_red)
            current_r = risk_status.get("current_r", 5.0)
            st.metric("Current $R", f"${current_r:.2f}")
        
        with risk_col3:
            reason = risk_status.get("reason", "All systems operational")
            st.info(f"**Status:** {reason}")
    
    st.divider()
    
    # Kill Switch / Flatten All
    st.markdown("## 🔴 Emergency Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔴 Flatten All / Kill Switch", type="primary", use_container_width=True):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/system/flatten_all",
                    json={"reason": "manual_button"},
                    timeout=2
                )
                if response.status_code == 200:
                    st.success("✅ All positions flattened successfully")
                else:
                    st.error(f"❌ Error: {response.text}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    st.divider()
    
    # Open Orders
    st.markdown("## 📋 Open Orders")
    try:
        orders_response = requests.get(f"{API_BASE_URL}/api/system/orders", timeout=2)
        if orders_response.status_code == 200:
            orders_data = orders_response.json()
            orders = orders_data.get("orders", [])
            
            if orders:
                df_orders = pd.DataFrame(orders)
                st.dataframe(df_orders, use_container_width=True, hide_index=True)
            else:
                st.info("No open orders")
        else:
            st.warning("Could not fetch orders")
    except Exception as e:
        st.warning(f"Error fetching orders: {e}")
    
    st.divider()
    
    # Positions
    st.markdown("## 📊 Active Positions")
    try:
        positions_response = requests.get(f"{API_BASE_URL}/api/system/positions", timeout=2)
        if positions_response.status_code == 200:
            positions_data = positions_response.json()
            positions = positions_data.get("positions", [])
            
            if positions:
                df_positions = pd.DataFrame(positions)
                st.dataframe(df_positions, use_container_width=True, hide_index=True)
            else:
                st.info("No active positions")
        else:
            st.warning("Could not fetch positions")
    except Exception as e:
        st.warning(f"Error fetching positions: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: rgba(255,255,255,0.5);'>"
        "Transmission™ - Adaptive Trading Middleware | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

