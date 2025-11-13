/**
 * Price Chart with Overlays
 * Based on UniversalBar[] with gear shading, support/resistance, signals
 */

import { UniversalBar, GearDecision } from '@/lib/types';
import { GlassCard } from './ui/GlassCard';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

interface PriceChartProps {
  bars: UniversalBar[];
  currentGear: GearDecision | null;
  supportLevel?: number;
  resistanceLevel?: number;
  signals?: Array<{ timestamp: string; price: number; type: 'entry' | 'exit'; direction: 'long' | 'short' }>;
  isLoading?: boolean;
}

export function PriceChart({ bars, currentGear, supportLevel, resistanceLevel, signals, isLoading }: PriceChartProps) {
  if (isLoading || !bars || bars.length === 0) {
    return (
      <GlassCard>
        <div className="text-xl font-bold text-white mb-4">Price Chart</div>
        <div className="h-64 flex items-center justify-center text-white/60">
          Loading chart data...
        </div>
      </GlassCard>
    );
  }

  // Transform bars for Recharts
  const chartData = bars.map((bar) => ({
    time: new Date(bar.timestamp).toLocaleTimeString(),
    open: bar.open,
    high: bar.high,
    low: bar.low,
    close: bar.close,
    volume: bar.volume,
    vwap: bar.vwap,
  }));

  const getGearColor = (gear: string | null) => {
    if (!gear) return 'rgba(156, 163, 175, 0.1)';
    const colors: Record<string, string> = {
      P: 'rgba(239, 68, 68, 0.2)',
      R: 'rgba(234, 179, 8, 0.2)',
      N: 'rgba(156, 163, 175, 0.2)',
      D: 'rgba(34, 197, 94, 0.2)',
      L: 'rgba(59, 130, 246, 0.2)',
    };
    return colors[gear] || 'rgba(156, 163, 175, 0.1)';
  };

  return (
    <GlassCard>
      <div className="text-xl font-bold text-white mb-4">Price Chart</div>
      
      <div className="relative">
        {/* Gear Background Shading */}
        {currentGear && (
          <div
            className="absolute inset-0 pointer-events-none z-0"
            style={{
              background: `linear-gradient(to right, ${getGearColor(currentGear.gear as string)} 0%, transparent 100%)`,
            }}
          />
        )}

        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <XAxis dataKey="time" stroke="#fff" opacity={0.5} />
            <YAxis stroke="#fff" opacity={0.5} domain={['dataMin', 'dataMax']} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '12px',
                backdropFilter: 'blur(10px)',
              }}
            />
            
            {/* Support Level */}
            {supportLevel && (
              <ReferenceLine
                y={supportLevel}
                stroke="#10b981"
                strokeDasharray="5 5"
                label={{ value: 'Support', position: 'right', fill: '#10b981' }}
              />
            )}
            
            {/* Resistance Level */}
            {resistanceLevel && (
              <ReferenceLine
                y={resistanceLevel}
                stroke="#ef4444"
                strokeDasharray="5 5"
                label={{ value: 'Resistance', position: 'right', fill: '#ef4444' }}
              />
            )}
            
            {/* Price Line */}
            <Line
              type="monotone"
              dataKey="close"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
            
            {/* VWAP Line */}
            {bars[0]?.vwap && (
              <Line
                type="monotone"
                dataKey="vwap"
                stroke="#a855f7"
                strokeWidth={1.5}
                strokeDasharray="3 3"
                dot={false}
              />
            )}
          </LineChart>
        </ResponsiveContainer>

        {/* Signals Overlay */}
        {signals && signals.length > 0 && (
          <div className="absolute top-4 right-4 space-y-1">
            {signals.map((signal, i) => (
              <div
                key={i}
                className={`text-xs px-2 py-1 rounded ${
                  signal.type === 'entry'
                    ? signal.direction === 'long'
                      ? 'bg-green-500/80 text-white'
                      : 'bg-red-500/80 text-white'
                    : 'bg-gray-500/80 text-white'
                }`}
              >
                {signal.type === 'entry' ? (signal.direction === 'long' ? '↑ Entry' : '↓ Entry') : 'Exit'}
              </div>
            ))}
          </div>
        )}
      </div>
    </GlassCard>
  );
}

