import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
// Position type - defined inline since backend response may vary
interface Position {
  position_id: string;
  symbol: string;
  side: 'long' | 'short';
  size: number;
  entry_price: number;
  current_price?: number;
  unrealized_pnl?: number;
  unrealized_pnl_r?: number;
}
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
                <TableCell>{formatNumber(position.size)}</TableCell>
                <TableCell>{formatNumber(position.entry_price)}</TableCell>
                <TableCell className={(position.unrealized_pnl ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}>
                  {position.unrealized_pnl !== undefined ? formatNumber(position.unrealized_pnl) : '—'}
                </TableCell>
                <TableCell className={(position.unrealized_pnl_r ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}>
                  {position.unrealized_pnl_r !== undefined ? formatR(position.unrealized_pnl_r) : '—'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

