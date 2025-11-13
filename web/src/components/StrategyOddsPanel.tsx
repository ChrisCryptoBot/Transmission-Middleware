/**
 * Strategy Odds Panel - Core of VEGUS
 * Shows odds for each strategy in current gear/regime
 */

import { GlassCard } from './ui/GlassCard';
import { StatusBadge } from './ui/StatusBadge';
import { TrendingUp, TrendingDown, Activity, Zap, Target, BarChart3, AlertCircle } from 'lucide-react';

interface StrategyOdds {
  name: string;
  odds: number; // 0-100
  expectedR: number;
  edgeStrength: number; // 0-1
  decayDetected: boolean;
}

interface StrategyOddsPanelProps {
  currentGear: string;
  currentRegime: string;
  strategies: StrategyOdds[];
  bestStrategy: string;
  isLoading?: boolean;
}

const strategyIcons: Record<string, any> = {
  'Mean Reversion': TrendingDown,
  'Momentum': TrendingUp,
  'Breakout': Zap,
  'Scalping': Activity,
  'Range': BarChart3,
  'Trend': TrendingUp,
  'Alpha Harvest': Target,
  'Shock/Chaos': AlertCircle,
};

const getOddsColor = (odds: number): string => {
  if (odds >= 70) return 'text-green-400';
  if (odds >= 50) return 'text-yellow-400';
  if (odds >= 30) return 'text-orange-400';
  return 'text-red-400';
};

const getOddsBgColor = (odds: number): string => {
  if (odds >= 70) return 'bg-green-500';
  if (odds >= 50) return 'bg-yellow-500';
  if (odds >= 30) return 'bg-orange-500';
  return 'bg-red-500';
};

export function StrategyOddsPanel({
  currentGear,
  currentRegime,
  strategies,
  bestStrategy,
  isLoading,
}: StrategyOddsPanelProps) {
  if (isLoading) {
    return (
      <GlassCard>
        <div className="text-white/60">Loading strategy odds...</div>
      </GlassCard>
    );
  }

  return (
    <GlassCard>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-2xl font-bold text-white">Strategy Odds</h2>
          <div className="flex items-center gap-3">
            <StatusBadge status={`Gear ${currentGear}`} color="blue" />
            <StatusBadge status={currentRegime} color="purple" />
          </div>
        </div>
        <div className="text-sm text-white/70">
          Best Strategy: <span className="text-green-400 font-semibold">{bestStrategy}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {strategies.map((strategy) => {
          const Icon = strategyIcons[strategy.name] || Activity;
          const isBest = strategy.name === bestStrategy;
          
          return (
            <div
              key={strategy.name}
              className={`p-4 rounded-xl border-2 transition-all ${
                isBest
                  ? 'border-green-400/50 bg-green-500/10'
                  : 'border-white/10 bg-white/5'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Icon className="w-5 h-5 text-white/70" />
                  <span className="font-semibold text-white text-sm">{strategy.name}</span>
                </div>
                {isBest && (
                  <StatusBadge status="Best" color="green" />
                )}
                {strategy.decayDetected && (
                  <StatusBadge status="Decay" color="red" />
                )}
              </div>

              {/* Odds Display */}
              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-white/60">Odds</span>
                  <span className={`text-2xl font-bold ${getOddsColor(strategy.odds)}`}>
                    {strategy.odds}%
                  </span>
                </div>
                <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getOddsBgColor(strategy.odds)} transition-all duration-500`}
                    style={{ width: `${strategy.odds}%` }}
                  />
                </div>
              </div>

              {/* Expected R */}
              <div className="mb-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-white/60">Expected R</span>
                  <span className={`text-sm font-semibold ${
                    strategy.expectedR > 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {strategy.expectedR > 0 ? '+' : ''}{strategy.expectedR.toFixed(2)}R
                  </span>
                </div>
              </div>

              {/* Edge Strength */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-white/60">Edge Strength</span>
                  <span className="text-xs font-semibold text-white">
                    {(strategy.edgeStrength * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple-500 transition-all duration-500"
                    style={{ width: `${strategy.edgeStrength * 100}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
}

