/**
 * Transmission Gear Dial
 * Displays current gear (P/R/N/D/L) with direction and confidence
 */

import { GearDecision } from '@/lib/types';
import { GlassCard } from './ui/GlassCard';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

interface TransmissionGearDialProps {
  gear: GearDecision | null;
  isLoading?: boolean;
}

const gearColors: Record<string, string> = {
  P: 'from-red-500 to-red-700',
  R: 'from-yellow-500 to-yellow-700',
  N: 'from-gray-400 to-gray-600',
  D: 'from-green-500 to-green-700',
  L: 'from-blue-500 to-blue-700',
};

const gearGlows: Record<string, string> = {
  P: 'gear-glow-park',
  R: 'gear-glow-reverse',
  N: 'gear-glow-neutral',
  D: 'gear-glow-drive',
  L: 'gear-glow-low',
};

export function TransmissionGearDial({ gear, isLoading }: TransmissionGearDialProps) {
  if (isLoading || !gear) {
    return (
      <GlassCard className="text-center">
        <div className="text-sm text-white/60 mb-2">Transmission</div>
        <div className="text-4xl text-white/40">--</div>
        <div className="text-xs text-white/40 mt-1">Loading...</div>
      </GlassCard>
    );
  }

  const gearKey = typeof gear.gear === 'string' ? gear.gear : 'N';
  const gearColor = gearColors[gearKey] || gearColors.N;
  const gearGlow = gearGlows[gearKey] || '';

  return (
    <GlassCard className="relative overflow-hidden">
      <div className={`absolute inset-0 bg-gradient-to-br ${gearColor} opacity-20`} />
      <div className="relative">
        <div className="text-center">
          <div className="text-sm text-white/60 mb-4">Transmission Gear</div>
          
          {/* Gear Display */}
          <div className={`relative w-48 h-48 mx-auto mb-4 ${gearGlow} transition-all duration-600`}>
            {/* Outer ring */}
            <div className="absolute inset-0 rounded-full border-8 border-white/20 flex items-center justify-center">
              {/* Gear teeth */}
              {[...Array(12)].map((_, i) => (
                <div
                  key={i}
                  className="absolute w-4 h-8 bg-white/30"
                  style={{
                    transform: `rotate(${i * 30}deg) translateY(-88px)`,
                    transformOrigin: '50% 88px',
                  }}
                />
              ))}
              
              {/* Inner gear */}
              <div className={`w-36 h-36 rounded-full bg-gradient-to-br ${gearColor} flex items-center justify-center shadow-2xl`}>
                <div className="text-center">
                  <div className="text-6xl font-black text-white">{gearKey}</div>
                  <div className="text-xs text-white/80 uppercase tracking-widest font-bold mt-1">
                    GEAR
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Direction Indicator */}
          <div className="flex items-center justify-center gap-2 mb-2">
            {gear.direction === 'bullish' && <ArrowUp className="w-5 h-5 text-green-400" />}
            {gear.direction === 'bearish' && <ArrowDown className="w-5 h-5 text-red-400" />}
            {gear.direction === 'neutral' && <Minus className="w-5 h-5 text-gray-400" />}
            <span className="text-sm text-white/70 capitalize">{gear.direction}</span>
          </div>

          {/* Confidence Ring */}
          <div className="flex items-center justify-center gap-2 mb-2">
            <div className="text-xs text-white/60">Confidence:</div>
            <div className="w-24 h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                style={{ width: `${gear.confidence * 100}%` }}
              />
            </div>
            <div className="text-xs text-white/60">{Math.round(gear.confidence * 100)}%</div>
          </div>

          {/* Reason Tags */}
          {gear.reasonTags && gear.reasonTags.length > 0 && (
            <div className="flex flex-wrap gap-1 justify-center mt-2">
              {gear.reasonTags.slice(0, 3).map((tag, i) => (
                <span
                  key={i}
                  className="text-xs px-2 py-0.5 rounded-full bg-white/10 text-white/70"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </GlassCard>
  );
}

