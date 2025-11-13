/**
 * Risk Module Summary - Comprehensive risk metrics
 */

import { GlassCard } from './ui/GlassCard';
import { AlertTriangle, Shield } from 'lucide-react';
import { formatR } from '@/lib/utils';

interface RiskModuleSummaryProps {
  riskTemperature: number; // 0-100
  currentRUsed: number;
  dailyLossLimit: number;
  dailyLimitRemaining: number;
  weeklyLimitRemaining: number;
  positionSizingSuggestion: number;
  portfolioExposure: number; // %
  correlationRisk: number; // 0-1
  isLoading?: boolean;
}

export function RiskModuleSummary({
  riskTemperature,
  currentRUsed,
  dailyLossLimit,
  dailyLimitRemaining,
  weeklyLimitRemaining,
  positionSizingSuggestion,
  portfolioExposure,
  correlationRisk,
  isLoading,
}: RiskModuleSummaryProps) {
  if (isLoading) {
    return (
      <GlassCard>
        <div className="text-white/60">Loading risk data...</div>
      </GlassCard>
    );
  }

  const getRiskColor = (temp: number) => {
    if (temp < 30) return 'text-green-400';
    if (temp < 60) return 'text-yellow-400';
    if (temp < 80) return 'text-orange-400';
    return 'text-red-400';
  };

  return (
    <GlassCard>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
          <Shield className="w-6 h-6" />
          Risk Module Summary
        </h2>
      </div>

      {/* Risk Temperature */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-white/70">Risk Temperature</span>
          <span className={`text-2xl font-bold ${getRiskColor(riskTemperature)}`}>
            {riskTemperature.toFixed(0)}°
          </span>
        </div>
        <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              riskTemperature < 30
                ? 'bg-green-500'
                : riskTemperature < 60
                ? 'bg-yellow-500'
                : riskTemperature < 80
                ? 'bg-orange-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${riskTemperature}%` }}
          />
        </div>
      </div>

      {/* R Usage */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="text-sm text-white/70 mb-1">Current R Used</div>
          <div className="text-2xl font-bold text-white">{formatR(currentRUsed)}</div>
        </div>
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="text-sm text-white/70 mb-1">Daily Loss Limit</div>
          <div className="text-2xl font-bold text-white">{formatR(dailyLossLimit)}</div>
        </div>
      </div>

      {/* Limits Remaining */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 rounded-xl bg-green-500/10 border border-green-400/30">
          <div className="text-sm text-white/70 mb-1">Daily Limit Remaining</div>
          <div className="text-2xl font-bold text-green-400">{formatR(dailyLimitRemaining)}</div>
          <div className="text-xs text-white/60 mt-1">
            {((dailyLimitRemaining / dailyLossLimit) * 100).toFixed(0)}% remaining
          </div>
        </div>
        <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-400/30">
          <div className="text-sm text-white/70 mb-1">Weekly Limit Remaining</div>
          <div className="text-2xl font-bold text-blue-400">{formatR(weeklyLimitRemaining)}</div>
        </div>
      </div>

      {/* Position Sizing & Exposure */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="text-sm text-white/70 mb-1">Position Sizing Suggestion</div>
          <div className="text-2xl font-bold text-white">{positionSizingSuggestion.toFixed(2)} units</div>
        </div>
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="text-sm text-white/70 mb-1">Portfolio Exposure</div>
          <div className="text-2xl font-bold text-white">{portfolioExposure.toFixed(1)}%</div>
        </div>
      </div>

      {/* Correlation Risk */}
      <div className="p-4 rounded-xl bg-white/5 border border-white/10">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-white/70">Correlation Risk</span>
          <span className={`text-lg font-bold ${
            correlationRisk < 0.3 ? 'text-green-400' : correlationRisk < 0.6 ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {(correlationRisk * 100).toFixed(0)}%
          </span>
        </div>
        <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              correlationRisk < 0.3 ? 'bg-green-500' : correlationRisk < 0.6 ? 'bg-yellow-500' : 'bg-red-500'
            }`}
            style={{ width: `${correlationRisk * 100}%` }}
          />
        </div>
        {correlationRisk > 0.6 && (
          <div className="flex items-center gap-2 text-red-400 text-xs mt-2">
            <AlertTriangle className="w-4 h-4" />
            <span>High correlation - consider diversification</span>
          </div>
        )}
      </div>
    </GlassCard>
  );
}

