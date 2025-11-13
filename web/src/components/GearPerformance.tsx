import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import { GearPerformanceResponse } from '@/lib/types';

type Gear = 'P' | 'R' | 'N' | 'D' | 'L';

const gearLabels: Record<Gear, string> = {
  P: 'PARK',
  R: 'REVERSE',
  N: 'NEUTRAL',
  D: 'DRIVE',
  L: 'LOW',
};

const gearColors: Record<Gear, { text: string; bg: string; border: string }> = {
  P: { text: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' },
  R: { text: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' },
  N: { text: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200' },
  D: { text: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' },
  L: { text: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200' },
};

export function GearPerformance() {
  const { data: performance, isLoading } = useQuery<GearPerformanceResponse[]>({
    queryKey: ['gear-performance'],
    queryFn: async () => (await api.get('/system/gear/performance')).data,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance by Gear</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  if (!performance || performance.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance by Gear</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground">No performance data available</div>
        </CardContent>
      </Card>
    );
  }

  // Create a map for quick lookup
  const performanceMap = new Map<Gear, GearPerformanceResponse>();
  performance.forEach((p) => {
    performanceMap.set(p.gear, p);
  });

  // Order: D, L, R, N, P (most relevant first)
  const gearOrder: Gear[] = ['D', 'L', 'R', 'N', 'P'];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Performance by Gear</CardTitle>
        <p className="text-sm text-muted-foreground">
          Trading performance metrics for each transmission gear state
        </p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {gearOrder.map((gear) => {
            const perf = performanceMap.get(gear);
            const colors = gearColors[gear];

            if (!perf) {
              return (
                <Card key={gear} className={`${colors.bg} ${colors.border}`}>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <div className={`text-2xl font-bold ${colors.text} mb-2`}>
                        {gear}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {gearLabels[gear]}
                      </div>
                      <div className="text-xs text-muted-foreground mt-2">
                        No data
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            }

            const winRate = perf.win_rate ? (perf.win_rate * 100).toFixed(1) : '—';
            const profitFactor = perf.profit_factor ? perf.profit_factor.toFixed(2) : '—';
            const totalR = perf.total_r !== null ? perf.total_r.toFixed(2) : '—';

            return (
              <Card key={gear} className={`${colors.bg} ${colors.border}`}>
                <CardContent className="pt-6">
                  <div className="text-center mb-4">
                    <div className={`text-3xl font-bold ${colors.text} mb-1`}>
                      {gear}
                    </div>
                    <div className="text-sm font-medium">
                      {gearLabels[gear]}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Trades</span>
                      <span className="font-semibold">{perf.trades}</span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Wins / Losses</span>
                      <span className="font-semibold">
                        <span className="text-green-600">{perf.wins}</span>
                        {' / '}
                        <span className="text-red-600">{perf.losses}</span>
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Win Rate</span>
                      <span className={`font-semibold ${
                        perf.win_rate && perf.win_rate >= 0.5 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {winRate}%
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Profit Factor</span>
                      <span className={`font-semibold ${
                        perf.profit_factor && perf.profit_factor >= 1.0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {profitFactor}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Total R</span>
                      <span className={`font-semibold ${
                        perf.total_r && perf.total_r >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {totalR}R
                      </span>
                    </div>

                    {perf.avg_win_r !== null && perf.avg_loss_r !== null && (
                      <div className="pt-2 border-t">
                        <div className="text-xs text-muted-foreground mb-1">Avg Win / Loss</div>
                        <div className="flex justify-between text-sm">
                          <span className="text-green-600">
                            {perf.avg_win_r.toFixed(2)}R
                          </span>
                          <span className="text-red-600">
                            {perf.avg_loss_r.toFixed(2)}R
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

