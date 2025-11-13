import { useState, useEffect } from 'react';
import { Radio, Gauge, TrendingUp } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { SystemStatusResponse } from '@/lib/types';

interface TransmissionVisualizerProps {
  status: SystemStatusResponse | undefined;
  isLoading?: boolean;
}

type Gear = 'P' | 'R' | 'N' | 'D' | 'L';

const gearMap: Record<Gear, { label: string; strategy: string; color: string }> = {
  P: { label: 'Park', strategy: 'Trading Locked', color: 'from-red-500 to-red-700' },
  R: { label: 'Reverse', strategy: 'Recovery Mode', color: 'from-orange-500 to-orange-700' },
  N: { label: 'Neutral', strategy: 'Standby', color: 'from-gray-400 to-gray-600' },
  D: { label: 'Drive', strategy: 'Normal Trading', color: 'from-emerald-500 to-blue-500' },
  L: { label: 'Low', strategy: 'Risk Downshift', color: 'from-yellow-500 to-yellow-700' },
};

export function TransmissionVisualizer({ status, isLoading }: TransmissionVisualizerProps) {
  const [isShifting, setIsShifting] = useState(false);
  const [rpm, setRpm] = useState(3000);
  const [marketSpeed, setMarketSpeed] = useState(50);

  const currentGear = (status?.gear || 'N') as Gear;
  const currentConfig = gearMap[currentGear];

  // Simulate RPM and speed based on system state
  useEffect(() => {
    if (!status) return;

    // Map daily R to RPM (negative R = lower RPM, positive = higher)
    const baseRpm = 3000;
    const rMultiplier = (status.daily_pnl_r + 2) * 1000; // Scale -2R to +2R range
    setRpm(Math.max(1000, Math.min(7000, baseRpm + rMultiplier)));

    // Map market conditions to speed
    const speedBase = 50;
    const regimeSpeed = status.current_regime === 'TREND' ? 20 : status.current_regime === 'VOLATILE' ? -15 : 0;
    setMarketSpeed(Math.max(20, Math.min(100, speedBase + regimeSpeed)));
  }, [status]);

  // Detect gear shifts
  useEffect(() => {
    if (!status?.gear) return;
    setIsShifting(true);
    const timer = setTimeout(() => setIsShifting(false), 600);
    return () => clearTimeout(timer);
  }, [status?.gear]);

  if (isLoading || !status) {
    return (
      <GlassCard>
        <div className="text-white/60">Loading transmission data...</div>
      </GlassCard>
    );
  }

  return (
    <GlassCard className="relative overflow-hidden">
      <div className="absolute inset-0 opacity-20">
        <div className={`absolute inset-0 bg-gradient-to-br ${currentConfig.color} blur-3xl`} />
      </div>

      <div className="relative">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-bold text-white">System Transmission</h2>
          <div className="flex gap-2">
            {isShifting && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-yellow-500/20 border border-yellow-400/30 text-yellow-100 animate-pulse">
                <Radio className="w-4 h-4" />
                <span className="text-sm font-medium">Shifting...</span>
              </div>
            )}
            <StatusBadge status={`Strategy: ${status.active_strategy || 'N/A'}`} color="blue" />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
          {/* RPM Gauge */}
          <div className="flex flex-col items-center">
            <div className="relative w-48 h-48">
              <svg className="w-full h-full" viewBox="0 0 200 200">
                <circle
                  cx="100"
                  cy="100"
                  r="80"
                  fill="none"
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth="12"
                  strokeDasharray="377"
                  strokeDashoffset="94"
                  transform="rotate(135 100 100)"
                />
                <circle
                  cx="100"
                  cy="100"
                  r="80"
                  fill="none"
                  stroke="url(#rpmGradient)"
                  strokeWidth="12"
                  strokeLinecap="round"
                  strokeDasharray="377"
                  strokeDashoffset={94 + (283 * (1 - rpm / 7000))}
                  transform="rotate(135 100 100)"
                  className="transition-all duration-1000"
                />
                <defs>
                  <linearGradient id="rpmGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#10b981" />
                    <stop offset="50%" stopColor="#fbbf24" />
                    <stop offset="100%" stopColor="#ef4444" />
                  </linearGradient>
                </defs>
              </svg>

              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <Gauge className="w-8 h-8 text-white/60 mb-2" />
                <div className="text-4xl font-bold text-white">{Math.round(rpm / 100) / 10}k</div>
                <div className="text-sm text-white/60 uppercase tracking-wide">RPM</div>
              </div>
            </div>
            <div className="text-center mt-4">
              <div className="text-white/60 text-sm">Market Volatility</div>
            </div>
          </div>

          {/* Gear Indicator with Teeth */}
          <div className="flex flex-col items-center">
            <div
              className={`relative w-64 h-64 transition-all duration-600 ${
                isShifting ? 'scale-110 rotate-12' : 'scale-100 rotate-0'
              }`}
            >
              {/* Outer gear ring */}
              <div className="absolute inset-0 rounded-full border-8 border-white/20 flex items-center justify-center">
                {/* Gear teeth */}
                {[...Array(12)].map((_, i) => (
                  <div
                    key={i}
                    className="absolute w-4 h-8 bg-white/30"
                    style={{
                      transform: `rotate(${i * 30}deg) translateY(-120px)`,
                      transformOrigin: '50% 120px',
                    }}
                  />

                ))}

                {/* Inner gear with gradient */}
                <div
                  className={`w-48 h-48 rounded-full bg-gradient-to-br ${currentConfig.color} flex items-center justify-center shadow-2xl transition-all duration-600`}
                >
                  <div className="text-center">
                    <div className="text-7xl font-black text-white">{currentGear}</div>
                    <div className="text-sm text-white/80 uppercase tracking-widest font-bold mt-2">GEAR</div>
                  </div>
                </div>

                {/* Rotating animation effect */}
                {isShifting && (
                  <div className="absolute inset-0 rounded-full border-4 border-white/50 animate-ping" />
                )}
              </div>
            </div>

            <div className="text-center mt-6">
              <div className={`text-2xl font-bold bg-gradient-to-r ${currentConfig.color} bg-clip-text text-transparent mb-1`}>
                {currentConfig.label}
              </div>
              <div className="text-white/60 text-sm">Current Gear</div>
            </div>
          </div>

          {/* Speed Gauge */}
          <div className="flex flex-col items-center">
            <div className="relative w-48 h-48">
              <svg className="w-full h-full" viewBox="0 0 200 200">
                <circle
                  cx="100"
                  cy="100"
                  r="80"
                  fill="none"
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth="12"
                  strokeDasharray="377"
                  strokeDashoffset="94"
                  transform="rotate(135 100 100)"
                />
                <circle
                  cx="100"
                  cy="100"
                  r="80"
                  fill="none"
                  stroke="url(#speedGradient)"
                  strokeWidth="12"
                  strokeLinecap="round"
                  strokeDasharray="377"
                  strokeDashoffset={94 + (283 * (1 - marketSpeed / 100))}
                  transform="rotate(135 100 100)"
                  className="transition-all duration-1000"
                />
                <defs>
                  <linearGradient id="speedGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="50%" stopColor="#8b5cf6" />
                    <stop offset="100%" stopColor="#ec4899" />
                  </linearGradient>
                </defs>
              </svg>

              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <TrendingUp className="w-8 h-8 text-white/60 mb-2" />
                <div className="text-4xl font-bold text-white">{Math.round(marketSpeed)}</div>
                <div className="text-sm text-white/60 uppercase tracking-wide">Speed</div>
              </div>
            </div>
            <div className="text-center mt-4">
              <div className="text-white/60 text-sm">Market Momentum</div>
            </div>
          </div>
        </div>

        {/* Gear Reference Bar */}
        <div className="mt-8 p-6 rounded-xl bg-white/5 border border-white/10">
          <div className="flex items-center justify-between">
            {(['P', 'R', 'N', 'D', 'L'] as Gear[]).map((gear) => {
              const config = gearMap[gear];
              const isActive = gear === currentGear;
              return (
                <div key={gear} className="text-center flex-1">
                  <div className={`text-2xl font-bold mb-1 ${isActive ? 'text-white' : 'text-white/40'}`}>
                    {gear}
                  </div>
                  <div className="text-xs text-white/60 uppercase">{config.label}</div>
                  <div className={`text-xs font-medium ${
                    gear === 'P' ? 'text-red-400' :
                    gear === 'R' ? 'text-orange-400' :
                    gear === 'N' ? 'text-gray-400' :
                    gear === 'D' ? 'text-emerald-400' :
                    'text-yellow-400'
                  }`}>
                    {config.strategy}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

