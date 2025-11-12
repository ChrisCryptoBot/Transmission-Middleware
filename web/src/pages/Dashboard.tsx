import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useWebSocket } from '@/lib/ws';
import { useUIStore } from '@/state/uiStore';
import { StatusCard } from '@/components/StatusCard';
import { KillSwitch } from '@/components/KillSwitch';
import { OrdersTable } from '@/components/OrdersTable';
import { PositionsTable } from '@/components/PositionsTable';
import { useEffect } from 'react';
import { WSEvent } from '@/lib/types';

export default function Dashboard() {
  const { message, isConnected } = useWebSocket();
  const addWSEvent = useUIStore((state) => state.addWSEvent);
  const addToast = useUIStore((state) => state.addToast);

  // System status
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['system-status'],
    queryFn: async () => (await api.get('/system/status')).data,
    refetchInterval: 2000,
  });

  // Open orders
  const { data: ordersData, isLoading: ordersLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: async () => (await api.get('/system/orders')).data,
    refetchInterval: 3000,
  });

  // Positions
  const { data: positionsData, isLoading: positionsLoading } = useQuery({
    queryKey: ['positions'],
    queryFn: async () => (await api.get('/system/positions')).data,
    refetchInterval: 3000,
  });

  // Handle WebSocket messages
  useEffect(() => {
    if (message) {
      const event = message as WSEvent;
      addWSEvent(event);

      // Show toast notifications for important events
      switch (event.type) {
        case 'constraint_violation':
        case 'guard_reject':
          addToast({
            type: 'warning',
            message: `Signal rejected: ${event.reason || 'Unknown reason'}`,
          });
          break;
        case 'order_submitted':
          addToast({
            type: 'info',
            message: `Order submitted: ${event.order_id}`,
          });
          break;
        case 'fill':
          addToast({
            type: 'success',
            message: `Order filled: ${event.fill?.broker_order_id || 'Unknown'}`,
          });
          break;
        case 'flatten_all':
          addToast({
            type: 'warning',
            message: `All positions flattened: ${event.reason || 'Unknown reason'}`,
          });
          break;
        case 'regime_change':
          addToast({
            type: 'info',
            message: `Regime changed to: ${event.regime}`,
          });
          break;
      }
    }
  }, [message, addWSEvent, addToast]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Beyond Candlesticks</h1>
          <p className="text-muted-foreground">Transmission™ Dashboard</p>
        </div>
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
            isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-600' : 'bg-red-600'}`} />
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <StatusCard status={status} isLoading={statusLoading} />
        </div>
        <div>
          <KillSwitch />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <OrdersTable orders={ordersData?.orders || []} isLoading={ordersLoading} />
        <PositionsTable positions={positionsData?.positions || []} isLoading={positionsLoading} />
      </div>
    </div>
  );
}

export default Dashboard;

