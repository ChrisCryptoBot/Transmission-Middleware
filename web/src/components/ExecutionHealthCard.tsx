/**
 * Execution Health Card
 * Displays spread, latency, and book depth status
 */

import { ExecutionState } from '@/lib/types';
import { GlassCard } from './ui/GlassCard';
import { StatusBadge } from './ui/StatusBadge';

interface ExecutionHealthCardProps {
  execution: ExecutionState | null;
  isLoading?: boolean;
}

export function ExecutionHealthCard({ execution, isLoading }: ExecutionHealthCardProps) {
  if (isLoading || !execution) {
    return (
      <GlassCard>
        <div className="text-sm text-white/60 mb-2">Execution Health</div>
        <div className="text-2xl text-white/40">--</div>
      </GlassCard>
    );
  }

  const getHealthStatus = () => {
    if (execution.spreadWidening || execution.bookThin || execution.connectionUnstable) {
      return { label: 'Poor', color: 'red' as const };
    }
    if (execution.spreadBps > 5 || execution.apiLatencyMs > 100) {
      return { label: 'Mixed', color: 'yellow' as const };
    }
    return { label: 'Good', color: 'green' as const };
  };

  const health = getHealthStatus();

  return (
    <GlassCard>
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-white/60">Execution Health</div>
        <StatusBadge status={health.label} color={health.color} />
      </div>

      <div className="space-y-3">
        {/* Spread */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-white/70">Spread</span>
          <span className="text-sm font-semibold text-white">
            {execution.spreadBps.toFixed(2)} bps
            {execution.spreadWidening && (
              <span className="ml-2 text-yellow-400">⚠</span>
            )}
          </span>
        </div>

        {/* Latency */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-white/70">API Latency</span>
          <span className="text-sm font-semibold text-white">
            {execution.apiLatencyMs.toFixed(0)} ms
          </span>
        </div>

        {/* Book Depth */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-white/70">Book Depth</span>
          <span className="text-sm font-semibold text-white">
            {execution.bookThin ? 'Thin' : 'Good'}
          </span>
        </div>

        {/* Connection */}
        {execution.connectionUnstable && (
          <div className="flex items-center gap-2 text-xs text-red-400">
            <span>⚠</span>
            <span>Connection Unstable</span>
          </div>
        )}
      </div>
    </GlassCard>
  );
}

