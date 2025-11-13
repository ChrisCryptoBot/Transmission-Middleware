/**
 * VEGUS Score Gauge
 * Displays environment quality score (0-100) with color coding
 */

import { VegusScore } from '@/lib/types';
import { GlassCard } from './ui/GlassCard';

interface VegusScoreGaugeProps {
  score: VegusScore | null;
  isLoading?: boolean;
}

export function VegusScoreGauge({ score, isLoading }: VegusScoreGaugeProps) {
  if (isLoading || !score) {
    return (
      <GlassCard className="text-center">
        <div className="text-sm text-white/60 mb-2">VEGUS Score</div>
        <div className="text-2xl text-white/40">--</div>
        <div className="text-xs text-white/40 mt-1">Loading...</div>
      </GlassCard>
    );
  }

  const getColor = (scoreValue: number) => {
    if (scoreValue <= 30) return 'text-red-400';
    if (scoreValue <= 55) return 'text-yellow-400';
    if (scoreValue <= 75) return 'text-green-400';
    return 'text-emerald-400';
  };

  const getBgColor = (scoreValue: number) => {
    if (scoreValue <= 30) return 'from-red-500/20 to-red-600/20';
    if (scoreValue <= 55) return 'from-yellow-500/20 to-yellow-600/20';
    if (scoreValue <= 75) return 'from-green-500/20 to-green-600/20';
    return 'from-emerald-500/20 to-emerald-600/20';
  };

  const circumference = 2 * Math.PI * 60; // radius = 60
  const offset = circumference - (score.score / 100) * circumference;

  return (
    <GlassCard className="relative overflow-hidden">
      <div className={`absolute inset-0 bg-gradient-to-br ${getBgColor(score.score)} opacity-50`} />
      <div className="relative">
        <div className="text-center mb-4">
          <div className="text-sm text-white/60 mb-2">VEGUS Score</div>
          <div className="relative inline-block">
            <svg className="w-32 h-32 transform -rotate-90">
              <circle
                cx="64"
                cy="64"
                r="60"
                stroke="rgba(255,255,255,0.1)"
                strokeWidth="8"
                fill="none"
              />
              <circle
                cx="64"
                cy="64"
                r="60"
                stroke="currentColor"
                strokeWidth="8"
                fill="none"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                className={getColor(score.score)}
                strokeLinecap="round"
                style={{ transition: 'stroke-dashoffset 0.5s ease' }}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className={`text-3xl font-bold ${getColor(score.score)}`}>
                  {score.score}
                </div>
                <div className="text-xs text-white/60 mt-1">{score.label}</div>
              </div>
            </div>
          </div>
        </div>
        <div className="text-xs text-white/70 text-center px-2">
          {score.explanation}
        </div>
      </div>
    </GlassCard>
  );
}

