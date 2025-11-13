/**
 * VEGUS Dashboard - Main Trading Interface
 * Professional Adaptive Trading Platform with Gear State Visualization
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useWebSocket } from '@/lib/ws';
import { useUIStore } from '@/state/uiStore';
import { StatusCard } from '@/components/StatusCard';
import { KillSwitch } from '@/components/KillSwitch';
import { OrdersTable } from '@/components/OrdersTable';
import { PositionsTable } from '@/components/PositionsTable';
import { ManualSignalForm } from '@/components/ManualSignalForm';
import { GearIndicator } from '@/components/GearIndicator';
import { TrackView } from '@/components/TrackView';
import { TelemetrySidebar} from '@/components/TelemetrySidebar';
import { LearningDashboard } from '@/components/LearningDashboard';
import { useEffect, useState, useMemo } from 'react';
import { WSEvent } from '@/lib/types';
import type { GearType } from '@/lib/types';
import { Activity, TrendingUp, Shield, Target, Zap, BarChart3 } from 'lucide-react';

export default function Dashboard() {
  const { message, isConnected } = useWebSocket();
  const addWSEvent = useUIStore((state) => state.addWSEvent);
  const addToast = useUIStore((state) => state.addToast);
  const [activeTab, setActiveTab] = useState<'overview' | 'trading' | 'analytics'>('overview');

  // System status (includes gear state)
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['system-status'],
    queryFn: async () => (await api.get('/system/status')).data,
    refetchInterval: 2000,
  });

  // Open orders
  const { data: ordersData, isLoading: ordersLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: async () => (await api.get('/system/orders')).data,
    refetchInterval: 3000,
  });

  // Positions
  const { data: positionsData, isLoading: positionsLoading } = useQuery({
    queryKey: ['positions'],
    queryFn: async () => (await api.get('/system/positions')).data,
    refetchInterval: 3000,
  });

  // Gear performance data
  const { data: gearPerformance } = useQuery({
    queryKey: ['gear-performance'],
    queryFn: async () => (await api.get('/system/gear/performance')).data,
    refetchInterval: 10000,
  });

  // Gear history (for future use)
  // const { data: gearHistory } = useQuery({
  //   queryKey: ['gear-history'],
  //   queryFn: async () => (await api.get('/system/gear/history?limit=20')).data,
  //   refetchInterval: 5000,
  // });

  // Trades for track view
  const { data: tradesData } = useQuery({
    queryKey: ['trades'],
    queryFn: async () => (await api.get('/trades?limit=50')).data,
    refetchInterval: 5000,
  });

  // Process trades into track view format
  const tradeHistory = useMemo(() => {
    if (!tradesData?.trades) return [];

    // Build equity curve from trades
    let runningEquity = 0;
    return tradesData.trades.map((trade: any) => {
      runningEquity += trade.pnl_r || 0;
      return {
        timestamp: trade.exit_time || trade.entry_time,
        equity_r: runningEquity,
        regime: trade.regime || 'UNKNOWN',
        gear: trade.gear_at_entry || 'N',
        win_loss: trade.pnl_r > 0 ? 'Win' : 'Loss',
        event: trade.event_type // Optional: spread_spike, news_blackout, etc.
      };
    });
  }, [tradesData]);

  // Build recent insights from trades
  const recentInsights = useMemo(() => {
    if (!tradesData?.trades) return [];

    return tradesData.trades.slice(0, 10).map((trade: any) => ({
      timestamp: trade.exit_time || trade.entry_time,
      symbol: trade.symbol,
      direction: trade.direction,
      gear_at_entry: trade.gear_at_entry || 'N',
      gear_at_exit: trade.gear_at_exit || 'N',
      regime: trade.regime || 'UNKNOWN',
      result_r: trade.pnl_r || 0,
      win_loss: trade.pnl_r > 0 ? 'Win' : 'Loss',
      acceptance_reason: trade.acceptance_reason,
      rejection_reason: trade.rejection_reason
    }));
  }, [tradesData]);

  // Mock telemetry data (replace with real API when available)
  const telemetryData = useMemo(() => ({
    marketRPM: Math.min(Math.max((status?.weekly_pnl_r || 0) * 20 + 50, 0), 100),
    mentalState: status?.can_trade ? 4 : 2,
    spreadStability: status?.can_trade ? 85 : 45,
    dllRemaining: Math.max(2.0 + (status?.daily_pnl_r || 0), 0),
    confidenceScore: status?.can_trade ? 0.75 : 0.35,
    executionQuality: 0.88
  }), [status]);

  // Handle WebSocket messages
  useEffect(() => {
    if (message) {
      const event = message as WSEvent;
      addWSEvent(event);

      // Show toast notifications for important events
      switch (event.type) {
        case 'constraint_violation':
        case 'guard_reject':
          addToast({
            type: 'warning',
            message: `⚠️ Signal rejected: ${event.reason || 'Unknown reason'}`,
          });
          break;
        case 'order_submitted':
          addToast({
            type: 'info',
            message: `📤 Order submitted: ${event.order_id}`,
          });
          break;
        case 'fill':
          addToast({
            type: 'success',
            message: `✅ Order filled: ${event.fill?.broker_order_id || 'Unknown'}`,
          });
          break;
        case 'flatten_all':
          addToast({
            type: 'warning',
            message: `🛑 All positions flattened: ${event.reason || 'Unknown reason'}`,
          });
          break;
        case 'regime_change':
          addToast({
            type: 'info',
            message: `🔄 Regime changed to: ${event.regime}`,
          });
          break;
        case 'gear_change':
          addToast({
            type: 'info',
            message: `⚙️ Gear shift: ${event.from_gear} → ${event.to_gear} (${event.gear_reason})`,
          });
          break;
      }
    }
  }, [message, addWSEvent, addToast]);

  const currentGear = (status?.gear || 'N') as GearType;
  const currentRegime = status?.current_regime || 'UNKNOWN';

  // Quick stats for header
  const quickStats = {
    dailyPnL: status?.daily_pnl_r || 0,
    weeklyPnL: status?.weekly_pnl_r || 0,
    openPositions: positionsData?.positions?.length || 0,
    openOrders: ordersData?.orders?.length || 0,
  };

  return (
    <div className="min-h-screen">
      {/* Professional Header */}
      <header className="glass-strong sticky top-0 z-50 border-b border-white/10">
        <div className="container-2xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo & Brand */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-primary flex items-center justify-center">
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-black text-gradient">
                    VEGUS
                  </h1>
                  <p className="text-xs text-neutral-400">Adaptive Trading Platform</p>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="hidden lg:flex items-center gap-6">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-green-400" />
                </div>
                <div>
                  <div className="text-xs text-neutral-400">Daily P&L</div>
                  <div className={`text-sm font-bold ${quickStats.dailyPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {quickStats.dailyPnL >= 0 ? '+' : ''}{quickStats.dailyPnL.toFixed(2)}R
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                  <Activity className="w-4 h-4 text-blue-400" />
                </div>
                <div>
                  <div className="text-xs text-neutral-400">Positions</div>
                  <div className="text-sm font-bold text-white">{quickStats.openPositions}</div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <Target className="w-4 h-4 text-purple-400" />
                </div>
                <div>
                  <div className="text-xs text-neutral-400">Orders</div>
                  <div className="text-sm font-bold text-white">{quickStats.openOrders}</div>
                </div>
              </div>
            </div>

            {/* Connection Status */}
            <div className="flex items-center gap-4">
              <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium glass ${
                isConnected
                  ? 'border border-green-500/30'
                  : 'border border-red-500/30'
              }`}>
                <div className={isConnected ? 'status-online' : 'status-offline'} />
                <span className={isConnected ? 'text-green-400' : 'text-red-400'}>
                  {isConnected ? 'Live' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container-2xl mx-auto px-6 py-8">

        {/* Navigation Tabs */}
        <div className="mb-8 glass rounded-2xl p-2 inline-flex gap-2">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-6 py-3 rounded-xl font-semibold flex items-center gap-2 transition-all ${
              activeTab === 'overview'
                ? 'bg-white/20 text-white shadow-lg'
                : 'text-neutral-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Overview
          </button>
          <button
            onClick={() => setActiveTab('trading')}
            className={`px-6 py-3 rounded-xl font-semibold flex items-center gap-2 transition-all ${
              activeTab === 'trading'
                ? 'bg-white/20 text-white shadow-lg'
                : 'text-neutral-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Activity className="w-4 h-4" />
            Trading
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-6 py-3 rounded-xl font-semibold flex items-center gap-2 transition-all ${
              activeTab === 'analytics'
                ? 'bg-white/20 text-white shadow-lg'
                : 'text-neutral-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Shield className="w-4 h-4" />
            Analytics
          </button>
        </div>

        {/* Overview Tab - VEGUS Transmission UI */}
        {activeTab === 'overview' && (
          <div className="space-y-8 animate-fade-in">
            <div className="grid grid-cols-12 gap-6">
          {/* Panel A: Track View (Main - 8 cols) */}
          <div className="col-span-12 lg:col-span-8">
            <TrackView
              tradeHistory={tradeHistory}
              currentGear={currentGear}
              currentRegime={currentRegime}
            />
          </div>

          {/* Panel B: Telemetry + Gear (Sidebar - 4 cols) */}
          <div className="col-span-12 lg:col-span-4 space-y-6">
            <GearIndicator
              currentGear={currentGear}
              reason={status?.gear_reason || 'Initializing...'}
              riskMultiplier={status?.gear_risk_multiplier || 0}
            />
            <TelemetrySidebar data={telemetryData} />
          </div>

          {/* Panel C: System Stats (Full width below) */}
          <div className="col-span-12 grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <StatusCard status={status} isLoading={statusLoading} />
            </div>
            <div>
              <KillSwitch />
            </div>
          </div>
            </div>
          </div>
        )}

        {/* Trading Tab - Orders & Positions */}
        {activeTab === 'trading' && (
          <div className="space-y-8 animate-fade-in">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <OrdersTable orders={ordersData?.orders || []} isLoading={ordersLoading} />
            <PositionsTable positions={positionsData?.positions || []} isLoading={positionsLoading} />
          </div>

            {/* Manual Signal Submission Section */}
            <div>
              <ManualSignalForm />
            </div>
          </div>
        )}

        {/* Analytics Tab - Performance Analysis */}
        {activeTab === 'analytics' && (
          <div className="space-y-8 animate-fade-in">
            <LearningDashboard
              gearPerformance={gearPerformance || []}
              recentInsights={recentInsights}
            />
          </div>
        )}
      </main>

      {/* Professional Footer */}
      <footer className="border-t border-white/10 mt-16">
        <div className="container-2xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between text-sm text-neutral-400">
            <div>
              © 2025 VEGUS. Adaptive Trading Platform.
            </div>
            <div className="flex items-center gap-6">
              <span>API v1.0</span>
              <span>Build 1.0.0</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

