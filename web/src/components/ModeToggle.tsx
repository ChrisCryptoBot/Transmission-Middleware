/**
 * Mode Toggle - Beginner/Advanced, Manual/Assisted/Auto
 */

import { GlassCard } from './ui/GlassCard';
import { Settings, User, Bot } from 'lucide-react';

export type UserMode = 'manual' | 'assisted' | 'auto';
export type ComplexityMode = 'beginner' | 'advanced';

interface ModeToggleProps {
  userMode: UserMode;
  complexityMode: ComplexityMode;
  onUserModeChange: (mode: UserMode) => void;
  onComplexityModeChange: (mode: ComplexityMode) => void;
}

export function ModeToggle({
  userMode,
  complexityMode,
  onUserModeChange,
  onComplexityModeChange,
}: ModeToggleProps) {
  return (
    <GlassCard padding="sm">
      <div className="flex items-center justify-between gap-4">
        {/* User Mode */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-white/70">Mode:</span>
          <div className="flex gap-1">
            <button
              onClick={() => onUserModeChange('manual')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                userMode === 'manual'
                  ? 'bg-purple-500/80 text-white'
                  : 'bg-white/10 text-white/60 hover:bg-white/20'
              }`}
              title="Manual - You execute trades yourself"
            >
              <User className="w-3 h-3 inline mr-1" />
              Manual
            </button>
            <button
              onClick={() => onUserModeChange('assisted')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                userMode === 'assisted'
                  ? 'bg-purple-500/80 text-white'
                  : 'bg-white/10 text-white/60 hover:bg-white/20'
              }`}
              title="Assisted - VEGUS proposes, you confirm"
            >
              Assisted
            </button>
            <button
              onClick={() => onUserModeChange('auto')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                userMode === 'auto'
                  ? 'bg-purple-500/80 text-white'
                  : 'bg-white/10 text-white/60 hover:bg-white/20'
              }`}
              title="Auto - Fully automated trading"
            >
              <Bot className="w-3 h-3 inline mr-1" />
              Auto
            </button>
          </div>
        </div>

        {/* Complexity Mode */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-white/70">View:</span>
          <div className="flex gap-1">
            <button
              onClick={() => onComplexityModeChange('beginner')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                complexityMode === 'beginner'
                  ? 'bg-blue-500/80 text-white'
                  : 'bg-white/10 text-white/60 hover:bg-white/20'
              }`}
            >
              Beginner
            </button>
            <button
              onClick={() => onComplexityModeChange('advanced')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                complexityMode === 'advanced'
                  ? 'bg-blue-500/80 text-white'
                  : 'bg-white/10 text-white/60 hover:bg-white/20'
              }`}
            >
              <Settings className="w-3 h-3 inline mr-1" />
              Advanced
            </button>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

