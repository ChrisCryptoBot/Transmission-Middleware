import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { TradeResponse } from '@/lib/types';
import { formatNumber, formatR, formatDateTime } from '@/lib/utils';
import { PerformanceCharts } from '@/components/PerformanceCharts';

export default function Trades() {
  const { data, isLoading } = useQuery({
    queryKey: ['trades'],
    queryFn: async () => (await api.get('/trades?limit=50')).data,
    refetchInterval: 5000,
  });

  const trades: TradeResponse[] = data?.trades || [];

  if (isLoading) {
    return (
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle>Trade History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-muted-foreground">Loading...</div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Performance Charts Section */}
      <PerformanceCharts />

      {/* Trade History Table */}
      <Card>
        <CardHeader>
          <CardTitle>Trade History ({data?.total || 0} total)</CardTitle>
        </CardHeader>
        <CardContent>
          {trades.length === 0 ? (
            <div className="text-muted-foreground">No trades found</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Time</TableHead>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Strategy</TableHead>
                  <TableHead>Entry</TableHead>
                  <TableHead>Exit</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Result</TableHead>
                  <TableHead>P&L (R)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trades.map((trade) => (
                  <TableRow key={trade.trade_id}>
                    <TableCell className="font-mono text-xs">{trade.trade_id}</TableCell>
                    <TableCell className="text-xs">{trade.timestamp_entry ? formatDateTime(trade.timestamp_entry) : formatDateTime(trade.entry_time)}</TableCell>
                    <TableCell>{trade.symbol}</TableCell>
                    <TableCell>
                      <span className={(trade.trade_type || trade.direction) === 'LONG' ? 'text-green-600' : 'text-red-600'}>
                        {trade.trade_type || trade.direction}
                      </span>
                    </TableCell>
                    <TableCell>{trade.strategy_used || '-'}</TableCell>
                    <TableCell>{formatNumber(trade.entry_price)}</TableCell>
                    <TableCell>{trade.exit_price ? formatNumber(trade.exit_price) : '—'}</TableCell>
                    <TableCell>{trade.position_size || trade.contracts}</TableCell>
                    <TableCell>
                      {trade.win_loss && (
                        <span className={`px-2 py-1 rounded text-xs ${
                          trade.win_loss === 'Win' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {trade.win_loss}
                        </span>
                      )}
                    </TableCell>
                    <TableCell className={(trade.result_r || trade.pnl_r || 0) >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {trade.result_r ? formatR(trade.result_r) : trade.pnl_r ? formatR(trade.pnl_r) : '—'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

