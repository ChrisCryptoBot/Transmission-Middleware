import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Position } from '@/lib/types';
import { formatNumber, formatR } from '@/lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface PositionsTableProps {
  positions: Position[];
  isLoading?: boolean;
}

export function PositionsTable({ positions, isLoading }: PositionsTableProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Active Positions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-neutral-400 animate-pulse">Loading positions...</div>
        </CardContent>
      </Card>
    );
  }

  if (positions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Active Positions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-neutral-400 text-center py-8">
            No active positions
          </div>
        </CardContent>
      </Card>
    );
  }

  const totalUnrealizedPnl = positions.reduce((sum, pos) => sum + (pos.unrealized_pnl || 0), 0);
  const totalUnrealizedPnlR = positions.reduce((sum, pos) => sum + (pos.unrealized_pnl_r || 0), 0);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Active Positions ({positions.length})</CardTitle>
          <div className="flex gap-4 text-sm">
            <div>
              <span className="text-neutral-400">Total P&L: </span>
              <span className={`font-bold ${totalUnrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${formatNumber(totalUnrealizedPnl, 2)}
              </span>
            </div>
            <div>
              <span className="text-neutral-400">Total R: </span>
              <span className={`font-bold ${totalUnrealizedPnlR >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {formatR(totalUnrealizedPnlR)}
              </span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-neutral-400">Symbol</TableHead>
                <TableHead className="text-neutral-400 text-right">Quantity</TableHead>
                <TableHead className="text-neutral-400 text-right">Avg Price</TableHead>
                <TableHead className="text-neutral-400 text-right">Unrealized P&L</TableHead>
                <TableHead className="text-neutral-400 text-right">Unrealized R</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {positions.map((position, index) => {
                const pnl = position.unrealized_pnl || 0;
                const pnlR = position.unrealized_pnl_r || 0;
                const isProfitable = pnl >= 0;

                return (
                  <TableRow key={`${position.symbol}-${index}`} className="hover:bg-white/5">
                    <TableCell className="font-bold text-white">
                      {position.symbol}
                    </TableCell>
                    <TableCell className="text-right text-white">
                      <span className={isProfitable ? 'text-green-400' : 'text-red-400'}>
                        {formatNumber(position.quantity || position.contracts, 0)}
                      </span>
                    </TableCell>
                    <TableCell className="text-right text-neutral-300 font-mono">
                      ${formatNumber(position.avg_price || position.entry_price, 2)}
                    </TableCell>
                    <TableCell className={`text-right font-bold ${isProfitable ? 'text-green-400' : 'text-red-400'}`}>
                      <span className="flex items-center justify-end gap-1">
                        {isProfitable ? (
                          <TrendingUp className="h-3 w-3" />
                        ) : (
                          <TrendingDown className="h-3 w-3" />
                        )}
                        ${formatNumber(pnl, 2)}
                      </span>
                    </TableCell>
                    <TableCell className={`text-right font-bold ${isProfitable ? 'text-green-400' : 'text-red-400'}`}>
                      {formatR(pnlR)}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

