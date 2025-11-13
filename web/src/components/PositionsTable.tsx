import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Position } from '@/lib/types';
import { formatNumber, formatR } from '@/lib/utils';

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
          <div className="text-muted-foreground">Loading...</div>
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
          <div className="text-muted-foreground">No active positions</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active Positions ({positions.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Symbol</TableHead>
              <TableHead>Quantity</TableHead>
              <TableHead>Avg Price</TableHead>
              <TableHead>Unrealized P&L</TableHead>
              <TableHead>Unrealized P&L (R)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {positions.map((position, index) => (
              <TableRow key={`${position.symbol}-${index}`}>
                <TableCell className="font-medium">{position.symbol}</TableCell>
                <TableCell>{formatNumber(position.quantity || position.contracts, 0)}</TableCell>
                <TableCell>{formatNumber(position.avg_price || position.entry_price, 2)}</TableCell>
                <TableCell className={(position.unrealized_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}>
                  {formatNumber(position.unrealized_pnl || 0, 2)}
                </TableCell>
                <TableCell className={(position.unrealized_pnl_r || 0) >= 0 ? 'text-green-600' : 'text-red-600'}>
                  {formatR(position.unrealized_pnl_r || 0)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

