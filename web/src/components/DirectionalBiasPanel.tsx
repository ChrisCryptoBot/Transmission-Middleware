/**
 * Directional Bias Panel - Detailed directional analysis
 */

import { GlassCard } from './ui/GlassCard';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

interface DirectionalBiasPanelProps {
  htfTrend: 'UP' | 'DOWN' | 'SIDEWAYS';
  ltfTrend: 'UP' | 'DOWN' | 'SIDEWAYS';
  biasConfidence: number; // 0-100
  trendStrength: number; // 0-100
  htfSupport: number;
  htfResistance: number;
  liquidityPools: Array<{ price: number; size: number; type: 'support' | 'resistance' }>;
  orderFlowImbalance?: number; // -1 to 1
  isLoading?: boolean;
}

export function DirectionalBiasPanel({
  htfTrend,
  ltfTrend,
  biasConfidence,
  trendStrength,
  htfSupport,
  htfResistance,
  liquidityPools,
  orderFlowImbalance,
  isLoading,
}: DirectionalBiasPanelProps) {
  if (isLoading) {
    return (
      <GlassCard>
        <div className="text-white/60">Loading directional bias...</div>
      </GlassCard>
    );
  }

  const getTrendColor = (trend: string) => {
    if (trend === 'UP') return 'text-green-400';
    if (trend === 'DOWN') return 'text-red-400';
    return 'text-gray-400';
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'UP') return <ArrowUp className="w-5 h-5" />;
    if (trend === 'DOWN') return <ArrowDown className="w-5 h-5" />;
    return <Minus className="w-5 h-5" />;
  };

  return (
    <GlassCard>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-4">Directional Bias</h2>

        {/* Trend Display */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="text-sm text-white/70 mb-2">HTF Trend</div>
            <div className="flex items-center gap-2">
              <div className={getTrendColor(htfTrend)}>
                {getTrendIcon(htfTrend)}
              </div>
              <span className={`text-xl font-bold ${getTrendColor(htfTrend)}`}>
                {htfTrend}
              </span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="text-sm text-white/70 mb-2">LTF Trend</div>
            <div className="flex items-center gap-2">
              <div className={getTrendColor(ltfTrend)}>
                {getTrendIcon(ltfTrend)}
              </div>
              <span className={`text-xl font-bold ${getTrendColor(ltfTrend)}`}>
                {ltfTrend}
              </span>
            </div>
          </div>
        </div>

        {/* Confidence & Strength */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-white/70">Bias Confidence</span>
              <span className="text-lg font-bold text-white">{biasConfidence.toFixed(0)}%</span>
            </div>
            <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all duration-500"
                style={{ width: `${biasConfidence}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-white/70">Trend Strength</span>
              <span className="text-lg font-bold text-white">{trendStrength.toFixed(0)}%</span>
            </div>
            <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 transition-all duration-500"
                style={{ width: `${trendStrength}%` }}
              />
            </div>
          </div>
        </div>

        {/* Key Levels */}
        <div className="mb-6">
          <div className="text-sm font-semibold text-white mb-3">Key Levels</div>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 rounded-lg bg-red-500/10 border border-red-400/30">
              <span className="text-sm text-white/70">HTF Resistance</span>
              <span className="text-lg font-bold text-red-400">{htfResistance.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-green-500/10 border border-green-400/30">
              <span className="text-sm text-white/70">HTF Support</span>
              <span className="text-lg font-bold text-green-400">{htfSupport.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Liquidity Pools */}
        {liquidityPools.length > 0 && (
          <div className="mb-6">
            <div className="text-sm font-semibold text-white mb-3">Liquidity Pools</div>
            <div className="space-y-2">
              {liquidityPools.map((pool, i) => (
                <div
                  key={i}
                  className={`flex items-center justify-between p-2 rounded-lg ${
                    pool.type === 'support'
                      ? 'bg-green-500/10 border border-green-400/30'
                      : 'bg-red-500/10 border border-red-400/30'
                  }`}
                >
                  <span className="text-xs text-white/70">
                    {pool.type === 'support' ? 'Support' : 'Resistance'} @ {pool.price.toFixed(2)}
                  </span>
                  <span className="text-xs text-white/60">Size: {pool.size}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Order Flow Imbalance */}
        {orderFlowImbalance !== undefined && (
          <div>
            <div className="text-sm font-semibold text-white mb-2">Order Flow Imbalance</div>
            <div className="flex items-center gap-3">
              <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    orderFlowImbalance > 0 ? 'bg-green-500' : 'bg-red-500'
                  }`}
                  style={{
                    width: `${Math.abs(orderFlowImbalance) * 100}%`,
                    marginLeft: orderFlowImbalance < 0 ? 'auto' : '0',
                  }}
                />
              </div>
              <span className={`text-sm font-bold ${
                orderFlowImbalance > 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {orderFlowImbalance > 0 ? '↑' : '↓'} {Math.abs(orderFlowImbalance * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        )}
      </div>
    </GlassCard>
  );
}

