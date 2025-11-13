/**
 * Execution Tab - Shows execution quality metrics
 */

import { ExecutionState } from '@/lib/types';
import { GlassCard } from '../ui/GlassCard';
import { StatusBadge } from '../ui/StatusBadge';

interface ExecutionTabProps {
  execution: ExecutionState | null;
  isLoading?: boolean;
}

export function ExecutionTab({ execution, isLoading }: ExecutionTabProps) {
  if (isLoading || !execution) {
    return (
      <div className="text-white/60">
        <h3 className="text-xl font-bold text-white mb-4">Execution Quality</h3>
        <div>Loading execution data...</div>
      </div>
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
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-white mb-4">Execution Quality</h3>

      {/* Overall Health */}
      <GlassCard>
        <div className="flex items-center justify-between mb-4">
          <div className="text-lg font-bold text-white">Overall Execution Health</div>
          <StatusBadge status={health.label} color={health.color} />
        </div>
        <div className="text-sm text-white/70">{execution.symbol}</div>
      </GlassCard>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Spread */}
        <GlassCard padding="sm">
          <div className="text-sm text-white/70 mb-2">Spread</div>
          <div className="text-2xl font-bold text-white mb-2">{execution.spreadBps.toFixed(2)} bps</div>
          {execution.spreadWidening && (
            <StatusBadge status="Widening" color="yellow" />
          )}
          <div className="mt-2 text-xs text-white/60">
            {execution.spreadBps < 2 ? 'Excellent' : execution.spreadBps < 5 ? 'Good' : 'Poor'}
          </div>
        </GlassCard>

        {/* API Latency */}
        <GlassCard padding="sm">
          <div className="text-sm text-white/70 mb-2">API Latency</div>
          <div className="text-2xl font-bold text-white mb-2">{execution.apiLatencyMs.toFixed(0)} ms</div>
          <div className="mt-2 text-xs text-white/60">
            {execution.apiLatencyMs < 50 ? 'Excellent' : execution.apiLatencyMs < 100 ? 'Good' : 'Slow'}
          </div>
        </GlassCard>

        {/* Slippage Estimate */}
        <GlassCard padding="sm">
          <div className="text-sm text-white/70 mb-2">Slippage Estimate</div>
          <div className="text-2xl font-bold text-white mb-2">{execution.slippageEstimateBps.toFixed(2)} bps</div>
          <div className="mt-2 text-xs text-white/60">Expected slippage</div>
        </GlassCard>

        {/* Book Depth */}
        <GlassCard padding="sm">
          <div className="text-sm text-white/70 mb-2">Order Book Depth</div>
          <div className="text-2xl font-bold text-white mb-2">
            {execution.bookThin ? 'Thin' : 'Good'}
          </div>
          <StatusBadge
            status={execution.bookThin ? 'Warning' : 'Healthy'}
            color={execution.bookThin ? 'yellow' : 'green'}
          />
        </GlassCard>

        {/* Connection Status */}
        <GlassCard padding="sm">
          <div className="text-sm text-white/70 mb-2">Connection Status</div>
          <div className="text-2xl font-bold text-white mb-2">
            {execution.connectionUnstable ? 'Unstable' : 'Stable'}
          </div>
          <StatusBadge
            status={execution.connectionUnstable ? 'Unstable' : 'Stable'}
            color={execution.connectionUnstable ? 'red' : 'green'}
          />
        </GlassCard>
      </div>

      {/* Execution Risks */}
      {(execution.spreadWidening || execution.bookThin || execution.connectionUnstable) && (
        <GlassCard>
          <div className="text-lg font-bold text-white mb-2">⚠️ Execution Risks</div>
          <ul className="space-y-1 text-sm text-white/70">
            {execution.spreadWidening && <li>• Spread is widening - higher execution costs</li>}
            {execution.bookThin && <li>• Order book is thin - potential slippage</li>}
            {execution.connectionUnstable && <li>• Connection unstable - execution delays possible</li>}
          </ul>
        </GlassCard>
      )}
    </div>
  );
}

