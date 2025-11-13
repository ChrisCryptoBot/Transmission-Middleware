/**
 * Intelligence Layers - Expected R, Edge Strength, Transmission Efficiency, Strategy Decay
 */

import { GlassCard } from './ui/GlassCard';
import { StatusBadge } from './ui/StatusBadge';
import { TrendingUp, Zap, Gauge, AlertCircle } from 'lucide-react';

interface IntelligenceLayersProps {
  expectedRPerStrategy: Record<string, number>; // Strategy name -> expected R
  edgeStrength: number; // 0-100
  transmissionEfficiency: number; // 0-100
  expectedPnl: number;
  actualPnl: number;
  strategyDecay: Array<{ strategy: string; decayScore: number; detected: boolean }>;
  isLoading?: boolean;
}

export function IntelligenceLayers({
  expectedRPerStrategy,
  edgeStrength,
  transmissionEfficiency,
  expectedPnl,
  actualPnl,
  strategyDecay,
  isLoading,
}: IntelligenceLayersProps) {
  if (isLoading) {
    return (
      <GlassCard>
        <div className="text-white/60">Loading intelligence data...</div>
      </GlassCard>
    );
  }

  const pnlEfficiency = actualPnl !== 0 && expectedPnl !== 0
    ? (actualPnl / expectedPnl) * 100
    : 0;

  return (
    <GlassCard>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Intelligence Layers</h2>
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Edge Strength */}
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            <span className="text-sm text-white/70">Edge Strength</span>
          </div>
          <div className={`text-3xl font-bold ${
            edgeStrength >= 70 ? 'text-green-400' : edgeStrength >= 50 ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {edgeStrength.toFixed(0)}%
          </div>
          <div className="w-full h-2 bg-white/10 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full ${
                edgeStrength >= 70 ? 'bg-green-500' : edgeStrength >= 50 ? 'bg-yellow-500' : 'bg-red-500'
              } transition-all duration-500`}
              style={{ width: `${edgeStrength}%` }}
            />
          </div>
        </div>

        {/* Transmission Efficiency */}
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Gauge className="w-5 h-5 text-blue-400" />
            <span className="text-sm text-white/70">Transmission Efficiency</span>
          </div>
          <div className={`text-3xl font-bold ${
            transmissionEfficiency >= 80 ? 'text-green-400' : transmissionEfficiency >= 60 ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {transmissionEfficiency.toFixed(0)}%
          </div>
          <div className="w-full h-2 bg-white/10 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full ${
                transmissionEfficiency >= 80 ? 'bg-green-500' : transmissionEfficiency >= 60 ? 'bg-yellow-500' : 'bg-red-500'
              } transition-all duration-500`}
              style={{ width: `${transmissionEfficiency}%` }}
            />
          </div>
        </div>

        {/* PnL Efficiency */}
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-purple-400" />
            <span className="text-sm text-white/70">PnL Efficiency</span>
          </div>
          <div className={`text-3xl font-bold ${
            pnlEfficiency >= 80 ? 'text-green-400' : pnlEfficiency >= 60 ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {pnlEfficiency.toFixed(0)}%
          </div>
          <div className="text-xs text-white/60 mt-1">
            Expected: ${expectedPnl.toFixed(2)} | Actual: ${actualPnl.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Expected R per Strategy */}
      <div className="mb-6">
        <h3 className="text-lg font-bold text-white mb-3">Expected R per Strategy</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(expectedRPerStrategy).map(([strategy, expectedR]) => (
            <div key={strategy} className="p-3 rounded-lg bg-white/5 border border-white/10">
              <div className="text-xs text-white/60 mb-1">{strategy}</div>
              <div className={`text-lg font-bold ${
                expectedR > 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {expectedR > 0 ? '+' : ''}{expectedR.toFixed(2)}R
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Strategy Decay Detector */}
      {strategyDecay.length > 0 && (
        <div>
          <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-400" />
            Strategy Decay Detector
          </h3>
          <div className="space-y-2">
            {strategyDecay
              .filter((s) => s.detected)
              .map((strategy, i) => (
                <div
                  key={i}
                  className="p-3 rounded-lg bg-red-500/10 border border-red-400/30"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-white">{strategy.strategy}</div>
                      <div className="text-xs text-white/70">
                        Decay Score: {strategy.decayScore.toFixed(0)}% - Strategy losing edge
                      </div>
                    </div>
                    <StatusBadge status="Decay" color="red" />
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </GlassCard>
  );
}

