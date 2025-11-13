/**
 * Odds Timeline - Chart showing how strategy odds changed over time
 */

import { GlassCard } from './ui/GlassCard';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface OddsDataPoint {
  timestamp: string;
  meanReversion: number;
  momentum: number;
  breakout: number;
  scalping: number;
  range: number;
  trend: number;
}

interface OddsTimelineProps {
  data: OddsDataPoint[];
  isLoading?: boolean;
}

export function OddsTimeline({ data, isLoading }: OddsTimelineProps) {
  if (isLoading || !data || data.length === 0) {
    return (
      <GlassCard>
        <div className="text-white/60">Loading odds timeline...</div>
      </GlassCard>
    );
  }

  const chartData = data.map((point) => ({
    time: new Date(point.timestamp).toLocaleTimeString(),
    'Mean Reversion': point.meanReversion,
    'Momentum': point.momentum,
    'Breakout': point.breakout,
    'Scalping': point.scalping,
    'Range': point.range,
    'Trend': point.trend,
  }));

  return (
    <GlassCard>
      <div className="mb-4">
        <h3 className="text-lg font-bold text-white">Strategy Odds Timeline (24h)</h3>
        <div className="text-sm text-white/60">How odds changed over time</div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <XAxis dataKey="time" stroke="#fff" opacity={0.5} />
          <YAxis stroke="#fff" opacity={0.5} domain={[0, 100]} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '12px',
              backdropFilter: 'blur(10px)',
            }}
          />
          <Legend />
          <Line type="monotone" dataKey="Mean Reversion" stroke="#ef4444" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="Momentum" stroke="#3b82f6" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="Breakout" stroke="#10b981" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="Scalping" stroke="#f59e0b" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="Range" stroke="#8b5cf6" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="Trend" stroke="#ec4899" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}

