/**
 * Bias Compass
 * Shows directional bias (bullish/bearish/neutral) with strength and HTF alignment
 */

import { DirectionalState } from '@/lib/types';
import { GlassCard } from './ui/GlassCard';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

interface BiasCompassProps {
  direction: DirectionalState | null;
  isLoading?: boolean;
}

export function BiasCompass({ direction, isLoading }: BiasCompassProps) {
  if (isLoading || !direction) {
    return (
      <GlassCard className="text-center">
        <div className="text-sm text-white/60 mb-2">Directional Bias</div>
        <div className="text-2xl text-white/40">--</div>
      </GlassCard>
    );
  }

  const getDirectionColor = () => {
    if (direction.direction === 'bullish') return 'text-green-400';
    if (direction.direction === 'bearish') return 'text-red-400';
    return 'text-gray-400';
  };

  const getDirectionIcon = () => {
    if (direction.direction === 'bullish') return <ArrowUp className="w-8 h-8" />;
    if (direction.direction === 'bearish') return <ArrowDown className="w-8 h-8" />;
    return <Minus className="w-8 h-8" />;
  };

  const rotation = direction.direction === 'bullish' ? 0 : direction.direction === 'bearish' ? 180 : 90;

  return (
    <GlassCard className="relative overflow-hidden">
      <div className="text-center">
        <div className="text-sm text-white/60 mb-4">Directional Bias</div>
        
        {/* Compass Circle */}
        <div className="relative w-32 h-32 mx-auto mb-4">
          {/* Outer ring */}
          <div className="absolute inset-0 rounded-full border-4 border-white/20" />
          
          {/* HTF Alignment Ring */}
          <div className="absolute inset-2 rounded-full border-2 border-white/10">
            <div
              className="absolute inset-0 rounded-full border-2 border-blue-400/50"
              style={{
                clipPath: `polygon(50% 50%, 50% 0%, ${50 + (direction.htfAlignment * 50)}% 0%, 50% 50%)`,
              }}
            />
          </div>
          
          {/* Direction Arrow */}
          <div
            className={`absolute inset-0 flex items-center justify-center ${getDirectionColor()}`}
            style={{
              transform: `rotate(${rotation}deg)`,
              transition: 'transform 0.5s ease',
            }}
          >
            {getDirectionIcon()}
          </div>
          
          {/* Center Strength Indicator */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className={`text-2xl font-bold ${getDirectionColor()}`}>
                {Math.round(direction.strength * 100)}%
              </div>
              <div className="text-xs text-white/60 capitalize">{direction.direction}</div>
            </div>
          </div>
        </div>

        {/* Strength Bar */}
        <div className="mb-2">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-white/60">Strength</span>
            <span className="text-xs text-white/70">{Math.round(direction.strength * 100)}%</span>
          </div>
          <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full ${getDirectionColor().replace('text-', 'bg-')} transition-all duration-500`}
              style={{ width: `${direction.strength * 100}%` }}
            />
          </div>
        </div>

        {/* HTF Alignment */}
        <div className="mb-2">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-white/60">HTF Alignment</span>
            <span className="text-xs text-white/70">{Math.round(direction.htfAlignment * 100)}%</span>
          </div>
          <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-500"
              style={{ width: `${direction.htfAlignment * 100}%` }}
            />
          </div>
        </div>

        {/* Momentum Score */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-white/60">Momentum</span>
            <span className="text-xs text-white/70">{Math.round(direction.momentumScore * 100)}%</span>
          </div>
          <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-purple-500 transition-all duration-500"
              style={{ width: `${direction.momentumScore * 100}%` }}
            />
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

