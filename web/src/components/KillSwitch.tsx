import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import { useUIStore } from '@/state/uiStore';
import { AlertTriangle, Power } from 'lucide-react';

export function KillSwitch() {
  const [isLoading, setIsLoading] = useState(false);
  const addToast = useUIStore((state) => state.addToast);

  const handleFlattenAll = async () => {
    const confirmed = confirm(
      '⚠️ KILL SWITCH CONFIRMATION\n\n' +
      'This will immediately flatten ALL open positions and close ALL pending orders.\n\n' +
      'This action CANNOT be undone.\n\n' +
      'Are you absolutely sure you want to proceed?'
    );

    if (!confirmed) {
      return;
    }

    setIsLoading(true);
    try {
      await api.post('/system/flatten_all', { reason: 'manual_kill_switch' });
      addToast({
        type: 'success',
        message: '✓ Kill switch activated - All positions flattened',
      });
    } catch (error: any) {
      addToast({
        type: 'error',
        message: error.response?.data?.detail || '✗ Failed to flatten positions',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="border-red-500/30 bg-red-500/5">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-red-400">
          <Power className="h-5 w-5" />
          Emergency Kill Switch
        </CardTitle>
        <CardDescription className="text-neutral-400">
          Immediately flatten all positions and cancel all orders
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button
          onClick={handleFlattenAll}
          disabled={isLoading}
          variant="danger"
          size="lg"
          className="w-full font-bold"
        >
          <AlertTriangle className="mr-2 h-5 w-5" />
          {isLoading ? 'Flattening All Positions...' : 'Flatten All Positions'}
        </Button>
        <p className="text-xs text-neutral-500 mt-3 text-center">
          Use only in emergency situations. This action cannot be undone.
        </p>
      </CardContent>
    </Card>
  );
}

