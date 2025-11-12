import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SystemStatusResponse } from '@/lib/types';
import { formatR } from '@/lib/utils';

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
          <div className="text-muted-foreground">Loading...</div>
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
          <div className="text-muted-foreground">No data available</div>
        </CardContent>
      </Card>
    );
  }

  const stateColors: Record<string, string> = {
    ready: 'text-green-600',
    trading: 'text-blue-600',
    paused: 'text-yellow-600',
    error: 'text-red-600',
    initializing: 'text-gray-600',
    analyzing: 'text-blue-600',
    signal_generated: 'text-purple-600',
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="text-sm text-muted-foreground">State</div>
          <div className={`text-xl font-medium ${stateColors[status.system_state] || ''}`}>
            {status.system_state.toUpperCase()}
          </div>
        </div>
        
        <div>
          <div className="text-sm text-muted-foreground">Regime</div>
          <div className="text-xl font-medium">
            {status.current_regime || '—'}
          </div>
        </div>
        
        <div>
          <div className="text-sm text-muted-foreground">Strategy</div>
          <div className="text-xl font-medium">
            {status.active_strategy || '—'}
          </div>
        </div>
        
        <div>
          <div className="text-sm text-muted-foreground">Can Trade</div>
          <div className={`text-xl font-medium ${status.can_trade ? 'text-green-600' : 'text-red-600'}`}>
            {status.can_trade ? 'Yes' : 'No'}
          </div>
          {!status.can_trade && (
            <div className="text-sm text-muted-foreground mt-1">
              {status.risk_reason}
            </div>
          )}
        </div>
        
        <div className="grid grid-cols-2 gap-4 pt-2 border-t">
          <div>
            <div className="text-sm text-muted-foreground">Daily P&L</div>
            <div className={`text-lg font-medium ${status.daily_pnl_r >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatR(status.daily_pnl_r)}
            </div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Weekly P&L</div>
            <div className={`text-lg font-medium ${status.weekly_pnl_r >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatR(status.weekly_pnl_r)}
            </div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Current R</div>
            <div className="text-lg font-medium">
              {formatR(status.current_r)}
            </div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Red Days</div>
            <div className="text-lg font-medium">
              {status.consecutive_red_days}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

