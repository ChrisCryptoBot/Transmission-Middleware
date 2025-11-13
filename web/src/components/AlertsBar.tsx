/**
 * Alerts & Notifications Bar
 * Shows critical alerts: regime change, gear shift, volatility spike, risk warnings, execution failures
 */

import { GlassCard } from './ui/GlassCard';
import { StatusBadge } from './ui/StatusBadge';
import { AlertTriangle, Zap, TrendingUp, Shield, X } from 'lucide-react';

export interface Alert {
  id: string;
  type: 'regime_change' | 'gear_shift' | 'volatility_spike' | 'risk_warning' | 'execution_failure' | 'info';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  timestamp: Date;
  acknowledged: boolean;
}

interface AlertsBarProps {
  alerts: Alert[];
  onDismiss: (id: string) => void;
  onAcknowledge: (id: string) => void;
}

const alertIcons = {
  regime_change: TrendingUp,
  gear_shift: Zap,
  volatility_spike: AlertTriangle,
  risk_warning: Shield,
  execution_failure: X,
  info: AlertTriangle,
};

const alertColors: Record<Alert['severity'], 'green' | 'yellow' | 'red' | 'blue' | 'purple' | 'gray'> = {
  low: 'blue',
  medium: 'yellow',
  high: 'red',
  critical: 'red',
};

export function AlertsBar({ alerts, onDismiss, onAcknowledge }: AlertsBarProps) {
  const unacknowledgedAlerts = alerts.filter((a) => !a.acknowledged).slice(0, 5);

  if (unacknowledgedAlerts.length === 0) {
    return null;
  }

  return (
    <GlassCard className="mb-4 border-2 border-yellow-400/50">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-yellow-400" />
          <h3 className="text-lg font-bold text-white">Active Alerts</h3>
          <StatusBadge status={`${unacknowledgedAlerts.length}`} color="yellow" />
        </div>
      </div>

      <div className="space-y-2">
        {unacknowledgedAlerts.map((alert) => {
          const Icon = alertIcons[alert.type];
          return (
            <div
              key={alert.id}
              className={`p-3 rounded-lg border ${
                alert.severity === 'critical'
                  ? 'bg-red-500/10 border-red-400/30'
                  : alert.severity === 'high'
                  ? 'bg-orange-500/10 border-orange-400/30'
                  : alert.severity === 'medium'
                  ? 'bg-yellow-500/10 border-yellow-400/30'
                  : 'bg-blue-500/10 border-blue-400/30'
              }`}
            >
              <div className="flex items-start gap-3">
                <Icon className={`w-5 h-5 mt-0.5 ${
                  alert.severity === 'critical' ? 'text-red-400' :
                  alert.severity === 'high' ? 'text-orange-400' :
                  alert.severity === 'medium' ? 'text-yellow-400' : 'text-blue-400'
                }`} />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-white">{alert.title}</span>
                    <StatusBadge
                      status={alert.severity.toUpperCase()}
                      color={alertColors[alert.severity]}
                    />
                  </div>
                  <div className="text-sm text-white/70 mb-1">{alert.message}</div>
                  <div className="text-xs text-white/50">
                    {alert.timestamp.toLocaleTimeString()}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => onAcknowledge(alert.id)}
                    className="px-2 py-1 text-xs rounded bg-white/10 hover:bg-white/20 text-white transition-colors"
                  >
                    Ack
                  </button>
                  <button
                    onClick={() => onDismiss(alert.id)}
                    className="px-2 py-1 text-xs rounded bg-white/10 hover:bg-white/20 text-white transition-colors"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
}

