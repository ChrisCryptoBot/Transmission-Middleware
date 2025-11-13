/**
 * Strategy Odds Tab
 * Shows which strategies perform best in current gear/regime
 */

import { GearPerformanceResponse, GearDecision } from '@/lib/types';
import { GlassCard } from '../ui/GlassCard';
import { StatusBadge } from '../ui/StatusBadge';
import { TrendingUp, AlertCircle } from 'lucide-react';

interface StrategyOddsTabProps {
  gearPerformance: GearPerformanceResponse[];
  currentGear: GearDecision | null;
  currentRegime?: string;
  isLoading?: boolean;
}

export function StrategyOddsTab({
  gearPerformance,
  currentGear,
  currentRegime,
  isLoading,
}: StrategyOddsTabProps) {
  if (isLoading || !gearPerformance || gearPerformance.length === 0) {
    return (
      <div className="text-white/60">
        <h3 className="text-xl font-bold text-white mb-4">Strategy Odds</h3>
        <div>Loading strategy performance data...</div>
      </div>
    );
  }

  // Filter strategies for current gear
  const currentGearPerf = gearPerformance.find((p) => p.gear === currentGear?.gear);

  // Strategy recommendations based on regime
  const getStrategyRecommendations = () => {
    if (!currentRegime) return [];
    
    const recommendations: Array<{ name: string; reason: string; avoid: boolean }> = [];
    
    if (currentRegime === 'TREND') {
      recommendations.push(
        { name: 'VWAP Pullback', reason: 'Best in trending markets', avoid: false },
        { name: 'Breakout', reason: 'Strong in trends', avoid: false },
        { name: 'Mean Reversion', reason: 'Avoid in strong trends', avoid: true }
      );
    } else if (currentRegime === 'RANGE') {
      recommendations.push(
        { name: 'ORB Retest', reason: 'Optimal for range markets', avoid: false },
        { name: 'Mean Reversion', reason: 'Good in ranges', avoid: false },
        { name: 'Trend Following', reason: 'Avoid in ranges', avoid: true }
      );
    } else if (currentRegime === 'VOLATILE') {
      recommendations.push(
        { name: 'Mean Reversion', reason: 'Best in volatile markets', avoid: false },
        { name: 'Scalping', reason: 'Quick in/out works', avoid: false },
        { name: 'Trend Following', reason: 'Whipsaws in volatility', avoid: true }
      );
    }
    
    return recommendations;
  };

  const recommendations = getStrategyRecommendations();

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-white mb-4">Strategy Odds</h3>

      {/* Current Gear Performance */}
      {currentGearPerf && (
        <GlassCard>
          <div className="text-lg font-bold text-white mb-4">
            Performance in Gear {currentGearPerf.gear}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-white/60 mb-1">Win Rate</div>
              <div className="text-2xl font-bold text-white">
                {(currentGearPerf.win_rate * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="text-sm text-white/60 mb-1">Profit Factor</div>
              <div className="text-2xl font-bold text-white">{currentGearPerf.profit_factor.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-sm text-white/60 mb-1">Total R</div>
              <div className={`text-2xl font-bold ${currentGearPerf.total_r > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {currentGearPerf.total_r > 0 ? '+' : ''}{currentGearPerf.total_r.toFixed(2)}R
              </div>
            </div>
            <div>
              <div className="text-sm text-white/60 mb-1">Trades</div>
              <div className="text-2xl font-bold text-white">{currentGearPerf.trades}</div>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Strategy Recommendations */}
      {recommendations.length > 0 && (
        <div className="space-y-4">
          <h4 className="text-lg font-bold text-white">Strategy Recommendations</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations
              .filter((r) => !r.avoid)
              .map((rec, i) => (
                <GlassCard key={i} padding="sm">
                  <div className="flex items-start gap-3">
                    <TrendingUp className="w-5 h-5 text-green-400 mt-0.5" />
                    <div className="flex-1">
                      <div className="font-bold text-white mb-1">{rec.name}</div>
                      <div className="text-sm text-white/70">{rec.reason}</div>
                      <StatusBadge status="Consider" color="green" className="mt-2" />
                    </div>
                  </div>
                </GlassCard>
              ))}

            {recommendations
              .filter((r) => r.avoid)
              .map((rec, i) => (
                <GlassCard key={i} padding="sm">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
                    <div className="flex-1">
                      <div className="font-bold text-white mb-1">{rec.name}</div>
                      <div className="text-sm text-white/70">{rec.reason}</div>
                      <StatusBadge status="Avoid" color="red" className="mt-2" />
                    </div>
                  </div>
                </GlassCard>
              ))}
          </div>
        </div>
      )}

      {/* All Gear Performance Comparison */}
      <div>
        <h4 className="text-lg font-bold text-white mb-4">Performance by Gear</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {gearPerformance.map((perf) => (
            <GlassCard key={perf.gear} padding="sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-white mb-2">Gear {perf.gear}</div>
                <div className="space-y-1 text-sm">
                  <div className="text-white/70">
                    WR: <span className="text-white">{(perf.win_rate * 100).toFixed(0)}%</span>
                  </div>
                  <div className="text-white/70">
                    PF: <span className="text-white">{perf.profit_factor.toFixed(2)}</span>
                  </div>
                  <div className={`text-white/70`}>
                    R: <span className={perf.total_r > 0 ? 'text-green-400' : 'text-red-400'}>
                      {perf.total_r > 0 ? '+' : ''}{perf.total_r.toFixed(1)}R
                    </span>
                  </div>
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      </div>
    </div>
  );
}

