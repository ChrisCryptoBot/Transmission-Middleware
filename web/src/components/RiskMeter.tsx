/**
 * Risk Meter
 * Displays daily/weekly R usage and drawdown
 */

import { RiskState } from '@/lib/types';
import { GlassCard } from './ui/GlassCard';
import { formatR } from '@/lib/utils';

interface RiskMeterProps {
  risk: RiskState | null;
  isLoading?: boolean;
}

export function RiskMeter({ risk, isLoading }: RiskMeterProps) {
  if (isLoading || !risk) {
    return (
      <GlassCard>
        <div className="text-sm text-white/60 mb-2">Risk Status</div>
        <div className="text-2xl text-white/40">--</div>
      </GlassCard>
    );
  }

  const dailyPercent = Math.min(Math.abs(risk.dailyRUsed) / 2, 1) * 100; // Assuming 2R limit
  const weeklyPercent = Math.min(Math.abs(risk.weeklyRUsed) / 5, 1) * 100; // Assuming 5R limit

  const getBarColor = (percent: number) => {
    if (percent < 50) return 'bg-green-500';
    if (percent < 75) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <GlassCard>
      <div className="text-sm text-white/60 mb-4">Risk Status</div>
      
      {/* Daily R */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs text-white/70">Daily R</span>
          <span className="text-sm font-semibold text-white">
            {formatR(risk.dailyRUsed)} / {formatR(2)}
          </span>
        </div>
        <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
          <div
            className={`h-full ${getBarColor(dailyPercent)} transition-all duration-500`}
            style={{ width: `${dailyPercent}%` }}
          />
        </div>
      </div>

      {/* Weekly R */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs text-white/70">Weekly R</span>
          <span className="text-sm font-semibold text-white">
            {formatR(risk.weeklyRUsed)} / {formatR(5)}
          </span>
        </div>
        <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
          <div
            className={`h-full ${getBarColor(weeklyPercent)} transition-all duration-500`}
            style={{ width: `${weeklyPercent}%` }}
          />
        </div>
      </div>

      {/* Drawdown */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs text-white/70">Drawdown</span>
          <span className={`text-sm font-semibold ${risk.currentDrawdownPct < 0 ? 'text-red-400' : 'text-green-400'}`}>
            {risk.currentDrawdownPct.toFixed(2)}%
          </span>
        </div>
        <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-red-500 transition-all duration-500"
            style={{ width: `${Math.min(Math.abs(risk.currentDrawdownPct), 100)}%` }}
          />
        </div>
      </div>
    </GlassCard>
  );
}

