/**
 * Transmission Logs Tab - Shows gear shift history with reasons
 */

import { GearShiftResponse } from '@/lib/types';
import { GlassCard } from '../ui/GlassCard';
import { formatDateTime } from '@/lib/utils';

interface TransmissionLogsTabProps {
  gearHistory: GearShiftResponse[];
  isLoading?: boolean;
}

export function TransmissionLogsTab({ gearHistory, isLoading }: TransmissionLogsTabProps) {
  if (isLoading || !gearHistory || gearHistory.length === 0) {
    return (
      <div className="text-white/60">
        <h3 className="text-xl font-bold text-white mb-4">Transmission Logs</h3>
        <div>No gear shift history available</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-white mb-4">Transmission Logs</h3>

      <div className="space-y-3">
        {gearHistory.map((shift, i) => (
          <GlassCard key={i} padding="sm">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                {/* Gear Transition */}
                <div className="flex items-center gap-3 mb-2">
                  <div className="text-2xl font-bold text-white">{shift.from_gear}</div>
                  <div className="text-white/60">→</div>
                  <div className="text-2xl font-bold text-white">{shift.to_gear}</div>
                  <div className="text-xs text-white/60 ml-auto">
                    {formatDateTime(shift.timestamp)}
                  </div>
                </div>

                {/* Reason */}
                <div className="text-sm text-white/70 mb-2">{shift.reason}</div>

                {/* Context */}
                <div className="flex flex-wrap gap-4 text-xs text-white/60">
                  <div>
                    Daily R: <span className="text-white">{shift.daily_r.toFixed(2)}R</span>
                  </div>
                  <div>
                    Weekly R: <span className="text-white">{shift.weekly_r.toFixed(2)}R</span>
                  </div>
                  {shift.consecutive_losses > 0 && (
                    <div>
                      Losses: <span className="text-red-400">{shift.consecutive_losses}</span>
                    </div>
                  )}
                  {shift.regime && (
                    <div>
                      Regime: <span className="text-white">{shift.regime}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  );
}

