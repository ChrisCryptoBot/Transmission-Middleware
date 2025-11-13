/**
 * Notification Center
 * Based on UI_Concept.txt section 8.1 - Top Navbar
 */

import { useState } from 'react';
import { Bell, X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';
import { GlassCard } from './ui/GlassCard';

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

interface NotificationCenterProps {
  notifications: Notification[];
  onDismiss: (id: string) => void;
  onMarkAllRead: () => void;
}

const iconMap = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: AlertCircle,
};

const colorMap = {
  info: 'blue',
  success: 'green',
  warning: 'yellow',
  error: 'red',
} as const;

export function NotificationCenter({ notifications, onDismiss, onMarkAllRead }: NotificationCenterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 transition-all duration-200"
      >
        <Bell className="w-5 h-5 text-white" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-bold">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <GlassCard className="absolute top-full mt-2 right-0 z-50 w-80 max-h-96 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <div className="text-lg font-bold text-white">Notifications</div>
              {unreadCount > 0 && (
                <button
                  onClick={onMarkAllRead}
                  className="text-xs text-white/60 hover:text-white transition-colors"
                >
                  Mark all read
                </button>
              )}
            </div>

            {notifications.length === 0 ? (
              <div className="text-center text-white/60 py-8">No notifications</div>
            ) : (
              <div className="space-y-2">
                {notifications.map((notification) => {
                  const Icon = iconMap[notification.type];
                  return (
                    <div
                      key={notification.id}
                      className={`p-3 rounded-lg border ${
                        notification.read
                          ? 'bg-white/5 border-white/10'
                          : 'bg-white/10 border-white/20'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <Icon className={`w-5 h-5 mt-0.5 text-${colorMap[notification.type]}-400`} />
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <div className="text-sm font-semibold text-white">{notification.title}</div>
                            <button
                              onClick={() => onDismiss(notification.id)}
                              className="text-white/40 hover:text-white transition-colors"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                          <div className="text-xs text-white/70 mb-1">{notification.message}</div>
                          <div className="text-xs text-white/50">
                            {notification.timestamp.toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </GlassCard>
        </>
      )}
    </div>
  );
}

