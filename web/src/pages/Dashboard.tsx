/**
 * VEGUS Dashboard - Complete Implementation
 * Based on UI_Concept.txt specifications
 */

import { useState, useEffect } from 'react';
import { useWebSocket } from '@/lib/ws';
import {
  WSGearChangeEvent,
} from '@/lib/types';
import { VegusScoreGauge } from '@/components/VegusScoreGauge';
import { TransmissionGearDial } from '@/components/TransmissionGearDial';
import { RiskMeter } from '@/components/RiskMeter';
import { ExecutionHealthCard } from '@/components/ExecutionHealthCard';
import { MarketEnvironmentHeatmap } from '@/components/MarketEnvironmentHeatmap';
import { PriceChart } from '@/components/PriceChart';
import { ModeToggle, UserMode, ComplexityMode } from '@/components/ModeToggle';
import { ProposedTradeCard } from '@/components/ProposedTradeCard';
import { BotStatusPanel } from '@/components/BotStatusPanel';
import { GlassCard } from '@/components/ui/GlassCard';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Zap } from 'lucide-react';
import { Sidebar } from '@/components/Sidebar';
import { AccountSelector } from '@/components/AccountSelector';
import { NotificationCenter, Notification } from '@/components/NotificationCenter';
import { Tooltip } from '@/components/Tooltip';
import { StrategyOddsPanel } from '@/components/StrategyOddsPanel';
import { TransmissionVisualization } from '@/components/TransmissionVisualization';
import { VegusScoreBreakdown } from '@/components/VegusScoreBreakdown';
import { DirectionalBiasPanel } from '@/components/DirectionalBiasPanel';
import { OddsTimeline } from '@/components/OddsTimeline';
import { IntelligenceLayers } from '@/components/IntelligenceLayers';
import {
  mockSystemStatus,
  mockRegimeState,
  mockDirectionalState,
  mockBars,
  mockVegusScore,
  mockRiskState,
  mockExecutionState,
  mockGearDecision,
} from '@/lib/mockData';

export default function Dashboard() {
  const [userMode, setUserMode] = useState<UserMode>('manual');
  const [complexityMode, setComplexityMode] = useState<ComplexityMode>('beginner');
  const [botRunning, setBotRunning] = useState(false);
  const [selectedAccountId, setSelectedAccountId] = useState('default');
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const { message, isConnected } = useWebSocket();

  // Use mock data instead of API calls
  const status = mockSystemStatus;
  const statusLoading = false;

  // Process WebSocket messages
  useEffect(() => {
    if (message && message.type === 'gear_change') {
      const gearEvent = message as WSGearChangeEvent;
      console.log('Gear change:', gearEvent);
    }
  }, [message]);

  // Use mock data
  const gearDecision = mockGearDecision;
  const riskState = mockRiskState;
  const executionState = mockExecutionState;
  const vegusScore = mockVegusScore;
  const regimeState = mockRegimeState;
  const directionalState = mockDirectionalState;

  // Mock proposed trade (for assisted mode)
  const proposedTrade = userMode === 'assisted' && status.can_trade
    ? {
        symbol: 'MNQ',
        direction: 'long' as const,
        entryPrice: 15050,
        stopLoss: 15000,
        takeProfit: 15150,
        size: 1,
        projectedR: 2.0,
        strategyConfidence: 0.75,
        reasonTags: ['TREND_HIGH', 'VWAP_PULLBACK'],
        currentRisk: `${status.daily_pnl_r.toFixed(2)}R used`,
        environmentQuality: vegusScore?.label || 'Favorable',
      }
    : null;

  // Mock accounts (should come from backend)
  const accounts = [
    {
      accountId: 'default',
      baseCurrency: 'USD',
      equity: 10000,
      maxRiskPerTradePct: 1.0,
      maxDailyRiskR: 2,
      maxWeeklyRiskR: 5,
      propMode: false,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="flex">
        {/* Left Sidebar */}
        <Sidebar className="hidden lg:block" />

        {/* Main Content */}
        <div className="flex-1 p-4 md:p-8">
          {/* Header */}
          <div className="max-w-[1440px] mx-auto mb-6">
            <GlassCard className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500">
                  <Zap className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-white">VEGUS</h1>
                  <p className="text-white/60">Universal Trading Transmission</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <AccountSelector
                  accounts={accounts}
                  selectedAccountId={selectedAccountId}
                  onAccountChange={setSelectedAccountId}
                />
                <NotificationCenter
                  notifications={notifications}
                  onDismiss={(id) => setNotifications((n) => n.filter((not) => not.id !== id))}
                  onMarkAllRead={() => setNotifications((n) => n.map((not) => ({ ...not, read: true })))}
                />
                <StatusBadge
                  status={isConnected ? '🟢 Connected' : '🔴 Disconnected'}
                  color={isConnected ? 'green' : 'red'}
                />
                <StatusBadge
                  status={status.system_state || 'Loading...'}
                  color={status.can_trade ? 'green' : 'yellow'}
                />
                <div className="text-right">
                  <div className="text-xs text-white/60">API Latency</div>
                  <div className="text-sm font-medium text-white">{executionState?.apiLatencyMs || 0}ms</div>
                </div>
              </div>
            </GlassCard>
          </div>

          {/* Mode Toggle */}
          <div className="max-w-[1440px] mx-auto mb-6">
            <ModeToggle
              userMode={userMode}
              complexityMode={complexityMode}
              onUserModeChange={setUserMode}
              onComplexityModeChange={setComplexityMode}
            />
          </div>

          {/* Top Row - Overview Cards */}
          <div className="max-w-[1440px] mx-auto mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Tooltip
                content={
                  <div>
                    <div className="font-bold mb-2">VEGUS Score Components:</div>
                    <div>Market Quality: {(vegusScore?.componentBreakdown.marketQuality || 0) * 100}%</div>
                    <div>Risk Pressure: {(vegusScore?.componentBreakdown.riskPressure || 0) * 100}%</div>
                    <div>Execution Quality: {(vegusScore?.componentBreakdown.executionQuality || 0) * 100}%</div>
                    <div>Psychological Safety: {(vegusScore?.componentBreakdown.psychologicalSafety || 0) * 100}%</div>
                  </div>
                }
              >
                <div>
                  <VegusScoreGauge score={vegusScore} isLoading={statusLoading} />
                </div>
              </Tooltip>
              <Tooltip
                content={
                  <div>
                    <div className="font-bold mb-2">Gear Decision:</div>
                    <div>Current: {gearDecision?.gear}</div>
                    <div>Confidence: {gearDecision ? Math.round(gearDecision.confidence * 100) : 0}%</div>
                    <div>Direction: {gearDecision?.direction}</div>
                    {gearDecision?.reasonTags && gearDecision.reasonTags.length > 0 && (
                      <div className="mt-2">
                        <div className="font-bold">Reasons:</div>
                        {gearDecision.reasonTags.map((tag, i) => (
                          <div key={i}>• {tag}</div>
                        ))}
                      </div>
                    )}
                  </div>
                }
              >
                <div>
                  <TransmissionGearDial gear={gearDecision} isLoading={statusLoading} />
                </div>
              </Tooltip>
              <Tooltip
                content={
                  <div>
                    <div className="font-bold mb-2">Risk Status:</div>
                    <div>Daily R: {riskState?.dailyRUsed.toFixed(2)}R / 2R limit</div>
                    <div>Weekly R: {riskState?.weeklyRUsed.toFixed(2)}R / 5R limit</div>
                    <div>Drawdown: {riskState?.currentDrawdownPct.toFixed(2)}%</div>
                  </div>
                }
              >
                <div>
                  <RiskMeter risk={riskState} isLoading={statusLoading} />
                </div>
              </Tooltip>
              <Tooltip
                content={
                  <div>
                    <div className="font-bold mb-2">Execution Health:</div>
                    <div>Spread: {executionState?.spreadBps.toFixed(2)} bps</div>
                    <div>Latency: {executionState?.apiLatencyMs}ms</div>
                    <div>Book Depth: {executionState?.bookThin ? 'Thin' : 'Good'}</div>
                    <div>Connection: {executionState?.connectionUnstable ? 'Unstable' : 'Stable'}</div>
                  </div>
                }
              >
                <div>
                  <ExecutionHealthCard execution={executionState} isLoading={statusLoading} />
                </div>
              </Tooltip>
            </div>
          </div>

          {/* Strategy Odds Panel - Core of VEGUS */}
          <div className="max-w-[1440px] mx-auto mb-6">
            <StrategyOddsPanel
              currentGear={status.gear || 'N'}
              currentRegime={status.current_regime || 'UNKNOWN'}
              strategies={[
                { name: 'Mean Reversion', odds: 45, expectedR: 0.8, edgeStrength: 0.6, decayDetected: false },
                { name: 'Momentum', odds: 72, expectedR: 1.5, edgeStrength: 0.8, decayDetected: false },
                { name: 'Breakout', odds: 65, expectedR: 1.2, edgeStrength: 0.7, decayDetected: false },
                { name: 'Scalping', odds: 38, expectedR: 0.5, edgeStrength: 0.4, decayDetected: true },
                { name: 'Range', odds: 55, expectedR: 0.9, edgeStrength: 0.65, decayDetected: false },
                { name: 'Trend', odds: 78, expectedR: 1.8, edgeStrength: 0.85, decayDetected: false },
                { name: 'Alpha Harvest', odds: 42, expectedR: 0.7, edgeStrength: 0.55, decayDetected: false },
                { name: 'Shock/Chaos', odds: 25, expectedR: -0.5, edgeStrength: 0.2, decayDetected: false },
              ]}
              bestStrategy="Trend"
              isLoading={statusLoading}
            />
          </div>

          {/* Transmission Visualization */}
          <div className="max-w-[1440px] mx-auto mb-6">
            <TransmissionVisualization
              currentGear={status.gear === 'P' ? 5 : status.gear === 'R' ? 2 : status.gear === 'N' ? 3 : status.gear === 'D' ? 4 : 1}
              rpm={65}
              torque={72}
              speed={58}
              temperature={status.daily_pnl_r < -1 ? 75 : 35}
              mode={userMode}
              shiftTimer={120}
              stabilityScore={78}
              load={0}
              fuel={85}
              ecoMode={!status.can_trade}
              sportMode={status.can_trade && status.daily_pnl_r > 0}
              isLoading={statusLoading}
            />
          </div>

          {/* VEGUS Score Breakdown */}
          <div className="max-w-[1440px] mx-auto mb-6">
            <VegusScoreBreakdown score={vegusScore} isLoading={statusLoading} />
          </div>

          {/* Intelligence Layers */}
          <div className="max-w-[1440px] mx-auto mb-6">
            <IntelligenceLayers
              expectedRPerStrategy={{
                'Mean Reversion': 0.8,
                'Momentum': 1.5,
                'Breakout': 1.2,
                'Trend': 1.8,
              }}
              edgeStrength={75}
              transmissionEfficiency={82}
              expectedPnl={150}
              actualPnl={142}
              strategyDecay={[
                { strategy: 'Scalping', decayScore: 65, detected: true },
              ]}
              isLoading={statusLoading}
            />
          </div>

          {/* Middle Row - Market Environment & Chart */}
          <div className="max-w-[1440px] mx-auto mb-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Market Environment Heatmap */}
              <div className="lg:col-span-2">
                <MarketEnvironmentHeatmap
                  regimes={
                    regimeState
                      ? {
                          '1m': regimeState,
                          '5m': regimeState,
                          '15m': regimeState,
                          '1h': regimeState,
                          HTF: regimeState,
                        }
                      : undefined
                  }
                  isLoading={statusLoading}
                />
              </div>
              {/* Directional Bias Panel */}
              <div>
                <DirectionalBiasPanel
                  htfTrend={status.daily_pnl_r > 0 ? 'UP' : status.daily_pnl_r < 0 ? 'DOWN' : 'SIDEWAYS'}
                  ltfTrend={status.daily_pnl_r > 0 ? 'UP' : status.daily_pnl_r < 0 ? 'DOWN' : 'SIDEWAYS'}
                  biasConfidence={directionalState?.strength ? directionalState.strength * 100 : 65}
                  trendStrength={directionalState?.momentumScore ? directionalState.momentumScore * 100 : 58}
                  htfSupport={15000}
                  htfResistance={15100}
                  liquidityPools={[
                    { price: 15050, size: 1000, type: 'support' },
                    { price: 15080, size: 800, type: 'resistance' },
                  ]}
                  orderFlowImbalance={0.3}
                  isLoading={statusLoading}
                />
              </div>
            </div>
          </div>

          {/* Odds Timeline */}
          <div className="max-w-[1440px] mx-auto mb-6">
            <OddsTimeline
              data={Array.from({ length: 24 }, (_, i) => ({
                timestamp: new Date(Date.now() - (24 - i) * 60 * 60 * 1000).toISOString(),
                meanReversion: 40 + Math.random() * 20,
                momentum: 60 + Math.random() * 20,
                breakout: 50 + Math.random() * 20,
                scalping: 30 + Math.random() * 20,
                range: 45 + Math.random() * 20,
                trend: 70 + Math.random() * 20,
              }))}
              isLoading={statusLoading}
            />
          </div>

          {/* Price Chart */}
          <div className="max-w-[1440px] mx-auto mb-6">
            <PriceChart
              bars={mockBars}
              currentGear={gearDecision}
              supportLevel={15000}
              resistanceLevel={15100}
              isLoading={statusLoading}
            />
          </div>

          {/* Proposed Trade Card (Assisted Mode) */}
          {userMode === 'assisted' && proposedTrade && (
            <div className="max-w-[1440px] mx-auto mb-6">
              <ProposedTradeCard
                trade={proposedTrade}
                onConfirm={() => console.log('Trade confirmed')}
                onReject={() => console.log('Trade rejected')}
              />
            </div>
          )}

          {/* Bot Status Panel (Auto Mode) */}
          {userMode === 'auto' && (
            <div className="max-w-[1440px] mx-auto mb-6">
              <BotStatusPanel
                isRunning={botRunning}
                positions={[]}
                onToggle={() => setBotRunning(!botRunning)}
                onKillSwitch={() => {
                  setBotRunning(false);
                  console.log('Kill switch activated');
                }}
              />
            </div>
          )}

          {/* Detailed Panels - No redundant tabs, content is in sidebar routes */}
        </div>
      </div>
    </div>
  );
}
