import { create } from 'zustand';
import { WSEvent } from '@/lib/types';

interface UIState {
  // WebSocket events
  wsEvents: WSEvent[];
  addWSEvent: (event: WSEvent) => void;
  clearWSEvents: () => void;
  
  // Toast notifications
  toasts: Array<{ id: string; type: 'success' | 'error' | 'warning' | 'info'; message: string }>;
  addToast: (toast: Omit<UIState['toasts'][0], 'id'>) => void;
  removeToast: (id: string) => void;
  
  // UI state
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  wsEvents: [],
  addWSEvent: (event) =>
    set((state) => ({
      wsEvents: [...state.wsEvents.slice(-99), event], // Keep last 100 events
    })),
  clearWSEvents: () => set({ wsEvents: [] }),
  
  toasts: [],
  addToast: (toast) =>
    set((state) => ({
      toasts: [
        ...state.toasts,
        { ...toast, id: Date.now().toString() + Math.random().toString(36).substr(2, 9) },
      ],
    })),
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
  
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));

