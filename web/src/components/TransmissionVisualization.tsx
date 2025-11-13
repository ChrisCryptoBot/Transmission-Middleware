/**
 * Transmission Visualization - Literal gear/transmission display
 * Shows RPM, Torque, Speed, Temperature, Mode, Shift Timer, Stability
 */

import { GlassCard } from './ui/GlassCard';
import { StatusBadge } from './ui/StatusBadge';
// Icons removed - not used in component

interface TransmissionVisualizationProps {
  currentGear: number; // 1-6
  rpm: number; // ATR percentile (0-100)
  torque: number; // VWAP slope strength (0-100)
  speed: number; // Market velocity (0-100)
  temperature: number; // Risk stress (0-100)
  mode: 'manual' | 'assisted' | 'auto';
  shiftTimer: number; // Seconds until next shift allowed
  stabilityScore: number; // 0-100
  load: number; // Open positions
  fuel: number; // Available capital %
  ecoMode: boolean;
  sportMode: boolean;
  isLoading?: boolean;
}

const gearLabels: Record<number, string> = {
  1: 'Scalp',
  2: 'Mean Reversion',
  3: 'Momentum',
  4: 'Trend / Breakout',
  5: 'Risk-Off',
  6: 'Alpha Harvest',
};

export function TransmissionVisualization({
  currentGear,
  rpm,
  torque,
  speed,
  temperature,
  mode,
  shiftTimer,
  stabilityScore,
  load,
  fuel,
  ecoMode,
  sportMode,
  isLoading,
}: TransmissionVisualizationProps) {
  if (isLoading) {
    return (
      <GlassCard>
        <div className="text-white/60">Loading transmission data...</div>
      </GlassCard>
    );
  }

  const getTemperatureColor = (temp: number) => {
    if (temp < 30) return 'text-green-400';
    if (temp < 60) return 'text-yellow-400';
    if (temp < 80) return 'text-orange-400';
    return 'text-red-400';
  };

  const getStabilityColor = (score: number) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <GlassCard>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Transmission System</h2>
        <div className="flex items-center gap-3">
          <StatusBadge status={`Gear ${currentGear}: ${gearLabels[currentGear]}`} color="blue" />
          <StatusBadge status={mode.toUpperCase()} color={mode === 'auto' ? 'green' : 'yellow'} />
          {ecoMode && <StatusBadge status="ECO" color="green" />}
          {sportMode && <StatusBadge status="SPORT" color="red" />}
        </div>
      </div>

      {/* Main Transmission Display */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Gear Display */}
        <div className="lg:col-span-1">
          <div className="relative w-48 h-48 mx-auto">
            {/* Outer ring with gear teeth */}
            <div className="absolute inset-0 rounded-full border-8 border-white/20 flex items-center justify-center">
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
              <div className="w-36 h-36 rounded-full bg-gradient-to-br from-blue-500 to-purple-700 flex items-center justify-center shadow-2xl">
                <div className="text-center">
                  <div className="text-6xl font-black text-white">{currentGear}</div>
                  <div className="text-xs text-white/80 uppercase tracking-widest font-bold mt-1">
                    {gearLabels[currentGear]}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Gauges */}
        <div className="lg:col-span-2 grid grid-cols-2 gap-4">
          {/* RPM Gauge */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="text-sm text-white/70 mb-2">RPM (Volatility)</div>
            <div className="relative w-32 h-32 mx-auto">
              <svg className="w-32 h-32 transform -rotate-90">
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth="8"
                  fill="none"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={2 * Math.PI * 56}
                  strokeDashoffset={2 * Math.PI * 56 * (1 - rpm / 100)}
                  className="text-blue-400"
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">{rpm.toFixed(0)}</div>
                  <div className="text-xs text-white/60">ATR %ile</div>
                </div>
              </div>
            </div>
          </div>

          {/* Speed Gauge */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="text-sm text-white/70 mb-2">Speed (Velocity)</div>
            <div className="relative w-32 h-32 mx-auto">
              <svg className="w-32 h-32 transform -rotate-90">
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth="8"
                  fill="none"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={2 * Math.PI * 56}
                  strokeDashoffset={2 * Math.PI * 56 * (1 - speed / 100)}
                  className="text-green-400"
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">{speed.toFixed(0)}</div>
                  <div className="text-xs text-white/60">ROC</div>
                </div>
              </div>
            </div>
          </div>

          {/* Torque Gauge */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="text-sm text-white/70 mb-2">Torque (Momentum)</div>
            <div className="relative w-32 h-32 mx-auto">
              <svg className="w-32 h-32 transform -rotate-90">
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth="8"
                  fill="none"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={2 * Math.PI * 56}
                  strokeDashoffset={2 * Math.PI * 56 * (1 - torque / 100)}
                  className="text-purple-400"
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">{torque.toFixed(0)}</div>
                  <div className="text-xs text-white/60">VWAP</div>
                </div>
              </div>
            </div>
          </div>

          {/* Temperature Gauge */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="text-sm text-white/70 mb-2">Temperature (Risk)</div>
            <div className="relative w-32 h-32 mx-auto">
              <svg className="w-32 h-32 transform -rotate-90">
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth="8"
                  fill="none"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={2 * Math.PI * 56}
                  strokeDashoffset={2 * Math.PI * 56 * (1 - temperature / 100)}
                  className={getTemperatureColor(temperature)}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className={`text-2xl font-bold ${getTemperatureColor(temperature)}`}>
                    {temperature.toFixed(0)}
                  </div>
                  <div className="text-xs text-white/60">Stress</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Status Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-3 rounded-xl bg-white/5 border border-white/10">
          <div className="text-xs text-white/60 mb-1">Stability</div>
          <div className={`text-xl font-bold ${getStabilityColor(stabilityScore)}`}>
            {stabilityScore.toFixed(0)}%
          </div>
        </div>
        <div className="p-3 rounded-xl bg-white/5 border border-white/10">
          <div className="text-xs text-white/60 mb-1">Load</div>
          <div className="text-xl font-bold text-white">{load} positions</div>
        </div>
        <div className="p-3 rounded-xl bg-white/5 border border-white/10">
          <div className="text-xs text-white/60 mb-1">Fuel</div>
          <div className="text-xl font-bold text-white">{fuel.toFixed(0)}%</div>
        </div>
        <div className="p-3 rounded-xl bg-white/5 border border-white/10">
          <div className="text-xs text-white/60 mb-1">Shift Timer</div>
          <div className="text-xl font-bold text-white">
            {shiftTimer > 0 ? `${shiftTimer}s` : 'Ready'}
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

