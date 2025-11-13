import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
// Order type - defined inline since backend response may vary
interface Order {
  order_id: string;
  symbol: string;
  side: 'buy' | 'sell' | 'BUY' | 'SELL';
  order_type?: string;
  quantity: number;
  filled_qty?: number;
  price?: number;
  avg_price?: number;
  status: string;
  timestamp: string;
}
import { formatNumber } from '@/lib/utils';

interface OrdersTableProps {
  orders: Order[];
  isLoading?: boolean;
}

export function OrdersTable({ orders, isLoading }: OrdersTableProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Open Orders</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  if (orders.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Open Orders</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground">No open orders</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Open Orders ({orders.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Order ID</TableHead>
              <TableHead>Symbol</TableHead>
              <TableHead>Side</TableHead>
              <TableHead>Quantity</TableHead>
              <TableHead>Filled</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Avg Price</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {orders.map((order) => (
              <TableRow key={order.order_id}>
                <TableCell className="font-mono text-xs">{order.order_id}</TableCell>
                <TableCell>{order.symbol}</TableCell>
                <TableCell>
                  <span className={order.side === 'BUY' ? 'text-green-600' : 'text-red-600'}>
                    {order.side}
                  </span>
                </TableCell>
                <TableCell>{formatNumber(order.quantity)}</TableCell>
                <TableCell>{order.filled_qty !== undefined ? formatNumber(order.filled_qty) : '—'}</TableCell>
                <TableCell>{order.order_type}</TableCell>
                <TableCell>
                  <span className={`px-2 py-1 rounded text-xs ${
                    order.status === 'FILLED' ? 'bg-green-100 text-green-800' :
                    order.status === 'PARTIALLY_FILLED' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {order.status}
                  </span>
                </TableCell>
                <TableCell>{order.avg_price ? formatNumber(order.avg_price) : '—'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

