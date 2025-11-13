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
import { TelemetrySidebar } from '@/components/TelemetrySidebar';
import { useEffect, useState, useMemo } from 'react';
import { WSEvent } from '@/lib/types';
type GearType = 'P' | 'R' | 'N' | 'D' | 'L';

export default function Dashboard() {
  const { message, isConnected } = useWebSocket();
  const addWSEvent = useUIStore((state) => state.addWSEvent);
  const addToast = useUIStore((state) => state.addToast);
  const [activeTab, setActiveTab] = useState<'overview' | 'trading' | 'learning'>('overview');

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

  // Gear performance data (not currently used in UI)
  // const { data: gearPerformance } = useQuery({
  //   queryKey: ['gear-performance'],
  //   queryFn: async () => (await api.get('/system/gear/performance')).data,
  //   refetchInterval: 10000,
  // });

  // Gear history (not currently used in UI)
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

  // Build recent insights from trades (not currently used in UI)
  // const recentInsights = useMemo(() => {
  //   if (!tradesData?.trades) return [];

  //   return tradesData.trades.slice(0, 10).map((trade: any) => ({
  //     timestamp: trade.exit_time || trade.entry_time,
  //     symbol: trade.symbol,
  //     direction: trade.direction,
  //     gear_at_entry: trade.gear_at_entry || 'N',
  //     gear_at_exit: trade.gear_at_exit || 'N',
  //     regime: trade.regime || 'UNKNOWN',
  //     result_r: trade.pnl_r || 0,
  //     win_loss: trade.pnl_r > 0 ? 'Win' : 'Loss',
  //     acceptance_reason: trade.acceptance_reason,
  //     rejection_reason: trade.rejection_reason
  //   }));
  // }, [tradesData]);

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
          const rejectEvent = event as any;
          addToast({
            type: 'warning',
            message: `Signal rejected: ${rejectEvent.reason || 'Unknown reason'}`,
          });
          break;
        case 'order_submitted':
          const orderEvent = event as any;
          addToast({
            type: 'info',
            message: `Order submitted: ${orderEvent.order_id || 'Unknown'}`,
          });
          break;
        case 'fill':
          const fillEvent = event as any;
          addToast({
            type: 'success',
            message: `Order filled: ${fillEvent.fill?.broker_order_id || 'Unknown'}`,
          });
          break;
        case 'flatten_all':
          const flattenEvent = event as any;
          addToast({
            type: 'warning',
            message: `All positions flattened: ${flattenEvent.reason || 'Unknown reason'}`,
          });
          break;
        case 'regime_change':
          const regimeEvent = event as any;
          addToast({
            type: 'info',
            message: `Regime changed to: ${regimeEvent.regime || 'Unknown'}`,
          });
          break;
        case 'gear_change':
          const gearEvent = event as any;
          addToast({
            type: 'info',
            message: `⚙️ Gear shift: ${gearEvent.from_gear || '?'} → ${gearEvent.to_gear || '?'}`,
          });
          break;
      }
    }
  }, [message, addWSEvent, addToast]);

  const currentGear = (status?.gear || 'N') as GearType;
  const currentRegime = status?.current_regime || 'UNKNOWN';

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-black text-gradient bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent">
            Transmission™
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Adaptive Risk Management • Beyond Candlesticks
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium backdrop-blur-md ${
            isConnected
              ? 'bg-green-500/20 text-green-400 border border-green-500/30'
              : 'bg-red-500/20 text-red-400 border border-red-500/30'
          }`}>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
            {isConnected ? 'Live' : 'Disconnected'}
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="glass rounded-2xl p-2 inline-flex gap-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-6 py-2 rounded-xl font-medium transition-all ${
            activeTab === 'overview'
              ? 'bg-white/20 text-white shadow-lg'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('trading')}
          className={`px-6 py-2 rounded-xl font-medium transition-all ${
            activeTab === 'trading'
              ? 'bg-white/20 text-white shadow-lg'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          Trading
        </button>
        <button
          onClick={() => setActiveTab('learning')}
          className={`px-6 py-2 rounded-xl font-medium transition-all ${
            activeTab === 'learning'
              ? 'bg-white/20 text-white shadow-lg'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          Learning
        </button>
      </div>

      {/* Overview Tab - Transmission UI */}
      {activeTab === 'overview' && (
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
      )}

      {/* Trading Tab - Orders & Positions */}
      {activeTab === 'trading' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <OrdersTable orders={ordersData?.orders || []} isLoading={ordersLoading} />
            <PositionsTable positions={positionsData?.positions || []} isLoading={positionsLoading} />
          </div>

          {/* Manual Signal Submission Section */}
          <div className="mt-8">
            <ManualSignalForm />
          </div>
        </div>
      )}

      {/* Learning Tab - Performance Analysis */}
      {activeTab === 'learning' && (
        <div className="space-y-6">
          <div className="glass rounded-2xl p-6">
            <h2 className="text-2xl font-bold text-white mb-4">Performance Analysis</h2>
            <p className="text-gray-400">Learning dashboard coming soon...</p>
          </div>
        </div>
      )}
    </div>
  );
}

