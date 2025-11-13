/**
 * Bot Status Panel - For Automated Mode
 * Shows bot status, positions, kill switch
 */

import { GlassCard } from './ui/GlassCard';
import { StatusBadge } from './ui/StatusBadge';
import { Play, Pause, AlertTriangle, Power } from 'lucide-react';

interface BotStatusPanelProps {
  isRunning: boolean;
  positions: Array<{ symbol: string; direction: string; size: number; pnl: number }>;
  onToggle: () => void;
  onKillSwitch: () => void;
}

export function BotStatusPanel({ isRunning, positions, onToggle, onKillSwitch }: BotStatusPanelProps) {
  return (
    <GlassCard>
      <div className="text-lg font-bold text-white mb-4 flex items-center justify-between">
        <span>Bot Status</span>
        <StatusBadge
          status={isRunning ? 'Running' : 'Paused'}
          color={isRunning ? 'green' : 'yellow'}
        />
      </div>

      {/* Controls */}
      <div className="flex gap-3 mb-4">
        <button
          onClick={onToggle}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-xl font-semibold transition-all duration-200 ${
            isRunning
              ? 'bg-yellow-500/80 hover:bg-yellow-500 text-white'
              : 'bg-green-500/80 hover:bg-green-500 text-white'
          }`}
        >
          {isRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          {isRunning ? 'Pause' : 'Start'}
        </button>
        <button
          onClick={onKillSwitch}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-red-500/80 hover:bg-red-500 text-white font-semibold transition-all duration-200"
        >
          <Power className="w-4 h-4" />
          Kill Switch
        </button>
      </div>

      {/* Current Positions */}
      <div className="mb-4">
        <div className="text-sm font-bold text-white mb-2">Current Positions ({positions.length})</div>
        {positions.length > 0 ? (
          <div className="space-y-2">
            {positions.map((pos, i) => (
              <div key={i} className="flex items-center justify-between p-2 rounded bg-white/5">
                <div>
                  <span className="text-white font-medium">{pos.symbol}</span>
                  <span className={`ml-2 text-sm ${pos.direction === 'long' ? 'text-green-400' : 'text-red-400'}`}>
                    {pos.direction.toUpperCase()}
                  </span>
                </div>
                <div className="text-sm text-white/70">
                  {pos.size} @ {pos.pnl > 0 ? '+' : ''}${pos.pnl.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-white/60">No open positions</div>
        )}
      </div>

      {/* Warning */}
      {isRunning && positions.length > 0 && (
        <div className="flex items-center gap-2 text-yellow-400 text-sm">
          <AlertTriangle className="w-4 h-4" />
          <span>Bot is actively trading - monitor positions</span>
        </div>
      )}
    </GlassCard>
  );
}

