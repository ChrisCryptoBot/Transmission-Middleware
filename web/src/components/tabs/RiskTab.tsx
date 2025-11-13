/**
 * Risk Tab - Shows risk metrics, violations, concentration risk
 */

import { RiskState } from '@/lib/types';
import { GlassCard } from '../ui/GlassCard';
import { formatR } from '@/lib/utils';
import { AlertTriangle, Shield, TrendingDown } from 'lucide-react';

interface RiskTabProps {
  risk: RiskState | null;
  isLoading?: boolean;
}

export function RiskTab({ risk, isLoading }: RiskTabProps) {
  if (isLoading || !risk) {
    return (
      <div className="text-white/60">
        <h3 className="text-xl font-bold text-white mb-4">Risk Management</h3>
        <div>Loading risk data...</div>
      </div>
    );
  }

  const dailyPercent = Math.min(Math.abs(risk.dailyRUsed) / 2, 1) * 100;
  const weeklyPercent = Math.min(Math.abs(risk.weeklyRUsed) / 5, 1) * 100;

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-white mb-4">Risk Management</h3>

      {/* Risk Budget */}
      <GlassCard>
        <div className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5" />
          Risk Budget
        </div>

        {/* Daily R */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-white/70">Daily R Used</span>
            <span className="text-sm font-semibold text-white">
              {formatR(risk.dailyRUsed)} / {formatR(2)}
            </span>
          </div>
          <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                dailyPercent < 50 ? 'bg-green-500' : dailyPercent < 75 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${dailyPercent}%` }}
            />
          </div>
          <div className="text-xs text-white/60 mt-1">
            {dailyPercent < 50
              ? 'Within safe limits'
              : dailyPercent < 75
              ? 'Approaching limit'
              : '⚠️ Limit reached'}
          </div>
        </div>

        {/* Weekly R */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-white/70">Weekly R Used</span>
            <span className="text-sm font-semibold text-white">
              {formatR(risk.weeklyRUsed)} / {formatR(5)}
            </span>
          </div>
          <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                weeklyPercent < 50 ? 'bg-green-500' : weeklyPercent < 75 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${weeklyPercent}%` }}
            />
          </div>
        </div>
      </GlassCard>

      {/* Drawdown */}
      <GlassCard>
        <div className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <TrendingDown className="w-5 h-5" />
          Drawdown
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-white/70 mb-1">Current Drawdown</div>
            <div className={`text-2xl font-bold ${risk.currentDrawdownPct < 0 ? 'text-red-400' : 'text-green-400'}`}>
              {risk.currentDrawdownPct.toFixed(2)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-white/70 mb-1">Max Drawdown</div>
            <div className="text-2xl font-bold text-white">{risk.maxDrawdownPct.toFixed(2)}%</div>
          </div>
        </div>
      </GlassCard>

      {/* Mental Risk */}
      <GlassCard>
        <div className="text-lg font-bold text-white mb-4">Mental Risk Score</div>
        <div className="mb-2">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-white/70">Psychological Pressure</span>
            <span className="text-sm font-semibold text-white">{(risk.mentalRiskScore * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                risk.mentalRiskScore < 0.3 ? 'bg-green-500' : risk.mentalRiskScore < 0.7 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${risk.mentalRiskScore * 100}%` }}
            />
          </div>
        </div>
        {risk.mentalRiskScore > 0.7 && (
          <div className="flex items-center gap-2 text-yellow-400 text-sm">
            <AlertTriangle className="w-4 h-4" />
            <span>High psychological pressure - consider cooldown</span>
          </div>
        )}
      </GlassCard>

      {/* Risk Flags */}
      {(risk.propLimitHit || risk.blackSwanFlag) && (
        <GlassCard>
          <div className="text-lg font-bold text-red-400 mb-2 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Risk Flags
          </div>
          <ul className="space-y-1 text-sm text-white/70">
            {risk.propLimitHit && <li>• Prop trading limit hit</li>}
            {risk.blackSwanFlag && <li>• Black swan event detected</li>}
          </ul>
        </GlassCard>
      )}
    </div>
  );
}

