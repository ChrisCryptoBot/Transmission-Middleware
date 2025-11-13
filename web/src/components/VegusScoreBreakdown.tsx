/**
 * VEGUS Score Breakdown
 * Detailed breakdown of score components
 */

import { GlassCard } from './ui/GlassCard';
import { VegusScore } from '@/lib/types';

interface VegusScoreBreakdownProps {
  score: VegusScore | null;
  isLoading?: boolean;
}

export function VegusScoreBreakdown({ score, isLoading }: VegusScoreBreakdownProps) {
  if (isLoading || !score) {
    return (
      <GlassCard>
        <div className="text-white/60">Loading VEGUS score breakdown...</div>
      </GlassCard>
    );
  }

  const components = [
    {
      label: 'Probability of Good Trading Environment',
      value: score.componentBreakdown.marketQuality * 100,
      description: 'Overall market conditions favorability',
    },
    {
      label: 'Edge Availability Score',
      value: (1 - score.componentBreakdown.riskPressure) * 100,
      description: 'How much edge is available in current conditions',
    },
    {
      label: 'Market Fairness Score',
      value: score.componentBreakdown.executionQuality * 100,
      description: 'Market is fair vs. manipulated',
    },
    {
      label: 'Liquidity Health Score',
      value: score.componentBreakdown.executionQuality * 100,
      description: 'Order book depth and execution quality',
    },
    {
      label: 'Volatility Regime Score',
      value: score.componentBreakdown.marketQuality * 100,
      description: 'Volatility is in favorable range',
    },
    {
      label: 'Psychological Safety',
      value: score.componentBreakdown.psychologicalSafety * 100,
      description: 'Mental state and risk pressure',
    },
  ];

  const getColor = (value: number) => {
    if (value >= 75) return 'text-green-400';
    if (value >= 50) return 'text-yellow-400';
    if (value >= 25) return 'text-orange-400';
    return 'text-red-400';
  };

  const getBgColor = (value: number) => {
    if (value >= 75) return 'bg-green-500';
    if (value >= 50) return 'bg-yellow-500';
    if (value >= 25) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <GlassCard>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">VEGUS Score Breakdown</h2>
        <div className="text-sm text-white/70">{score.explanation}</div>
      </div>

      <div className="space-y-4">
        {components.map((component, i) => (
          <div key={i}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex-1">
                <div className="text-sm font-semibold text-white">{component.label}</div>
                <div className="text-xs text-white/60">{component.description}</div>
              </div>
              <div className={`text-xl font-bold ${getColor(component.value)}`}>
                {component.value.toFixed(0)}%
              </div>
            </div>
            <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden">
              <div
                className={`h-full ${getBgColor(component.value)} transition-all duration-500`}
                style={{ width: `${component.value}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Overall Score */}
      <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-400/30">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-white/70 mb-1">Overall VEGUS Score</div>
            <div className="text-3xl font-bold text-white">{score.score}/100</div>
            <div className="text-sm text-white/70 mt-1">{score.label}</div>
          </div>
          <div className={`text-4xl font-black ${getColor(score.score)}`}>
            {score.score}
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

