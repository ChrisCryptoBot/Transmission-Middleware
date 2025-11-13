/**
 * Psychology Tab - Mental state, streaks, cooldown suggestions
 */

import { RiskState } from '@/lib/types';
import { GlassCard } from '../ui/GlassCard';
import { StatusBadge } from '../ui/StatusBadge';
import { Brain, AlertCircle, CheckCircle } from 'lucide-react';

interface PsychologyTabProps {
  risk: RiskState | null;
  consecutiveLosses?: number;
  consecutiveWins?: number;
  isLoading?: boolean;
}

export function PsychologyTab({ risk, consecutiveLosses = 0, consecutiveWins = 0, isLoading }: PsychologyTabProps) {
  if (isLoading || !risk) {
    return (
      <div className="text-white/60">
        <h3 className="text-xl font-bold text-white mb-4">Psychology</h3>
        <div>Loading psychology data...</div>
      </div>
    );
  }

  const needsCooldown = risk.mentalRiskScore > 0.7 || consecutiveLosses >= 3;

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-white mb-4">Psychology</h3>

      {/* Mental Risk Score */}
      <GlassCard>
        <div className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Brain className="w-5 h-5" />
          Mental Risk Assessment
        </div>
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-white/70">Mental Risk Score</span>
            <span className="text-sm font-semibold text-white">{(risk.mentalRiskScore * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                risk.mentalRiskScore < 0.3
                  ? 'bg-green-500'
                  : risk.mentalRiskScore < 0.7
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${risk.mentalRiskScore * 100}%` }}
            />
          </div>
          <div className="text-xs text-white/60 mt-1">
            {risk.mentalRiskScore < 0.3
              ? 'Calm - Good mental state'
              : risk.mentalRiskScore < 0.7
              ? 'Moderate pressure - Stay disciplined'
              : 'High pressure - Consider break'}
          </div>
        </div>
      </GlassCard>

      {/* Streak Analysis */}
      <GlassCard>
        <div className="text-lg font-bold text-white mb-4">Streak Analysis</div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-white/70 mb-1">Consecutive Wins</div>
            <div className={`text-2xl font-bold ${consecutiveWins > 0 ? 'text-green-400' : 'text-gray-400'}`}>
              {consecutiveWins}
            </div>
            {consecutiveWins >= 3 && (
              <StatusBadge status="Hot Streak" color="green" className="mt-2" />
            )}
          </div>
          <div>
            <div className="text-sm text-white/70 mb-1">Consecutive Losses</div>
            <div className={`text-2xl font-bold ${consecutiveLosses > 0 ? 'text-red-400' : 'text-gray-400'}`}>
              {consecutiveLosses}
            </div>
            {consecutiveLosses >= 2 && (
              <StatusBadge status="Loss Streak" color="red" className="mt-2" />
            )}
          </div>
        </div>
      </GlassCard>

      {/* Cooldown Suggestions */}
      {needsCooldown ? (
        <GlassCard>
          <div className="text-lg font-bold text-yellow-400 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Cooldown Recommended
          </div>
          <div className="space-y-2 text-sm text-white/70">
            {risk.mentalRiskScore > 0.7 && (
              <p>• Mental risk score is high ({Math.round(risk.mentalRiskScore * 100)}%)</p>
            )}
            {consecutiveLosses >= 3 && (
              <p>• {consecutiveLosses} consecutive losses - emotional recovery needed</p>
            )}
            <p className="mt-4 text-white">
              <strong>Recommendation:</strong> Take a break, review trades, return when mentally fresh.
            </p>
          </div>
        </GlassCard>
      ) : (
        <GlassCard>
          <div className="text-lg font-bold text-green-400 mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            Mental State: Healthy
          </div>
          <div className="text-sm text-white/70">
            Your mental risk score is within healthy limits. Continue trading with discipline.
          </div>
        </GlassCard>
      )}
    </div>
  );
}

