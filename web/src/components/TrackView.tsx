/**
 * TrackView Component
 *
 * Primary visualizer: Vehicle moving along equity curve track
 * Track height = equity, color = regime, markers = gears
 */

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

type RegimeType = 'TREND' | 'RANGE' | 'VOLATILE' | 'UNKNOWN';
type GearType = 'P' | 'R' | 'N' | 'D' | 'L';

interface TradePoint {
  timestamp: string;
  equity_r: number;
  regime: RegimeType;
  gear: GearType;
  win_loss?: string;
  event?: string; // 'spread_spike' | 'news_blackout' | 'mental_drop' | 'loss_limit' | 'take_profit'
}

interface TrackViewProps {
  tradeHistory: TradePoint[];
  currentGear: GearType;
  currentRegime: RegimeType;
  className?: string;
}

// Regime colors
const REGIME_COLORS: Record<RegimeType, string> = {
  TREND: '#8b5cf6',    // Purple
  RANGE: '#3b82f6',    // Blue
  VOLATILE: '#ef4444', // Red
  UNKNOWN: '#6b7280'   // Gray
};

// Gear icons/markers
const GEAR_MARKERS: Record<GearType, { color: string; label: string }> = {
  P: { color: '#ef4444', label: 'P' },
  R: { color: '#eab308', label: 'R' },
  N: { color: '#9ca3af', label: 'N' },
  D: { color: '#22c55e', label: 'D' },
  L: { color: '#3b82f6', label: 'L' }
};

// Event icons
const EVENT_ICONS: Record<string, string> = {
  spread_spike: '⚠️',
  news_blackout: '📰',
  mental_drop: '🧠',
  loss_limit: '❌',
  take_profit: '🎯'
};

export function TrackView({ tradeHistory, currentGear, currentRegime, className = '' }: TrackViewProps) {
  // Process trade data for visualization
  const chartData = useMemo(() => {
    return tradeHistory.map((trade, index) => ({
      index,
      equity_r: trade.equity_r,
      timestamp: new Date(trade.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      regime: trade.regime,
      gear: trade.gear,
      win_loss: trade.win_loss,
      event: trade.event
    }));
  }, [tradeHistory]);

  // Get current position (last point)
  const currentPosition = chartData[chartData.length - 1];
  const currentEquity = currentPosition?.equity_r || 0;

  // Calculate track statistics
  const peakEquity = Math.max(...chartData.map(d => d.equity_r));
  const drawdown = currentEquity - peakEquity;

  return (
    <div className={`relative ${className}`}>
      {/* Glass morphism container */}
      <div className="glass rounded-3xl p-6 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gradient">Track View</h2>
            <p className="text-sm text-gray-400 mt-1">Equity progression • {currentRegime} regime</p>
          </div>

          {/* Current stats */}
          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className="text-xs text-gray-500 uppercase tracking-wider">Current Equity</div>
              <div className={`text-2xl font-bold ${currentEquity >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {currentEquity >= 0 ? '+' : ''}{currentEquity.toFixed(2)}R
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-gray-500 uppercase tracking-wider">Drawdown</div>
              <div className={`text-2xl font-bold ${drawdown >= -0.5 ? 'text-yellow-500' : 'text-red-500'}`}>
                {drawdown.toFixed(2)}R
              </div>
            </div>
          </div>
        </div>

        {/* Track visualization */}
        <div className="relative h-96">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
            >
              {/* Gradient definitions */}
              <defs>
                <linearGradient id="trackGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={REGIME_COLORS[currentRegime]} stopOpacity={0.8}/>
                  <stop offset="95%" stopColor={REGIME_COLORS[currentRegime]} stopOpacity={0.1}/>
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />

              <XAxis
                dataKey="timestamp"
                stroke="rgba(255,255,255,0.4)"
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
              />

              <YAxis
                stroke="rgba(255,255,255,0.4)"
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
                label={{ value: 'Equity (R)', angle: -90, position: 'insideLeft', fill: 'rgba(255,255,255,0.6)' }}
              />

              {/* Zero line */}
              <ReferenceLine y={0} stroke="rgba(255,255,255,0.3)" strokeDasharray="3 3" />

              <Tooltip
                contentStyle={{
                  background: 'rgba(0, 0, 0, 0.8)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '12px',
                  backdropFilter: 'blur(10px)',
                  padding: '12px'
                }}
                labelStyle={{ color: '#fff', fontWeight: 'bold', marginBottom: '8px' }}
                itemStyle={{ color: '#fff' }}
                formatter={(value: number) => [`${value.toFixed(2)}R`, 'Equity']}
              />

              {/* Main equity line */}
              <Line
                type="monotone"
                dataKey="equity_r"
                stroke={REGIME_COLORS[currentRegime]}
                strokeWidth={3}
                dot={(props: any) => {
                  const { cx, cy, payload } = props;
                  const gear = payload.gear;
                  const winLoss = payload.win_loss;

                  return (
                    <g>
                      {/* Trade dot */}
                      <circle
                        cx={cx}
                        cy={cy}
                        r={winLoss ? 6 : 4}
                        fill={winLoss === 'Win' ? '#22c55e' : winLoss === 'Loss' ? '#ef4444' : (gear && GEAR_MARKERS[gear as GearType]?.color) || '#6b7280'}
                        stroke="#fff"
                        strokeWidth={2}
                        opacity={0.9}
                      />

                      {/* Gear marker label */}
                      {gear && (
                        <text
                          x={cx}
                          y={cy - 12}
                          fill={GEAR_MARKERS[gear as GearType]?.color || '#6b7280'}
                          fontSize={10}
                          fontWeight="bold"
                          textAnchor="middle"
                        >
                          {gear}
                        </text>
                      )}

                      {/* Event icon */}
                      {payload.event && (
                        <text
                          x={cx}
                          y={cy + 18}
                          fontSize={16}
                          textAnchor="middle"
                        >
                          {EVENT_ICONS[payload.event]}
                        </text>
                      )}
                    </g>
                  );
                }}
                activeDot={{ r: 8, strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>

          {/* Vehicle indicator (current position) */}
          <motion.div
            className="absolute top-1/2 right-8 transform -translate-y-1/2"
            animate={{
              scale: [1, 1.1, 1],
              rotate: [0, 5, -5, 0]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            <div
              className="relative w-12 h-12 rounded-full flex items-center justify-center"
              style={{
                background: `radial-gradient(circle, ${GEAR_MARKERS[currentGear as GearType]?.color || '#6b7280'} 0%, ${GEAR_MARKERS[currentGear as GearType]?.color || '#6b7280'}80 100%)`,
                boxShadow: `0 0 30px ${GEAR_MARKERS[currentGear as GearType]?.color || '#6b7280'}80`
              }}
            >
              <div className="text-2xl font-black text-white">
                {currentGear}
              </div>

              {/* Velocity indicator */}
              <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
                <div className="text-xs text-gray-400 font-medium">
                  {currentRegime}
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-8 mt-6 pt-6 border-t border-white/10">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-xs text-gray-400">Win</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-xs text-gray-400">Loss</span>
          </div>
          {(['P', 'R', 'N', 'D', 'L'] as GearType[]).map(gear => (
            <div key={gear} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: GEAR_MARKERS[gear as GearType]?.color || '#6b7280' }}
              />
              <span className="text-xs text-gray-400">{gear} Gear</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
