/**
 * LearningDashboard Component
 *
 * Trade learning and insights panel:
 * - Performance by gear (P/R/N/D/L)
 * - Performance by regime
 * - Recent trade explanations
 * - Win rate analysis
 */

import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { TrendingUp, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';

type GearType = 'P' | 'R' | 'N' | 'D' | 'L';
type RegimeType = 'TREND' | 'RANGE' | 'VOLATILE';

interface GearPerformance {
  gear: GearType;
  trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  profit_factor: number;
  total_r: number;
}

interface TradeInsight {
  timestamp: string;
  symbol: string;
  direction: 'LONG' | 'SHORT';
  gear_at_entry: GearType;
  gear_at_exit: GearType;
  regime: RegimeType;
  result_r: number;
  win_loss: 'Win' | 'Loss';
  acceptance_reason?: string;
  rejection_reason?: string;
}

interface LearningDashboardProps {
  gearPerformance: GearPerformance[];
  recentInsights: TradeInsight[];
  className?: string;
}

const GEAR_COLORS: Record<GearType, string> = {
  P: '#f87171', // red-400
  R: '#fbbf24', // amber-400
  N: '#a3a3a3', // neutral-400
  D: '#4ade80', // green-400
  L: '#60a5fa'  // blue-400
};

const GEAR_LABELS: Record<GearType, string> = {
  P: 'Park',
  R: 'Reverse',
  N: 'Neutral',
  D: 'Drive',
  L: 'Low'
};

export function LearningDashboard({ gearPerformance, recentInsights, className = '' }: LearningDashboardProps) {
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="glass rounded-2xl p-6">
        <h2 className="text-2xl font-bold text-gradient mb-1">Analytics Dashboard</h2>
        <p className="text-sm text-neutral-400">Performance analysis & trade insights</p>
      </div>

      {/* Performance by Gear */}
      <div className="glass rounded-2xl p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-green-400" />
          Performance by Gear
        </h3>

        {/* Win Rate Chart */}
        <div className="h-64 mb-6">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={gearPerformance} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis
                dataKey="gear"
                stroke="rgba(255,255,255,0.4)"
                tick={{ fill: 'rgba(255,255,255,0.6)' }}
              />
              <YAxis
                stroke="rgba(255,255,255,0.4)"
                tick={{ fill: 'rgba(255,255,255,0.6)' }}
                label={{ value: 'Win Rate (%)', angle: -90, position: 'insideLeft', fill: 'rgba(255,255,255,0.6)' }}
              />
              <Tooltip
                contentStyle={{
                  background: 'rgba(0, 0, 0, 0.8)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '12px',
                  backdropFilter: 'blur(10px)',
                }}
                formatter={(value: number) => `${value.toFixed(1)}%`}
              />
              <Bar dataKey="win_rate" radius={[8, 8, 0, 0]}>
                {gearPerformance.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={GEAR_COLORS[entry.gear]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Gear Stats Grid */}
        <div className="grid grid-cols-5 gap-3">
          {gearPerformance.map((perf) => (
            <motion.div
              key={perf.gear}
              className="bg-white/5 rounded-xl p-4 hover-lift"
              whileHover={{ scale: 1.05 }}
              transition={{ duration: 0.2 }}
            >
              <div
                className="text-2xl font-black mb-2"
                style={{ color: GEAR_COLORS[perf.gear] }}
              >
                {perf.gear}
              </div>
              <div className="text-xs text-neutral-500 uppercase mb-2">{GEAR_LABELS[perf.gear]}</div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-neutral-400">Trades</span>
                  <span className="text-white font-medium">{perf.trades}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-neutral-400">Win Rate</span>
                  <span className={`font-medium ${perf.win_rate >= 60 ? 'text-green-400' : perf.win_rate >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                    {perf.win_rate.toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-neutral-400">P/F</span>
                  <span className={`font-medium ${perf.profit_factor >= 1.5 ? 'text-green-400' : perf.profit_factor >= 1.0 ? 'text-amber-400' : 'text-red-400'}`}>
                    {perf.profit_factor.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-neutral-400">Total R</span>
                  <span className={`font-medium ${perf.total_r >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {perf.total_r >= 0 ? '+' : ''}{perf.total_r.toFixed(1)}R
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Recent Trade Insights */}
      <div className="glass rounded-2xl p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-blue-400" />
          Recent Trade Insights
        </h3>

        <div className="space-y-3">
          {recentInsights.slice(0, 5).map((insight, index) => (
            <motion.div
              key={index}
              className="bg-white/5 rounded-xl p-4 hover-lift"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3">
                  {/* Win/Loss Indicator */}
                  {insight.win_loss === 'Win' ? (
                    <CheckCircle2 className="w-5 h-5 text-green-400" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-400" />
                  )}

                  {/* Trade Info */}
                  <div>
                    <div className="font-medium text-white">
                      {insight.symbol} {insight.direction}
                    </div>
                    <div className="text-xs text-neutral-400">
                      {new Date(insight.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>

                {/* Result R */}
                <div className={`text-lg font-bold ${insight.result_r >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {insight.result_r >= 0 ? '+' : ''}{insight.result_r.toFixed(2)}R
                </div>
              </div>

              {/* Gear & Regime Tags */}
              <div className="flex items-center gap-2 mb-2">
                <div
                  className="px-2 py-1 rounded-full text-xs font-bold"
                  style={{
                    backgroundColor: `${GEAR_COLORS[insight.gear_at_entry]}20`,
                    color: GEAR_COLORS[insight.gear_at_entry]
                  }}
                >
                  Entry: {insight.gear_at_entry} Gear
                </div>
                {insight.gear_at_exit && insight.gear_at_exit !== insight.gear_at_entry && (
                  <div
                    className="px-2 py-1 rounded-full text-xs font-bold"
                    style={{
                      backgroundColor: `${GEAR_COLORS[insight.gear_at_exit]}20`,
                      color: GEAR_COLORS[insight.gear_at_exit]
                    }}
                  >
                    Exit: {insight.gear_at_exit} Gear
                  </div>
                )}
                <div className="px-2 py-1 rounded-full text-xs font-medium bg-purple-500/20 text-purple-400">
                  {insight.regime}
                </div>
              </div>

              {/* Reason */}
              {insight.acceptance_reason && (
                <div className="text-xs text-neutral-400 mt-2">
                  ✓ {insight.acceptance_reason}
                </div>
              )}
              {insight.rejection_reason && (
                <div className="text-xs text-red-400 mt-2">
                  ✗ {insight.rejection_reason}
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </div>

      {/* Key Insights Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="glass rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-green-400 mb-1">
            {((gearPerformance.find(p => p.gear === 'D')?.win_rate || 0)).toFixed(0)}%
          </div>
          <div className="text-xs text-neutral-400 uppercase tracking-wider">Drive Win Rate</div>
        </div>
        <div className="glass rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-blue-400 mb-1">
            {((gearPerformance.find(p => p.gear === 'L')?.win_rate || 0)).toFixed(0)}%
          </div>
          <div className="text-xs text-neutral-400 uppercase tracking-wider">Low Win Rate</div>
        </div>
        <div className="glass rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-amber-400 mb-1">
            {((gearPerformance.find(p => p.gear === 'R')?.win_rate || 0)).toFixed(0)}%
          </div>
          <div className="text-xs text-neutral-400 uppercase tracking-wider">Reverse Win Rate</div>
        </div>
      </div>
    </div>
  );
}
