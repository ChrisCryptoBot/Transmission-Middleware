/**
 * Educational Tooltip - For Beginner Mode
 * Shows explanations for each metric
 */

import { Info } from 'lucide-react';
import { Tooltip } from './Tooltip';

interface EducationalTooltipProps {
  metric: string;
  explanation: string;
  showInBeginnerMode?: boolean;
  isBeginnerMode: boolean;
}

const explanations: Record<string, string> = {
  'VEGUS Score': 'Overall trading environment quality (0-100). Higher = better conditions for trading.',
  'Gear': 'Transmission gear represents trading aggressiveness. P=Park (no trading), R=Reverse (defensive), N=Neutral, D=Drive (active), L=Low (cautious).',
  'Regime': 'Market condition: TREND (directional), RANGE (sideways), VOLATILE (choppy).',
  'R': 'Risk unit. 1R = your stop loss distance × position size. All P&L measured in R multiples.',
  'Daily R': 'Total risk used today in R units. Limit typically 2R per day.',
  'Weekly R': 'Total risk used this week in R units. Limit typically 5R per week.',
  'Drawdown': 'Current loss from peak equity. High drawdown = reduce risk.',
  'Strategy Odds': 'Probability each strategy will succeed in current market conditions.',
  'Transmission': 'Visual representation of trading system state. RPM=volatility, Speed=trend, Torque=momentum.',
  'Execution Health': 'Quality of order fills. Good = tight spreads, fast fills, low slippage.',
  'Risk Temperature': 'Overall risk level. Green=safe, Yellow=moderate, Red=dangerous.',
  'Bias': 'Market direction preference. Bullish=up, Bearish=down, Neutral=sideways.',
  'HTF': 'Higher Timeframe. Longer-term trend context (4h, daily, weekly).',
  'LTF': 'Lower Timeframe. Shorter-term trend (1m, 5m, 15m).',
  'Liquidity': 'Ease of entering/exiting positions. High liquidity = tight spreads, deep order book.',
  'Slippage': 'Difference between expected and actual fill price. Lower is better.',
  'Edge': 'Statistical advantage. Higher edge = better expected returns.',
  'Decay': 'Strategy losing effectiveness. May need adjustment or pause.',
};

export function EducationalTooltip({
  metric,
  explanation,
  showInBeginnerMode = true,
  isBeginnerMode,
}: EducationalTooltipProps) {
  if (!isBeginnerMode || !showInBeginnerMode) return null;

  const tooltipText = explanations[metric] || explanation;

  return (
    <Tooltip
      content={
        <div>
          <div className="font-bold mb-1">{metric}</div>
          <div className="text-sm">{tooltipText}</div>
        </div>
      }
    >
      <button className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-blue-500/20 hover:bg-blue-500/30 border border-blue-400/30 transition-colors">
        <Info className="w-3 h-3 text-blue-400" />
      </button>
    </Tooltip>
  );
}

