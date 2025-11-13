import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Order } from '@/lib/types';
import { formatNumber } from '@/lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';

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
          <div className="text-neutral-400 animate-pulse">Loading orders...</div>
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
          <div className="text-neutral-400 text-center py-8">
            No open orders
          </div>
        </CardContent>
      </Card>
    );
  }

  const getStatusBadgeVariant = (status: string): 'success' | 'warning' | 'secondary' | 'default' => {
    switch (status) {
      case 'FILLED':
        return 'success';
      case 'PARTIALLY_FILLED':
        return 'warning';
      case 'PENDING':
      case 'NEW':
        return 'default';
      default:
        return 'secondary';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Open Orders ({orders.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-neutral-400">Order ID</TableHead>
                <TableHead className="text-neutral-400">Symbol</TableHead>
                <TableHead className="text-neutral-400">Side</TableHead>
                <TableHead className="text-neutral-400 text-right">Quantity</TableHead>
                <TableHead className="text-neutral-400 text-right">Filled</TableHead>
                <TableHead className="text-neutral-400">Type</TableHead>
                <TableHead className="text-neutral-400">Status</TableHead>
                <TableHead className="text-neutral-400 text-right">Avg Price</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orders.map((order) => (
                <TableRow key={order.order_id} className="hover:bg-white/5">
                  <TableCell className="font-mono text-xs text-neutral-300">
                    {order.order_id.slice(0, 8)}...
                  </TableCell>
                  <TableCell className="font-semibold text-white">
                    {order.symbol}
                  </TableCell>
                  <TableCell>
                    <span className={`flex items-center gap-1 font-semibold ${
                      order.side === 'LONG' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {order.side === 'LONG' ? (
                        <TrendingUp className="h-3 w-3" />
                      ) : (
                        <TrendingDown className="h-3 w-3" />
                      )}
                      {order.side}
                    </span>
                  </TableCell>
                  <TableCell className="text-right text-white">
                    {formatNumber(order.quantity || order.contracts, 0)}
                  </TableCell>
                  <TableCell className="text-right text-neutral-300">
                    {formatNumber(order.filled_qty || 0, 0)}
                  </TableCell>
                  <TableCell className="text-neutral-300 text-xs uppercase">
                    {order.order_type || 'MARKET'}
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusBadgeVariant(order.status)}>
                      {order.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right text-white font-mono">
                    {order.avg_price ? `$${formatNumber(order.avg_price, 2)}` : '—'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

