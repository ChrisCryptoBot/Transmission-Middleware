/**
 * Market Environment Heatmap
 * Multi-timeframe grid showing vol state, trend strength, liquidity, momentum, range compression
 */

import { GlassCard } from './ui/GlassCard';
import { RegimeState } from '@/lib/types';

interface MarketEnvironmentHeatmapProps {
  regimes?: Record<string, RegimeState>;
  isLoading?: boolean;
}

const timeframes = ['1m', '5m', '15m', '1h', 'HTF'];
const metrics = ['Trend', 'Volatility', 'Liquidity', 'Momentum', 'Range'];

const getColorForValue = (value: number, metric: string): string => {
  // Normalize value to 0-1 range
  const normalized = Math.max(0, Math.min(1, value));
  
  if (metric === 'Trend') {
    // Green for strong trend, red for weak
    if (normalized > 0.7) return 'bg-green-500/80';
    if (normalized > 0.4) return 'bg-yellow-500/80';
    return 'bg-red-500/80';
  }
  
  if (metric === 'Volatility') {
    // Red for high vol, green for low vol
    if (normalized > 0.7) return 'bg-red-500/80';
    if (normalized > 0.4) return 'bg-yellow-500/80';
    return 'bg-green-500/80';
  }
  
  if (metric === 'Liquidity') {
    // Green for high liquidity, red for low
    if (normalized > 0.7) return 'bg-green-500/80';
    if (normalized > 0.4) return 'bg-yellow-500/80';
    return 'bg-red-500/80';
  }
  
  if (metric === 'Momentum') {
    // Green for strong momentum, gray for weak
    if (normalized > 0.7) return 'bg-green-500/80';
    if (normalized > 0.4) return 'bg-blue-500/80';
    return 'bg-gray-500/80';
  }
  
  if (metric === 'Range') {
    // Blue for compressed, red for expanded
    if (normalized > 0.7) return 'bg-red-500/80';
    if (normalized > 0.4) return 'bg-yellow-500/80';
    return 'bg-blue-500/80';
  }
  
  return 'bg-gray-500/80';
};

export function MarketEnvironmentHeatmap({ regimes, isLoading }: MarketEnvironmentHeatmapProps) {
  if (isLoading || !regimes) {
    return (
      <GlassCard>
        <div className="text-xl font-bold text-white mb-4">Market Environment Map</div>
        <div className="text-white/60">Loading market data...</div>
      </GlassCard>
    );
  }

  const getValue = (tf: string, metric: string): number => {
    const regime = regimes[tf];
    if (!regime) return 0.5;
    
    switch (metric) {
      case 'Trend':
        return regime.trendProb;
      case 'Volatility':
        return regime.volPercentile / 100;
      case 'Liquidity':
        return regime.liquidityScore;
      case 'Momentum':
        return regime.vwapSlope > 0 ? Math.min(1, regime.vwapSlope * 10) : 0;
      case 'Range':
        return regime.chopScore; // High chop = range, low = trend
      default:
        return 0.5;
    }
  };

  return (
    <GlassCard>
      <div className="text-xl font-bold text-white mb-4">Market Environment Map</div>
      
      <div className="overflow-x-auto">
        <div className="min-w-[600px]">
          {/* Header Row */}
          <div className="grid grid-cols-6 gap-2 mb-2">
            <div className="text-sm font-medium text-white/60">Timeframe</div>
            {metrics.map((metric) => (
              <div key={metric} className="text-sm font-medium text-white/60 text-center">
                {metric}
              </div>
            ))}
          </div>

          {/* Data Rows */}
          {timeframes.map((tf) => (
            <div key={tf} className="grid grid-cols-6 gap-2 mb-2">
              <div className="text-sm font-medium text-white flex items-center">{tf}</div>
              {metrics.map((metric) => {
                const value = getValue(tf, metric);
                const colorClass = getColorForValue(value, metric);
                return (
                  <div
                    key={metric}
                    className={`aspect-square rounded-lg flex items-center justify-center text-xs font-bold text-white border border-white/10 transition-all duration-200 hover:scale-110 ${colorClass}`}
                    title={`${tf} ${metric}: ${(value * 100).toFixed(0)}%`}
                  >
                    {(value * 100).toFixed(0)}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-xs text-white/60">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-green-500/80" />
          <span>Strong</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-yellow-500/80" />
          <span>Moderate</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-red-500/80" />
          <span>Weak</span>
        </div>
      </div>
    </GlassCard>
  );
}

