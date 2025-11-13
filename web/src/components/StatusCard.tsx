import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SystemStatusResponse } from '@/lib/types';
import { formatR } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

interface StatusCardProps {
  status: SystemStatusResponse | undefined;
  isLoading?: boolean;
}

export function StatusCard({ status, isLoading }: StatusCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-neutral-400 animate-pulse">Loading system status...</div>
        </CardContent>
      </Card>
    );
  }

  if (!status) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-neutral-400">No data available</div>
        </CardContent>
      </Card>
    );
  }

  const stateConfig: Record<string, { color: string; badgeVariant: 'default' | 'secondary' | 'success' | 'destructive' | 'outline' }> = {
    ready: { color: 'text-green-400', badgeVariant: 'success' },
    trading: { color: 'text-blue-400', badgeVariant: 'default' },
    paused: { color: 'text-amber-400', badgeVariant: 'outline' },
    error: { color: 'text-red-400', badgeVariant: 'destructive' },
    initializing: { color: 'text-neutral-400', badgeVariant: 'secondary' },
    analyzing: { color: 'text-indigo-400', badgeVariant: 'default' },
    signal_generated: { color: 'text-purple-400', badgeVariant: 'default' },
  };

  const config = stateConfig[status.system_state] || { color: 'text-neutral-400', badgeVariant: 'secondary' as const };

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* System State Badge */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-neutral-400">State</span>
          <Badge variant={config.badgeVariant} className="font-semibold">
            {status.system_state.replace('_', ' ').toUpperCase()}
          </Badge>
        </div>

        {/* Regime & Strategy */}
        <div className="grid grid-cols-2 gap-4">
          <div className="metric-card">
            <div className="text-xs text-neutral-400 uppercase tracking-wide mb-1">Regime</div>
            <div className="text-lg font-bold text-white">
              {status.current_regime || '—'}
            </div>
          </div>

          <div className="metric-card">
            <div className="text-xs text-neutral-400 uppercase tracking-wide mb-1">Strategy</div>
            <div className="text-lg font-bold text-white">
              {status.active_strategy || '—'}
            </div>
          </div>
        </div>

        {/* Trading Status */}
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="flex items-center justify-between">
            <span className="text-sm text-neutral-400">Trading Enabled</span>
            <span className={`text-lg font-bold ${status.can_trade ? 'text-green-400' : 'text-red-400'}`}>
              {status.can_trade ? '✓ Yes' : '✗ No'}
            </span>
          </div>
          {!status.can_trade && (
            <div className="text-xs text-neutral-400 mt-2 pt-2 border-t border-white/10">
              {status.risk_reason}
            </div>
          )}
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-2 gap-3">
          <div className="metric-card">
            <div className="text-xs text-neutral-400 uppercase tracking-wide mb-1">Daily P&L</div>
            <div className={`text-xl font-bold ${status.daily_pnl_r >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {formatR(status.daily_pnl_r)}
            </div>
          </div>

          <div className="metric-card">
            <div className="text-xs text-neutral-400 uppercase tracking-wide mb-1">Weekly P&L</div>
            <div className={`text-xl font-bold ${status.weekly_pnl_r >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {formatR(status.weekly_pnl_r)}
            </div>
          </div>

          <div className="metric-card">
            <div className="text-xs text-neutral-400 uppercase tracking-wide mb-1">Current R</div>
            <div className="text-xl font-bold text-white">
              {formatR(status.current_r)}
            </div>
          </div>

          <div className="metric-card">
            <div className="text-xs text-neutral-400 uppercase tracking-wide mb-1">Red Days</div>
            <div className={`text-xl font-bold ${status.consecutive_red_days > 0 ? 'text-amber-400' : 'text-white'}`}>
              {status.consecutive_red_days}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

