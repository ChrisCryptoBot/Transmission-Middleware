/**
 * Market Tab - Shows RegimeState and MarketConditionSnapshot values
 * Beginner mode: GOOD / OK / BAD tags
 * Advanced mode: full numbers
 */

import { RegimeState } from '@/lib/types';
import { GlassCard } from '../ui/GlassCard';
import { StatusBadge } from '../ui/StatusBadge';

interface MarketTabProps {
  regime: RegimeState | null;
  isBeginnerMode: boolean;
  isLoading?: boolean;
}

const getStatusTag = (value: number, higherIsBetter: boolean = true): { label: string; color: 'green' | 'yellow' | 'red' } => {
  const threshold = higherIsBetter ? 0.5 : 0.5;
  if (higherIsBetter) {
    if (value > 0.7) return { label: 'GOOD', color: 'green' };
    if (value > threshold) return { label: 'OK', color: 'yellow' };
    return { label: 'BAD', color: 'red' };
  } else {
    if (value < 0.3) return { label: 'GOOD', color: 'green' };
    if (value < threshold) return { label: 'OK', color: 'yellow' };
    return { label: 'BAD', color: 'red' };
  }
};

export function MarketTab({ regime, isBeginnerMode, isLoading }: MarketTabProps) {
  if (isLoading || !regime) {
    return (
      <div className="text-white/60">
        <h3 className="text-xl font-bold text-white mb-4">Market Conditions</h3>
        <div>Loading market data...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-white mb-4">Market Conditions</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Trend Probability */}
        <GlassCard padding="sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-white/70">Trend Probability</span>
            {isBeginnerMode && (
              <StatusBadge
                {...getStatusTag(regime.trendProb)}
                status={getStatusTag(regime.trendProb).label}
              />
            )}
          </div>
          {!isBeginnerMode && (
            <div className="text-2xl font-bold text-white">{(regime.trendProb * 100).toFixed(1)}%</div>
          )}
          <div className="w-full h-2 bg-white/10 rounded-full mt-2">
            <div
              className="h-full bg-green-500 transition-all duration-500"
              style={{ width: `${regime.trendProb * 100}%` }}
            />
          </div>
        </GlassCard>

        {/* Range Probability */}
        <GlassCard padding="sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-white/70">Range Probability</span>
            {isBeginnerMode && (
              <StatusBadge
                {...getStatusTag(regime.rangeProb)}
                status={getStatusTag(regime.rangeProb).label}
              />
            )}
          </div>
          {!isBeginnerMode && (
            <div className="text-2xl font-bold text-white">{(regime.rangeProb * 100).toFixed(1)}%</div>
          )}
          <div className="w-full h-2 bg-white/10 rounded-full mt-2">
            <div
              className="h-full bg-blue-500 transition-all duration-500"
              style={{ width: `${regime.rangeProb * 100}%` }}
            />
          </div>
        </GlassCard>

        {/* Volatility Percentile */}
        <GlassCard padding="sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-white/70">Volatility Percentile</span>
            {isBeginnerMode && (
              <StatusBadge
                {...getStatusTag(regime.volPercentile / 100, false)}
                status={getStatusTag(regime.volPercentile / 100, false).label}
              />
            )}
          </div>
          {!isBeginnerMode && (
            <div className="text-2xl font-bold text-white">{regime.volPercentile.toFixed(1)}%</div>
          )}
          <div className="w-full h-2 bg-white/10 rounded-full mt-2">
            <div
              className="h-full bg-yellow-500 transition-all duration-500"
              style={{ width: `${regime.volPercentile}%` }}
            />
          </div>
        </GlassCard>

        {/* ADX */}
        <GlassCard padding="sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-white/70">ADX (Trend Strength)</span>
            {isBeginnerMode && (
              <StatusBadge
                {...getStatusTag(regime.adx / 50)}
                status={getStatusTag(regime.adx / 50).label}
              />
            )}
          </div>
          {!isBeginnerMode && (
            <div className="text-2xl font-bold text-white">{regime.adx.toFixed(1)}</div>
          )}
        </GlassCard>

        {/* VWAP Slope */}
        <GlassCard padding="sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-white/70">VWAP Slope</span>
            {isBeginnerMode && (
              <StatusBadge
                {...getStatusTag(regime.vwapSlope > 0 ? Math.abs(regime.vwapSlope) : 0)}
                status={regime.vwapSlope > 0 ? 'GOOD' : 'BAD'}
                color={regime.vwapSlope > 0 ? 'green' : 'red'}
              />
            )}
          </div>
          {!isBeginnerMode && (
            <div className={`text-2xl font-bold ${regime.vwapSlope > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {regime.vwapSlope > 0 ? '+' : ''}{regime.vwapSlope.toFixed(3)}%
            </div>
          )}
        </GlassCard>

        {/* Liquidity Score */}
        <GlassCard padding="sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-white/70">Liquidity Score</span>
            {isBeginnerMode && (
              <StatusBadge
                {...getStatusTag(regime.liquidityScore)}
                status={getStatusTag(regime.liquidityScore).label}
              />
            )}
          </div>
          {!isBeginnerMode && (
            <div className="text-2xl font-bold text-white">{(regime.liquidityScore * 100).toFixed(1)}%</div>
          )}
          <div className="w-full h-2 bg-white/10 rounded-full mt-2">
            <div
              className="h-full bg-cyan-500 transition-all duration-500"
              style={{ width: `${regime.liquidityScore * 100}%` }}
            />
          </div>
        </GlassCard>

        {/* Chop Score */}
        <GlassCard padding="sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-white/70">Chop Score</span>
            {isBeginnerMode && (
              <StatusBadge
                {...getStatusTag(regime.chopScore, false)}
                status={getStatusTag(regime.chopScore, false).label}
              />
            )}
          </div>
          {!isBeginnerMode && (
            <div className="text-2xl font-bold text-white">{(regime.chopScore * 100).toFixed(1)}%</div>
          )}
        </GlassCard>

        {/* Event Risk Score */}
        <GlassCard padding="sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-white/70">Event Risk</span>
            {isBeginnerMode && (
              <StatusBadge
                {...getStatusTag(regime.eventRiskScore, false)}
                status={getStatusTag(regime.eventRiskScore, false).label}
              />
            )}
          </div>
          {!isBeginnerMode && (
            <div className="text-2xl font-bold text-white">{(regime.eventRiskScore * 100).toFixed(1)}%</div>
          )}
        </GlassCard>

        {/* BB Width */}
        <GlassCard padding="sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-white/70">BB Width</span>
            {isBeginnerMode && (
              <StatusBadge
                {...getStatusTag(regime.bbWidth > 1 ? 0.7 : regime.bbWidth)}
                status={getStatusTag(regime.bbWidth > 1 ? 0.7 : regime.bbWidth).label}
              />
            )}
          </div>
          {!isBeginnerMode && (
            <div className="text-2xl font-bold text-white">{regime.bbWidth.toFixed(2)}x</div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}

