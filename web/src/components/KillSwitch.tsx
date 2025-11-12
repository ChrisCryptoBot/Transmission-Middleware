import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { useUIStore } from '@/state/uiStore';
import { AlertTriangle } from 'lucide-react';

export function KillSwitch() {
  const [isLoading, setIsLoading] = useState(false);
  const addToast = useUIStore((state) => state.addToast);

  const handleFlattenAll = async () => {
    if (!confirm('Are you sure you want to flatten all positions? This action cannot be undone.')) {
      return;
    }

    setIsLoading(true);
    try {
      await api.post('/system/flatten_all', { reason: 'manual_ui' });
      addToast({
        type: 'success',
        message: 'All positions flattened successfully',
      });
    } catch (error: any) {
      addToast({
        type: 'error',
        message: error.response?.data?.detail || 'Failed to flatten positions',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button
      onClick={handleFlattenAll}
      disabled={isLoading}
      variant="destructive"
      className="w-full"
    >
      <AlertTriangle className="mr-2 h-4 w-4" />
      {isLoading ? 'Flattening...' : '🔴 Flatten All / Kill Switch'}
    </Button>
  );
}

