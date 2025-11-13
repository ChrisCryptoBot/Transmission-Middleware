/**
 * Execution Health Details - Comprehensive execution metrics
 */

import { GlassCard } from './ui/GlassCard';
import { StatusBadge } from './ui/StatusBadge';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface ExecutionHealthDetailsProps {
  slippageTrend: number[]; // Last N slippage values
  fillQuality: number; // 0-100
  apiLatency: number; // ms
  orderRejectionRate: number; // 0-100
  executionScore: number; // 0-100
  spreadCostImpact: number; // bps
  isLoading?: boolean;
}

export function ExecutionHealthDetails({
  slippageTrend,
  fillQuality,
  apiLatency,
  orderRejectionRate,
  executionScore,
  spreadCostImpact,
  isLoading,
}: ExecutionHealthDetailsProps) {
  if (isLoading) {
    return (
      <GlassCard>
        <div className="text-white/60">Loading execution details...</div>
      </GlassCard>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const avgSlippage = slippageTrend.length > 0
    ? slippageTrend.reduce((a, b) => a + b, 0) / slippageTrend.length
    : 0;

  return (
    <GlassCard>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Execution Health Details</h2>
      </div>

      {/* Overall Score */}
      <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/30">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-white/70 mb-1">Overall Execution Score</div>
            <div className={`text-3xl font-bold ${getScoreColor(executionScore)}`}>
              {executionScore.toFixed(0)}/100
            </div>
          </div>
          <StatusBadge
            status={executionScore >= 80 ? 'Excellent' : executionScore >= 60 ? 'Good' : 'Poor'}
            color={executionScore >= 80 ? 'green' : executionScore >= 60 ? 'yellow' : 'red'}
          />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Slippage Trend */}
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="text-sm text-white/70 mb-2">Avg Slippage</div>
          <div className="text-2xl font-bold text-white mb-2">{avgSlippage.toFixed(2)} bps</div>
          <div className="flex items-center gap-1">
            {slippageTrend.length > 1 && (
              slippageTrend[slippageTrend.length - 1] > slippageTrend[0] ? (
                <TrendingUp className="w-4 h-4 text-red-400" />
              ) : (
                <TrendingDown className="w-4 h-4 text-green-400" />
              )
            )}
            <span className="text-xs text-white/60">
              {slippageTrend.length > 1 && slippageTrend[slippageTrend.length - 1] > slippageTrend[0]
                ? 'Increasing'
                : 'Decreasing'}
            </span>
          </div>
        </div>

        {/* Fill Quality */}
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="text-sm text-white/70 mb-2">Fill Quality</div>
          <div className={`text-2xl font-bold ${getScoreColor(fillQuality)}`}>
            {fillQuality.toFixed(0)}%
          </div>
          <div className="w-full h-2 bg-white/10 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full ${getScoreColor(fillQuality).replace('text-', 'bg-')} transition-all duration-500`}
              style={{ width: `${fillQuality}%` }}
            />
          </div>
        </div>

        {/* API Latency */}
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="text-sm text-white/70 mb-2">API Latency</div>
          <div className={`text-2xl font-bold ${
            apiLatency < 50 ? 'text-green-400' : apiLatency < 100 ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {apiLatency.toFixed(0)} ms
          </div>
          <div className="text-xs text-white/60 mt-1">
            {apiLatency < 50 ? 'Excellent' : apiLatency < 100 ? 'Good' : 'Slow'}
          </div>
        </div>

        {/* Order Rejection Rate */}
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="text-sm text-white/70 mb-2">Rejection Rate</div>
          <div className={`text-2xl font-bold ${
            orderRejectionRate < 5 ? 'text-green-400' : orderRejectionRate < 10 ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {orderRejectionRate.toFixed(1)}%
          </div>
          {orderRejectionRate > 10 && (
            <div className="text-xs text-red-400 mt-1">⚠ High rejection rate</div>
          )}
        </div>

        {/* Spread Cost Impact */}
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="text-sm text-white/70 mb-2">Spread Cost Impact</div>
          <div className={`text-2xl font-bold ${
            spreadCostImpact < 2 ? 'text-green-400' : spreadCostImpact < 5 ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {spreadCostImpact.toFixed(2)} bps
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

